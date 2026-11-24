"""Publicación de resultados, ranking y estadísticas institucionales en MySQL."""
from dataclasses import dataclass

from sqlalchemy import text

from infraestructura.persistencia.repositories.repositorio_sql import RepositorioSQL


@dataclass(frozen=True)
class EstadisticasDirector:
    ciclos: list
    filas: list
    resumen: dict


class PublicacionExamenORMRepositorio(RepositorioSQL):
    """Implementa IPublicacionRepositorio. La regla de publicación vive en sp_publicar_examen."""

    def publicar(self, examen, usuario):
        with self.motor.begin() as c:
            c.execute(text('CALL sp_publicar_examen(:examen,:usuario)'), {'examen': examen, 'usuario': usuario})

    def ranking(self, examen):
        return self._consultar('SELECT * FROM vw_ranking_examen WHERE id_examen=:examen ORDER BY posicion,estudiante', {'examen': examen})

    def datos_director(self, ciclo):
        ciclos = self._consultar('SELECT id_ciclo,nombre FROM ciclos_preparacion ORDER BY id_ciclo DESC')
        filas = self._consultar("""SELECT e.id_examen,e.nombre examen,e.fecha_programada,a.nombre area,COUNT(*) participantes,
            AVG(r.porcentaje) promedio,MAX(r.porcentaje) maximo,MIN(r.porcentaje) minimo
            FROM vw_resultados_publicados r JOIN examenes e ON e.id_examen=r.id_examen
            JOIN areas a ON a.id_area=e.id_area JOIN simulacros s ON s.id_simulacro=e.id_simulacro
            WHERE (:ciclo=0 OR s.id_ciclo=:ciclo) GROUP BY e.id_examen,e.nombre,e.fecha_programada,a.nombre
            ORDER BY e.fecha_programada,e.id_examen""", {'ciclo': ciclo})
        resumen = self._consultar("""SELECT COUNT(DISTINCT r.id_estudiante) estudiantes, AVG(r.porcentaje) promedio,
            MAX(r.porcentaje) maximo,MIN(r.porcentaje) minimo FROM vw_resultados_publicados r
            JOIN examenes e ON e.id_examen=r.id_examen JOIN simulacros s ON s.id_simulacro=e.id_simulacro
            WHERE (:ciclo=0 OR s.id_ciclo=:ciclo)""", {'ciclo': ciclo})[0]
        return EstadisticasDirector(ciclos, filas, resumen)
