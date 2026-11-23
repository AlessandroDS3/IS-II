"""Rutas de diseño de evaluaciones: simulacros, espacio del examen, configuración y claves."""
from flask import abort, current_app, flash, redirect, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from aplicacion.servicios.diseno_examen_app_service import MAX_BYTES_CSV_CLAVE, respuestas_desde_csv
from presentacion.controllers.soporte_web import (ETAPAS_EXAMEN, ROL_COORDINADOR, Ruta, pagina, registrar_vistas,
                                                  seleccionar_examen)

PREFIJO_PUNTAJE = 'puntaje_'
PREFIJO_RESPUESTA = 'respuesta_'
COORDINADOR = 'COORDINADOR'


def _campos_con_prefijo(formulario, prefijo, omitir_vacios=False):
    return {clave.removeprefix(prefijo): valor for clave, valor in formulario.items()
            if clave.startswith(prefijo) and (not omitir_vacios or valor.strip())}


class RutasDiseno:
    def __init__(self, servicios):
        self.simulacros_servicio = servicios.simulacros
        self.diseno = servicios.diseno

    def rutas(self):
        sims = (self.simulacros_servicio,)
        diseno = (self.diseno,)
        return [
            Ruta('/coordinador/simulacros', 'simulacros', self.simulacros, ('GET', 'POST'), COORDINADOR, sims),
            Ruta('/coordinador/examenes/<int:simulacro_id>', 'espacio_examen', self.espacio_examen, rol=COORDINADOR, servicios=sims),
            Ruta('/coordinador/configurar-examen', 'configurar_examen', self.configurar_examen, ('GET', 'POST'), COORDINADOR, diseno),
            Ruta('/coordinador/versiones/<int:id>/clave', 'guardar_clave', self.guardar_clave, ('POST',), COORDINADOR, diseno),
        ]

    def _ejecutar_accion_simulacro(self, accion):
        usuario = session['usuario_id']
        if accion == 'simulacro':
            datos = request.form.to_dict()
            datos['areas'] = request.form.getlist('areas')
            self.simulacros_servicio.crear_simulacro(datos, usuario)
        elif accion == 'agregar_areas':
            self.simulacros_servicio.agregar_areas(request.form.get('simulacro'), request.form.getlist('areas'), usuario)
        elif accion == 'examen':
            self.simulacros_servicio.crear_examen(request.form.to_dict(), usuario)
        elif accion in ('habilitar', 'cerrar'):
            self.simulacros_servicio.habilitar_preguntas(request.form.get('examen'), accion)
        else:
            raise ValueError('Acción no válida.')

    def simulacros(self):
        if request.method == 'POST':
            try:
                self._ejecutar_accion_simulacro(request.form.get('accion'))
                flash('Registro guardado.', 'ok')
                return redirect(url_for('simulacros'))
            except ValueError as error:
                flash(str(error), 'error')
            except SQLAlchemyError:
                # Incluye las restricciones de la base (IntegrityError) y las reglas de sus triggers (OperationalError).
                current_app.logger.exception('No se pudo guardar el simulacro o examen')
                flash('No se pudo guardar: verifica la fecha y que no exista otro examen para esa área.', 'error')
        sims, examenes, ciclos, areas = self.simulacros_servicio.listar()
        return pagina('coordinador/simulacros.html', ROL_COORDINADOR, simulacros=sims, examenes=examenes, ciclos=ciclos, areas=areas)

    def espacio_examen(self, simulacro_id):
        contexto = self.simulacros_servicio.abrir_aplicacion(simulacro_id, request.args.get('examen', default=0, type=int) or 0)
        if not contexto:
            abort(404)
        resumen = self.simulacros_servicio.resumen_examen(contexto['id_examen'])
        siguiente = self.simulacros_servicio.siguiente_etapa(contexto, resumen)
        return pagina('coordinador/espacio_examen.html', ROL_COORDINADOR, contexto_examen=contexto,
                      etapas_examen=ETAPAS_EXAMEN, resumen=resumen, siguiente=siguiente)

    def _configurar(self, examen):
        try:
            if not examen:
                raise ValueError('Selecciona un examen.')
            puntajes = _campos_con_prefijo(request.form, PREFIJO_PUNTAJE, omitir_vacios=True)
            self.diseno.configurar(examen, request.form.getlist('preguntas'), puntajes, request.form.getlist('versiones'),
                                   request.form.get('penalizacion'), session['usuario_id'])
            flash('Examen configurado y aprobado. Ahora revisa las claves de cada versión.', 'ok')
            return redirect(url_for('configurar_examen', examen=examen))
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo configurar el examen')
            flash('No se pudo guardar la configuración; verifica que las preguntas y el examen sigan disponibles.', 'error')
        return None

    def configurar_examen(self):
        examen = seleccionar_examen()
        if request.method == 'POST':
            respuesta = self._configurar(examen)
            if respuesta is not None:
                return respuesta
        consulta = self.diseno.consultar(examen)
        distribucion = self.diseno.distribucion(examen) if consulta.actual else []
        return pagina('coordinador/configurar_examen.html', ROL_COORDINADOR, examen=examen, examenes=consulta.examenes,
                      actual=consulta.actual, preguntas=consulta.preguntas, versiones=consulta.versiones,
                      claves=consulta.claves, distribucion=distribucion)

    def guardar_clave(self, id):
        examen = seleccionar_examen()
        try:
            respuestas = _campos_con_prefijo(request.form, PREFIJO_RESPUESTA)
            archivo = request.files.get('archivo')
            if archivo and archivo.filename:
                respuestas = respuestas_desde_csv(archivo.read(MAX_BYTES_CSV_CLAVE + 1))
            self.diseno.crear_clave(id, respuestas, request.form.get('motivo'), session['usuario_id'])
            flash('Nueva revisión de clave confirmada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo confirmar la clave')
            flash('No se pudo confirmar la clave; comprueba que cada respuesta sea una alternativa de la pregunta.', 'error')
        return redirect(url_for('configurar_examen', examen=examen))


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasDiseno(servicios).rutas())
