"""Registro de la decisión tomada al revisar una versión de pregunta."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RevisionPregunta:
    version_revisada_id: int | None
    responsable_id: int | None
    decision: str
    observacion: str = ''
    id: int | None = None
    fecha: datetime = field(default_factory=datetime.now)
