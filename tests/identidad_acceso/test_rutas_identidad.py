"""Regresiones HTTP del registro de vistas, sesiones y formularios."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'Sistema_Academico'))

from _soporte import registrar_rutas_identidad_prueba as registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb


class TestRutasWeb(unittest.TestCase):
    def setUp(self):
        self.acceso = Mock()
        self.cuenta = dict(id=7, usuario='ana', nombre='Ana', roles=['COORDINADOR'])
        self.acceso.iniciar_sesion.return_value = self.cuenta
        self.acceso.consultar_cuenta_activa.return_value = self.cuenta
        self.servicios = ServiciosWeb(acceso=self.acceso, usuarios=Mock())
        self.servicios.usuarios.listar.return_value = []
        self.app = self.crear_app(self.servicios)
        self.cliente = self.app.test_client()
        # Permite verificar los datos de las vistas sin depender del HTML.
        self.render = patch(
            'presentacion.controllers.rutas_identidad.render_template',
            side_effect=lambda plantilla, **datos: {'plantilla': plantilla, **datos},
        ).start()
        patch('presentacion.controllers.soporte_web.render_template', side_effect=self.render.side_effect).start()
        self.addCleanup(patch.stopall)

    def crear_app(self, servicios):
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY='pruebas')
        app.logger.disabled = True
        registrar_rutas(app, servicios)
        return app

    def autenticar(self):
        with self.cliente.session_transaction() as sesion:
            sesion.update(usuario='ana', usuario_id=7, nombre='Ana', roles=['COORDINADOR'])

    def test_todas_las_rutas_privadas_exigen_sesion(self):
        publicas = {'static', 'login', 'elegir_rol', 'salir'}
        for regla in self.app.url_map.iter_rules():
            if regla.endpoint not in {'usuarios', 'estado_usuario', 'cambiar_roles_usuario'}:
                continue
            url = str(regla).replace('<int:id>', '1').replace('<int:simulacro_id>', '1')
            for metodo in regla.methods - {'HEAD', 'OPTIONS'}:
                with self.subTest(endpoint=regla.endpoint, metodo=metodo):
                    respuesta = self.cliente.open(url, method=metodo)
                    self.assertEqual(respuesta.status_code, 302)
                    self.assertEqual(respuesta.location, '/')
        self.acceso.consultar_cuenta_activa.assert_not_called()

    def test_login_y_seleccion_de_rol(self):
        for roles, destino in [(['COORDINADOR'], '/coordinador'), (['DOCENTE'], '/docente'),
                               (['DIRECTOR'], '/director'), (['ESTUDIANTE'], '/estudiante'),
                               (['COORDINADOR', 'DOCENTE'], '/elegir-rol')]:
            with self.subTest(roles=roles):
                self.cuenta['roles'] = roles
                respuesta = self.cliente.post('/', data={'usuario': 'ana', 'contrasena': 'clave'})
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(respuesta.location, destino)
                with self.cliente.session_transaction() as sesion:
                    self.assertEqual(sesion['roles'], roles)
                    self.assertEqual(sesion['usuario_id'], 7)

    def test_errores_de_login_conservan_codigos_http(self):
        for cuenta, error, estado in [(None, None, 401),
                                      ({**self.cuenta, 'roles': []}, None, 403),
                                      (None, SQLAlchemyError('sin conexión'), 503)]:
            with self.subTest(estado=estado):
                self.acceso.iniciar_sesion.return_value = cuenta
                self.acceso.iniciar_sesion.side_effect = error
                respuesta = self.cliente.post('/')
                self.assertEqual(respuesta.status_code, estado)
                self.assertEqual(respuesta.json['plantilla'], 'comun/login.html')

    def test_sin_servicio_de_acceso_login_devuelve_503(self):
        cliente = self.crear_app(ServiciosWeb()).test_client()
        self.assertEqual(cliente.post('/').status_code, 503)

    def test_cambiar_roles_sin_servicio_responde_503_y_conserva_la_sesion(self):
        self.app = self.crear_app(ServiciosWeb(acceso=self.acceso))
        self.cliente = self.app.test_client()
        self.autenticar()
        respuesta = self.cliente.post('/coordinador/usuarios/8/roles',
                                      data={'roles': ['DOCENTE']})
        self.assertEqual(respuesta.status_code, 503)
        with self.cliente.session_transaction() as sesion:
            self.assertEqual(sesion['usuario_id'], 7)

    def test_cinco_fallos_bloquean_la_siguiente_peticion_sin_consultar_cuenta(self):
        self.acceso.iniciar_sesion.return_value = None
        for _ in range(5):
            self.assertEqual(self.cliente.post('/', data={'usuario': ' ana '}).status_code, 401)
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 429)
        self.assertEqual(self.acceso.iniciar_sesion.call_count, 5)

    def test_bloqueo_no_afecta_a_otro_usuario(self):
        self.acceso.iniciar_sesion.return_value = None
        for _ in range(5):
            self.cliente.post('/', data={'usuario': 'ana'})
        self.assertEqual(self.cliente.post('/', data={'usuario': 'otro'}).status_code, 401)

    def test_bloqueo_vence_y_login_correcto_reinicia_los_fallos(self):
        tiempo = [1000]
        self.app.extensions['limitador_acceso'].reloj = lambda: tiempo[0]
        self.acceso.iniciar_sesion.return_value = None
        for _ in range(5):
            self.cliente.post('/', data={'usuario': 'ana'})
        self.acceso.iniciar_sesion.return_value = self.cuenta
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 429)
        tiempo[0] += 300
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 302)
        self.acceso.iniciar_sesion.return_value = None
        for _ in range(4):
            self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 401)
        self.acceso.iniciar_sesion.return_value = self.cuenta
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 302)
        self.acceso.iniciar_sesion.return_value = None
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 401)

    def test_fallos_de_base_de_datos_no_bloquean_la_cuenta(self):
        self.acceso.iniciar_sesion.side_effect = SQLAlchemyError('sin conexión')
        for _ in range(6):
            self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 503)
        self.acceso.iniciar_sesion.side_effect = None
        self.assertEqual(self.cliente.post('/', data={'usuario': 'ana'}).status_code, 302)

    def test_permisos_se_actualizan_desde_la_cuenta_activa(self):
        self.autenticar()
        self.cuenta['roles'] = ['DOCENTE']
        self.assertEqual(self.cliente.get('/coordinador/usuarios').status_code, 403)
        with self.cliente.session_transaction() as sesion:
            self.assertEqual(sesion['roles'], ['DOCENTE'])

    def test_director_puede_abrir_panel_coordinador(self):
        self.autenticar()
        self.cuenta['roles'] = ['DIRECTOR']
        self.assertEqual(self.cliente.get('/coordinador/usuarios').status_code, 200)

    def test_cuenta_revocada_o_distinta_limpia_sesion(self):
        for cuenta in [None, {**self.cuenta, 'id': 8}]:
            with self.subTest(cuenta=cuenta):
                self.autenticar()
                self.acceso.consultar_cuenta_activa.return_value = cuenta
                respuesta = self.cliente.get('/coordinador/usuarios')
                self.assertEqual(respuesta.location, '/')
                with self.cliente.session_transaction() as sesion:
                    self.assertNotIn('usuario', sesion)

    def test_error_al_verificar_sesion_devuelve_503(self):
        self.autenticar()
        self.acceso.consultar_cuenta_activa.side_effect = SQLAlchemyError('sin conexión')
        self.assertEqual(self.cliente.get('/coordinador/usuarios').status_code, 503)

    def test_dependencias_aisladas_entre_aplicaciones(self):
        otra = self.crear_app(ServiciosWeb()).test_client()
        self.assertEqual(otra.post('/').status_code, 503)
        self.assertEqual(self.cliente.post('/').location, '/coordinador')

    def test_salir_limpia_sesion_y_solo_acepta_post(self):
        self.autenticar()
        self.assertEqual(self.cliente.get('/salir').status_code, 405)
        self.assertEqual(self.cliente.post('/salir').location, '/')
        with self.cliente.session_transaction() as sesion:
            self.assertNotIn('usuario', sesion)








if __name__ == '__main__':
    unittest.main()
