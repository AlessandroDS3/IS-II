"""Rutas del banco de preguntas: revisión del coordinador y autoría del docente."""
from pathlib import Path

from flask import abort, current_app, flash, redirect, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from presentacion.controllers.soporte_web import (ROL_COORDINADOR, ROL_DOCENTE, Ruta, enviar_imagen_privada, pagina,
                                                  registrar_vistas)

CLAVES_IMAGEN = ('ENUNCIADO', 'A', 'B', 'C', 'D', 'E')
FILTROS_BANCO = ('estado', 'examen', 'materia', 'area', 'eje')
COORDINADOR = 'COORDINADOR'
DOCENTE = 'DOCENTE'
GET_POST = ('GET', 'POST')


class RutasBancoPreguntas:
    def __init__(self, servicios):
        self.preguntas_servicio = servicios.preguntas
        self.autoria = servicios.autoria
        self.imagenes = servicios.imagenes_preguntas

    def rutas(self):
        banco = (self.preguntas_servicio,)
        autoria = (self.autoria,)
        return [
            Ruta('/coordinador/preguntas', 'banco_preguntas', self.banco_preguntas, rol=COORDINADOR, servicios=banco),
            Ruta('/coordinador/preguntas/<int:id>/revision', 'revisar_pregunta', self.revisar_pregunta, ('POST',), COORDINADOR, banco),
            Ruta('/docente', 'docente', self.docente, rol=DOCENTE, servicios=autoria),
            Ruta('/docente/temas', 'docente_tema', self.docente_tema, ('POST',), DOCENTE, autoria),
            Ruta('/docente/preguntas/<int:id>', 'docente_detalle', self.docente_detalle, rol=DOCENTE, servicios=autoria),
            Ruta('/docente/preguntas/nueva', 'docente_crear', self.docente_crear, GET_POST, DOCENTE, autoria),
            Ruta('/docente/preguntas/<int:id>/editar', 'docente_editar', self.docente_editar, GET_POST, DOCENTE, autoria),
            Ruta('/docente/imagenes/<int:id>', 'docente_imagen', self.docente_imagen, rol=DOCENTE, servicios=autoria),
            Ruta('/coordinador/preguntas/imagenes/<int:id>', 'coordinador_imagen_pregunta', self.coordinador_imagen_pregunta,
                 rol=COORDINADOR, servicios=autoria),
            Ruta('/docente/estadisticas', 'docente_estadisticas', self.docente_estadisticas, rol=DOCENTE, servicios=autoria),
        ]

    def banco_preguntas(self):
        try:
            filas, materias, areas, ejes = self.preguntas_servicio.consultar_banco(request.args.to_dict())
        except ValueError as error:
            flash(str(error), 'error')
            return redirect(url_for('banco_preguntas'))
        return pagina('coordinador/banco_preguntas.html', ROL_COORDINADOR, preguntas=filas, materias=materias, areas=areas,
                      ejes=ejes, filtros=request.args)

    def revisar_pregunta(self, id):
        try:
            self.preguntas_servicio.revisar_pregunta(id, int(request.form.get('version', '0')), request.form.get('accion'),
                                                     request.form.get('observacion'), session['usuario_id'])
            flash('Revisión guardada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo revisar la pregunta')
            flash('No se pudo completar la revisión. Verifica que tenga área y versión válida.', 'error')
        filtros = {clave: request.form.get(clave, '') for clave in FILTROS_BANCO}
        return redirect(url_for('banco_preguntas', **filtros))

    def docente(self):
        try:
            preguntas = self.autoria.preguntas(session['usuario_id'], request.args)
        except ValueError as error:
            flash(str(error), 'error')
            return redirect(url_for('docente'))
        materias, _, _ = self.autoria.catalogos(session['usuario_id'])
        return pagina('docente/docente_preguntas.html', ROL_DOCENTE, preguntas=preguntas, materias=materias,
                      examenes=self.autoria.examenes(), filtros=request.args)

    def docente_tema(self):
        try:
            self.autoria.crear_tema(session['usuario_id'], request.form.get('materia'), request.form.get('nombre'))
            flash('Tema registrado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('docente_crear'))

    def _guardar_imagenes(self, guardadas):
        """Guarda las imágenes recibidas en el diccionario indicado (para poder limpiarlas si algo falla)."""
        for clave in CLAVES_IMAGEN:
            archivo = request.files.get('imagen_' + clave)
            if archivo and archivo.filename:
                guardadas[clave] = self.imagenes.guardar(archivo)

    def _guardar_pregunta(self, pregunta, pregunta_id):
        guardadas = {}
        try:
            self._guardar_imagenes(guardadas)
            self.autoria.guardar(session['usuario_id'], request.form, guardadas, pregunta_id)
        except (ValueError, SQLAlchemyError) as error:
            for ruta, _ in guardadas.values():
                Path(ruta).unlink(missing_ok=True)
            if isinstance(error, SQLAlchemyError):
                current_app.logger.exception('No se pudo guardar la pregunta')
                flash('No se pudo guardar la pregunta. Revisa los datos y la conexión.', 'error')
            else:
                flash(str(error), 'error')
            return None
        flash('Pregunta guardada.' if request.form.get('accion') == 'guardar' else 'Pregunta enviada a revisión.', 'ok')
        examen = request.form.get('examen') or (pregunta['id_examen_destino'] if pregunta else '') or ''
        return redirect(url_for('docente', examen=examen))

    def _formulario(self, pregunta_id=None):
        pregunta = self.autoria.obtener(session['usuario_id'], pregunta_id) if pregunta_id else None
        if pregunta_id and not pregunta:
            abort(404)
        if pregunta and pregunta['estado'] != 'BORRADOR':
            flash('Solo se pueden editar preguntas en borrador.', 'error')
            return redirect(url_for('docente'))
        materias, temas, areas = self.autoria.catalogos(session['usuario_id'])
        if request.method == 'POST':
            respuesta = self._guardar_pregunta(pregunta, pregunta_id)
            if respuesta is not None:
                return respuesta
        datos = request.form if request.method == 'POST' else request.args
        return pagina('docente/docente_formulario.html', ROL_DOCENTE, pregunta=pregunta, materias=materias, temas=temas,
                      areas=areas, examenes=self.autoria.examenes(), datos=datos)

    def docente_detalle(self, id):
        pregunta = self.autoria.obtener(session['usuario_id'], id, request.args.get('version', type=int))
        if not pregunta:
            abort(404)
        return pagina('docente/docente_detalle.html', ROL_DOCENTE, pregunta=pregunta)

    def docente_crear(self):
        return self._formulario()

    def docente_editar(self, id):
        return self._formulario(id)

    def _imagen(self, imagen_id, coordinador=False):
        return enviar_imagen_privada(self.autoria.imagen(session['usuario_id'], imagen_id, coordinador), self.imagenes.directorio)

    def docente_imagen(self, id):
        return self._imagen(id)

    def coordinador_imagen_pregunta(self, id):
        return self._imagen(id, True)

    def docente_estadisticas(self):
        return pagina('docente/docente_estadisticas.html', ROL_DOCENTE, estadisticas=self.autoria.estadisticas(session['usuario_id']))


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasBancoPreguntas(servicios).rutas())
