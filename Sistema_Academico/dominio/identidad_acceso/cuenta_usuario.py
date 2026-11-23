"""Cuenta de acceso de un usuario del sistema."""
from dataclasses import dataclass, field

from dominio.identidad_acceso.autorizacion import Autorizacion


@dataclass
class CuentaUsuario:
    nombre_usuario: str
    password_hash: str
    roles: list = field(default_factory=list)
    activa: bool = True
    id: int | None = None

    def asignar_roles(self, roles, actor_es_director=False):
        Autorizacion.validar_roles(roles, actor_es_director)
        self.roles = list(roles)

    def desactivar(self):
        self.activa = False

    def activar(self):
        self.activa = True

    def cambiar_credencial(self, nuevo_hash):
        if not nuevo_hash:
            raise ValueError('La credencial no puede estar vacía.')
        self.password_hash = nuevo_hash
