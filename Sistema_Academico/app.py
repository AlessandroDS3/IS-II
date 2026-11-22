"""Composición de la aplicación Flask y de sus dependencias."""
import logging
import os
import secrets
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import create_engine

from aplicacion.servicios.autoria_preguntas_app_service import AutoriaPreguntasAppService
from aplicacion.servicios.calculo_resultado_app_service import CalculoResultadoAppService
from aplicacion.servicios.cuenta_usuario_app_service import CuentaUsuarioAppService
from aplicacion.servicios.diseno_examen_app_service import DisenoExamenAppService
from aplicacion.servicios.estudiante_app_service import EstudianteAppService
from aplicacion.servicios.gestion_usuarios_app_service import GestionUsuariosAppService
from aplicacion.servicios.importacion_cartillas_app_service import ImportacionCartillasAppService
from aplicacion.servicios.organizacion_app_service import OrganizacionAppService
from aplicacion.servicios.panel_pendientes_app_service import PanelPendientesAppService
from aplicacion.servicios.pregunta_app_service import PreguntaAppService
from aplicacion.servicios.publicacion_examen_app_service import PublicacionExamenAppService
from aplicacion.servicios.resultados_estudiante_app_service import ResultadosEstudianteAppService
from aplicacion.servicios.revision_lecturas_app_service import RevisionLecturasAppService
from aplicacion.servicios.simulacro_app_service import SimulacroAppService
from infraestructura.archivos.imagenes_preguntas import ImagenesPreguntas
from infraestructura.archivos.preparador_cartillas import PreparadorCartillas
from infraestructura.persistencia.repositories.calculo_resultados_repositorio import CalculoResultadosRepositorio
from infraestructura.persistencia.repositories.cargas_omr_repositorio import CargasOMRRepositorio
from infraestructura.persistencia.repositories.cuenta_usuario_orm_repositorio import CuentaUsuarioORMRepositorio
from infraestructura.persistencia.repositories.diseno_examen_repositorio import DisenoExamenRepositorio
from infraestructura.persistencia.repositories.estudiante_orm_repositorio import EstudianteORMRepositorio
from infraestructura.persistencia.repositories.examen_orm_repositorio import ExamenORMRepositorio
from infraestructura.persistencia.repositories.gestion_usuarios_repositorio import GestionUsuariosRepositorio
from infraestructura.persistencia.repositories.organizacion_repositorio import OrganizacionRepositorio
from infraestructura.persistencia.repositories.panel_pendientes_repositorio import PanelPendientesRepositorio
from infraestructura.persistencia.repositories.pregunta_orm_repositorio import PreguntaORMRepositorio
from infraestructura.persistencia.repositories.preguntas_docente_repositorio import PreguntasDocenteRepositorio
from infraestructura.persistencia.repositories.publicacion_examen_orm_repositorio import PublicacionExamenORMRepositorio
from infraestructura.persistencia.repositories.resultados_estudiante_repositorio import ResultadosEstudianteRepositorio
from infraestructura.persistencia.repositories.revision_lecturas_repositorio import RevisionLecturasRepositorio
from infraestructura.persistencia.repositories.simulacro_orm_repositorio import SimulacroORMRepositorio
from infraestructura.seguridad.protector_credenciales_werkzeug import ProtectorCredencialesWerkzeug
from infraestructura.vision.lector_burbujas_opencv import LectorBurbujasOpenCV
from presentacion.controllers.rutas_web import registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb

logger = logging.getLogger(__name__)

RAIZ = Path(__file__).parent
DATOS_PRIVADOS = RAIZ / 'datos_privados'
MAX_SUBIDA_BYTES = 40 * 1024 * 1024


def _clave_secreta():
    clave = os.environ.get('SISTEMA_SECRET_KEY')
    if clave:
        return clave
    logger.warning('SISTEMA_SECRET_KEY no está definida: se usa una clave temporal y las sesiones se perderán al reiniciar. '
                   'Defínela en producción y cuando se usen varios procesos.')
    return secrets.token_hex(32)


def _cookie_segura():
    return os.environ.get('SISTEMA_COOKIE_SECURE', '').lower() in ('1', 'true', 'si', 'sí')


def construir_servicios(motor, protector):
    """Crea los servicios de aplicación conectados a sus repositorios."""
    return ServiciosWeb(
        acceso=CuentaUsuarioAppService(CuentaUsuarioORMRepositorio(motor), protector),
        usuarios=GestionUsuariosAppService(GestionUsuariosRepositorio(motor), protector),
        estudiantes=EstudianteAppService(EstudianteORMRepositorio(motor)),
        organizacion=OrganizacionAppService(OrganizacionRepositorio(motor)),
        panel=PanelPendientesAppService(PanelPendientesRepositorio(motor)),
        simulacros=SimulacroAppService(SimulacroORMRepositorio(motor), ExamenORMRepositorio(motor)),
        diseno=DisenoExamenAppService(DisenoExamenRepositorio(motor)),
        preguntas=PreguntaAppService(PreguntaORMRepositorio(motor)),
        autoria=AutoriaPreguntasAppService(PreguntasDocenteRepositorio(motor)),
        imagenes_preguntas=ImagenesPreguntas(DATOS_PRIVADOS / 'preguntas'),
        cartillas=ImportacionCartillasAppService(CargasOMRRepositorio(motor), PreparadorCartillas(DATOS_PRIVADOS / 'cartillas'),
                                                 LectorBurbujasOpenCV()),
        revision_lecturas=RevisionLecturasAppService(RevisionLecturasRepositorio(motor)),
        calculo=CalculoResultadoAppService(CalculoResultadosRepositorio(motor)),
        publicacion=PublicacionExamenAppService(PublicacionExamenORMRepositorio(motor)),
        resultados_estudiante=ResultadosEstudianteAppService(ResultadosEstudianteRepositorio(motor)),
    )


def crear_app(servicio_prueba=None, database_url=None):
    """Crea la aplicación. database_url tiene prioridad sobre la variable SISTEMA_DATABASE_URL."""
    app = Flask(__name__, template_folder='presentacion/vistas', static_folder='presentacion/vistas/recursos', static_url_path='/recursos')
    app.secret_key = _clave_secreta()
    CSRFProtect(app)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=_cookie_segura(),
                      MAX_CONTENT_LENGTH=MAX_SUBIDA_BYTES)
    url = database_url or os.environ.get('SISTEMA_DATABASE_URL')
    if url:
        servicios = construir_servicios(create_engine(url, pool_pre_ping=True), ProtectorCredencialesWerkzeug())
    else:
        servicios = ServiciosWeb(acceso=servicio_prueba)
    registrar_rutas(app, servicios)
    return app


if __name__ == '__main__':
    crear_app().run(debug=False)
