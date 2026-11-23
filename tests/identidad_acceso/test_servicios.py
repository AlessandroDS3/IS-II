import unittest
from unittest.mock import Mock, create_autospec
import _soporte  # Configura los imports de la aplicación.
from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from aplicacion.servicios.cuenta_usuario_app_service import CuentaUsuarioAppService
from aplicacion.servicios.gestion_usuarios_app_service import GestionUsuariosAppService
from dominio.identidad_acceso.i_cuenta_repositorio import ICuentaRepositorio
from dominio.identidad_acceso.i_gestion_usuarios_repositorio import IGestionUsuariosRepositorio


class TestCuentaUsuarioAppService(unittest.TestCase):

    def setUp(self):
        self.repositorio = Mock(spec_set=ICuentaRepositorio)
        self.protector = Mock(spec_set=IProtectorCredenciales)
        self.servicio = CuentaUsuarioAppService(self.repositorio, self.protector)
        self.cuenta = {
            "id": 7, "usuario": "ana", "password_hash": "hash-seguro",
            "activa": True, "roles": ["DOCENTE"]
        }

    def test_inicia_sesion_y_verifica_hash_con_la_credencial(self):
        # Inicializar
        self.repositorio.buscar_por_nombre.return_value = self.cuenta
        self.protector.verificar.return_value = True

        # Ejecutar
        resultado = self.servicio.iniciar_sesion("ana", "Clave123!")

        # Verificar
        self.assertIs(resultado, self.cuenta)
        self.repositorio.buscar_por_nombre.assert_called_once_with("ana")
        self.protector.verificar.assert_called_once_with("hash-seguro", "Clave123!")

    def test_cuenta_inactiva_no_verifica_contrasena(self):
        # Inicializar
        self.cuenta["activa"] = False
        self.repositorio.buscar_por_nombre.return_value = self.cuenta

        # Ejecutar
        resultado = self.servicio.iniciar_sesion("ana", "Clave123!")

        # Verificar
        self.assertIsNone(resultado)
        self.protector.verificar.assert_not_called()

    def test_rechaza_contrasena_incorrecta(self):
        # Inicializar
        self.repositorio.buscar_por_nombre.return_value = self.cuenta
        self.protector.verificar.return_value = False

        # Ejecutar
        resultado = self.servicio.iniciar_sesion("ana", "incorrecta")

        # Verificar
        self.assertIsNone(resultado)
        self.protector.verificar.assert_called_once_with("hash-seguro", "incorrecta")


    def test_usuario_inexistente_no_verifica_contrasena(self):
        # Inicializar
        self.repositorio.buscar_por_nombre.return_value = None

        # Ejecutar
        resultado = self.servicio.iniciar_sesion("nadie", "Clave123!")

        # Verificar
        self.assertIsNone(resultado)
        self.protector.verificar.assert_not_called()

    def test_consulta_devuelve_cuenta_activa(self):
        # Inicializar
        self.repositorio.buscar_por_nombre.return_value = self.cuenta

        # Ejecutar
        resultado = self.servicio.consultar_cuenta_activa("ana")

        # Verificar
        self.assertIs(resultado, self.cuenta)
        self.repositorio.buscar_por_nombre.assert_called_once_with("ana")
        self.protector.verificar.assert_not_called()

class TestGestionUsuariosAppService(unittest.TestCase):

    def setUp(self):
        self.repositorio = create_autospec(
            IGestionUsuariosRepositorio, instance=True, spec_set=True)
        self.protector = Mock(spec_set=IProtectorCredenciales)
        self.protector.generar_hash.return_value = "hash-seguro"
        self.servicio = GestionUsuariosAppService(self.repositorio, self.protector)
        self.formulario = {
            "username": " ana ", "nombres": " Ana ", "apellidos": " Perez ",
            "contrasena": "Clave123!", "roles": ["DOCENTE"]
        }

    def test_crea_usuario_con_datos_normalizados_y_clave_protegida(self):
        # Inicializar
        formulario = self.formulario

        # Ejecutar
        self.servicio.crear(formulario, director=False)

        # Verificar
        self.protector.generar_hash.assert_called_once_with("Clave123!")
        self.repositorio.crear.assert_called_once_with(
            {"username": "ana", "nombres": "Ana", "apellidos": "Perez"},
            "hash-seguro", ["DOCENTE"]
        )

    def test_rechaza_contrasena_de_siete_caracteres(self):
        # Inicializar
        self.formulario["contrasena"] = "1234567"

        # Ejecutar y verificar
        with self.assertRaises(ValueError):
            self.servicio.crear(self.formulario, director=False)
        self.repositorio.crear.assert_not_called()
        self.protector.generar_hash.assert_not_called()

    def test_contrasena_nueva_debe_combinar_letras_y_numeros(self):
        for clave in ('abcdefgh', '12345678', '!!!!1234', 'abcdefgh!'):
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                self.servicio.crear({**self.formulario, 'contrasena': clave}, director=False)
        self.repositorio.crear.assert_not_called()
        self.protector.generar_hash.assert_not_called()


    def test_rechaza_username_vacio_sin_persistir(self):
        # Inicializar
        self.formulario["username"] = "   "

        # Ejecutar y verificar
        with self.assertRaises(ValueError):
            self.servicio.crear(self.formulario, director=False)
        self.repositorio.crear.assert_not_called()
        self.protector.generar_hash.assert_not_called()

    def test_estado_invalido_no_se_envia_al_repositorio(self):
        # Inicializar
        estado = "BLOQUEADO"

        # Ejecutar y verificar
        with self.assertRaises(ValueError):
            self.servicio.cambiar_estado(7, estado, director=True)
        self.repositorio.estado.assert_not_called()

    def test_cambiar_roles_entrega_politica_de_director_y_estudiante(self):
        # Inicializar
        roles = ["DOCENTE", "COORDINADOR"]

        # Ejecutar
        self.servicio.cambiar_roles(7, roles, director=False, actor=99)

        # Verificar
        argumentos = self.repositorio.cambiar_roles.call_args.args
        self.assertEqual(argumentos[:2], (7, roles))
        validar = argumentos[2]
        validar({'es_director': False, 'estudiante_vinculado': False})
        with self.assertRaises(PermissionError):
            validar({'es_director': True, 'estudiante_vinculado': False})
        with self.assertRaises(ValueError):
            validar({'es_director': False, 'estudiante_vinculado': True})

    def test_no_cambia_roles_propios_ni_abre_una_transaccion(self):
        with self.assertRaisesRegex(ValueError, 'propia cuenta'):
            self.servicio.cambiar_roles(7, ['DOCENTE'], director=True, actor=7)
        self.repositorio.cambiar_roles.assert_not_called()

    def test_estado_valida_la_cuenta_consultada_por_el_repositorio(self):
        self.servicio.cambiar_estado(7, 'INACTIVO', director=False)
        argumentos = self.repositorio.estado.call_args.args
        self.assertEqual(argumentos[:2], (7, 'INACTIVO'))
        validar = argumentos[2]
        validar({'es_director': False})
        with self.assertRaises(PermissionError):
            validar({'es_director': True})

if __name__ == "__main__":
    unittest.main()
