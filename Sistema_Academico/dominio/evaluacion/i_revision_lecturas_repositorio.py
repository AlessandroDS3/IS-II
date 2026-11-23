"""Puerto de persistencia para revisar lecturas, validar cartillas y revisar resultados."""
from typing import Protocol


class IRevisionLecturasRepositorio(Protocol):
    def examenes(self):
        """Exámenes con su área."""

    def lecturas(self, examen):
        """Respuestas leídas de las cartillas vigentes con su última corrección."""

    def historial_lecturas(self, examen):
        """Correcciones manuales del examen."""

    def corregir(self, respuesta_id, resolucion, marca, motivo, usuario):
        """Registra una corrección manual de una respuesta leída."""

    def validar_cartilla(self, cartilla_id):
        """Valida una cartilla sin lecturas pendientes."""

    def imagen_cartilla(self, cartilla):
        """Ruta de la imagen de una cartilla vigente."""

    def resultados(self, examen):
        """Resultados vigentes del examen."""

    def resultado(self, examen, resultado):
        """Un resultado vigente del examen o None."""

    def detalle_coordinador(self, resultado):
        """Detalle por pregunta de un resultado."""

    def revisar_resultado(self, resultado, usuario):
        """Marca como revisado un resultado calculado."""
