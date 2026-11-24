"""Puertos de persistencia de la publicación de resultados."""
from typing import Protocol


class IPublicacionRepositorio(Protocol):
    def examenes(self):
        """Exámenes con su área."""

    def publicar(self, examen, usuario):
        """Publica (o republica) los resultados revisados del examen."""

    def ranking(self, examen):
        """Ranking publicado del examen."""

    def datos_director(self, ciclo):
        """EstadisticasDirector con ciclos, filas por examen y resumen."""


class IResultadosEstudianteRepositorio(Protocol):
    def mis_resultados(self, usuario):
        """Resultados publicados del estudiante vinculado a la cuenta."""

    def mi_resultado(self, usuario, resultado):
        """Un resultado publicado del estudiante o None."""

    def detalle(self, usuario, resultado):
        """Detalle por pregunta de un resultado publicado del estudiante."""

    def materias(self, usuario, resultado):
        """Resumen por materia de un resultado publicado del estudiante."""
