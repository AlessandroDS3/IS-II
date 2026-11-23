"""Rutas de evaluación: carga de cartillas, lecturas, validación, cálculo y revisión de resultados."""
from pathlib import Path

from flask import abort, current_app, flash, redirect, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from dominio.evaluacion.identificacion_cartilla import decodificar_lectura
from presentacion.controllers.soporte_web import (ROL_COORDINADOR, Ruta, enviar_imagen_privada, es_carga_por_lotes,
                                                  numero_pagina, pagina, registrar_vistas, seleccionar_examen)

TAMANO_PAGINA = 200
PLANTILLA_CARTILLAS = 'coordinador/cartillas.html'
COORDINADOR = 'COORDINADOR'
POST = ('POST',)


class RutasEvaluacion:
    def __init__(self, app, servicios):
        self.cartillas_servicio = servicios.cartillas
        self.revision = servicios.revision_lecturas
        self.calculo = servicios.calculo
        self.publicacion = servicios.publicacion
        self.raiz_cartillas = Path(app.root_path) / 'datos_privados' / 'cartillas'

    def rutas(self):
        cartillas = (self.cartillas_servicio,)
        revision = (self.revision,)
        return [
            Ruta('/coordinador/cartillas', 'cartillas', self.cartillas, ('GET', 'POST'), COORDINADOR, cartillas),
            Ruta('/coordinador/cartillas/<int:id>/identificar', 'identificar_cartilla', self.identificar_cartilla, POST, COORDINADOR, cartillas),
            Ruta('/coordinador/cargas/<int:id>', 'detalle_carga', self.detalle_carga, rol=COORDINADOR, servicios=cartillas),
            Ruta('/coordinador/cargas/<int:id>/imagen', 'imagen_entrada', self.imagen_entrada, rol=COORDINADOR, servicios=cartillas),
            Ruta('/coordinador/cargas/<int:id>/resolver', 'resolver_carga', self.resolver_carga, POST, COORDINADOR, cartillas),
            Ruta('/coordinador/cartillas/<int:id>/registrar', 'registrar_cartilla', self.registrar_cartilla, POST, COORDINADOR, cartillas),
            Ruta('/coordinador/cartillas/<int:id>/descartar', 'descartar_cartilla', self.descartar_cartilla, POST, COORDINADOR, cartillas),
            Ruta('/coordinador/lecturas', 'lecturas', self.lecturas, rol=COORDINADOR, servicios=revision),
            Ruta('/coordinador/cartillas/<int:id>/imagen', 'imagen_cartilla', self.imagen_cartilla, rol=COORDINADOR, servicios=revision),
            Ruta('/coordinador/lecturas/<int:id>/corregir', 'corregir_lectura', self.corregir_lectura, POST, COORDINADOR, revision),
            Ruta('/coordinador/cartillas/<int:id>/validar', 'validar_cartilla', self.validar_cartilla, POST, COORDINADOR, revision),
            Ruta('/coordinador/resultados', 'resultados_coordinador', self.resultados_coordinador, rol=COORDINADOR,
                 servicios=(self.revision, self.publicacion)),
            Ruta('/coordinador/resultados/<int:id>/detalle', 'detalle_resultado_coordinador', self.detalle_resultado_coordinador,
                 rol=COORDINADOR, servicios=revision),
            Ruta('/coordinador/resultados/<int:id>/revisar', 'revisar_resultado', self.revisar_resultado, POST, COORDINADOR, revision),
            Ruta('/coordinador/resultados/calcular', 'calcular_resultados', self.calcular_resultados, POST, COORDINADOR, (self.calculo,)),
        ]

    # ------------------------------------------------------------------ cargas de cartillas
    def _leer_archivo(self, archivo):
        return archivo.read(self.cartillas_servicio.preparador.MAX_BYTES + 1)

    @staticmethod
    def _volver_cartillas():
        return redirect(url_for('cartillas', examen=request.form.get('examen', ''), pagina=numero_pagina(request.form),
                                estado=request.form.get('estado', '')))

    def _importar_cartillas(self, examen_id):
        if examen_id <= 0:
            raise ValueError('Selecciona un examen.')
        datos = [(Path(archivo.filename.replace('\\', '/')).name, self._leer_archivo(archivo))
                 for archivo in request.files.getlist('archivos') if archivo.filename]
        creadas = self.cartillas_servicio.importar_lote(examen_id, datos, session['usuario_id'])
        if es_carga_por_lotes():
            return {'creadas': creadas}
        flash(f'Se registraron {creadas} páginas nuevas. Las duplicadas se omitieron.', 'ok')
        return redirect(url_for('cartillas', examen=examen_id))

    def _contexto_cartillas(self, examen_id):
        servicio = self.cartillas_servicio
        examenes = servicio.examenes()
        num_pagina = numero_pagina(request.args)
        estado = request.args.get('estado', '')
        filas = servicio.listar(examen_id, num_pagina, estado) if examen_id else []
        resumen = servicio.resumen(examen_id) if examen_id else {}
        estudiantes, versiones = servicio.opciones_identificacion(examen_id) if examen_id else ([], [])
        area_actual = next((e['area'] for e in examenes if e['id_examen'] == examen_id), '')
        entradas = [dict(entrada) for entrada in filas[:TAMANO_PAGINA]]
        for entrada in entradas:
            entrada['lectura'] = decodificar_lectura(entrada['lectura_json'])
            entrada['identificacion'] = servicio.identificar_para_vista(entrada, estudiantes, versiones, area_actual)
        return {'examenes': examenes, 'entradas': entradas, 'examen_id': examen_id, 'estudiantes': estudiantes,
                'versiones': versiones, 'pagina': num_pagina, 'hay_siguiente': len(filas) > TAMANO_PAGINA,
                'estado': estado, 'resumen': resumen, 'area_actual': area_actual}

    def cartillas(self):
        try:
            examen_id = int(request.values.get('examen', '0'))
            if request.method == 'POST':
                return self._importar_cartillas(examen_id)
            contexto = self._contexto_cartillas(examen_id)
        except ValueError as error:
            if es_carga_por_lotes():
                return {'error': str(error)}, 400
            flash(str(error), 'error')
            return redirect(url_for('cartillas'))
        except SQLAlchemyError:
            current_app.logger.exception('Error al gestionar cartillas')
            if es_carga_por_lotes():
                return {'error': 'No se pudo acceder a la base de datos.'}, 503
            flash('No se pudo acceder a las cargas. Comprueba la conexión y la actualización de la base.', 'error')
            return pagina(PLANTILLA_CARTILLAS, ROL_COORDINADOR, examenes=[], entradas=[], examen_id=0), 503
        return pagina(PLANTILLA_CARTILLAS, ROL_COORDINADOR, **contexto)

    def identificar_cartilla(self, id):
        try:
            self.cartillas_servicio.resolver_identificacion(id, request.form.get('estudiante'), request.form.get('version'))
            flash('Identificación guardada. La cartilla todavía está pendiente de registro.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return self._volver_cartillas()

    def _entrada_o_404(self, entrada_id):
        entrada = self.cartillas_servicio.obtener(entrada_id)
        if not entrada:
            abort(404)
        return entrada

    def detalle_carga(self, id):
        entrada = self._entrada_o_404(id)
        return pagina('coordinador/detalle_carga.html', ROL_COORDINADOR, entrada=entrada, historial=self.cartillas_servicio.historial(id))

    def imagen_entrada(self, id):
        entrada = self._entrada_o_404(id)
        historial_id = request.args.get('historial', type=int)
        if historial_id:
            entrada = self.cartillas_servicio.archivo_anterior(id, historial_id)
            if not entrada:
                abort(404)
        return enviar_imagen_privada(entrada['ruta_imagen'], self.raiz_cartillas, entrada['nombre_archivo'])

    def _resolver_entrada(self, id_entrada, accion):
        if accion == 'reintentar':
            self.cartillas_servicio.reintentar_lectura(id_entrada, session['usuario_id'], request.form.get('motivo'))
        elif accion == 'reemplazar':
            archivo = request.files.get('imagen')
            if not archivo or not archivo.filename:
                raise ValueError('Selecciona la imagen de reemplazo.')
            self.cartillas_servicio.reemplazar_imagen(id_entrada, session['usuario_id'], request.form.get('motivo'),
                                                      archivo.filename, self._leer_archivo(archivo))
        else:
            raise ValueError('Acción no válida.')

    def resolver_carga(self, id):
        entrada = self._entrada_o_404(id)
        try:
            self._resolver_entrada(id, request.form.get('accion'))
            flash('Intento registrado. Revisa el nuevo estado y confirma de nuevo la identificación.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo resolver la carga %s', id)
            flash('No se pudo guardar la operación. Comprueba la conexión.', 'error')
        return redirect(url_for('detalle_carga', id=id, examen=entrada['examen_id'], pagina=numero_pagina(request.form),
                                estado=request.form.get('estado', '')))

    def registrar_cartilla(self, id):
        try:
            cartilla_id = self.cartillas_servicio.registrar_cartilla(id, session['usuario_id'], request.form.get('motivo'))
            flash(f'Cartilla {cartilla_id} registrada; las lecturas requieren revisión.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('Error registrando cartilla %s', id)
            flash('No se pudo registrar la cartilla; verifica el examen y su versión.', 'error')
        return self._volver_cartillas()

    def descartar_cartilla(self, id):
        try:
            self.cartillas_servicio.descartar_entrada(id, request.form.get('motivo'))
            flash('Entrada descartada y conservada para consulta.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return self._volver_cartillas()

    # ------------------------------------------------------------------ lecturas y resultados
    def lecturas(self):
        examen = seleccionar_examen()
        return pagina('coordinador/lecturas.html', ROL_COORDINADOR, examenes=self.revision.examenes(), examen=examen,
                      lecturas=self.revision.lecturas(examen) if examen else [],
                      historial=self.revision.historial_lecturas(examen) if examen else [])

    def imagen_cartilla(self, id):
        return enviar_imagen_privada(self.revision.imagen_cartilla(id), self.raiz_cartillas)

    def corregir_lectura(self, id):
        try:
            self.revision.corregir(id, request.form.get('resolucion'), request.form.get('marca'), request.form.get('motivo'), session['usuario_id'])
            flash('Corrección guardada conservando la lectura original.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('Error al guardar la corrección')
            flash('No se pudo guardar la corrección.', 'error')
        return redirect(url_for('lecturas', examen=seleccionar_examen()))

    def validar_cartilla(self, id):
        try:
            self.revision.validar_cartilla(id)
            flash('Cartilla validada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('lecturas', examen=seleccionar_examen()))

    def resultados_coordinador(self):
        examen = seleccionar_examen()
        return pagina('coordinador/resultados_coordinador.html', ROL_COORDINADOR, examenes=self.revision.examenes(), examen=examen,
                      resultados=self.revision.resultados(examen) if examen else [], ranking=self.publicacion.ranking(examen))

    def detalle_resultado_coordinador(self, id):
        examen = seleccionar_examen()
        resultado = self.revision.resultado(examen, id)
        if not resultado:
            abort(404)
        return pagina('coordinador/detalle_resultado_coordinador.html', ROL_COORDINADOR, resultado=resultado, examen=examen,
                      detalle=self.revision.detalle_coordinador(id))

    def revisar_resultado(self, id):
        try:
            self.revision.revisar_resultado(id, session['usuario_id'])
            flash('Resultado marcado como revisado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo revisar el resultado')
            flash('No se pudo revisar: el detalle debe coincidir con los totales.', 'error')
        return redirect(url_for('resultados_coordinador', examen=seleccionar_examen()))

    def calcular_resultados(self):
        examen = seleccionar_examen()
        try:
            cantidad = self.calculo.calcular_resultados(examen, session['usuario_id'])
            flash(f'Se calcularon {cantidad} resultados nuevos; revísalos antes de publicar.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudieron calcular los resultados')
            flash('No se pudo calcular. Comprueba las cartillas, claves y política de puntaje.', 'error')
        return redirect(url_for('resultados_coordinador', examen=examen))


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasEvaluacion(app, servicios).rutas())
