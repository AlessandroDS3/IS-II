"""Persistencia de cuentas; las políticas se validan dentro de la transacción."""
from sqlalchemy import column, select, table, text


class GestionUsuariosRepositorio:
    def __init__(self, motor):
        self.motor = motor

    def listar(self):
        with self.motor.connect() as conexion:
            return conexion.execute(text("""
                SELECT u.id_usuario, u.username, u.nombres, u.apellidos, u.estado,
                       GROUP_CONCAT(r.nombre ORDER BY r.nombre SEPARATOR ', ') AS roles
                FROM usuarios u
                LEFT JOIN usuario_roles ur ON ur.id_usuario = u.id_usuario
                LEFT JOIN roles r ON r.id_rol = ur.id_rol
                GROUP BY u.id_usuario, u.username, u.nombres, u.apellidos, u.estado
                ORDER BY u.username
            """)).mappings().all()

    def crear(self, datos, hash_clave, roles):
        with self.motor.begin() as conexion:
            resultado = conexion.execute(text("""
                INSERT INTO usuarios(username, password_hash, nombres, apellidos, estado)
                VALUES (:username, :clave, :nombres, :apellidos, 'ACTIVO')
            """), {**datos, 'clave': hash_clave})
            id_usuario = resultado.lastrowid
            self._asignar_roles(conexion, id_usuario, roles)
            self._sincronizar_perfiles(conexion, id_usuario, roles)

    @staticmethod
    def _cuenta_bloqueada(conexion, id_usuario):
        usuarios = table('usuarios', column('id_usuario'))
        asignaciones = table('usuario_roles', column('id_usuario'), column('id_rol'))
        roles = table('roles', column('id_rol'), column('nombre'))
        estudiantes = table('estudiantes', column('id_usuario'))
        es_director = select(asignaciones.c.id_usuario).join(
            roles, roles.c.id_rol == asignaciones.c.id_rol
        ).where(asignaciones.c.id_usuario == usuarios.c.id_usuario,
                roles.c.nombre == 'DIRECTOR').exists()
        vinculado = select(estudiantes.c.id_usuario).where(
            estudiantes.c.id_usuario == usuarios.c.id_usuario).exists()
        consulta = select(
            usuarios.c.id_usuario, es_director.label('es_director'),
            vinculado.label('estudiante_vinculado')
        ).where(usuarios.c.id_usuario == id_usuario).with_for_update()
        cuenta = conexion.execute(consulta).mappings().first()
        if cuenta is None:
            raise ValueError('La cuenta no existe.')
        return cuenta

    def estado(self, id_usuario, estado, validar_cuenta):
        with self.motor.begin() as conexion:
            cuenta = self._cuenta_bloqueada(conexion, id_usuario)
            validar_cuenta(cuenta)
            conexion.execute(text('UPDATE usuarios SET estado=:estado WHERE id_usuario=:id'),
                             {'id': id_usuario, 'estado': estado})

    def cambiar_roles(self, id_usuario, roles, validar_cuenta):
        with self.motor.begin() as conexion:
            cuenta = self._cuenta_bloqueada(conexion, id_usuario)
            validar_cuenta(cuenta)
            conexion.execute(text('DELETE FROM usuario_roles WHERE id_usuario=:id'),
                             {'id': id_usuario})
            self._asignar_roles(conexion, id_usuario, roles)
            self._sincronizar_perfiles(conexion, id_usuario, roles)

    @staticmethod
    def _asignar_roles(conexion, id_usuario, roles):
        for rol in roles:
            conexion.execute(text("""
                INSERT INTO usuario_roles(id_usuario, id_rol)
                SELECT :id, id_rol FROM roles WHERE nombre=:rol
            """), {'id': id_usuario, 'rol': rol})

    @staticmethod
    def _sincronizar_perfiles(conexion, id_usuario, roles):
        # Los nombres de tablas proceden de esta lista cerrada, nunca del formulario.
        perfiles = (('DOCENTE', 'docentes'), ('COORDINADOR', 'coordinadores'),
                    ('DIRECTOR', 'directores'))
        for rol, tabla in perfiles:
            if rol in roles:
                conexion.execute(text(f"""
                    INSERT INTO {tabla}(id_usuario)
                    SELECT :id WHERE NOT EXISTS (
                        SELECT 1 FROM {tabla} WHERE id_usuario=:id
                    )
                """), {'id': id_usuario})
