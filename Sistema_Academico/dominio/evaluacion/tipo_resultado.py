"""Tipo de respuesta usado al calificar (columna detalle_resultado.tipo_respuesta)."""
from enum import StrEnum


class TipoResultado(StrEnum):
    UNICA = 'UNICA'
    BLANCO = 'BLANCO'
    MULTIPLE_CONFIRMADA = 'MULTIPLE_CONFIRMADA'
