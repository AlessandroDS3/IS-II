#!/usr/bin/python
# -*- coding: utf-8 -*-

class Autorizacion:
    @staticmethod
    def puede_acceder(roles, requerido):
        return requerido in roles or (requerido == 'COORDINADOR' and 'DIRECTOR' in roles)

    @staticmethod
    def validar_roles(roles, director):
        if not roles or any(r not in ('ESTUDIANTE', 'DOCENTE', 'COORDINADOR', 'DIRECTOR') for r in roles) or len(set(roles)) != len(roles):
            raise ValueError('Roles no válidos.')
        if 'ESTUDIANTE' in roles and len(roles) != 1:
            raise ValueError('El rol estudiante no se puede combinar con otros roles.')
        if 'DIRECTOR' in roles and not director:
            raise PermissionError('Solo un director puede asignar el rol director.')

    @staticmethod
    def validar_modificacion_cuenta(es_director, actor_director):
        if es_director and not actor_director:
            raise PermissionError('Solo un director puede modificar cuentas de director.')

    @staticmethod
    def validar_roles_estudiante(roles, estudiante_vinculado):
        if estudiante_vinculado and roles != ['ESTUDIANTE']:
            raise ValueError('Esta cuenta está vinculada a un estudiante y debe conservar su rol.')

    def verificar_permiso(self, cuenta, operacion):
        raise NotImplementedError('La autorización por operación está pendiente de definir; use puede_acceder para verificar roles.')

    def verificar_acceso_a_resultado(self, cuenta, estudiante_id):
        raise NotImplementedError('La autorización de resultados requiere verificar la vinculación del estudiante en el servicio de resultados.')
