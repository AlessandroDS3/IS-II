"""Regresiones HTTP del registro de vistas, sesiones y formularios."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'Sistema_Academico'))

from presentacion.controllers.rutas_web import registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb


class TestRutasWeb(unittest.TestCase):
    def setUp(self):
        self.acceso = Mock()
        self.cuenta = dict(id=7, usuario='ana', nombre='Ana', roles=['COORDINADOR'])
        self.acceso.iniciar_sesion.return_value = self.cuenta
        self.acceso.consultar_cuenta_activa.return_value = self.cuenta
        self.servicios = ServiciosWeb(servicio=self.acceso)
        self.app = self.crear_app(self.servicios)
        self.cliente = self.app.test_client()
        # Permite verificar los datos de las vistas sin depender del HTML.
        self.render = patch(
            'presentacion.controllers.rutas_web.render_template',
            side_effect=lambda plantilla, **datos: {'plantilla': plantilla, **datos},
        ).start()
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
            if regla.endpoint in publicas:
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
        self.servicios.servicio = None
        self.assertEqual(self.cliente.post('/').status_code, 503)

    def test_permisos_se_actualizan_desde_la_cuenta_activa(self):
        self.autenticar()
        self.cuenta['roles'] = ['DOCENTE']
        self.assertEqual(self.cliente.get('/coordinador').status_code, 403)
        with self.cliente.session_transaction() as sesion:
            self.assertEqual(sesion['roles'], ['DOCENTE'])

    def test_director_puede_abrir_panel_coordinador(self):
        self.autenticar()
        self.cuenta['roles'] = ['DIRECTOR']
        self.assertEqual(self.cliente.get('/coordinador').status_code, 200)

    def test_cuenta_revocada_o_distinta_limpia_sesion(self):
        for cuenta in [None, {**self.cuenta, 'id': 8}]:
            with self.subTest(cuenta=cuenta):
                self.autenticar()
                self.acceso.consultar_cuenta_activa.return_value = cuenta
                respuesta = self.cliente.get('/coordinador')
                self.assertEqual(respuesta.location, '/')
                with self.cliente.session_transaction() as sesion:
                    self.assertNotIn('usuario', sesion)

    def test_error_al_verificar_sesion_devuelve_503(self):
        self.autenticar()
        self.acceso.consultar_cuenta_activa.side_effect = SQLAlchemyError('sin conexión')
        self.assertEqual(self.cliente.get('/coordinador').status_code, 503)

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

    def test_importacion_de_cartillas_con_respuesta_json(self):
        self.autenticar()
        cartillas = self.servicios.cartillas_servicio = Mock()
        cartillas.preparador.MAX_BYTES = 100
        cartillas.importar_lote.return_value = 2
        respuesta = self.cliente.post('/coordinador/cartillas', data={
            'examen': '3', 'archivos': (io.BytesIO(b'imagen'), 'carpeta/cartilla.png'),
        }, headers={'X-Carga-Lote': '1'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, {'creadas': 2})
        cartillas.importar_lote.assert_called_once_with(3, [('cartilla.png', b'imagen')], 7)

    def test_errores_de_importacion_conservan_json_y_estado(self):
        self.autenticar()
        cartillas = self.servicios.cartillas_servicio = Mock()
        for examen, error, estado in [('0', None, 400), ('3', ValueError('inválido'), 400),
                                      ('3', SQLAlchemyError('sin conexión'), 503)]:
            with self.subTest(examen=examen, estado=estado):
                cartillas.importar_lote.side_effect = error
                respuesta = self.cliente.post('/coordinador/cartillas', data={'examen': examen},
                                              headers={'X-Carga-Lote': '1'})
                self.assertEqual(respuesta.status_code, estado)
                self.assertIn('error', respuesta.json)

    def test_listado_de_cartillas_conserva_paginacion_e_identificacion(self):
        self.autenticar()
        cartillas = self.servicios.cartillas_servicio = Mock()
        cartillas.examenes.return_value = [{'id_examen': 3, 'area': 'Ciencias'}]
        cartillas.listar.return_value = [{'lectura_json': '{"marca": "A"}'} for _ in range(201)]
        cartillas.resumen.return_value = {'total': 201}
        cartillas.opciones_identificacion.return_value = ([], [])
        cartillas.identificar_para_vista.return_value = {'estado': 'PENDIENTE'}
        respuesta = self.cliente.get('/coordinador/cartillas?examen=3&pagina=2&estado=PENDIENTE')
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json
        self.assertEqual(len(datos['entradas']), 200)
        self.assertTrue(datos['hay_siguiente'])
        self.assertEqual(datos['entradas'][0]['lectura'], {'marca': 'A'})
        self.assertEqual(datos['entradas'][0]['identificacion'], {'estado': 'PENDIENTE'})
        cartillas.listar.assert_called_once_with(3, 2, 'PENDIENTE')

    def test_clave_csv_y_formulario_llegan_al_servicio(self):
        self.autenticar()
        diseno = self.servicios.diseno_servicio = Mock()
        for datos in [
            {'examen': '3', 'respuesta_1': 'A', 'motivo': 'Revisión'},
            {'examen': '3', 'archivo': (io.BytesIO(b'\xef\xbb\xbfpregunta,respuesta\n\n1, A\n'), 'clave.csv'),
             'motivo': 'Revisión'},
        ]:
            with self.subTest(datos=datos.keys()):
                respuesta = self.cliente.post('/coordinador/versiones/4/clave', data=datos)
                self.assertEqual(respuesta.location, '/coordinador/configurar-examen?examen=3')
                diseno.crear_clave.assert_called_with(4, {'1': 'A'}, 'Revisión', 7)

    def test_claves_csv_invalidas_no_se_guardan(self):
        self.autenticar()
        diseno = self.servicios.diseno_servicio = Mock()
        for contenido in [b'1,A\n1,B', b'1,A,extra', b'\xff', b'x' * 100001]:
            with self.subTest(contenido=contenido[:15]):
                respuesta = self.cliente.post('/coordinador/versiones/4/clave', data={
                    'examen': '3', 'archivo': (io.BytesIO(contenido), 'clave.csv'),
                })
                self.assertEqual(respuesta.status_code, 302)
                diseno.crear_clave.assert_not_called()
                with self.cliente.session_transaction() as sesion:
                    self.assertEqual(sesion['_flashes'][-1][0], 'error')

    def test_fallo_de_segunda_imagen_elimina_la_primera_guardada(self):
        self.autenticar()
        self.cuenta['roles'] = ['DOCENTE']
        docente = self.servicios.docente_servicio = Mock()
        docente.catalogos.return_value = ([], [], [])
        docente.examenes.return_value = []
        imagenes = self.servicios.imagenes_preguntas = Mock()
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'primera.png'
            ruta.write_bytes(b'imagen')
            imagenes.guardar.side_effect = [(str(ruta), 'image/png'), ValueError('imagen inválida')]
            respuesta = self.cliente.post('/docente/preguntas/nueva', data={
                'imagen_ENUNCIADO': (io.BytesIO(b'imagen'), 'primera.png'),
                'imagen_A': (io.BytesIO(b'invalida'), 'segunda.png'),
            })
            self.assertEqual(respuesta.status_code, 200)
            self.assertFalse(ruta.exists())
            docente.guardar.assert_not_called()


if __name__ == '__main__':
    unittest.main()
