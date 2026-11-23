"""Casos de uso de administración de cuentas de usuario."""
from aplicacion.puertos.i_protector_credenciales import IProtectorCredenciales
from dominio.identidad_acceso.autorizacion import Autorizacion
from dominio.identidad_acceso.i_gestion_usuarios_repositorio import IGestionUsuariosRepositorio
from dominio.identidad_acceso.politica_contrasena import cumple_longitud, validar_contrasena

ESTADOS_CUENTA = ('ACTIVO', 'INACTIVO')
CAMPOS_OBLIGATORIOS = ('username', 'nombres', 'apellidos')


class GestionUsuariosAppService:
    def __init__(self, repositorio: IGestionUsuariosRepositorio, protector: IProtectorCredenciales):
        self.repositorio = repositorio
        self.protector = protector

    def crear(self, formulario, director):
        datos = {campo: formulario.get(campo, '').strip() for campo in CAMPOS_OBLIGATORIOS}
        roles = formulario.get('roles', [])
        clave = formulario.get('contrasena', '')
        if not all(datos.values()) or not cumple_longitud(clave) or not roles:
            raise ValueError('Complete usuario, nombres y apellidos, seleccione roles y use una contraseña de al menos 8 caracteres.')
        validar_contrasena(clave)
        Autorizacion.validar_roles(roles, director)
        self.repositorio.crear(datos, self.protector.generar_hash(clave), roles)

    def cambiar_estado(self, id_usuario, estado, director):
        if estado not in ESTADOS_CUENTA:
            raise ValueError('Estado no válido.')
        self.repositorio.estado(id_usuario, estado, director)

    def listar(self):
        return self.repositorio.listar()

    def cambiar_roles(self, id_usuario, roles, director, actor):
        Autorizacion.validar_roles(roles, director)
        if id_usuario == actor:
            raise ValueError('No puedes cambiar los roles de tu propia cuenta.')
        self.repositorio.cambiar_roles(id_usuario, roles, director)

