"""Contenedor de los servicios que necesita la capa web (inyección de dependencias)."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiciosWeb:
    """Cada campo es None cuando la base de datos no está configurada; las rutas responden 503."""
    acceso: Any = None
    usuarios: Any = None
    estudiantes: Any = None
    organizacion: Any = None
    panel: Any = None
    simulacros: Any = None
    diseno: Any = None
    preguntas: Any = None
    autoria: Any = None
    imagenes_preguntas: Any = None
    cartillas: Any = None
    revision_lecturas: Any = None
    calculo: Any = None
    publicacion: Any = None
    resultados_estudiante: Any = None
