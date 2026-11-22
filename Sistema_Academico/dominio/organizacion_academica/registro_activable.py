"""Comportamiento común de los registros que se activan y desactivan sin borrarse."""
from dataclasses import dataclass

from dominio.organizacion_academica.estado_registro import EstadoRegistro


@dataclass
class RegistroActivable:
    nombre: str
    estado: EstadoRegistro = EstadoRegistro.ACTIVO
    id: int | None = None

    @property
    def activo(self):
        return self.estado == EstadoRegistro.ACTIVO

    def activar(self):
        if self.estado == EstadoRegistro.FINALIZADO:
            raise ValueError('Un ciclo finalizado no puede reactivarse.')
        self.estado = EstadoRegistro.ACTIVO

    def desactivar(self):
        if self.estado == EstadoRegistro.FINALIZADO:
            raise ValueError('Un ciclo finalizado no puede reactivarse.')
        self.estado = EstadoRegistro.INACTIVO
