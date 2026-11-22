"""Registro de las rutas HTTP. Cada contexto define sus rutas en su propio módulo."""
from flask import abort, request, session

from dominio.identidad_acceso.autorizacion import Autorizacion
from presentacion.controllers import (rutas_banco_preguntas, rutas_diseno, rutas_evaluacion, rutas_identidad,
                                      rutas_organizacion, rutas_publicacion)
from presentacion.controllers.soporte_web import ETAPAS_EXAMEN, crear_proteger

# Páginas de detalle que se muestran dentro de la etapa indicada del espacio del examen.
ETAPA_DE_DETALLE = {'detalle_resultado_coordinador': 'resultados_coordinador', 'detalle_carga': 'cartillas'}
MODULOS_DE_RUTAS = (rutas_identidad, rutas_organizacion, rutas_banco_preguntas, rutas_diseno, rutas_evaluacion, rutas_publicacion)


def _registrar_contexto_examen(app, servicios):
    simulacros = servicios.simulacros
    cartillas = servicios.cartillas

    def examen_de_la_peticion():
        if request.endpoint == 'detalle_carga' and cartillas:
            entrada = cartillas.obtener(request.view_args['id'])
            return entrada['examen_id'] if entrada else 0
        return request.values.get('examen', type=int)

    @app.context_processor
    def contexto_navegacion():
        etapa = ETAPA_DE_DETALLE.get(request.endpoint, request.endpoint)
        if (etapa not in ETAPAS_EXAMEN or request.endpoint == 'espacio_examen'
                or not simulacros or not session.get('usuario')
                or not Autorizacion.puede_acceder(session.get('roles', []), 'COORDINADOR')):
            return {}
        examen = examen_de_la_peticion()
        if not examen:
            return {}
        contexto = simulacros.contexto_examen(examen)
        if not contexto:
            abort(404)
        return {'contexto_examen': contexto, 'etapas_examen': ETAPAS_EXAMEN, 'etapa_examen': etapa}


def registrar_rutas(app, servicios):
    """Registra el menú contextual del examen y las rutas de todos los módulos."""
    _registrar_contexto_examen(app, servicios)
    proteger = crear_proteger(app, servicios.acceso)
    for modulo in MODULOS_DE_RUTAS:
        modulo.registrar(app, proteger, servicios)
