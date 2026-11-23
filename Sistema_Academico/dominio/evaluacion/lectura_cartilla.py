"""Procesamiento (lectura OMR o manual) de una cartilla."""
from dataclasses import dataclass, field
from datetime import datetime

from dominio.evaluacion.estado_lectura import EstadoLectura


@dataclass
class LecturaCartilla:
    cartilla_id: int
    version_lector: str | None = None
    configuracion_lector: dict | None = None
    responsable_id: int | None = None
    estado: EstadoLectura = EstadoLectura.REQUIERE_REVISION
    procesada_en: datetime = field(default_factory=datetime.now)
    lectura_origen_id_opcional: int | None = None
    confirmada_por_opcional: int | None = None
    confirmada_en_opcional: datetime | None = None
    id: int | None = None
