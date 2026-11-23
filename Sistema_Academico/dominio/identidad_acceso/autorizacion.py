"""Reglas de autorización por rol."""
from dominio.identidad_acceso.rol import Rol

ROLES_VALIDOS = tuple(rol.value for rol in Rol)


class Autorizacion:
    @staticmethod
    def puede_acceder(roles, requerido):
        return requerido in roles or (requerido == Rol.COORDINADOR and Rol.DIRECTOR in roles)

    @staticmethod
    def validar_roles(roles, director):
        if not roles or any(r not in ROLES_VALIDOS for r in roles) or len(set(roles)) != len(roles):
            raise ValueError('Roles no válidos.')
        if Rol.ESTUDIANTE in roles and len(roles) != 1:
            raise ValueError('El rol estudiante no se puede combinar con otros roles.')
        if Rol.DIRECTOR in roles and not director:
            raise PermissionError('Solo un director puede asignar el rol director.')

    @staticmethod
    def validar_modificacion_cuenta(es_director, actor_director):
        if es_director and not actor_director:
            raise PermissionError('Solo un director puede modificar cuentas de director.')
