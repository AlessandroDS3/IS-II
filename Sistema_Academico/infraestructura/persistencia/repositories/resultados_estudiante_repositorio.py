"""Consultas de resultados publicados desde la cuenta del estudiante."""
from infraestructura.persistencia.repositories.repositorio_sql import RepositorioSQL

SQL_MIS_RESULTADOS = """SELECT r.*, ex.nombre examen, ex.fecha_programada, a.nombre area
    FROM vw_resultados_publicados r JOIN estudiantes e ON e.id_estudiante=r.id_estudiante
    JOIN examenes ex ON ex.id_examen=r.id_examen JOIN areas a ON a.id_area=ex.id_area
    WHERE e.id_usuario=:usuario AND e.estado='ACTIVO'"""


class ResultadosEstudianteRepositorio(RepositorioSQL):
    """Implementa IResultadosEstudianteRepositorio."""

    def mis_resultados(self, usuario):
        return self._consultar(SQL_MIS_RESULTADOS + ' ORDER BY ex.fecha_programada DESC,r.id_examen DESC', {'usuario': usuario})

    def mi_resultado(self, usuario, resultado):
        filas = self._consultar(SQL_MIS_RESULTADOS + ' AND r.id_resultado=:resultado', {'usuario': usuario, 'resultado': resultado})
        return filas[0] if filas else None

    def detalle(self, usuario, resultado):
        return self._consultar("""SELECT ep.numero_pregunta,d.respuesta_marcada,d.respuesta_correcta,d.tipo_respuesta,d.es_correcta,d.puntaje_obtenido
            FROM detalle_resultado d JOIN examen_preguntas ep ON ep.id_examen_pregunta=d.id_examen_pregunta
            JOIN vw_resultados_publicados r ON r.id_resultado=d.id_resultado JOIN estudiantes e ON e.id_estudiante=r.id_estudiante
            WHERE e.id_usuario=:usuario AND e.estado='ACTIVO' AND r.id_resultado=:resultado ORDER BY ep.numero_pregunta""", {'usuario': usuario, 'resultado': resultado})

    def materias(self, usuario, resultado):
        return self._consultar("""SELECT m.nombre,rm.preguntas_total,rm.correctas,rm.incorrectas,rm.blanco,rm.puntaje
            FROM resultado_materia rm JOIN materias m ON m.id_materia=rm.id_materia
            JOIN vw_resultados_publicados r ON r.id_resultado=rm.id_resultado JOIN estudiantes e ON e.id_estudiante=r.id_estudiante
            WHERE e.id_usuario=:usuario AND e.estado='ACTIVO' AND r.id_resultado=:resultado ORDER BY m.nombre""", {'usuario': usuario, 'resultado': resultado})
