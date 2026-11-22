"""Versión del contenido de una pregunta; una vez sellada no se modifica."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VersionPregunta:
    numero: int
    enunciado: str
    alternativa_correcta: str
    creada_por: int | None = None
    tema: int | None = None
    id: int | None = None
    imagen_opcional: str | None = None
    formula_opcional: str | None = None
    creada_en: datetime = field(default_factory=datetime.now)
    sellada: bool = False

    def sellar(self):
        self.sellada = True
