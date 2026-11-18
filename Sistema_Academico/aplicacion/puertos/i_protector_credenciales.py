#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class IProtectorCredenciales(ABC):
    @abstractmethod
    def generar_hash(self, contrasena):
        """Protege una contraseña antes de persistirla."""
        raise NotImplementedError

    @abstractmethod
    def verificar(self, hash_guardado, contrasena):
        """Comprueba una contraseña contra el hash almacenado."""
        raise NotImplementedError
