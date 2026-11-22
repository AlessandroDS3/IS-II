"""Puerto del banco de preguntas usado por el coordinador."""
from typing import Protocol


class IPreguntaRepositorio(Protocol):
    def preguntas(self, estado, materia, area, eje, examen=0):
        """Lista preguntas con sus alternativas e imágenes y los catálogos de filtro."""

    def revisar(self, pregunta_id, version_id, aprobar, observacion, usuario_id):
        """Aprueba o devuelve la versión vista de una pregunta en revisión."""
