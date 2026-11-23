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

    def test_servicio_autentica_cuenta_persistida_y_rechaza_cuenta_inactiva(self):
        self.gestion.crear(self.formulario, director=False)
        cuenta = self.sesiones.iniciar_sesion(' ana ', 'Clave123!')
        self.assertEqual(cuenta['usuario'], 'ana')
        self.assertEqual(cuenta['roles'], ['DOCENTE'])
        with self.motor.begin() as conexion:
            conexion.execute(text("UPDATE usuarios SET estado='INACTIVO'"))
        self.assertIsNone(self.sesiones.iniciar_sesion('ana', 'Clave123!'))

    def test_cambiar_roles_sin_duplicar_perfiles_y_actualizar_estado(self):
        self.gestion.crear(self.formulario, director=False)
        cuenta = self.sesiones.iniciar_sesion('ana', 'Clave123!')
        roles = ['DOCENTE', 'COORDINADOR']
        for _ in range(2):
            self.gestion.cambiar_roles(cuenta['id'], roles, director=True, actor=99)
        self.assertEqual(len(self.consultar('SELECT * FROM docentes')), 1)
        self.assertEqual(len(self.consultar('SELECT * FROM coordinadores')), 1)
        self.assertEqual(set(self.sesiones.consultar_cuenta_activa('ana')['roles']), set(roles))
        self.gestion.cambiar_estado(cuenta['id'], 'INACTIVO', director=True)
        self.assertIsNone(self.sesiones.consultar_cuenta_activa('ana'))

    def test_cuenta_director_no_se_modifica_por_otro_rol(self):
        self.formulario['roles'] = ['DIRECTOR']
        self.gestion.crear(self.formulario, director=True)
        cuenta = self.sesiones.consultar_cuenta_activa('ana')
        with self.assertRaises(PermissionError):
            self.gestion.cambiar_roles(cuenta['id'], ['DOCENTE'], director=False, actor=99)
        with self.assertRaises(PermissionError):
            self.gestion.cambiar_estado(cuenta['id'], 'INACTIVO', director=False)
        self.assertEqual(self.sesiones.consultar_cuenta_activa('ana')['roles'], ['DIRECTOR'])
        self.assertEqual(self.consultar('SELECT * FROM docentes'), [])

    def test_estudiante_vinculado_conserva_su_rol_sin_cambios_parciales(self):
        self.formulario['roles'] = ['ESTUDIANTE']
        self.gestion.crear(self.formulario, director=True)
        cuenta = self.sesiones.consultar_cuenta_activa('ana')
        with self.motor.begin() as conexion:
            conexion.execute(text('INSERT INTO estudiantes(id_usuario) VALUES (:id)'),
                             {'id': cuenta['id']})
        with self.assertRaisesRegex(ValueError, 'vinculada'):
            self.gestion.cambiar_roles(cuenta['id'], ['DOCENTE'], director=True, actor=99)
        self.assertEqual(self.sesiones.consultar_cuenta_activa('ana')['roles'], ['ESTUDIANTE'])
        self.gestion.cambiar_roles(cuenta['id'], ['ESTUDIANTE'], director=True, actor=99)

    def test_fallo_al_crear_perfil_revierte_el_cambio_de_roles(self):
        self.gestion.crear(self.formulario, director=False)
        cuenta = self.sesiones.consultar_cuenta_activa('ana')
        with self.motor.begin() as conexion:
            conexion.execute(text('DROP TABLE coordinadores'))
        from sqlalchemy.exc import SQLAlchemyError
        with self.assertRaises(SQLAlchemyError):
            self.gestion.cambiar_roles(cuenta['id'], ['COORDINADOR'], director=True, actor=99)
        self.assertEqual(self.sesiones.consultar_cuenta_activa('ana')['roles'], ['DOCENTE'])

if __name__ == "__main__":
    unittest.main()
