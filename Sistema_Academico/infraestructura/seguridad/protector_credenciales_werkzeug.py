#!/usr/bin/python
# -*- coding: utf-8 -*-

from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from werkzeug.security import generate_password_hash, check_password_hash


class ProtectorCredencialesWerkzeug(IProtectorCredenciales):
    def generar_hash(self, contrasena):
        return generate_password_hash(contrasena)

    def verificar(self, hash_guardado, contrasena):
        if not isinstance(hash_guardado, str) or not isinstance(contrasena, str):
            return False
        try:
            return check_password_hash(hash_guardado, contrasena)
        except (ValueError, TypeError):
            return False
