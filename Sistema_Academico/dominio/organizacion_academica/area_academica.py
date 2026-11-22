"""Área académica (Ingenierías, Biomédicas, Sociales...)."""
from dataclasses import dataclass

from dominio.organizacion_academica.registro_activable import RegistroActivable


@dataclass
class AreaAcademica(RegistroActivable):
    codigo: str = ''
