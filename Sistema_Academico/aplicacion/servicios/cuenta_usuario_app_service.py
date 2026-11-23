#!/usr/bin/python
# -*- coding: utf-8 -*-

from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from dominio.identidad_acceso.i_cuenta_repositorio import ICuentaRepositorio


class CuentaUsuarioAppService:
    def __init__(self, repositorio: ICuentaRepositorio, protector: IProtectorCredenciales):
        self.repositorio = repositorio
        self.protector = protector

    def iniciar_sesion(self, usuario, credencial):
        cuenta = self.repositorio.buscar_por_nombre(usuario.strip())
        if not cuenta or not cuenta["activa"] or not self.protector.verificar(cuenta["password_hash"], credencial):
            return None
        return cuenta

    def consultar_cuenta_activa(self, usuario):
        cuenta = self.repositorio.buscar_por_nombre(usuario)
        return cuenta if cuenta and cuenta['activa'] else None
