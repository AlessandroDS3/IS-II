"""Revisión de lecturas, validación de cartillas y revisión de resultados en MySQL."""
from sqlalchemy import text

from dominio.evaluacion.estado_cartilla import ESTADOS_CERRADOS
from infraestructura.persistencia.repositories.repositorio_sql import RepositorioSQL

SQL_RESULTADOS = """SELECT r.id_resultado,r.estado,r.puntaje_obtenido,e.codigo_estudiante,CONCAT(e.nombres,' ',e.apellidos) estudiante
    FROM resultados_examen r JOIN estudiantes e ON e.id_estudiante=r.id_estudiante JOIN cartillas c ON c.id_cartilla=r.id_cartilla
    WHERE r.id_examen=:examen AND r.vigente=1 AND c.vigente=1"""


class RevisionLecturasRepositorio(RepositorioSQL):
    """Implementa IRevisionLecturasRepositorio."""

    def lecturas(self, examen):
        return self._consultar("""SELECT c.id_cartilla,c.estado,e.nombres,e.apellidos,r.id_respuesta_detectada,
            r.numero_pregunta,r.respuesta_detectada,r.requiere_revision,cm.resolucion,cm.respuesta_nueva,cm.motivo
            FROM cartillas c JOIN estudiantes e ON e.id_estudiante=c.id_estudiante
            JOIN procesamiento_cartilla pc ON pc.id_procesamiento=(SELECT MAX(p.id_procesamiento) FROM procesamiento_cartilla p WHERE p.id_cartilla=c.id_cartilla)
            JOIN respuestas_detectadas r ON r.id_procesamiento=pc.id_procesamiento
            JOIN examen_preguntas ep ON ep.id_version_examen=c.id_version AND ep.numero_pregunta=r.numero_pregunta
            LEFT JOIN correcciones_manual cm ON cm.id_correccion=(SELECT MAX(x.id_correccion) FROM correcciones_manual x WHERE x.id_respuesta_detectada=r.id_respuesta_detectada)
            WHERE c.id_examen=:examen AND c.vigente=1 ORDER BY e.apellidos,e.nombres,r.numero_pregunta""", {'examen': examen})

    def historial_lecturas(self, examen):
        return self._consultar("""SELECT c.id_cartilla,r.numero_pregunta,cm.respuesta_anterior,cm.respuesta_nueva,
            cm.resolucion,cm.motivo,cm.fecha_correccion,u.username AS usuario
            FROM correcciones_manual cm JOIN respuestas_detectadas r ON r.id_respuesta_detectada=cm.id_respuesta_detectada
            JOIN cartillas c ON c.id_cartilla=r.id_cartilla JOIN usuarios u ON u.id_usuario=cm.usuario_correccion
            WHERE c.id_examen=:examen ORDER BY cm.id_correccion DESC""", {'examen': examen})

    def corregir(self, respuesta_id, resolucion, marca, motivo, usuario):
        with self.motor.begin() as c:
            fila = c.execute(text("""SELECT r.respuesta_detectada,c.id_cartilla,c.id_examen,c.estado,c.vigente
                FROM respuestas_detectadas r JOIN cartillas c ON c.id_cartilla=r.id_cartilla
                JOIN examen_preguntas ep ON ep.id_version_examen=c.id_version AND ep.numero_pregunta=r.numero_pregunta
                WHERE r.id_respuesta_detectada=:id AND r.id_procesamiento=(SELECT MAX(pc.id_procesamiento) FROM procesamiento_cartilla pc WHERE pc.id_cartilla=c.id_cartilla) FOR UPDATE"""), {'id': respuesta_id}).mappings().first()
            if not fila or not fila['vigente'] or fila['estado'] in ESTADOS_CERRADOS:
                raise ValueError('La lectura no está disponible para modificar.')
            if c.execute(text('SELECT COUNT(*) FROM resultados_examen WHERE id_cartilla=:id AND vigente=1'), {'id': fila['id_cartilla']}).scalar_one():
                raise ValueError('La cartilla ya tiene un resultado vigente; se requiere un proceso de recalificación.')
            anterior = c.execute(text('SELECT respuesta_nueva FROM correcciones_manual WHERE id_respuesta_detectada=:id ORDER BY id_correccion DESC LIMIT 1'), {'id': respuesta_id}).first()
            c.execute(text("INSERT INTO correcciones_manual(id_respuesta_detectada,respuesta_anterior,respuesta_nueva,resolucion,usuario_correccion,motivo) VALUES (:id,:anterior,:marca,:resolucion,:usuario,:motivo)"), {'id': respuesta_id, 'anterior': anterior[0] if anterior else fila['respuesta_detectada'], 'marca': marca, 'resolucion': resolucion, 'usuario': usuario, 'motivo': motivo})

    def validar_cartilla(self, cartilla_id):
        with self.motor.begin() as c:
            fila = c.execute(text('SELECT estado,vigente,id_version FROM cartillas WHERE id_cartilla=:id FOR UPDATE'), {'id': cartilla_id}).mappings().first()
            if not fila or not fila['vigente'] or fila['estado'] in ESTADOS_CERRADOS:
                raise ValueError('La cartilla no está disponible para validar.')
            # El lector conserva las 90 posiciones físicas. Solo las preguntas de
            # esta versión se revisan y validan; un blanco dentro del examen sí cuenta.
            parametros = {'id': cartilla_id, 'version': fila['id_version']}
            pendientes = c.execute(text("""SELECT COUNT(*) FROM respuestas_detectadas r
                JOIN examen_preguntas ep ON ep.id_version_examen=:version AND ep.numero_pregunta=r.numero_pregunta
                WHERE r.id_procesamiento=(SELECT MAX(id_procesamiento) FROM procesamiento_cartilla WHERE id_cartilla=:id)
                AND r.requiere_revision=1 AND NOT EXISTS (SELECT 1 FROM correcciones_manual cm WHERE cm.id_respuesta_detectada=r.id_respuesta_detectada)"""), parametros).scalar_one()
            total = c.execute(text('''SELECT COUNT(*) FROM respuestas_detectadas r
                JOIN examen_preguntas ep ON ep.id_version_examen=:version AND ep.numero_pregunta=r.numero_pregunta
                WHERE r.id_procesamiento=(SELECT MAX(id_procesamiento) FROM procesamiento_cartilla WHERE id_cartilla=:id)'''), parametros).scalar_one()
            if not total or pendientes:
                raise ValueError('Debes resolver todas las lecturas pendientes antes de validar.')
            faltantes = c.execute(text("""SELECT COUNT(*) FROM examen_preguntas ep WHERE ep.id_version_examen=:version AND NOT EXISTS
                (SELECT 1 FROM respuestas_detectadas r WHERE r.numero_pregunta=ep.numero_pregunta AND r.id_procesamiento=(SELECT MAX(id_procesamiento) FROM procesamiento_cartilla WHERE id_cartilla=:id))"""), parametros).scalar_one()
            esperadas = c.execute(text('SELECT COUNT(*) FROM examen_preguntas WHERE id_version_examen=:version'), {'version': fila['id_version']}).scalar_one()
            if not esperadas or faltantes or total != esperadas:
                raise ValueError('Las lecturas no coinciden con las preguntas configuradas para esta versión.')
            c.execute(text("UPDATE procesamiento_cartilla SET resultado='EXITOSO' WHERE id_procesamiento=(SELECT id FROM (SELECT MAX(id_procesamiento) id FROM procesamiento_cartilla WHERE id_cartilla=:id) ultimo)"), {'id': cartilla_id})
            c.execute(text("UPDATE cartillas SET estado='VALIDADA' WHERE id_cartilla=:id"), {'id': cartilla_id})

    def imagen_cartilla(self, cartilla):
        filas = self._consultar('SELECT archivo_imagen FROM cartillas WHERE id_cartilla=:id AND vigente=1', {'id': cartilla})
        return filas[0]['archivo_imagen'] if filas else None

    def resultados(self, examen):
        return self._consultar(SQL_RESULTADOS + ' ORDER BY r.puntaje_obtenido DESC,e.apellidos', {'examen': examen})

    def resultado(self, examen, resultado):
        filas = self._consultar(SQL_RESULTADOS + ' AND r.id_resultado=:resultado', {'examen': examen, 'resultado': resultado})
        return filas[0] if filas else None

    def detalle_coordinador(self, resultado):
        return self._consultar("""SELECT ep.numero_pregunta,d.respuesta_marcada,d.respuesta_correcta,d.tipo_respuesta,d.es_correcta,d.puntaje_obtenido
            FROM detalle_resultado d JOIN examen_preguntas ep ON ep.id_examen_pregunta=d.id_examen_pregunta
            JOIN resultados_examen r ON r.id_resultado=d.id_resultado WHERE r.id_resultado=:resultado AND r.vigente=1 ORDER BY ep.numero_pregunta""", {'resultado': resultado})

    def revisar_resultado(self, resultado, usuario):
        with self.motor.begin() as c:
            n = c.execute(text("UPDATE resultados_examen SET estado='REVISADO',revisado_por=:usuario,fecha_revision=NOW() WHERE id_resultado=:id AND estado='CALCULADO' AND vigente=1"), {'id': resultado, 'usuario': usuario}).rowcount
            if not n:
                raise ValueError('El resultado no está disponible para revisión.')
