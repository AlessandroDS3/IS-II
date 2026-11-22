"""Materia perteneciente a un eje temático."""
from dataclasses import dataclass

from dominio.organizacion_academica.registro_activable import RegistroActivable


@dataclass
class Materia(RegistroActivable):
    eje_id: int | None = None
