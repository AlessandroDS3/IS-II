"""Ciclo de preparación con sus grupos."""
from dataclasses import dataclass, field
from datetime import date

from dominio.organizacion_academica.estado_registro import EstadoRegistro
from dominio.organizacion_academica.grupo import Grupo
from dominio.organizacion_academica.registro_activable import RegistroActivable


@dataclass
class Ciclo(RegistroActivable):
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    grupos: list = field(default_factory=list)

    def agregar_grupo(self, nombre, horario=None, aula=None):
        if not self.activo:
            raise ValueError('El ciclo debe estar activo.')
        grupo = Grupo(nombre=nombre, ciclo_id=self.id, horario=horario, aula=aula)
        self.grupos.append(grupo)
        return grupo

    def desactivar_grupo(self, grupo_id):
        grupo = next((g for g in self.grupos if g.id == grupo_id), None)
        if grupo is None:
            raise ValueError('El elemento no existe.')
        grupo.desactivar()

    def finalizar(self):
        if self.estado == EstadoRegistro.FINALIZADO:
            raise ValueError('Un ciclo finalizado no puede reactivarse.')
        self.estado = EstadoRegistro.FINALIZADO
