"""Casos de uso de gestión de estudiantes."""
from dominio.organizacion_academica.estudiante import Estudiante
from dominio.organizacion_academica.i_estudiante_repositorio import IEstudianteRepositorio


class EstudianteAppService:
    def __init__(self, repositorio: IEstudianteRepositorio):
        self.repositorio = repositorio

    def registrar_estudiante(self, datos):
        self.repositorio.guardar(Estudiante.validar_datos(datos))

    def listar(self, busqueda=''):
        return self.repositorio.listar({'busqueda': busqueda.strip()})

    def actualizar(self, id_estudiante, datos):
        return self.repositorio.actualizar(id_estudiante, Estudiante.validar_datos(datos))

    def cambiar_estado(self, id_estudiante, estado):
        return self.repositorio.cambiar_estado(id_estudiante, Estudiante.validar_estado(estado))

    def buscar_por_id(self, id_estudiante):
        return self.repositorio.buscar_por_id(id_estudiante)

    def cambiar_asignacion(self, id_estudiante, grupo, area, fecha):
        fecha, area, grupo = Estudiante.validar_cambio(fecha, area, grupo)
        self.repositorio.cambiar_asignacion(id_estudiante, grupo, area, fecha)

    def consultar_asignaciones(self, id_estudiante):
        return self.repositorio.consultar_asignaciones(id_estudiante)

    def vincular_cuenta(self, id_estudiante, nombre_usuario):
        return self.repositorio.vincular_cuenta(id_estudiante, nombre_usuario.strip())
