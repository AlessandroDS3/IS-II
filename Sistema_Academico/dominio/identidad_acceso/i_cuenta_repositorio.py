#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class ICuentaRepositorio(ABC):
    @abstractmethod
    def guardar(self, cuenta_usuario):
        raise NotImplementedError

    @abstractmethod
    def buscar_por_id(self, id):
        raise NotImplementedError

    @abstractmethod
    def listar(self, filtros):
        raise NotImplementedError

    @abstractmethod
    def buscar_por_nombre(self, nombre):
        raise NotImplementedError
