"""Alternativa de respuesta de una versión de pregunta."""
from dataclasses import dataclass

from dominio.banco_preguntas.letra import Letra


@dataclass(frozen=True)
class Alternativa:
    letra: Letra
    texto: str
    imagen_opcional: str | None = None
    formula_opcional: str | None = None
