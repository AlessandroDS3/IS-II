"""Roles del sistema (mismos nombres que la tabla roles)."""
from enum import StrEnum


class Rol(StrEnum):
    ESTUDIANTE = 'ESTUDIANTE'
    DOCENTE = 'DOCENTE'
    COORDINADOR = 'COORDINADOR'
    DIRECTOR = 'DIRECTOR'


ROLES_CON_PANEL = (Rol.COORDINADOR, Rol.DIRECTOR, Rol.ESTUDIANTE, Rol.DOCENTE)
ROLES_CON_PERFIL = ((Rol.DOCENTE, 'docentes'), (Rol.COORDINADOR, 'coordinadores'), (Rol.DIRECTOR, 'directores'))
