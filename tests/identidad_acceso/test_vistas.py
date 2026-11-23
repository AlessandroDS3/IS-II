"""Mensajes accesibles de la vista de gestion de cuentas."""
from pathlib import Path
import unittest
from unittest.mock import Mock

from flask import Flask, flash, render_template, session
from flask_wtf.csrf import CSRFProtect
import _soporte
from presentacion.controllers.rutas_web import registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb


class TestVistaUsuarios(unittest.TestCase):
    def pagina_usuarios(self, roles_actor, roles_cuenta='DOCENTE'):
        vistas = Path(__file__).resolve().parents[2] / 'Sistema_Academico/presentacion/vistas'
        app = Flask(__name__, template_folder=str(vistas))
        app.config.update(TESTING=True, SECRET_KEY='solo-pruebas')
        CSRFProtect(app)
        acceso = Mock()
        acceso.consultar_cuenta_activa.return_value = {
            'id': 1, 'roles': roles_actor,
        }
        usuarios = Mock()
        usuarios.listar.return_value = [{
            'id_usuario': 7, 'username': '<script>alert(1)</script>',
            'nombres': 'Ana', 'apellidos': 'Perez', 'roles': roles_cuenta,
            'estado': 'ACTIVO',
        }]
        registrar_rutas(app, ServiciosWeb(servicio=acceso, usuarios_servicio=usuarios))
        cliente = app.test_client()
        with cliente.session_transaction() as sesion:
            sesion.update(usuario='actor', usuario_id=1, nombre='Actor', roles=roles_actor)
        respuesta = cliente.get('/coordinador/usuarios')
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_data(as_text=True)

    def test_formularios_comparten_roles_y_conservan_seleccion_csrf_y_escape(self):
        html = self.pagina_usuarios(['COORDINADOR'])
        for rol in ('ESTUDIANTE', 'DOCENTE', 'COORDINADOR'):
            self.assertEqual(html.count(f'name="roles" value="{rol}"'), 2)
        self.assertNotIn('value="DIRECTOR"', html)
        self.assertIn('value="DOCENTE" checked', html)
        self.assertEqual(html.count('name="csrf_token"'), html.count('<form'))
        self.assertIn('/coordinador/usuarios/7/roles', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)

    def test_director_disponible_solo_para_actor_director(self):
        html = self.pagina_usuarios(['DIRECTOR'], 'DIRECTOR')
        self.assertEqual(html.count('name="roles" value="DIRECTOR"'), 2)
        self.assertIn('value="DIRECTOR" checked', html)
        html = self.pagina_usuarios(['COORDINADOR'], 'DIRECTOR')
        self.assertIn('Solo director', html)
        self.assertNotIn('/coordinador/usuarios/7/roles', html)

    def test_mensaje_se_renderiza_en_output_y_conserva_escape_html(self):
        vistas = Path(__file__).resolve().parents[2] / 'Sistema_Academico/presentacion/vistas'
        app = Flask(__name__, template_folder=str(vistas))
        app.secret_key = 'solo-pruebas'
        CSRFProtect(app)
        registrar_rutas(app, ServiciosWeb())
        with app.test_request_context():
            session['roles'] = ['COORDINADOR']
            flash('Cuenta <script>alert(1)</script> registrada.', 'ok')
            html = render_template(
                'coordinador/usuarios.html', rol='Coordinador', nombre='Ana',
                usuarios=[], es_director=False, contexto_examen=None,
            )
        self.assertIn('<output>Cuenta &lt;script&gt;alert(1)&lt;/script&gt; registrada.</output>', html)
        self.assertNotIn('role="status"', html)
        self.assertNotIn('<script>', html)
