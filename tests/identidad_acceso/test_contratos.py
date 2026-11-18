"""Contratos completos y rechazo explicito de operaciones no soportadas."""
import unittest

import _soporte
from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from dominio.identidad_acceso.autorizacion import Autorizacion
from dominio.identidad_acceso.i_cuenta_repositorio import ICuentaRepositorio
from infraestructura.persistencia.repositories.cuenta_usuario_orm_repositorio import CuentaUsuarioORMRepositorio
from infraestructura.seguridad.protector_credenciales_werkzeug import ProtectorCredencialesWerkzeug


class TestContratosIdentidadAcceso(unittest.TestCase):
    def test_interfaces_no_se_pueden_usar_como_implementaciones(self):
        for contrato in [ICuentaRepositorio, IProtectorCredenciales]:
            with self.subTest(contrato=contrato.__name__), self.assertRaises(TypeError):
                contrato()

    def test_repositorio_rechaza_operaciones_pendientes_antes_de_abrir_conexion(self):
        repositorio = CuentaUsuarioORMRepositorio(None)
        for operacion, argumento in [('guardar', object()), ('buscar_por_id', 7), ('listar', {})]:
            metodo = getattr(repositorio, operacion)
            with self.subTest(operacion=operacion), self.assertRaises(NotImplementedError):
                metodo(argumento)

    def test_autorizaciones_sin_politica_no_devuelven_aprobacion_silenciosa(self):
        autorizacion = Autorizacion()
        for operacion in ['verificar_permiso', 'verificar_acceso_a_resultado']:
            metodo = getattr(autorizacion, operacion)
            with self.subTest(operacion=operacion), self.assertRaises(NotImplementedError):
                metodo(None, None)

    def test_protector_concreto_verifica_claves_y_rechaza_hash_invalido(self):
        protector = ProtectorCredencialesWerkzeug()
        clave = 'Prueba123!'
        protegido = protector.generar_hash(clave)
        self.assertNotEqual(protegido, clave)
        self.assertTrue(protector.verificar(protegido, clave))
        self.assertFalse(protector.verificar(protegido, 'incorrecta'))
        self.assertFalse(protector.verificar(None, clave))
