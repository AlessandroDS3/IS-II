"""Estados de un simulacro (mismos valores que la columna simulacros.estado)."""
from enum import StrEnum


class EstadoSimulacro(StrEnum):
    ABIERTO = 'ABIERTO'
    CERRADO = 'CERRADO'
    INACTIVO = 'INACTIVO'
