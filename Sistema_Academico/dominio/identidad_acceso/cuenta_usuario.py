#!/usr/bin/python
# -*- coding: utf-8 -*-

from .autorizacion import Autorizacion


class CuentaUsuario:
    def __init__(self):
        self.id = None
        self.nombre_usuario = None
        self.password_hash = None
        self.roles = None
        self.activa = None

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
