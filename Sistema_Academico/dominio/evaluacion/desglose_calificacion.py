"""Resultado completo de calificar una cartilla."""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class DesgloseCalificacion:
    detalles: list = field(default_factory=list)
    materias: dict = field(default_factory=dict)
    correctas: int = 0
    incorrectas: int = 0
    blancos: int = 0
    puntaje_total: Decimal = Decimal(0)
