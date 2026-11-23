"""Soporte de pruebas: imports y base SQLite temporal, sin acceder a MySQL."""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "Sistema_Academico"))


def registrar_rutas_identidad_prueba(app, servicios):
    """Pruebas aisladas del módulo; los otros módulos solo aportan enlaces al menú."""
    from presentacion.controllers.rutas_identidad import registrar
    from presentacion.controllers.soporte_web import crear_proteger
    registrar(app, crear_proteger(app, servicios.acceso), servicios)
    # Estos destinos permiten renderizar el menú sin cargar módulos ajenos.
    for destino in ('coordinador', 'director', 'docente', 'estudiante', 'simulacros',
                    'estudiantes', 'organizacion', 'banco_preguntas', 'configurar_examen',
                    'cartillas', 'lecturas', 'resultados_coordinador', 'reportes'):
        app.add_url_rule('/' + destino, destino, lambda: 'Destino de otro módulo')


class BaseSQLite:
    def setUp(self):
        self.motor = create_engine("sqlite+pysqlite:///:memory:")
        self.addCleanup(self.motor.dispose)
        with self.motor.begin() as conexion:
            conexion.execute(text("""
                CREATE TABLE usuarios (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    estado TEXT NOT NULL
                )
            """))
            conexion.execute(text(
                "CREATE TABLE roles (id_rol INTEGER PRIMARY KEY, nombre TEXT UNIQUE)"
            ))
            conexion.execute(text("""
                CREATE TABLE usuario_roles (
                    id_usuario INTEGER NOT NULL, id_rol INTEGER NOT NULL,
                    UNIQUE(id_usuario, id_rol)
                )
            """))
            conexion.execute(text(
                "CREATE TABLE docentes (id_usuario INTEGER UNIQUE NOT NULL)"
            ))
            for tabla in ('coordinadores', 'directores', 'estudiantes'):
                conexion.execute(text(
                    f'CREATE TABLE {tabla} (id_usuario INTEGER UNIQUE NOT NULL)'))
            conexion.execute(text(
                "INSERT INTO roles(id_rol,nombre) VALUES "
                "(1,'DOCENTE'), (2,'COORDINADOR'), (3,'DIRECTOR'), (4,'ESTUDIANTE')"
            ))

    def consultar(self, sql, parametros=None):
        with self.motor.connect() as conexion:
            return conexion.execute(text(sql), parametros or {}).mappings().all()
