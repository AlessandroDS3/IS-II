import unittest

from Sistema_Academico.dominio.identidad_acceso.cuenta_usuario import CuentaUsuario


class TestEstadoCuentaUsuario(unittest.TestCase):

    def test_activar_cuenta(self):
        # Inicializar
        cuenta = CuentaUsuario()
        cuenta.activa = False

        # Ejecutar
        cuenta.activar()

        # Verificar
        self.assertTrue(cuenta.activa)

    def test_desactivar_cuenta(self):
        # Inicializar
        cuenta = CuentaUsuario()
        cuenta.activa = True

        # Ejecutar
        cuenta.desactivar()

        # Verificar
        self.assertFalse(cuenta.activa)

    def test_asignar_roles_valida_y_no_comparte_la_lista_recibida(self):
        cuenta = CuentaUsuario()
        roles = ['DOCENTE']
        cuenta.asignar_roles(roles)
        roles.append('DIRECTOR')
        self.assertEqual(cuenta.roles, ['DOCENTE'])

    def test_roles_invalidos_o_sin_autorizacion_conservan_roles_previos(self):
        cuenta = CuentaUsuario()
        cuenta.asignar_roles(['DOCENTE'])
        for roles, error in [([], ValueError), (['ADMIN'], ValueError),
                             (['ESTUDIANTE', 'DOCENTE'], ValueError),
                             (['DIRECTOR'], PermissionError)]:
            with self.subTest(roles=roles), self.assertRaises(error):
                cuenta.asignar_roles(roles)
            self.assertEqual(cuenta.roles, ['DOCENTE'])

    def test_asignacion_de_director_requiere_autorizacion_explicita(self):
        cuenta = CuentaUsuario()
        cuenta.asignar_roles(['DIRECTOR'], director=True)
        self.assertEqual(cuenta.roles, ['DIRECTOR'])

    def test_cambiar_credencial_rechaza_valores_vacios_sin_perder_el_hash(self):
        cuenta = CuentaUsuario()
        cuenta.cambiar_credencial('hash-protegido')
        for invalido in [None, '', '   ', 123]:
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                cuenta.cambiar_credencial(invalido)
            self.assertEqual(cuenta.password_hash, 'hash-protegido')


if __name__ == "__main__":
    unittest.main()
