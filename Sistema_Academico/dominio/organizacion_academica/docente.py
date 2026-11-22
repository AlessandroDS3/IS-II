"""Docente con las materias que tiene asignadas."""
from dataclasses import dataclass, field


@dataclass
class Docente:
    cuenta_id: int
    materia_ids: set = field(default_factory=set)
    activo: bool = True
    id: int | None = None

    def asignar_materia(self, materia_id):
        if not self.activo:
            raise ValueError('Selecciona un docente, una materia y un eje activos.')
        self.materia_ids.add(materia_id)

    def retirar_materia(self, materia_id):
        if materia_id not in self.materia_ids:
            raise ValueError('La asignación no existe o ya está inactiva.')
        self.materia_ids.discard(materia_id)

    def desactivar(self):
        self.activo = False
