"""Persistencia de cuentas de usuario, sus roles y los perfiles asociados a cada rol."""
from sqlalchemy import text

from dominio.identidad_acceso.autorizacion import Autorizacion
from dominio.identidad_acceso.rol import ROLES_CON_PERFIL, Rol

SQL_ASIGNAR_ROL = text('INSERT INTO usuario_roles(id_usuario,id_rol) SELECT :id,id_rol FROM roles WHERE nombre=:rol')


class GestionUsuariosRepositorio:
    """Implementa IGestionUsuariosRepositorio."""

    def __init__(self, motor):
        self.motor = motor

    def listar(self):
        with self.motor.connect() as c:
            return c.execute(text("SELECT u.id_usuario,u.username,u.nombres,u.apellidos,u.estado,GROUP_CONCAT(r.nombre ORDER BY r.nombre SEPARATOR ', ') AS roles FROM usuarios u LEFT JOIN usuario_roles ur ON ur.id_usuario=u.id_usuario LEFT JOIN roles r ON r.id_rol=ur.id_rol GROUP BY u.id_usuario,u.username,u.nombres,u.apellidos,u.estado ORDER BY u.username")).mappings().all()

    @staticmethod
    def _asignar_roles(c, id_usuario, roles):
        for rol in roles:
            c.execute(SQL_ASIGNAR_ROL, {'id': id_usuario, 'rol': str(rol)})

    @staticmethod
    def _sincronizar_perfiles(c, id_usuario, roles):
        """Crea la fila de perfil (docentes, coordinadores, directores) de cada rol que la necesita, sin duplicarla."""
        for rol, tabla in ROLES_CON_PERFIL:
            if rol in roles:
                c.execute(text(f'INSERT INTO {tabla}(id_usuario) SELECT :id WHERE NOT EXISTS (SELECT 1 FROM {tabla} WHERE id_usuario=:id)'), {'id': id_usuario})

    @staticmethod
    def _cuenta_bloqueada(c, id_usuario):
        return c.execute(text("SELECT u.id_usuario, EXISTS(SELECT 1 FROM usuario_roles ur JOIN roles r ON r.id_rol=ur.id_rol WHERE ur.id_usuario=u.id_usuario AND r.nombre='DIRECTOR') AS es_director FROM usuarios u WHERE u.id_usuario=:id FOR UPDATE"), {'id': id_usuario}).mappings().first()

    def crear(self, datos, hash_clave, roles):
        with self.motor.begin() as c:
            id_usuario = c.execute(text("INSERT INTO usuarios(username,password_hash,nombres,apellidos,estado) VALUES (:username,:clave,:nombres,:apellidos,'ACTIVO')"), {**datos, 'clave': hash_clave}).lastrowid
            self._asignar_roles(c, id_usuario, roles)
            self._sincronizar_perfiles(c, id_usuario, roles)

    def estado(self, id_usuario, estado, director):
        with self.motor.begin() as c:
            cuenta = self._cuenta_bloqueada(c, id_usuario)
            if not cuenta:
                raise ValueError('La cuenta no existe.')
            Autorizacion.validar_modificacion_cuenta(cuenta['es_director'], director)
            c.execute(text('UPDATE usuarios SET estado=:estado WHERE id_usuario=:id'), {'id': id_usuario, 'estado': estado})

    def cambiar_roles(self, id_usuario, roles, director):
        with self.motor.begin() as c:
            cuenta = self._cuenta_bloqueada(c, id_usuario)
            if not cuenta:
                raise ValueError('La cuenta no existe.')
            Autorizacion.validar_modificacion_cuenta(cuenta['es_director'], director)
            vinculado = c.execute(text('SELECT COUNT(*) FROM estudiantes WHERE id_usuario=:id'), {'id': id_usuario}).scalar_one()
            if vinculado and list(roles) != [Rol.ESTUDIANTE]:
                raise ValueError('Esta cuenta está vinculada a un estudiante y debe conservar su rol.')
            c.execute(text('DELETE FROM usuario_roles WHERE id_usuario=:id'), {'id': id_usuario})
            self._asignar_roles(c, id_usuario, roles)
            self._sincronizar_perfiles(c, id_usuario, roles)
