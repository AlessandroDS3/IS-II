"""Revisión numerada de la clave de respuestas de una versión de examen."""
from dataclasses import dataclass, field
from datetime import datetime

from dominio.banco_preguntas.letra import LETRAS


@dataclass
class RevisionClave:
    examen_id: int
    cuadernillo_id: int
    numero_revision: int
    respuestas_por_posicion: dict
    responsable_id: int
    motivo: str
    confirmada: bool = False
    creada_en: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def confirmar(self):
        if self.confirmada:
            raise ValueError('La revisión de clave ya está confirmada.')
        if not (self.motivo or '').strip():
            raise ValueError('Indica el motivo de la nueva revisión de clave.')
        if not self.respuestas_por_posicion or any(v not in LETRAS for v in self.respuestas_por_posicion.values()):
            raise ValueError('Cada respuesta debe estar entre A y E.')
        self.confirmada = True
