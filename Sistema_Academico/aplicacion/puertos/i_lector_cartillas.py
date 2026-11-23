"""Puerto del lector óptico de cartillas."""
from typing import Any, NotRequired, Protocol, TypedDict


class PropuestaLectura(TypedDict):
    """Resultado de leer una cartilla. Si exito es False, error explica el rechazo."""
    exito: bool
    version_lector: str
    error: NotRequired[str]
    dni: NotRequired[str | None]
    controles: NotRequired[dict[str, Any]]
    respuestas: NotRequired[list[dict[str, Any]]]
    resumen: NotRequired[dict[str, Any]]
    detalle: NotRequired[dict[str, Any]]


class ILectorCartillas(Protocol):
    def leer(self, imagen_ref, plantilla_ref=None) -> PropuestaLectura:
        """Lee la imagen; plantilla_ref None usa la plantilla incluida con el lector."""
