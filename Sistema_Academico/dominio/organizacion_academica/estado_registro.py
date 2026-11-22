"""Estados de los registros de organización académica (áreas, ejes, materias, ciclos, grupos, estudiantes)."""
from enum import StrEnum


class EstadoRegistro(StrEnum):
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    FINALIZADO = 'FINALIZADO'


ESTADOS_BASICOS = (EstadoRegistro.ACTIVO, EstadoRegistro.INACTIVO)
