"""Puerto para generar y verificar hashes de contraseñas."""
from typing import Protocol


class IProtectorCredenciales(Protocol):
    def generar_hash(self, contrasena) -> str:
        """Protege una contraseña antes de persistirla."""

    def verificar(self, hash_guardado, contrasena) -> bool:
        """Comprueba una contraseña contra el hash almacenado."""
