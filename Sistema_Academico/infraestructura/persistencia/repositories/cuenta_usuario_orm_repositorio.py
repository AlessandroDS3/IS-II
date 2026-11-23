#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import text


class CuentaUsuarioORMRepositorio:

    def __init__(self, motor):
        self.motor = motor

    def buscar_por_nombre(self, nombre):
        with self.motor.connect() as conexion:
            usuario = conexion.execute(text("SELECT id_usuario, username, password_hash, nombres, estado FROM usuarios WHERE username = :nombre"), {"nombre": nombre}).mappings().first()
            if usuario is None:
                return None
            roles = conexion.execute(text("SELECT r.nombre FROM roles r JOIN usuario_roles ur ON ur.id_rol = r.id_rol WHERE ur.id_usuario = :id"), {"id": usuario["id_usuario"]}).scalars().all()
        return {"id": usuario["id_usuario"], "usuario": usuario["username"], "nombre": usuario["nombres"], "password_hash": usuario["password_hash"], "activa": usuario["estado"] == "ACTIVO", "roles": list(roles)}
