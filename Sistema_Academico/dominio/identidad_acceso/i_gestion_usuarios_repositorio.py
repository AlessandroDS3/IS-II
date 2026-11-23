from typing import Protocol


class IGestionUsuariosRepositorio(Protocol):
    def listar(self): ...
    def crear(self, datos, hash_clave, roles): ...
    def estado(self, id_usuario, estado, validar_cuenta):
        """Valida la cuenta bloqueada y actualiza su estado en una transacción."""

    def cambiar_roles(self, id_usuario, roles, validar_cuenta):
        """Valida la cuenta bloqueada y sustituye sus roles en una transacción."""
