"""Puerto de persistencia para la autoría de preguntas por parte del docente."""
from typing import Protocol


class IAutoriaPreguntasRepositorio(Protocol):
    def catalogos(self, usuario):
        """Materias asignadas, temas y áreas activas del docente."""

    def examenes(self):
        """Exámenes disponibles como destino de preguntas."""

    def crear_tema(self, usuario, materia, nombre):
        """Registra un tema en una materia asignada al docente."""

    def preguntas(self, usuario, estado, materia, examen=0):
        """Preguntas del docente filtradas."""

    def obtener(self, usuario, pregunta, version=None):
        """Detalle de una pregunta del docente (versión activa o indicada)."""

    def guardar(self, usuario, contenido):
        """Guarda una pregunta nueva o una nueva versión a partir de un ContenidoPregunta."""

    def estadisticas(self, usuario):
        """Estadísticas de las preguntas publicadas de las materias del docente."""

    def imagen(self, usuario, imagen, coordinador=False):
        """Ruta de una imagen de pregunta si el usuario puede verla."""
