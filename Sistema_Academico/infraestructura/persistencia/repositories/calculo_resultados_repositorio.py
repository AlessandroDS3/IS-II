"""Cálculo inicial transaccional de resultados de cartillas validadas."""
from sqlalchemy import text

from dominio.diseno_evaluaciones.conjunto_calificacion import ConjuntoCalificacion
from dominio.diseno_evaluaciones.estado_examen import ESTADOS_CON_CLAVE
from dominio.evaluacion.calificador_resultados import calificar

SQL_RESPUESTAS = text("""SELECT ep.id_examen_pregunta,ep.id_version_pregunta,ep.puntaje,p.id_materia,rd.id_respuesta_detectada,rd.respuesta_detectada lectura,
    cm.id_correccion,cm.resolucion,cm.respuesta_nueva corregida,pr.respuesta_correcta clave
    FROM examen_preguntas ep JOIN pregunta_versiones pv ON pv.id_version=ep.id_version_pregunta
    JOIN preguntas p ON p.id_pregunta=pv.id_pregunta JOIN plantilla_respuestas pr ON pr.id_revision_clave=:clave AND pr.numero_pregunta=ep.numero_pregunta
    JOIN respuestas_detectadas rd ON rd.id_procesamiento=:proceso AND rd.numero_pregunta=ep.numero_pregunta
    LEFT JOIN correcciones_manual cm ON cm.id_correccion=(SELECT MAX(x.id_correccion) FROM correcciones_manual x WHERE x.id_respuesta_detectada=rd.id_respuesta_detectada)
    WHERE ep.id_version_examen=:version ORDER BY ep.numero_pregunta""")
SQL_INSERTAR_RESULTADO = text("""INSERT INTO resultados_examen(id_revision_clave,id_configuracion,calculado_por,id_estudiante,id_examen,id_version,id_cartilla,id_procesamiento,respuestas_correctas,respuestas_incorrectas,respuestas_blanco,puntaje_obtenido,numero_calculo) VALUES (:clave,:config,:usuario,:estudiante,:examen,:version,:cartilla,:proceso,:buenas,:malas,:blancas,:puntaje,:numero)""")
SQL_INSERTAR_DETALLE = text("""INSERT INTO detalle_resultado(id_resultado,id_examen_pregunta,id_version_examen,id_version_pregunta,id_respuesta_detectada,id_correccion_aplicada,tipo_respuesta,respuesta_marcada,respuesta_correcta,es_correcta,puntaje_obtenido) VALUES (:resultado,:pregunta,:version,:version_pregunta,:lectura,:correccion,:tipo,:marcada,:correcta,:es_correcta,:puntaje)""")
SQL_INSERTAR_MATERIA = text('INSERT INTO resultado_materia(id_resultado,id_materia,preguntas_total,correctas,incorrectas,blanco,puntaje) VALUES (:resultado,:materia,:total,:correctas,:incorrectas,:blancos,:puntaje)')


class CalculoResultadosRepositorio:
    """Implementa ICalculoRepositorio."""

    def __init__(self, motor):
        self.motor = motor

    def calcular(self, examen, usuario):
        with self.motor.begin() as c:
            estado = c.execute(text('SELECT estado FROM examenes WHERE id_examen=:id FOR UPDATE'), {'id': examen}).scalar_one_or_none()
            if estado not in ESTADOS_CON_CLAVE:
                raise ValueError('El examen debe estar aprobado.')
            config = c.execute(text("SELECT id_configuracion,puntaje_incorrecta FROM configuracion_puntaje WHERE id_examen=:id AND estado='CONFIRMADA' ORDER BY numero_revision DESC LIMIT 1"), {'id': examen}).mappings().first()
            if not config:
                raise ValueError('Falta una política de puntaje confirmada.')
            cartillas = c.execute(text("SELECT id_cartilla,id_estudiante,id_version FROM cartillas WHERE id_examen=:id AND vigente=1 AND estado='VALIDADA' FOR UPDATE"), {'id': examen}).mappings().all()
            if not cartillas:
                raise ValueError('No hay cartillas vigentes validadas.')
            pendientes = [cartilla for cartilla in cartillas if not self._tiene_resultado(c, cartilla)]
            for cartilla in pendientes:
                self._calcular_cartilla(c, examen, usuario, config, cartilla)
            return len(pendientes)

    @staticmethod
    def _tiene_resultado(c, cartilla):
        return c.execute(text('SELECT COUNT(*) FROM resultados_examen WHERE id_cartilla=:id AND vigente=1'), {'id': cartilla['id_cartilla']}).scalar_one()

    @staticmethod
    def _calcular_cartilla(c, examen, usuario, config, cartilla):
        clave = c.execute(text("SELECT id_revision_clave FROM revisiones_clave WHERE id_version_examen=:id AND estado='CONFIRMADA' ORDER BY numero_revision DESC LIMIT 1"), {'id': cartilla['id_version']}).scalar_one_or_none()
        proceso = c.execute(text("SELECT id_procesamiento FROM procesamiento_cartilla WHERE id_cartilla=:id AND resultado='EXITOSO' ORDER BY numero_intento DESC LIMIT 1"), {'id': cartilla['id_cartilla']}).scalar_one_or_none()
        if not proceso:
            raise ValueError('Todas las cartillas necesitan una clave confirmada y lectura validada.')
        ConjuntoCalificacion(examen, clave, config['id_configuracion']).validar_claves_y_politica()
        filas = c.execute(SQL_RESPUESTAS, {'clave': clave, 'proceso': proceso, 'version': cartilla['id_version']}).mappings().all()
        cantidad = c.execute(text('SELECT COUNT(*) FROM examen_preguntas WHERE id_version_examen=:version'), {'version': cartilla['id_version']}).scalar_one()
        if not cantidad or len(filas) != cantidad:
            raise ValueError('La clave o las lecturas no cubren todas las preguntas.')
        desglose = calificar(filas, config['puntaje_incorrecta'])
        numero = c.execute(text('SELECT COALESCE(MAX(numero_calculo),0)+1 FROM resultados_examen WHERE id_estudiante=:estudiante AND id_examen=:examen'), {'estudiante': cartilla['id_estudiante'], 'examen': examen}).scalar_one()
        resultado = c.execute(SQL_INSERTAR_RESULTADO, {
            'clave': clave, 'config': config['id_configuracion'], 'usuario': usuario, 'estudiante': cartilla['id_estudiante'],
            'examen': examen, 'version': cartilla['id_version'], 'cartilla': cartilla['id_cartilla'], 'proceso': proceso,
            'buenas': desglose.correctas, 'malas': desglose.incorrectas, 'blancas': desglose.blancos,
            'puntaje': desglose.puntaje_total, 'numero': numero}).lastrowid
        for d in desglose.detalles:
            c.execute(SQL_INSERTAR_DETALLE, {'resultado': resultado, 'pregunta': d['id_examen_pregunta'], 'version': cartilla['id_version'],
                                             'version_pregunta': d['id_version_pregunta'], 'lectura': d['id_respuesta_detectada'],
                                             'correccion': d['id_correccion'], 'tipo': d['tipo'], 'marcada': d['marcada'],
                                             'correcta': d['clave'], 'es_correcta': d['correcta'], 'puntaje': d['obtenido']})
        for materia, m in desglose.materias.items():
            c.execute(SQL_INSERTAR_MATERIA, dict(m, resultado=resultado, materia=materia))
