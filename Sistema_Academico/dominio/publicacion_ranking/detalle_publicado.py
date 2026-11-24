"""Detalle por pregunta de un resultado publicado."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DetallePublicado:
    posicion: int
    item_id: int
    pregunta_id: int
    version_pregunta_id: int
    respuesta_efectiva: str | None
    respuesta_correcta: str
    tipo_resultado: str
    puntaje_aplicado: Decimal
    materia_id: int | None = None
    autor_id: int | None = None
    respuesta_observada: str | None = None
