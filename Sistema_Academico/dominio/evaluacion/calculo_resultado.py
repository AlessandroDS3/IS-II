"""Resultado calculado de una cartilla; debe revisarse antes de publicarse."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from dominio.evaluacion.estado_calculo import EstadoCalculo


@dataclass
class CalculoResultado:
    participacion_id: int
    cartilla_id: int
    lectura_id: int
    revision_clave_id: int
    revision_politica_id: int
    calculado_por: int
    puntaje_total: Decimal = Decimal(0)
    aciertos: int = 0
    incorrectas: int = 0
    blancos: int = 0
    conjunto_id: int | None = None
    estado_revision: EstadoCalculo = EstadoCalculo.CALCULADO
    calculado_en: datetime = field(default_factory=datetime.now)
    revisado_por_opcional: int | None = None
    revisado_en_opcional: datetime | None = None
    id: int | None = None

    def marcar_revisado(self, revisor_id, fecha=None):
        if self.estado_revision != EstadoCalculo.CALCULADO:
            raise ValueError('El resultado no está disponible para revisión.')
        self.estado_revision = EstadoCalculo.REVISADO
        self.revisado_por_opcional = revisor_id
        self.revisado_en_opcional = fecha or datetime.now()
