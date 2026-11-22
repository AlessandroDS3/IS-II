"""Inicio local del sistema académico con MySQL.

Configuración por variables de entorno (valores por defecto entre paréntesis):
SISTEMA_MYSQL_HOST (localhost), SISTEMA_MYSQL_PORT (3306), SISTEMA_MYSQL_USER (root),
SISTEMA_MYSQL_DB (sistema_evaluacion), SISTEMA_MYSQL_PASSWORD (o archivo local no versionado mysql_clave.local),
SISTEMA_HOST (127.0.0.1) y SISTEMA_PORT (5000).
"""
import os
import sys
from pathlib import Path

ARCHIVO_CLAVE = Path(__file__).with_name('mysql_clave.local')


def leer_clave():
    clave = os.environ.get('SISTEMA_MYSQL_PASSWORD')
    if clave is None and ARCHIVO_CLAVE.is_file():
        clave = ARCHIVO_CLAVE.read_text(encoding='utf-8').strip()
    return clave


def configuracion_mysql(clave):
    from sqlalchemy.engine import URL
    return URL.create(
        'mysql+pymysql',
        username=os.environ.get('SISTEMA_MYSQL_USER', 'root'),
        password=clave,
        host=os.environ.get('SISTEMA_MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('SISTEMA_MYSQL_PORT', '3306')),
        database=os.environ.get('SISTEMA_MYSQL_DB', 'sistema_evaluacion'),
        query={'charset': 'utf8mb4'},
    )


def comprobar_conexion(url):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    motor = create_engine(url, pool_pre_ping=True, hide_parameters=True)
    try:
        with motor.connect() as conexion:
            conexion.execute(text('SELECT id_usuario, username, password_hash, nombres, estado FROM usuarios LIMIT 0'))
            conexion.execute(text('SELECT r.nombre FROM roles r JOIN usuario_roles ur ON ur.id_rol = r.id_rol LIMIT 0'))
    except SQLAlchemyError as error:
        print('No se pudo conectar a MySQL o no se encontraron las tablas de acceso.')
        print(f'Tipo de error: {type(error).__name__}')
        return False
    finally:
        motor.dispose()
    return True


def main():
    # Las dependencias se importan aquí para mostrar un mensaje claro si falta alguna.
    try:
        import sqlalchemy  # noqa: F401
        from app import crear_app
    except ModuleNotFoundError as error:
        print(f'Falta la dependencia {error.name}. Instala las dependencias con: python -m pip install -r requirements.txt')
        return 1
    clave = leer_clave()
    if clave is None:
        print('Configura SISTEMA_MYSQL_PASSWORD o crea mysql_clave.local con la contraseña de MySQL.')
        return 1
    url = configuracion_mysql(clave)
    print(f'Conectando a MySQL: {url.host}:{url.port}, base {url.database}...')
    if not comprobar_conexion(url):
        return 1
    host = os.environ.get('SISTEMA_HOST', '127.0.0.1')
    puerto = int(os.environ.get('SISTEMA_PORT', '5000'))
    print(f'Conexión establecida. Abre http://{host}:{puerto}/ en el navegador.')
    print('Para detener el servidor, pulsa Ctrl+C.')
    crear_app(database_url=url).run(host=host, port=puerto, debug=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
