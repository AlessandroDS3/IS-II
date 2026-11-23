"""Rutas de identidad y acceso: inicio de sesión, selección de rol y administración de cuentas."""
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dominio.identidad_acceso.limitador_intentos import LimitadorIntentos
from dominio.identidad_acceso.rol import ROLES_CON_PANEL, Rol
from presentacion.controllers.soporte_web import ROL_COORDINADOR, Ruta, pagina, registrar_vistas

PLANTILLA_LOGIN = 'comun/login.html'
COORDINADOR = 'COORDINADOR'


def _es_director():
    return Rol.DIRECTOR in session['roles']


def _rechazar_login(mensaje, codigo):
    flash(mensaje, 'error')
    return render_template(PLANTILLA_LOGIN), codigo


class RutasIdentidad:
    def __init__(self, servicios):
        self.acceso = servicios.acceso
        self.usuarios_servicio = servicios.usuarios
        self.limitador = LimitadorIntentos()

    def rutas(self):
        usuarios = (self.usuarios_servicio,)
        return [
            Ruta('/', 'login', self.login, ('GET', 'POST')),
            Ruta('/elegir-rol', 'elegir_rol', self.elegir_rol),
            Ruta('/salir', 'salir', self.salir, ('POST',)),
            Ruta('/coordinador/usuarios', 'usuarios', self.usuarios, ('GET', 'POST'), COORDINADOR, usuarios),
            Ruta('/coordinador/usuarios/<int:id>/estado', 'estado_usuario', self.estado_usuario, ('POST',), COORDINADOR, usuarios),
            Ruta('/coordinador/usuarios/<int:id>/roles', 'cambiar_roles_usuario', self.cambiar_roles_usuario, ('POST',), COORDINADOR, usuarios),
        ]

    def login(self):
        if request.method != 'POST':
            return render_template(PLANTILLA_LOGIN)
        if self.acceso is None:
            return _rechazar_login('Configure la conexión a la base de datos para iniciar sesión.', 503)
        usuario = request.form.get('usuario', '')
        if self.limitador.bloqueado(usuario.strip()):
            return _rechazar_login('Demasiados intentos fallidos. Espera unos minutos antes de volver a intentarlo.', 429)
        try:
            cuenta = self.acceso.iniciar_sesion(usuario, request.form.get('contrasena', ''))
        except SQLAlchemyError:
            current_app.logger.exception('Error de conexión al consultar la cuenta')
            return _rechazar_login('No se pudo consultar la base de datos. Revise la conexión.', 503)
        if not cuenta:
            self.limitador.registrar_fallo(usuario.strip())
            return _rechazar_login('Usuario o contraseña incorrectos, o cuenta inactiva.', 401)
        self.limitador.reiniciar(usuario.strip())
        roles = [r for r in cuenta['roles'] if r in ROLES_CON_PANEL]
        if not roles:
            return _rechazar_login('Esta cuenta no tiene acceso a los paneles disponibles.', 403)
        session.clear()
        session.update(usuario=cuenta['usuario'], usuario_id=cuenta['id'], nombre=cuenta['nombre'], roles=roles)
        return redirect(url_for('elegir_rol') if len(roles) > 1 else url_for(roles[0].lower()))

    @staticmethod
    def elegir_rol():
        if not session.get('usuario'):
            return redirect(url_for('login'))
        return render_template('comun/elegir_rol.html', roles=session['roles'])

    @staticmethod
    def salir():
        session.clear()
        return redirect(url_for('login'))

    def usuarios(self):
        es_director = _es_director()
        if request.method == 'POST':
            try:
                datos = request.form.to_dict()
                datos['roles'] = request.form.getlist('roles')
                self.usuarios_servicio.crear(datos, es_director)
                flash('Cuenta creada correctamente.', 'ok')
                return redirect(url_for('usuarios'))
            except (ValueError, PermissionError) as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('El nombre de usuario ya está registrado.', 'error')
        try:
            lista = self.usuarios_servicio.listar()
        except SQLAlchemyError:
            current_app.logger.exception('Error al consultar usuarios')
            abort(503)
        return pagina('coordinador/usuarios.html', ROL_COORDINADOR, usuarios=lista, es_director=es_director)

    def estado_usuario(self, id):
        try:
            self.usuarios_servicio.cambiar_estado(id, request.form.get('estado', ''), _es_director())
            flash('Estado actualizado.', 'ok')
        except (ValueError, PermissionError) as error:
            flash(str(error), 'error')
        return redirect(url_for('usuarios'))

    def cambiar_roles_usuario(self, id):
        try:
            self.usuarios_servicio.cambiar_roles(id, request.form.getlist('roles'), _es_director(), session['usuario_id'])
            flash('Roles actualizados.', 'ok')
        except (ValueError, PermissionError) as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('Error al modificar roles')
            flash('No se pudieron actualizar los roles.', 'error')
        return redirect(url_for('usuarios'))


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasIdentidad(servicios).rutas())
