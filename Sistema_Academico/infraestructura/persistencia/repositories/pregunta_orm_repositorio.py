"""Consulta y revisión del banco de preguntas por parte del coordinador."""
from sqlalchemy import bindparam, text

from dominio.banco_preguntas.estado_pregunta import EstadoPregunta
from dominio.banco_preguntas.pregunta import MENSAJE_VERSION_CAMBIADA


class PreguntaORMRepositorio:
    """Implementa IPreguntaRepositorio sobre SQLAlchemy Core."""

    def __init__(self, motor):
        self.motor = motor

    def preguntas(self, estado, materia, area, eje, examen=0):
        with self.motor.connect() as c:
            filas = c.execute(text("""SELECT p.id_pregunta,p.estado,m.nombre AS materia,pv.id_version,pv.enunciado,pv.respuesta_correcta,CONCAT(u.nombres,' ',u.apellidos) AS autor
                FROM preguntas p JOIN materias m ON m.id_materia=p.id_materia
                JOIN pregunta_versiones pv ON pv.id_pregunta=p.id_pregunta AND pv.estado='ACTIVA'
                JOIN docentes d ON d.id_docente=p.id_autor_docente JOIN usuarios u ON u.id_usuario=d.id_usuario
                WHERE (:estado='' OR p.estado=:estado) AND (:materia=0 OR p.id_materia=:materia)
                AND (:eje=0 OR m.id_eje=:eje)
                AND (:area=0 OR EXISTS(SELECT 1 FROM pregunta_areas pa WHERE pa.id_pregunta=p.id_pregunta AND pa.id_area=:area))
                AND (:examen=0 OR p.id_examen_destino=:examen OR EXISTS (
                    SELECT 1 FROM examen_preguntas ep JOIN versiones_examen ve ON ve.id_version=ep.id_version_examen
                    JOIN pregunta_versiones vx ON vx.id_version=ep.id_version_pregunta
                    WHERE ve.id_examen=:examen AND vx.id_pregunta=p.id_pregunta))
                ORDER BY p.id_pregunta DESC LIMIT 200"""), {'estado': estado, 'materia': materia, 'area': area, 'eje': eje, 'examen': examen}).mappings().all()
            materias = c.execute(text('SELECT id_materia,nombre FROM materias ORDER BY nombre')).mappings().all()
            areas = c.execute(text('SELECT id_area,nombre FROM areas ORDER BY nombre')).mappings().all()
            ejes = c.execute(text('SELECT id_eje,nombre FROM ejes_tematicos ORDER BY nombre')).mappings().all()
            versiones = [fila['id_version'] for fila in filas]
            alternativas = self._agrupar_por_version(c, versiones, 'SELECT id_version,letra,contenido FROM alternativas_pregunta WHERE id_version IN :versiones ORDER BY letra')
            imagenes = self._agrupar_por_version(c, versiones, 'SELECT id_imagen,id_version,ubicacion,letra FROM pregunta_imagenes WHERE id_version IN :versiones ORDER BY orden,id_imagen')
            filas = [dict(fila, alternativas=alternativas.get(fila['id_version'], []), imagenes=imagenes.get(fila['id_version'], [])) for fila in filas]
            return filas, materias, areas, ejes

    @staticmethod
    def _agrupar_por_version(c, versiones, sql):
        grupos = {}
        if versiones:
            consulta = text(sql).bindparams(bindparam('versiones', expanding=True))
            for fila in c.execute(consulta, {'versiones': versiones}).mappings():
                grupos.setdefault(fila['id_version'], []).append(fila)
        return grupos

    def revisar(self, pregunta_id, version_id, aprobar, observacion, usuario_id):
        with self.motor.begin() as c:
            pregunta = c.execute(text("SELECT p.estado,pv.id_version,pv.sellada FROM preguntas p JOIN pregunta_versiones pv ON pv.id_pregunta=p.id_pregunta AND pv.estado='ACTIVA' WHERE p.id_pregunta=:id FOR UPDATE"), {'id': pregunta_id}).mappings().first()
            if not pregunta or pregunta['estado'] != EstadoPregunta.REVISION or pregunta['id_version'] != version_id:
                raise ValueError(MENSAJE_VERSION_CAMBIADA)
            if aprobar:
                # El trigger trg_registrar_aprobacion_inicial deja constancia de la aprobación en revisiones_pregunta.
                c.execute(text("UPDATE preguntas SET estado='APROBADA', aprobado_por=:usuario WHERE id_pregunta=:id"), {'usuario': usuario_id, 'id': pregunta_id})
            else:
                c.execute(text("UPDATE preguntas SET estado='BORRADOR' WHERE id_pregunta=:id"), {'id': pregunta_id})
                c.execute(text("INSERT INTO revisiones_pregunta(id_version_pregunta,id_pregunta,id_usuario_revision,estado_anterior,estado_nuevo,observacion) VALUES (:version,:id,:usuario,'REVISION','BORRADOR',:observacion)"), {'version': version_id, 'id': pregunta_id, 'usuario': usuario_id, 'observacion': observacion})
