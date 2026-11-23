from dominio.identidad_acceso.autorizacion import Autorizacion
from dominio.identidad_acceso.i_gestion_usuarios_repositorio import IGestionUsuariosRepositorio
from dominio.identidad_acceso.politica_contrasena import validar_contrasena


class GestionUsuariosAppService:
    def __init__(self, repositorio: IGestionUsuariosRepositorio, protector):
        self.repositorio = repositorio
        self.protector = protector

    def crear(self, formulario, director):
        datos = {campo: formulario.get(campo, "").strip() for campo in ("username", "nombres", "apellidos")}
        roles = formulario.get("roles", [])
        clave = formulario.get("contrasena", "")
        if not all(datos.values()) or not roles:
            raise ValueError("Complete usuario, nombres y apellidos y seleccione roles.")
        validar_contrasena(clave)
        Autorizacion.validar_roles(roles, director)
        self.repositorio.crear(datos, self.protector.generar_hash(clave), roles)

    def cambiar_estado(self, id_usuario, estado, director):
        if estado not in ("ACTIVO", "INACTIVO"):
            raise ValueError("Estado no válido.")
        def validar_cuenta(cuenta):
            Autorizacion.validar_modificacion_cuenta(cuenta['es_director'], director)

        self.repositorio.estado(id_usuario, estado, validar_cuenta)

    def listar(self):
        return self.repositorio.listar()

    def cambiar_roles(self, id_usuario, roles, director, actor):
        Autorizacion.validar_roles(roles, director)
        if id_usuario == actor:
            raise ValueError('No puedes cambiar los roles de tu propia cuenta.')

        def validar_cuenta(cuenta):
            Autorizacion.validar_modificacion_cuenta(cuenta['es_director'], director)
            Autorizacion.validar_roles_estudiante(roles, cuenta['estudiante_vinculado'])

        self.repositorio.cambiar_roles(id_usuario, roles, validar_cuenta)
