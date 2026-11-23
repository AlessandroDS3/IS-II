"""Puerto de persistencia del cálculo de resultados."""
from typing import Protocol


class ICalculoRepositorio(Protocol):
    def calcular(self, examen, usuario):
        """Calcula los resultados de las cartillas validadas que aún no tienen resultado; devuelve la cantidad."""
