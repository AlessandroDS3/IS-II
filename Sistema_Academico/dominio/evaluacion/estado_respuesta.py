"""Resolución manual de una respuesta leída (columna correcciones_manual.resolucion)."""
from enum import StrEnum


class EstadoRespuesta(StrEnum):
    MARCA_UNICA = 'MARCA_UNICA'
    BLANCO = 'BLANCO'
    MULTIPLE_CONFIRMADA = 'MULTIPLE_CONFIRMADA'
