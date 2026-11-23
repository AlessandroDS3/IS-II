"""Estados de un examen (mismos valores que la columna examenes.estado)."""
from enum import StrEnum


class EstadoExamen(StrEnum):
    BORRADOR = 'BORRADOR'
    CONFIGURACION = 'CONFIGURACION'
    APROBADO = 'APROBADO'
    APLICADO = 'APLICADO'
    CERRADO = 'CERRADO'


ESTADOS_CONFIGURABLES = (EstadoExamen.BORRADOR, EstadoExamen.CONFIGURACION)
ESTADOS_CON_CLAVE = (EstadoExamen.APROBADO, EstadoExamen.APLICADO, EstadoExamen.CERRADO)
