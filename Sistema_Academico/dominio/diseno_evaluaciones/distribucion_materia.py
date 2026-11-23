"""Cantidad de preguntas y puntaje por pregunta de una materia dentro de un examen."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DistribucionMateria:
    materia_id: int
    cantidad_preguntas: int
    puntaje_por_pregunta: Decimal
    eje_id: int | None = None

    def puntaje_materia_derivado(self):
        return Decimal(self.cantidad_preguntas) * Decimal(self.puntaje_por_pregunta)
