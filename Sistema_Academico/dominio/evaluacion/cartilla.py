"""Cartilla física recibida dentro de una participación."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Cartilla:
    numero_recepcion: int
    cuadernillo_id: int
    imagen: str
    recibida_por: int | None = None
    recibida_en: datetime = field(default_factory=datetime.now)
    vigente: bool = True
    motivo_reemplazo_opcional: str | None = None
    motivo_recepcion_tardia_opcional: str | None = None
    cartilla_origen_id_opcional: int | None = None
    invalidada_por_rectificacion_id_opcional: int | None = None
    lectura_confirmada_id_opcional: int | None = None
    id: int | None = None
