"""Puerto de consulta de cuentas para autenticación."""
from typing import Protocol


class ICuentaRepositorio(Protocol):
    def buscar_por_nombre(self, nombre):
        """Devuelve los datos de acceso de la cuenta, o None si no existe."""
