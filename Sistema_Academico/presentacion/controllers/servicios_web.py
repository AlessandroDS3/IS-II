"""Dependencias de las vistas, agrupadas para componer cada aplicación."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aplicacion.servicios.calculo_resultado_app_service import CalculoResultadoAppService
    from aplicacion.servicios.cuenta_usuario_app_service import CuentaUsuarioAppService
    from aplicacion.servicios.diseno_examen_app_service import DisenoExamenAppService
    from aplicacion.servicios.docente_app_service import DocenteAppService
    from aplicacion.servicios.estudiante_app_service import EstudianteAppService
    from aplicacion.servicios.gestion_usuarios_app_service import GestionUsuariosAppService
    from aplicacion.servicios.importacion_cartillas_app_service import ImportacionCartillasAppService
    from aplicacion.servicios.organizacion_app_service import OrganizacionAppService
    from aplicacion.servicios.panel_pendientes_app_service import PanelPendientesAppService
    from aplicacion.servicios.pregunta_app_service import PreguntaAppService
    from aplicacion.servicios.resultados_app_service import ResultadosAppService
    from aplicacion.servicios.simulacro_app_service import SimulacroAppService
    from infraestructura.archivos.imagenes_preguntas import ImagenesPreguntas


@dataclass(kw_only=True)
class ServiciosWeb:
    servicio: CuentaUsuarioAppService | None = None
    estudiantes_servicio: EstudianteAppService | None = None
    usuarios_servicio: GestionUsuariosAppService | None = None
    organizacion_servicio: OrganizacionAppService | None = None
    panel_servicio: PanelPendientesAppService | None = None
    simulacros_servicio: SimulacroAppService | None = None
    preguntas_servicio: PreguntaAppService | None = None
    cartillas_servicio: ImportacionCartillasAppService | None = None
    resultados_servicio: ResultadosAppService | None = None
    docente_servicio: DocenteAppService | None = None
    imagenes_preguntas: ImagenesPreguntas | None = None
    diseno_servicio: DisenoExamenAppService | None = None
    calculo_servicio: CalculoResultadoAppService | None = None
