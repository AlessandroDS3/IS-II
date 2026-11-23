"""Puerto para generar y verificar hashes de contraseñas."""
from typing import Protocol


class IProtectorCredenciales(Protocol):
    def generar_hash(self, contrasena) -> str:
        """Hash seguro de la contraseña."""

    def verificar(self, hash_guardado, contrasena) -> bool:
        """True si la contraseña corresponde al hash guardado."""
