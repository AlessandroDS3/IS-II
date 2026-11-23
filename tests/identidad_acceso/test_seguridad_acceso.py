"""Política de contraseñas y vencimiento del límite con un reloj simulado."""
import unittest
import _soporte
from dominio.identidad_acceso.limitador_intentos import LimitadorIntentos
from dominio.identidad_acceso.politica_contrasena import validar_contrasena


class TestPoliticaContrasena(unittest.TestCase):
    def test_rechaza_valores_invalidos_y_contrasenas_sin_la_combinacion(self):
        for clave in (None, 12345678, '', '   ', 'Abc1234', 'abcdefgh', '12345678'):
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                validar_contrasena(clave)

    def test_acepta_longitud_minima_y_contrasenas_mas_largas(self):
        for clave in ('Abcd1234', 'UnaClave1234!'):
            self.assertIsNone(validar_contrasena(clave))


class TestLimitadorIntentos(unittest.TestCase):
    def setUp(self):
        self.tiempo = 1000
        self.limitador = LimitadorIntentos(reloj=lambda: self.tiempo)

    def test_quinto_fallo_bloquea_y_el_limite_vence_a_los_cinco_minutos(self):
        for _ in range(4):
            self.limitador.registrar_fallo('ana')
        self.assertFalse(self.limitador.bloqueado('ana'))
        self.limitador.registrar_fallo('ana')
        self.assertTrue(self.limitador.bloqueado('ana'))
        self.tiempo += 299
        self.assertTrue(self.limitador.bloqueado('ana'))
        self.tiempo += 1
        self.assertFalse(self.limitador.bloqueado('ana'))

    def test_ventana_descarta_fallos_antiguos_sin_borrar_los_recientes(self):
        self.limitador.registrar_fallo('ana')
        self.tiempo += 100
        for _ in range(4):
            self.limitador.registrar_fallo('ana')
        self.assertTrue(self.limitador.bloqueado('ana'))
        self.tiempo += 200
        self.assertFalse(self.limitador.bloqueado('ana'))
        self.limitador.registrar_fallo('ana')
        self.assertTrue(self.limitador.bloqueado('ana'))

    def test_reinicio_por_exito_no_modifica_otros_usuarios(self):
        for _ in range(5):
            self.limitador.registrar_fallo('ana')
            self.limitador.registrar_fallo('luis')
        self.limitador.reiniciar('ana')
        self.assertFalse(self.limitador.bloqueado('ana'))
        self.assertTrue(self.limitador.bloqueado('luis'))
