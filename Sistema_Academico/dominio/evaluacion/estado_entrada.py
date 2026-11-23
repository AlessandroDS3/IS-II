"""Estados de una entrada de importación de cartillas (columna cargas_omr.estado)."""
from enum import StrEnum


class EstadoEntrada(StrEnum):
    PENDIENTE = 'PENDIENTE'
    REVISAR = 'REVISAR'
    ERROR = 'ERROR'
    DESCARTADA = 'DESCARTADA'
    REGISTRADA = 'REGISTRADA'


ESTADOS_FILTRABLES = ('',) + tuple(estado.value for estado in EstadoEntrada)
ESTADOS_DESCARTABLES = (EstadoEntrada.PENDIENTE, EstadoEntrada.REVISAR, EstadoEntrada.ERROR)
ESTADOS_REINTENTABLES = (EstadoEntrada.ERROR, EstadoEntrada.REVISAR)
