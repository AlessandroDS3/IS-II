"""Pruebas de identidad y acceso (Claudia)."""
import pytest

from aplicacion.servicios.gestion_usuarios_app_service import GestionUsuariosAppService
from app import crear_app
from dominio.identidad_acceso.autorizacion import Autorizacion
from dominio.identidad_acceso.cuenta_usuario import CuentaUsuario
from dominio.identidad_acceso.limitador_intentos import LimitadorIntentos
from dominio.identidad_acceso.politica_contrasena import validar_contrasena
from tests.conftest import RepositorioFalso


class Protector:
    def generar_hash(self, clave):
        return 'hash:' + clave


def test_autorizacion_director_hereda_coordinador():
    assert Autorizacion.puede_acceder(['DIRECTOR'], 'COORDINADOR')
    assert not Autorizacion.puede_acceder(['DOCENTE'], 'COORDINADOR')
    with pytest.raises(ValueError, match='estudiante'):
        Autorizacion.validar_roles(['ESTUDIANTE', 'DOCENTE'], True)
    with pytest.raises(PermissionError):
        Autorizacion.validar_roles(['DIRECTOR'], False)


def test_limitador_bloquea_y_expira():
    reloj = [0.0]
    limitador = LimitadorIntentos(max_intentos=2, ventana_segundos=10, reloj=lambda: reloj[0])
    limitador.registrar_fallo('ana')
    limitador.registrar_fallo('ana')
    assert limitador.bloqueado('ana')
    assert not limitador.bloqueado('luis')
    reloj[0] = 11
    assert not limitador.bloqueado('ana')


def test_politica_de_contrasena():
    with pytest.raises(ValueError, match='letras y números'):
        validar_contrasena('solo-letras')
    validar_contrasena('letras123')


def test_crear_cuenta_valida_politica_y_roles():
    repo = RepositorioFalso()
    servicio = GestionUsuariosAppService(repo, Protector())
    base = {'username': 'u', 'nombres': 'N', 'apellidos': 'A', 'roles': ['DOCENTE']}
    with pytest.raises(ValueError, match='8 caracteres'):
        servicio.crear(dict(base, contrasena='corta1'), False)
    with pytest.raises(ValueError, match='letras y números'):
        servicio.crear(dict(base, contrasena='sinnumeros'), False)
    servicio.crear(dict(base, contrasena='clave-1234'), False)
    assert repo.llamadas[-1][1][1] == 'hash:clave-1234'
    with pytest.raises(ValueError, match='propia cuenta'):
        servicio.cambiar_roles(3, ['DOCENTE'], True, 3)


def test_cuenta_usuario():
    cuenta = CuentaUsuario('u', 'h')
    cuenta.asignar_roles(['DOCENTE', 'COORDINADOR'])
    cuenta.desactivar()
    assert not cuenta.activa
    assert cuenta.roles == ['DOCENTE', 'COORDINADOR']
    with pytest.raises(ValueError):
        cuenta.cambiar_credencial('')


class AccesoFalso:
    def __init__(self):
        self.intentos = 0

    def iniciar_sesion(self, usuario, clave):
        self.intentos += 1
        return None


def test_login_se_bloquea_tras_cinco_fallos(monkeypatch):
    monkeypatch.delenv('SISTEMA_DATABASE_URL', raising=False)
    acceso = AccesoFalso()
    app = crear_app(servicio_prueba=acceso)
    app.config.update(WTF_CSRF_ENABLED=False)
    cliente = app.test_client()
    codigos = [cliente.post('/', data={'usuario': 'ana', 'contrasena': 'x'}).status_code for _ in range(6)]
    assert codigos == [401] * 5 + [429]
    assert acceso.intentos == 5
