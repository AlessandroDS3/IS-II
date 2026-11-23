"""Puerto de consulta de cuentas para autenticación."""
from typing import Protocol


class ICuentaRepositorio(Protocol):
    def buscar_por_nombre(self, nombre):
        """Cuenta con id, usuario, nombre, password_hash, activa y roles, o None."""
