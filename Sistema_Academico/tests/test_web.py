"""Pruebas transversales de la capa web y de exportación (Stefano)."""
import pytest

from app import crear_app
from presentacion.controllers.exportacion import celda_segura


class AccesoValido:
    def consultar_cuenta_activa(self, usuario):
        return {'id': 1, 'roles': ['COORDINADOR', 'DIRECTOR']}


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.delenv('SISTEMA_DATABASE_URL', raising=False)
    app = crear_app(servicio_prueba=AccesoValido())
    app.config.update(WTF_CSRF_ENABLED=False)
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion.update(usuario='coord', usuario_id=1, nombre='Coord', roles=['COORDINADOR', 'DIRECTOR'])
    return cliente


@pytest.mark.parametrize('metodo, url', [
    ('get', '/coordinador/usuarios'), ('post', '/coordinador/usuarios/2/roles'), ('get', '/coordinador/lecturas'),
    ('post', '/coordinador/lecturas/1/corregir'), ('post', '/coordinador/cartillas/1/validar'),
    ('get', '/coordinador/resultados/1/detalle'), ('post', '/coordinador/resultados/1/revisar'),
    ('post', '/coordinador/resultados/calcular'), ('post', '/coordinador/resultados/publicar'),
    ('get', '/coordinador/reportes'), ('get', '/coordinador/reportes/descargar?examen=1'),
    ('get', '/coordinador/reportes/excel?examen=1'), ('get', '/coordinador/cartillas/1/imagen'),
    ('post', '/coordinador/versiones/1/clave'), ('get', '/director'),
])
def test_sin_base_de_datos_todas_las_rutas_responden_503(cliente, metodo, url):
    assert getattr(cliente, metodo)(url).status_code == 503


def test_sin_sesion_redirige_al_login(monkeypatch):
    monkeypatch.delenv('SISTEMA_DATABASE_URL', raising=False)
    respuesta = crear_app(servicio_prueba=AccesoValido()).test_client().get('/coordinador')
    assert respuesta.status_code == 302
    assert respuesta.headers['Location'].endswith('/')


def test_celda_segura_neutraliza_formulas():
    assert celda_segura('=SUMA(A1)') == "'=SUMA(A1)"
    assert celda_segura(' -1') == "' -1"
    assert celda_segura('Ana') == 'Ana'
    assert celda_segura(5) == 5
