"""Estados de una pregunta del banco (mismos valores que la columna preguntas.estado)."""
from enum import StrEnum


class EstadoPregunta(StrEnum):
    BORRADOR = 'BORRADOR'
    REVISION = 'REVISION'
    APROBADA = 'APROBADA'
    INACTIVA = 'INACTIVA'
