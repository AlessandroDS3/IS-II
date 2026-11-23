"""Estados de un resultado calculado (columna resultados_examen.estado)."""
from enum import StrEnum


class EstadoCalculo(StrEnum):
    CALCULADO = 'CALCULADO'
    REVISADO = 'REVISADO'
    PUBLICADO = 'PUBLICADO'
