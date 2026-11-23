"""Puerto de persistencia de exámenes (contexto, resumen y habilitación de preguntas)."""
from typing import Protocol


class IExamenRepositorio(Protocol):
    def contexto_examen(self, examen):
        """Datos del examen y de las áreas de su simulacro, o None."""

    def abrir_aplicacion(self, simulacro, examen=0):
        """Contexto del examen indicado (o del primero) de un simulacro."""

    def resumen_examen(self, examen):
        """Contadores de avance del examen."""

    def crear_examen(self, datos, usuario_id):
        """Registra un examen para un área de un simulacro abierto."""

    def habilitar_preguntas(self, examen, habilitar):
        """Abre o cierra la recepción de preguntas del examen."""
