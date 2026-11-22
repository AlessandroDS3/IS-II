"""Configuración común de pruebas: permite importar los paquetes del sistema desde tests/."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


class RepositorioFalso:
    """Registra las llamadas recibidas y devuelve valores configurados por método."""

    def __init__(self, **respuestas):
        self.respuestas = respuestas
        self.llamadas = []

    def __getattr__(self, nombre):
        def metodo(*args, **kwargs):
            self.llamadas.append((nombre, args, kwargs))
            return self.respuestas.get(nombre)
        return metodo
