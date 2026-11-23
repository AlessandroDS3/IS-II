"""Resultado de un procesamiento de cartilla (columna procesamiento_cartilla.resultado)."""
from enum import StrEnum


class EstadoLectura(StrEnum):
    EXITOSO = 'EXITOSO'
    ERROR = 'ERROR'
    REQUIERE_REVISION = 'REQUIERE_REVISION'
