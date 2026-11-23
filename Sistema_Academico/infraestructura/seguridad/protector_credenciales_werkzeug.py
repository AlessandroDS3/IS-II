"""Adaptador de IProtectorCredenciales basado en werkzeug.security."""
from werkzeug.security import check_password_hash, generate_password_hash


class ProtectorCredencialesWerkzeug:
    """Implementa IProtectorCredenciales."""

    def generar_hash(self, contrasena):
        return generate_password_hash(contrasena)

    def verificar(self, hash_guardado, contrasena):
        try:
            return check_password_hash(hash_guardado, contrasena)
        except (ValueError, TypeError):
            return False
