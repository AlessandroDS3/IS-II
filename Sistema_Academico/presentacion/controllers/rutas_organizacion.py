"""Rutas de organización académica: panel del coordinador, estudiantes y catálogos."""
from flask import abort, current_app, flash, redirect, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from presentacion.controllers.soporte_web import ROL_COORDINADOR, Ruta, pagina, registrar_vistas

MSG_CODIGO_DUPLICADO = 'El código del estudiante ya está registrado.'
COORDINADOR = 'COORDINADOR'
GET_POST = ('GET', 'POST')
POST = ('POST',)


class RutasOrganizacion:
    def __init__(self, servicios):
        self.estudiantes_servicio = servicios.estudiantes
        self.organizacion_servicio = servicios.organizacion
        self.panel_servicio = servicios.panel

    def rutas(self):
        est = (self.estudiantes_servicio,)
        base = '/coordinador/estudiantes/<int:id>'
        return [
            Ruta('/coordinador', 'coordinador', self.coordinador, rol=COORDINADOR),
            Ruta('/coordinador/estudiantes', 'estudiantes', self.estudiantes, GET_POST, COORDINADOR, est),
            Ruta(base + '/editar', 'editar_estudiante', self.editar_estudiante, GET_POST, COORDINADOR, est),
            Ruta(base + '/estado', 'estado_estudiante', self.estado_estudiante, POST, COORDINADOR, est),
            Ruta(base + '/cuenta', 'vincular_estudiante', self.vincular_estudiante, POST, COORDINADOR, est),
            Ruta(base + '/asignaciones', 'asignaciones_estudiante', self.asignaciones_estudiante, GET_POST, COORDINADOR, est),
            Ruta('/coordinador/organizacion', 'organizacion', self.organizacion, GET_POST, COORDINADOR, (self.organizacion_servicio,)),
        ]

    def coordinador(self):
        pendientes = None
        if self.panel_servicio:
            try:
                pendientes = self.panel_servicio.consultar_pendientes()
            except SQLAlchemyError:
                current_app.logger.exception('No se pudieron consultar los pendientes')
        return pagina('coordinador/inicio.html', ROL_COORDINADOR, pendientes=pendientes)

    def estudiantes(self):
        if request.method == 'POST':
            try:
                self.estudiantes_servicio.registrar_estudiante(request.form.to_dict())
                flash('Estudiante registrado correctamente.', 'ok')
                return redirect(url_for('estudiantes'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash(MSG_CODIGO_DUPLICADO, 'error')
        try:
            lista = self.estudiantes_servicio.listar(request.args.get('q', ''))
        except SQLAlchemyError:
            current_app.logger.exception('Error al consultar estudiantes')
            abort(503)
        return pagina('coordinador/estudiantes.html', ROL_COORDINADOR, estudiantes=lista, busqueda=request.args.get('q', ''))

    def _estudiante_o_404(self, id_estudiante):
        registro = self.estudiantes_servicio.buscar_por_id(id_estudiante)
        if not registro:
            abort(404)
        return registro

    def editar_estudiante(self, id):
        registro = self._estudiante_o_404(id)
        if request.method == 'POST':
            try:
                self.estudiantes_servicio.actualizar(id, request.form.to_dict())
                flash('Estudiante actualizado correctamente.', 'ok')
                return redirect(url_for('estudiantes'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash(MSG_CODIGO_DUPLICADO, 'error')
        return pagina('coordinador/editar_estudiante.html', ROL_COORDINADOR, estudiante=registro)

    def estado_estudiante(self, id):
        try:
            if not self.estudiantes_servicio.cambiar_estado(id, request.form.get('estado', '')):
                abort(404)
            flash('Estado actualizado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('estudiantes'))

    def vincular_estudiante(self, id):
        try:
            self.estudiantes_servicio.vincular_cuenta(id, request.form.get('usuario', ''))
            flash('Cuenta vinculada correctamente.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except IntegrityError:
            flash('Esa cuenta ya está vinculada a otro estudiante.', 'error')
        return redirect(url_for('editar_estudiante', id=id))

    def asignaciones_estudiante(self, id):
        estudiante = self._estudiante_o_404(id)
        if request.method == 'POST':
            try:
                self.estudiantes_servicio.cambiar_asignacion(id, request.form.get('grupo'), request.form.get('area'), request.form.get('fecha'))
                flash('Asignación actualizada conservando el historial.', 'ok')
                return redirect(url_for('asignaciones_estudiante', id=id))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('No se pudo guardar la asignación: revisa los periodos y datos seleccionados.', 'error')
        areas, grupos, opciones_areas, opciones_grupos = self.estudiantes_servicio.consultar_asignaciones(id)
        return pagina('coordinador/asignaciones.html', ROL_COORDINADOR, estudiante=estudiante, areas=areas, grupos=grupos,
                      opciones_areas=opciones_areas, opciones_grupos=opciones_grupos)

    def organizacion(self):
        if request.method == 'POST':
            try:
                self.organizacion_servicio.ejecutar(request.form.get('accion'), request.form.get('tipo', ''), request.form.to_dict())
                flash('Operación realizada correctamente.', 'ok')
                return redirect(url_for('organizacion'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('No se pudo guardar: comprueba el código o el elemento seleccionado.', 'error')
        return pagina('coordinador/organizacion.html', ROL_COORDINADOR, catalogos=self.organizacion_servicio.listar())


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasOrganizacion(servicios).rutas())
