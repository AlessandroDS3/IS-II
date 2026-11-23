#!/usr/bin/python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from .autorizacion import Autorizacion


@dataclass
class CuentaUsuario:
    nombre_usuario: str
    password_hash: str = field(repr=False)
    roles: list = field(default_factory=list)
    activa: bool = True
    id: int | None = None

    def asignar_roles(self, roles, director=False):
        nuevos_roles = list(roles)
        Autorizacion.validar_roles(nuevos_roles, director)
        self.roles = nuevos_roles

    def desactivar(self):
        self.activa = False

    def activar(self):
        self.activa = True

    def cambiar_credencial(self, nuevo_hash):
        if not isinstance(nuevo_hash, str) or not nuevo_hash.strip():
            raise ValueError('La credencial protegida no puede estar vacía.')
        self.password_hash = nuevo_hash
