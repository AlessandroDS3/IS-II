"""Puerto de persistencia de la configuración de exámenes y sus claves."""
from typing import Protocol


class IDisenoExamenRepositorio(Protocol):
    def consultar(self, examen):
        """ConsultaConfiguracion con exámenes, examen actual, preguntas, versiones y claves."""

    def distribucion(self, examen):
        """Distribución de preguntas por materia del examen."""

    def configurar(self, examen, ids, puntajes, versiones, penalizacion, usuario):
        """Configura y aprueba la estructura del examen."""

    def crear_clave(self, version, respuestas, motivo, usuario):
        """Crea y confirma una nueva revisión de clave."""
