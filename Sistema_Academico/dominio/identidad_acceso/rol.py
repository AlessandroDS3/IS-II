#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import StrEnum

class Rol(StrEnum):
    ESTUDIANTE = 'ESTUDIANTE'
    DOCENTE = 'DOCENTE'
    COORDINADOR = 'COORDINADOR'
    DIRECTOR = 'DIRECTOR'


ROLES_CON_PANEL = (Rol.COORDINADOR, Rol.DIRECTOR, Rol.ESTUDIANTE, Rol.DOCENTE)
ROLES_CON_PERFIL = (
    (Rol.DOCENTE, 'docentes'), (Rol.COORDINADOR, 'coordinadores'),
    (Rol.DIRECTOR, 'directores'),
)


def roles_asignables(es_director):
    return tuple(rol for rol in Rol if es_director or rol != Rol.DIRECTOR)
