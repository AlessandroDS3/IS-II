"""Puerto de persistencia de simulacros."""
from typing import Protocol


class ISimulacroRepositorio(Protocol):
    def simulacros(self):
        """Simulacros, exámenes, ciclos y áreas activas para la vista de gestión."""

    def crear_simulacro(self, datos, usuario_id):
        """Registra un simulacro con un examen por cada área indicada."""

    def agregar_areas(self, simulacro, areas, usuario_id):
        """Añade exámenes de nuevas áreas a un simulacro abierto."""
