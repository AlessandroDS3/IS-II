"""Agregado Simulacro: evento de evaluación con un examen por área."""
from dataclasses import dataclass, field
from datetime import date

from dominio.diseno_evaluaciones.estado_simulacro import EstadoSimulacro

MAX_NOMBRE = 150


def validar_nombre(nombre):
    nombre = (nombre or '').strip()
    if not nombre or len(nombre) > MAX_NOMBRE:
        raise ValueError('Ingresa un nombre de hasta 150 caracteres.')
    return nombre


@dataclass
class Simulacro:
    ciclo_id: int
    nombre: str
    fecha_aplicacion: date
    estado: EstadoSimulacro = EstadoSimulacro.ABIERTO
    examenes_por_area: dict = field(default_factory=dict)
    id: int | None = None

    def _exigir_abierto(self):
        if self.estado != EstadoSimulacro.ABIERTO:
            raise ValueError('El examen no existe o está cerrado.')

    def registrar_examen(self, area_id, examen_id):
        self._exigir_abierto()
        if area_id in self.examenes_por_area:
            raise ValueError('Una de las áreas seleccionadas ya pertenece a este examen.')
        self.examenes_por_area[area_id] = examen_id

    def actualizar_datos(self, cambios):
        self._exigir_abierto()
        if 'nombre' in cambios:
            self.nombre = validar_nombre(cambios['nombre'])
        if 'fecha_aplicacion' in cambios:
            if self.examenes_por_area:
                raise ValueError('No cambiar la fecha de un simulacro que ya tiene exámenes.')
            self.fecha_aplicacion = cambios['fecha_aplicacion']

    def confirmar(self):
        """Cierra el simulacro a nuevas áreas una vez que tiene al menos un examen (ABIERTO -> CERRADO)."""
        self._exigir_abierto()
        if not self.examenes_por_area:
            raise ValueError('El simulacro necesita al menos un examen para confirmarse.')
        self.estado = EstadoSimulacro.CERRADO

    def desactivar(self, motivo):
        if not (motivo or '').strip():
            raise ValueError('Indica el motivo de la desactivación.')
        if self.estado == EstadoSimulacro.INACTIVO:
            raise ValueError('El simulacro ya está inactivo.')
        self.estado = EstadoSimulacro.INACTIVO
