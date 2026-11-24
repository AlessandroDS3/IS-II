"""Casos de uso del estudiante para consultar sus resultados publicados."""
from dominio.publicacion_ranking.i_publicacion_repositorio import IResultadosEstudianteRepositorio


class ResultadosEstudianteAppService:
    def __init__(self, repositorio: IResultadosEstudianteRepositorio):
        self.repositorio = repositorio

    def mis_resultados(self, usuario):
        return self.repositorio.mis_resultados(usuario)

    def mi_resultado(self, usuario, resultado):
        return self.repositorio.mi_resultado(usuario, resultado)

    def detalle(self, usuario, resultado):
        return self.repositorio.detalle(usuario, resultado)

    def materias(self, usuario, resultado):
        return self.repositorio.materias(usuario, resultado)
