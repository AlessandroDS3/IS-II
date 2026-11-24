"""Casos de uso de publicación de resultados, ranking y estadísticas institucionales."""
from dominio.publicacion_ranking.i_publicacion_repositorio import IPublicacionRepositorio


class PublicacionExamenAppService:
    def __init__(self, repositorio: IPublicacionRepositorio):
        self.repositorio = repositorio

    def examenes(self):
        return self.repositorio.examenes()

    def publicar(self, examen, usuario):
        if not examen:
            raise ValueError('Selecciona un examen.')
        return self.repositorio.publicar(examen, usuario)

    def ranking(self, examen):
        return self.repositorio.ranking(examen) if examen else []

    def estadisticas_director(self, ciclo):
        return self.repositorio.datos_director(ciclo)
