"""Persistencia transaccional de las preguntas que redacta el docente y de sus consultas."""
from sqlalchemy import bindparam, text

from dominio.banco_preguntas.estado_pregunta import EstadoPregunta

ENUNCIADO = 'ENUNCIADO'
MSG_MATERIA_NO_ASIGNADA = 'La materia no está asignada al docente.'

SQL_MATERIA_ASIGNADA = text("""SELECT COUNT(*) FROM docente_materias dm JOIN materias m ON m.id_materia=dm.id_materia
    WHERE dm.id_docente=:docente AND dm.id_materia=:materia AND dm.estado='ACTIVO'
    AND (:exigir_activa=0 OR m.estado='ACTIVO')""")


class PreguntasDocenteRepositorio:
    def __init__(self, motor):
        self.motor = motor

    # ------------------------------------------------------------------ consultas
    def catalogos(self, usuario):
        with self.motor.connect() as c:
            materias = c.execute(text("""SELECT m.id_materia,m.nombre,e.nombre eje FROM docente_materias dm
                JOIN docentes d ON d.id_docente=dm.id_docente JOIN materias m ON m.id_materia=dm.id_materia
                JOIN ejes_tematicos e ON e.id_eje=m.id_eje WHERE d.id_usuario=:usuario AND dm.estado='ACTIVO' AND m.estado='ACTIVO' ORDER BY m.nombre"""), {'usuario': usuario}).mappings().all()
            temas = c.execute(text("""SELECT t.id_tema,t.nombre,t.id_materia FROM temas t JOIN docente_materias dm ON dm.id_materia=t.id_materia
                JOIN docentes d ON d.id_docente=dm.id_docente WHERE d.id_usuario=:usuario AND dm.estado='ACTIVO' ORDER BY t.nombre"""), {'usuario': usuario}).mappings().all()
            areas = c.execute(text("SELECT id_area,nombre FROM areas WHERE estado='ACTIVO' ORDER BY nombre")).mappings().all()
            return materias, temas, areas

    def examenes(self):
        with self.motor.connect() as c:
            return c.execute(text("SELECT e.id_examen,e.nombre,e.fecha_programada,e.estado,e.admite_preguntas,e.id_area,a.nombre area,s.id_simulacro,s.nombre simulacro,s.estado estado_simulacro FROM examenes e JOIN areas a ON a.id_area=e.id_area JOIN simulacros s ON s.id_simulacro=e.id_simulacro ORDER BY e.fecha_programada DESC,e.id_examen DESC")).mappings().all()

    def preguntas(self, usuario, estado, materia, examen=0):
        with self.motor.connect() as c:
            return c.execute(text("""SELECT p.id_pregunta,p.estado,m.nombre materia,pv.enunciado,pv.numero_version,
                (SELECT r.observacion FROM revisiones_pregunta r WHERE r.id_pregunta=p.id_pregunta ORDER BY r.id_revision DESC LIMIT 1) observacion,
                (SELECT GROUP_CONCAT(DISTINCT CONCAT(ex.nombre,' · ',ar.nombre) SEPARATOR ', ') FROM examenes ex JOIN areas ar ON ar.id_area=ex.id_area WHERE ex.id_examen=p.id_examen_destino OR EXISTS (SELECT 1 FROM versiones_examen ve JOIN examen_preguntas ep ON ep.id_version_examen=ve.id_version JOIN pregunta_versiones vx ON vx.id_version=ep.id_version_pregunta WHERE ve.id_examen=ex.id_examen AND vx.id_pregunta=p.id_pregunta)) examenes
                FROM preguntas p JOIN docentes d ON d.id_docente=p.id_autor_docente JOIN materias m ON m.id_materia=p.id_materia
                JOIN pregunta_versiones pv ON pv.id_pregunta=p.id_pregunta AND pv.estado='ACTIVA'
                WHERE d.id_usuario=:usuario AND (:estado='' OR p.estado=:estado) AND (:materia=0 OR p.id_materia=:materia)
                AND (:examen=0 OR p.id_examen_destino=:examen OR EXISTS (SELECT 1 FROM versiones_examen ve JOIN examen_preguntas ep ON ep.id_version_examen=ve.id_version JOIN pregunta_versiones vx ON vx.id_version=ep.id_version_pregunta WHERE ve.id_examen=:examen AND vx.id_pregunta=p.id_pregunta))
                ORDER BY p.id_pregunta DESC"""), {'usuario': usuario, 'estado': estado, 'materia': materia, 'examen': examen}).mappings().all()

    def obtener(self, usuario, pregunta, version=None):
        with self.motor.connect() as c:
            fila = c.execute(text("""SELECT p.id_pregunta,p.id_materia,p.id_examen_destino,p.estado,pv.id_version,pv.numero_version,pv.enunciado,pv.respuesta_correcta,
                pt.id_tema FROM preguntas p JOIN docentes d ON d.id_docente=p.id_autor_docente
                JOIN pregunta_versiones pv ON pv.id_pregunta=p.id_pregunta AND ((:version IS NULL AND pv.estado='ACTIVA') OR pv.id_version=:version)
                LEFT JOIN pregunta_tema pt ON pt.id_pregunta=p.id_pregunta WHERE p.id_pregunta=:id AND d.id_usuario=:usuario"""), {'id': pregunta, 'usuario': usuario, 'version': version}).mappings().first()
            if not fila:
                return None
            version = fila['id_version']
            alternativas = c.execute(text('SELECT letra,contenido FROM alternativas_pregunta WHERE id_version=:id'), {'id': version}).mappings().all()
            areas = c.execute(text('SELECT id_area FROM pregunta_areas WHERE id_pregunta=:id'), {'id': pregunta}).scalars().all()
            imagenes = c.execute(text('SELECT id_imagen,ubicacion,letra FROM pregunta_imagenes WHERE id_version=:id ORDER BY orden,id_imagen'), {'id': version}).mappings().all()
            versiones = c.execute(text('SELECT id_version,numero_version,fecha_version,estado FROM pregunta_versiones WHERE id_pregunta=:id ORDER BY numero_version DESC'), {'id': pregunta}).mappings().all()
            return dict(fila, alternativas={x['letra']: x['contenido'] for x in alternativas}, areas=areas, imagenes=imagenes, versiones=versiones)

    def estadisticas(self, usuario):
        with self.motor.connect() as c:
            return c.execute(text("""SELECT m.nombre materia,e.nombre examen,p.id_pregunta,pv.enunciado,
                COUNT(*) respuestas,SUM(det.es_correcta) correctas,AVG(det.es_correcta)*100 porcentaje
                FROM detalle_resultado det JOIN vw_resultados_publicados r ON r.id_resultado=det.id_resultado
                JOIN examenes e ON e.id_examen=r.id_examen JOIN pregunta_versiones pv ON pv.id_version=det.id_version_pregunta
                JOIN preguntas p ON p.id_pregunta=pv.id_pregunta JOIN materias m ON m.id_materia=p.id_materia
                JOIN docente_materias dm ON dm.id_materia=m.id_materia AND dm.estado='ACTIVO'
                JOIN docentes d ON d.id_docente=dm.id_docente AND d.id_usuario=:usuario
                GROUP BY m.nombre,e.nombre,p.id_pregunta,pv.id_version,pv.enunciado ORDER BY m.nombre,e.nombre,p.id_pregunta"""), {'usuario': usuario}).mappings().all()

    def imagen(self, usuario, imagen, coordinador=False):
        with self.motor.connect() as c:
            return c.execute(text("""SELECT i.ruta_archivo FROM pregunta_imagenes i JOIN pregunta_versiones pv ON pv.id_version=i.id_version
                JOIN preguntas p ON p.id_pregunta=pv.id_pregunta JOIN docentes d ON d.id_docente=p.id_autor_docente
                WHERE i.id_imagen=:id AND (:coordinador=1 OR d.id_usuario=:usuario)"""), {'id': imagen, 'usuario': usuario, 'coordinador': int(coordinador)}).scalar_one_or_none()

    # ------------------------------------------------------------------ escritura
    @staticmethod
    def _materia_asignada(c, docente, materia, exigir_activa=False):
        return c.execute(SQL_MATERIA_ASIGNADA, {'docente': docente, 'materia': materia, 'exigir_activa': int(exigir_activa)}).scalar_one()

    @staticmethod
    def _docente(c, usuario, bloquear=False):
        sql = 'SELECT id_docente FROM docentes WHERE id_usuario=:usuario' + (' FOR UPDATE' if bloquear else '')
        return c.execute(text(sql), {'usuario': usuario}).scalar_one_or_none()

    def crear_tema(self, usuario, materia, nombre):
        with self.motor.begin() as c:
            docente = self._docente(c, usuario)
            if not docente or not self._materia_asignada(c, docente, materia, exigir_activa=True):
                raise ValueError(MSG_MATERIA_NO_ASIGNADA)
            c.execute(text('INSERT INTO temas(id_materia,nombre) VALUES (:materia,:nombre)'), {'materia': materia, 'nombre': nombre})

    def guardar(self, usuario, contenido):
        """Guarda una pregunta nueva o una nueva versión de un borrador a partir de un ContenidoPregunta."""
        with self.motor.begin() as c:
            docente = self._docente(c, usuario, bloquear=True)
            if not docente:
                raise ValueError('La cuenta no está vinculada a un docente.')
            if contenido.pregunta:
                pregunta, materia, numero = self._preparar_edicion(c, docente, contenido)
            else:
                pregunta, materia, numero = self._crear_pregunta(c, docente, contenido), contenido.materia, 1
            if not self._materia_asignada(c, docente, materia):
                raise ValueError('Ya no tienes asignada esta materia.')
            nueva = self._insertar_version(c, usuario, pregunta, numero, contenido)
            if contenido.version:
                self._copiar_imagenes_anteriores(c, contenido, nueva)
            self._insertar_imagenes_nuevas(c, usuario, contenido, nueva)
            if contenido.enviar:
                c.execute(text('UPDATE pregunta_versiones SET sellada=1 WHERE id_version=:id'), {'id': nueva})
                c.execute(text('UPDATE preguntas SET estado=:estado WHERE id_pregunta=:id'), {'id': pregunta, 'estado': EstadoPregunta.REVISION.value})
            return pregunta

    @staticmethod
    def _preparar_edicion(c, docente, contenido):
        actual = c.execute(text("""SELECT p.estado,p.id_materia,pv.id_version,pv.numero_version FROM preguntas p
            JOIN pregunta_versiones pv ON pv.id_pregunta=p.id_pregunta AND pv.estado='ACTIVA'
            WHERE p.id_pregunta=:id AND p.id_autor_docente=:docente FOR UPDATE"""), {'id': contenido.pregunta, 'docente': docente}).mappings().first()
        if not actual or actual['estado'] != EstadoPregunta.BORRADOR or actual['id_version'] != contenido.version:
            raise ValueError('La pregunta no es editable o cambió; vuelve a abrirla.')
        c.execute(text("UPDATE pregunta_versiones SET estado='HISTORICA' WHERE id_version=:id"), {'id': contenido.version})
        return contenido.pregunta, actual['id_materia'], actual['numero_version'] + 1

    def _crear_pregunta(self, c, docente, contenido):
        destino = c.execute(text("SELECT e.id_area FROM examenes e JOIN simulacros s ON s.id_simulacro=e.id_simulacro WHERE e.id_examen=:id AND e.estado IN ('BORRADOR','CONFIGURACION') AND e.admite_preguntas=1 AND s.estado='ABIERTO' FOR UPDATE"), {'id': contenido.examen}).scalar_one_or_none()
        if destino is None or destino not in contenido.areas:
            raise ValueError('Selecciona un examen activo para recibir preguntas y su área correspondiente.')
        tema = self._resolver_tema(c, docente, contenido)
        permitido = c.execute(text("""SELECT COUNT(*) FROM docente_materias dm JOIN materias m ON m.id_materia=dm.id_materia
            JOIN temas t ON t.id_materia=m.id_materia WHERE dm.id_docente=:docente AND dm.id_materia=:materia
            AND dm.estado='ACTIVO' AND m.estado='ACTIVO' AND t.id_tema=:tema"""), {'docente': docente, 'materia': contenido.materia, 'tema': tema}).scalar_one()
        if not permitido:
            raise ValueError('El tema debe pertenecer a una materia activa asignada al docente.')
        consulta = text("SELECT COUNT(*) FROM areas WHERE estado='ACTIVO' AND id_area IN :areas").bindparams(bindparam('areas', expanding=True))
        if c.execute(consulta, {'areas': contenido.areas}).scalar_one() != len(contenido.areas):
            raise ValueError('Las áreas seleccionadas no están disponibles.')
        pregunta = c.execute(text('INSERT INTO preguntas(id_materia,id_autor_docente,id_examen_destino) VALUES (:materia,:docente,:examen)'), {'materia': contenido.materia, 'docente': docente, 'examen': contenido.examen}).lastrowid
        c.execute(text('INSERT INTO pregunta_tema(id_pregunta,id_tema) VALUES (:pregunta,:tema)'), {'pregunta': pregunta, 'tema': tema})
        for area in contenido.areas:
            c.execute(text('INSERT INTO pregunta_areas(id_pregunta,id_area) VALUES (:pregunta,:area)'), {'pregunta': pregunta, 'area': area})
        return pregunta

    def _resolver_tema(self, c, docente, contenido):
        if not contenido.tema_nuevo:
            return contenido.tema
        if not self._materia_asignada(c, docente, contenido.materia):
            raise ValueError(MSG_MATERIA_NO_ASIGNADA)
        parametros = {'materia': contenido.materia, 'nombre': contenido.tema_nuevo}
        tema = c.execute(text('SELECT id_tema FROM temas WHERE id_materia=:materia AND nombre=:nombre LIMIT 1'), parametros).scalar_one_or_none()
        return tema or c.execute(text('INSERT INTO temas(id_materia,nombre) VALUES (:materia,:nombre)'), parametros).lastrowid

    @staticmethod
    def _insertar_version(c, usuario, pregunta, numero, contenido):
        nueva = c.execute(text('INSERT INTO pregunta_versiones(id_pregunta,numero_version,enunciado,respuesta_correcta,usuario_modifico) VALUES (:pregunta,:numero,:enunciado,:respuesta,:usuario)'), {'pregunta': pregunta, 'numero': numero, 'enunciado': contenido.enunciado, 'respuesta': contenido.respuesta, 'usuario': usuario}).lastrowid
        for letra, texto in contenido.alternativas.items():
            if texto:
                c.execute(text('INSERT INTO alternativas_pregunta(id_version,letra,contenido) VALUES (:version,:letra,:contenido)'), {'version': nueva, 'letra': letra, 'contenido': texto})
        return nueva

    @staticmethod
    def _copiar_imagenes_anteriores(c, contenido, nueva):
        anteriores = c.execute(text('SELECT ubicacion,letra,orden,ruta_archivo,tipo_archivo,tamano_kb,texto_alternativo,subido_por FROM pregunta_imagenes WHERE id_version=:id'), {'id': contenido.version}).mappings().all()
        for imagen in anteriores:
            clave = imagen['letra'] or ENUNCIADO
            if clave not in contenido.imagenes and (clave == ENUNCIADO or contenido.alternativas.get(clave)):
                c.execute(text('INSERT INTO pregunta_imagenes(id_version,ubicacion,letra,orden,ruta_archivo,tipo_archivo,tamano_kb,texto_alternativo,subido_por) VALUES (:version,:ubicacion,:letra,:orden,:ruta_archivo,:tipo_archivo,:tamano_kb,:texto_alternativo,:subido_por)'), dict(imagen, version=nueva))

    @staticmethod
    def _insertar_imagenes_nuevas(c, usuario, contenido, nueva):
        for clave, (ruta, tamano) in contenido.imagenes.items():
            if clave != ENUNCIADO and not contenido.alternativas.get(clave):
                raise ValueError('Una imagen de alternativa necesita una alternativa con texto.')
            es_enunciado = clave == ENUNCIADO
            c.execute(text("INSERT INTO pregunta_imagenes(id_version,ubicacion,letra,ruta_archivo,tipo_archivo,tamano_kb,subido_por) VALUES (:version,:ubicacion,:letra,:ruta,'image/png',:tamano,:usuario)"), {'version': nueva, 'ubicacion': ENUNCIADO if es_enunciado else 'ALTERNATIVA', 'letra': None if es_enunciado else clave, 'ruta': ruta, 'tamano': tamano, 'usuario': usuario})
