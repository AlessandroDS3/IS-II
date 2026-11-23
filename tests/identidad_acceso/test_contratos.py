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

    def test_repositorio_de_acceso_no_ofrece_operaciones_de_administracion(self):
        repositorio = CuentaUsuarioORMRepositorio(None)
        for operacion in ('guardar', 'buscar_por_id', 'listar'):
            with self.subTest(operacion=operacion):
                self.assertFalse(hasattr(repositorio, operacion))

    def test_autorizacion_expone_solo_las_politicas_implementadas(self):
        for operacion in ('verificar_permiso', 'verificar_acceso_a_resultado'):
            with self.subTest(operacion=operacion):
                self.assertFalse(hasattr(Autorizacion, operacion))

    def test_protector_concreto_verifica_claves_y_rechaza_hash_invalido(self):
        protector = ProtectorCredencialesWerkzeug()
        clave = 'Prueba123!'
        protegido = protector.generar_hash(clave)
        self.assertNotEqual(protegido, clave)
        self.assertTrue(protector.verificar(protegido, clave))
        self.assertFalse(protector.verificar(protegido, 'incorrecta'))
        for hash_guardado, contrasena in (
            (None, clave), (123, clave), ('', clave), ('invalido', clave),
            (protegido, None), (protegido, 123),
        ):
            with self.subTest(hash_guardado=hash_guardado, contrasena=contrasena):
                self.assertFalse(protector.verificar(hash_guardado, contrasena))
