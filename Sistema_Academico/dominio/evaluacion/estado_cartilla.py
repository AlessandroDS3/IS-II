"""Estados de una cartilla registrada (columna cartillas.estado)."""
from enum import StrEnum


class EstadoCartilla(StrEnum):
    REGISTRADA = 'REGISTRADA'
    PROCESADA = 'PROCESADA'
    OBSERVADA = 'OBSERVADA'
    VALIDADA = 'VALIDADA'
    ANULADA = 'ANULADA'


ESTADOS_CERRADOS = (EstadoCartilla.VALIDADA, EstadoCartilla.ANULADA)
