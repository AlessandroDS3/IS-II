"""Resultado de un estudiante dentro de una publicación."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EntradaPublicada:
    estudiante_id: int
    participacion_id: int | None
    calculo_id: int
    puntaje: Decimal
    puesto: int | None = None
