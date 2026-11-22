"""Eje temático que agrupa materias."""
from dataclasses import dataclass, field

from dominio.organizacion_academica.estado_registro import EstadoRegistro
from dominio.organizacion_academica.materia import Materia
from dominio.organizacion_academica.registro_activable import RegistroActivable


@dataclass
class EjeTematico(RegistroActivable):
    materias: list = field(default_factory=list)

    def agregar_materia(self, nombre):
        if not self.activo:
            raise ValueError('El eje temático debe estar activo.')
        materia = Materia(nombre=nombre, eje_id=self.id)
        self.materias.append(materia)
        return materia

    def desactivar_materia(self, materia_id):
        materia = next((m for m in self.materias if m.id == materia_id), None)
        if materia is None:
            raise ValueError('El elemento no existe.')
        materia.desactivar()

    def activar_materia(self, materia_id):
        if not self.activo:
            raise ValueError('Activa primero el eje de la materia.')
        materia = next((m for m in self.materias if m.id == materia_id), None)
        if materia is None:
            raise ValueError('El elemento no existe.')
        materia.estado = EstadoRegistro.ACTIVO
