"""Grupo académico de un ciclo."""
from dataclasses import dataclass

from dominio.organizacion_academica.registro_activable import RegistroActivable


@dataclass
class Grupo(RegistroActivable):
    ciclo_id: int | None = None
    horario: str | None = None
    aula: str | None = None
