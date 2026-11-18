"""Mensajes accesibles de la vista de gestion de cuentas."""
from pathlib import Path
import unittest

from flask import Flask, flash, render_template, session
from flask_wtf.csrf import CSRFProtect
import _soporte
from presentacion.controllers.rutas_web import registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb


class TestVistaUsuarios(unittest.TestCase):
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
