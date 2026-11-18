#!/usr/bin/python
# -*- coding: utf-8 -*-

class CuentaUsuarioController:
    def __init__(self, servicio):
        self.servicio = servicio

    def registrar_cuenta(self, datos):
        return self.servicio.registrar_cuenta(datos)

    def asignar_roles(self, cuenta_id, roles):
        return self.servicio.asignar_roles(cuenta_id, roles)

    def iniciar_sesion(self, usuario, credencial):
        return self.servicio.iniciar_sesion(usuario, credencial)

    def recuperar_acceso(self, solicitud):
        return self.servicio.recuperar_acceso(solicitud)
