"""Reglas de transición de la estructura de un examen."""
from dominio.diseno_evaluaciones.estado_examen import ESTADOS_CON_CLAVE, ESTADOS_CONFIGURABLES

# Orden de las preguntas por código de versión: A conserva el orden elegido y B lo invierte.
# Añadir una versión solo requiere registrar aquí su estrategia de ordenamiento.
ORDEN_POR_VERSION = {
    'A': lambda ids: list(ids),
    'B': lambda ids: list(reversed(ids)),
}
CODIGOS_VERSION = tuple(ORDEN_POR_VERSION)


class Examen:
    @staticmethod
    def validar_configuracion(estado, tiene_versiones):
        if estado not in ESTADOS_CONFIGURABLES:
            raise ValueError('El examen no está disponible para configurar.')
        if tiene_versiones:
            raise ValueError('El examen ya tiene versiones; no se reemplazará su configuración.')

    @staticmethod
    def validar_revision_clave(estado, tiene_resultados):
        if estado not in ESTADOS_CON_CLAVE:
            raise ValueError('La versión no pertenece a un examen aprobado.')
        if tiene_resultados:
            raise ValueError('Ya hay resultados vigentes. La corrección de clave requiere recalificación integral.')

    @staticmethod
    def ordenar_versiones(ids, codigo):
        ordenar = ORDEN_POR_VERSION.get(codigo)
        if ordenar is None:
            raise ValueError('Código de versión no válido.')
        return ordenar(ids)
