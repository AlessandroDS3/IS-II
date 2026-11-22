"""Letras de alternativa admitidas en una pregunta."""
from enum import StrEnum


class Letra(StrEnum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


LETRAS = tuple(letra.value for letra in Letra)
