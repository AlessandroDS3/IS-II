import unittest
from unittest.mock import Mock
from _soporte import BaseSQLite
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from aplicacion.servicios.cuenta_usuario_app_service import CuentaUsuarioAppService
from aplicacion.servicios.gestion_usuarios_app_service import GestionUsuariosAppService
from infraestructura.persistencia.repositories.cuenta_usuario_orm_repositorio import CuentaUsuarioORMRepositorio
from infraestructura.persistencia.repositories.gestion_usuarios_repositorio import GestionUsuariosRepositorio
from presentacion.controllers.cuenta_usuario_controller import CuentaUsuarioController


class TestIntegracionIdentidadAcceso(BaseSQLite, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.protector = Mock(spec_set=IProtectorCredenciales)
        self.protector.generar_hash.return_value = "hash-prueba"
        self.protector.verificar.return_value = True
        self.repositorio_gestion = GestionUsuariosRepositorio(self.motor)
        self.repositorio_cuenta = CuentaUsuarioORMRepositorio(self.motor)
        self.gestion = GestionUsuariosAppService(
            self.repositorio_gestion, self.protector
        )
        self.sesiones = CuentaUsuarioAppService(
            self.repositorio_cuenta, self.protector
        )
        self.formulario = {
            "username": "ana", "nombres": "Ana", "apellidos": "Perez",
            "contrasena": "Clave123!", "roles": ["DOCENTE"]
        }

    def test_crear_y_autenticar_cuenta_persistida(self):
        # Inicializar
        formulario = self.formulario

        # Ejecutar
        self.gestion.crear(formulario, director=False)
        resultado = self.sesiones.iniciar_sesion("ana", "Clave123!")

        # Verificar
        self.assertEqual(resultado["usuario"], "ana")
        self.assertEqual(resultado["roles"], ["DOCENTE"])
        self.assertTrue(resultado["activa"])
        self.assertNotEqual(resultado["password_hash"], formulario["contrasena"])
        perfiles = self.consultar("SELECT id_usuario FROM docentes")
        self.assertEqual(perfiles, [{"id_usuario": resultado["id"]}])


    def test_usuario_duplicado_no_deja_roles_ni_perfiles_adicionales(self):
        # Inicializar
        self.gestion.crear(self.formulario, director=False)

        # Ejecutar y verificar
        with self.assertRaises(IntegrityError):
            self.gestion.crear(self.formulario, director=False)
        self.assertEqual(len(self.consultar("SELECT * FROM usuarios")), 1)
        self.assertEqual(len(self.consultar("SELECT * FROM usuario_roles")), 1)
        self.assertEqual(len(self.consultar("SELECT * FROM docentes")), 1)

    def test_validacion_invalida_deja_la_base_sin_usuarios(self):
        # Inicializar
        self.formulario["roles"] = ["ESTUDIANTE", "DOCENTE"]

        # Ejecutar y verificar
        with self.assertRaises(ValueError):
            self.gestion.crear(self.formulario, director=True)
        self.assertEqual(self.consultar("SELECT * FROM usuarios"), [])
        self.assertEqual(self.consultar("SELECT * FROM usuario_roles"), [])
        self.protector.generar_hash.assert_not_called()

    def test_controlador_autentica_cuenta_persistida_y_rechaza_cuenta_inactiva(self):
        self.gestion.crear(self.formulario, director=False)
        controlador = CuentaUsuarioController(self.sesiones)
        cuenta = controlador.iniciar_sesion(' ana ', 'Clave123!')
        self.assertEqual(cuenta['usuario'], 'ana')
        self.assertEqual(cuenta['roles'], ['DOCENTE'])
        with self.motor.begin() as conexion:
            conexion.execute(text("UPDATE usuarios SET estado='INACTIVO'"))
        self.assertIsNone(controlador.iniciar_sesion('ana', 'Clave123!'))

    def test_controlador_propaga_operaciones_pendientes_sin_indicar_exito(self):
        controlador = CuentaUsuarioController(self.sesiones)
        for operacion, argumentos in [
            ('registrar_cuenta', ({},)),
            ('asignar_roles', (7, ['DOCENTE'])),
            ('recuperar_acceso', ({},)),
        ]:
            metodo = getattr(controlador, operacion)
            with self.subTest(operacion=operacion), self.assertRaises(NotImplementedError):
                metodo(*argumentos)
        self.assertEqual(self.consultar('SELECT * FROM usuarios'), [])

if __name__ == "__main__":
    unittest.main()
