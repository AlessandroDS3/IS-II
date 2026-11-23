"""Persistencia de las entradas de importación de cartillas (cargas OMR) y su registro como cartillas."""
import json

from sqlalchemy import text

from dominio.evaluacion.estado_entrada import ESTADOS_REINTENTABLES, EstadoEntrada
from dominio.evaluacion.identificacion_cartilla import decodificar_lectura, identificar_cartilla
from dominio.evaluacion.participacion import Participacion
from infraestructura.persistencia.repositories.repositorio_sql import RepositorioSQL

SQL_ENTRADA_BLOQUEADA = text('SELECT * FROM cargas_omr WHERE id=:id FOR UPDATE')
SQL_ESTUDIANTES_ACTIVOS = text("SELECT id_estudiante,codigo_estudiante,nombres,apellidos,dni FROM estudiantes WHERE estado='ACTIVO' ORDER BY apellidos,nombres")
SQL_VERSIONES_ACTIVAS = text("SELECT id_version,codigo_version FROM versiones_examen WHERE id_examen=:examen AND estado='ACTIVA' ORDER BY codigo_version")
SQL_ESTUDIANTE_ACTIVO = text("SELECT id_estudiante FROM estudiantes WHERE id_estudiante=:id AND estado='ACTIVO' FOR UPDATE")
SQL_VERSION_ACTIVA = text("SELECT id_version FROM versiones_examen WHERE id_version=:id AND id_examen=:examen AND estado='ACTIVA' FOR UPDATE")
SQL_GUARDAR_IDENTIFICACION = text('UPDATE cargas_omr SET estudiante_id=:estudiante,version_id=:version WHERE id=:id')


class CargasOMRRepositorio(RepositorioSQL):
    """Implementa ICargasOMR."""

    def listar(self, examen_id, pagina=1, estado=''):
        with self.motor.connect() as c:
            return c.execute(text("SELECT id,nombre_archivo,pagina,estado,lectura_json,error_texto,estudiante_id,version_id,cartilla_id FROM cargas_omr WHERE examen_id=:examen AND (:estado='' OR estado=:estado) ORDER BY id DESC LIMIT 201 OFFSET :desplazamiento"), {'examen': examen_id, 'estado': estado, 'desplazamiento': (pagina - 1) * 200}).mappings().all()

    def resumen(self, examen_id):
        with self.motor.connect() as c:
            return dict(c.execute(text('SELECT estado,COUNT(*) FROM cargas_omr WHERE examen_id=:examen GROUP BY estado'), {'examen': examen_id}).all())

    def obtener(self, entrada_id):
        with self.motor.connect() as c:
            fila = c.execute(text('SELECT * FROM cargas_omr WHERE id=:id'), {'id': entrada_id}).mappings().first()
            return dict(fila) if fila else None

    def preparar_reintento(self, entrada_id, usuario, motivo, archivo=None):
        with self.motor.begin() as c:
            fila = c.execute(SQL_ENTRADA_BLOQUEADA, {'id': entrada_id}).mappings().first()
            if not fila or fila['estado'] not in ESTADOS_REINTENTABLES or fila['cartilla_id']:
                raise ValueError('Solo puedes reintentar o reemplazar una entrada que aún no originó una cartilla.')
            if archivo is None and fila['pagina'] <= 0:
                raise ValueError('Este archivo no pudo convertirse a imagen. Adjunta una imagen legible de reemplazo.')
            if archivo:
                self._exigir_imagen_no_duplicada(c, fila, archivo, entrada_id)
            c.execute(text('''INSERT INTO historial_cargas_omr(carga_id,accion,usuario_id,motivo,datos_anteriores)
                VALUES (:id,:accion,:usuario,:motivo,:datos)'''), {'id': entrada_id, 'accion': 'REEMPLAZO' if archivo else 'REINTENTO', 'usuario': usuario, 'motivo': motivo, 'datos': json.dumps(dict(fila), ensure_ascii=False, default=str)})
            if archivo:
                c.execute(text('UPDATE cargas_omr SET ruta_imagen=:ruta,ruta_original=:ruta,huella=:huella,nombre_archivo=:nombre,pagina=1 WHERE id=:id'), dict(archivo, id=entrada_id))
            c.execute(text("UPDATE cargas_omr SET estado='PENDIENTE',lectura_json=NULL,error_texto=NULL,estudiante_id=NULL,version_id=NULL WHERE id=:id"), {'id': entrada_id})
            return archivo['ruta'] if archivo else fila['ruta_imagen']

    @staticmethod
    def _exigir_imagen_no_duplicada(c, fila, archivo, entrada_id):
        c.execute(text('SELECT id_examen FROM examenes WHERE id_examen=:id FOR UPDATE'), {'id': fila['examen_id']}).scalar_one()
        duplicada = c.execute(text("SELECT id FROM cargas_omr WHERE examen_id=:examen AND huella=:huella AND id<>:id AND estado<>'DESCARTADA' LIMIT 1"), {'examen': fila['examen_id'], 'huella': archivo['huella'], 'id': entrada_id}).scalar_one_or_none()
        if duplicada:
            raise ValueError('Esta imagen ya está cargada en el mismo examen.')

    def historial(self, entrada_id):
        with self.motor.connect() as c:
            return c.execute(text('''SELECT h.id,h.accion,h.motivo,h.creada_en,u.username usuario
                FROM historial_cargas_omr h JOIN usuarios u ON u.id_usuario=h.usuario_id
                WHERE h.carga_id=:id ORDER BY h.id DESC'''), {'id': entrada_id}).mappings().all()

    def archivo_anterior(self, entrada_id, historial_id):
        with self.motor.connect() as c:
            datos = c.execute(text('SELECT datos_anteriores FROM historial_cargas_omr WHERE carga_id=:entrada AND id=:historial'), {'entrada': entrada_id, 'historial': historial_id}).scalar_one_or_none()
            return decodificar_lectura(datos)

    def opciones_identificacion(self, examen_id):
        with self.motor.connect() as c:
            return self._opciones(c, examen_id)

    @staticmethod
    def _opciones(c, examen_id):
        estudiantes = c.execute(SQL_ESTUDIANTES_ACTIVOS).mappings().all()
        versiones = c.execute(SQL_VERSIONES_ACTIVAS, {'examen': examen_id}).mappings().all()
        return estudiantes, versiones

    def _identificacion_detectada(self, c, entrada):
        """Identificación que se deduce de la lectura (solo usa coincidencias únicas, así que el orden no influye)."""
        estudiantes, versiones = self._opciones(c, entrada['examen_id'])
        area = c.execute(text('SELECT a.nombre FROM examenes e JOIN areas a ON a.id_area=e.id_area WHERE e.id_examen=:id'), {'id': entrada['examen_id']}).scalar_one()
        return identificar_cartilla(decodificar_lectura(entrada['lectura_json']), estudiantes, versiones, area)

    @staticmethod
    def _exigir_coherencia(detectada, estudiante_id, version_id, mensaje_estudiante, mensaje_version):
        if detectada['bloqueo']:
            raise ValueError(detectada['bloqueo'])
        if detectada['estudiante'] and detectada['estudiante']['id_estudiante'] != estudiante_id:
            raise ValueError(mensaje_estudiante)
        if detectada['version'] and detectada['version']['id_version'] != version_id:
            raise ValueError(mensaje_version)

    def resolver_identificacion(self, id, estudiante_id, version_id):
        with self.motor.begin() as c:
            entrada = c.execute(SQL_ENTRADA_BLOQUEADA, {'id': id}).mappings().first()
            if not entrada or entrada['estado'] != EstadoEntrada.REVISAR:
                raise ValueError('La entrada no está disponible para identificar.')
            if entrada['estudiante_id'] is not None or entrada['version_id'] is not None:
                raise ValueError('La identificación ya fue guardada; su rectificación requiere un proceso con historial.')
            self._exigir_coherencia(self._identificacion_detectada(c, entrada), estudiante_id, version_id,
                                    'El estudiante seleccionado no coincide con el DNI detectado. Revisa la imagen.',
                                    'La versión seleccionada no coincide con la lectura o la única versión activa.')
            estudiante = c.execute(SQL_ESTUDIANTE_ACTIVO, {'id': estudiante_id}).scalar_one_or_none()
            version = c.execute(SQL_VERSION_ACTIVA, {'id': version_id, 'examen': entrada['examen_id']}).scalar_one_or_none()
            if not estudiante or not version:
                raise ValueError('El estudiante o la versión no están activos o no corresponden al examen.')
            c.execute(SQL_GUARDAR_IDENTIFICACION, {'id': id, 'estudiante': estudiante_id, 'version': version_id})

    def registrar_cartilla(self, id, usuario, motivo):
        with self.motor.begin() as c:
            fila = c.execute(SQL_ENTRADA_BLOQUEADA, {'id': id}).mappings().first()
            if not fila or fila['estado'] != EstadoEntrada.REVISAR:
                raise ValueError('La entrada no está disponible para registrar.')
            entrada = dict(fila)
            self._completar_identificacion(c, entrada)
            lectura = self._lectura_registrable(c, entrada)
            participacion = self._participacion(c, entrada)
            cartilla = self._insertar_cartilla(c, entrada, participacion, usuario, motivo)
            self._insertar_lectura(c, cartilla, usuario, lectura)
            c.execute(text("UPDATE cargas_omr SET estado='REGISTRADA',cartilla_id=:cartilla WHERE id=:id"), {'cartilla': cartilla, 'id': id})
            return cartilla

    def _completar_identificacion(self, c, entrada):
        detectada = self._identificacion_detectada(c, entrada)
        if detectada['bloqueo']:
            raise ValueError(detectada['bloqueo'])
        if not entrada['estudiante_id'] or not entrada['version_id']:
            if not detectada['completa']:
                raise ValueError('Faltan datos por identificar. Revisa el DNI, el área y la versión.')
            entrada['estudiante_id'] = detectada['estudiante']['id_estudiante']
            entrada['version_id'] = detectada['version']['id_version']
            c.execute(SQL_GUARDAR_IDENTIFICACION, {'id': entrada['id'], 'estudiante': entrada['estudiante_id'], 'version': entrada['version_id']})
        self._exigir_coherencia(detectada, entrada['estudiante_id'], entrada['version_id'],
                                'La identificación guardada no coincide con el DNI detectado. Revisa la entrada antes de registrarla.',
                                'La versión guardada no coincide con la cartilla o con la única versión activa.')

    @staticmethod
    def _lectura_registrable(c, entrada):
        if not c.execute(SQL_ESTUDIANTE_ACTIVO, {'id': entrada['estudiante_id']}).scalar_one_or_none():
            raise ValueError('El estudiante ya no está activo.')
        if not c.execute(SQL_VERSION_ACTIVA, {'id': entrada['version_id'], 'examen': entrada['examen_id']}).scalar_one_or_none():
            raise ValueError('La versión ya no está activa o no pertenece al examen.')
        lectura = decodificar_lectura(entrada['lectura_json'])
        if not lectura or not lectura.get('exito'):
            raise ValueError('La lectura no es válida para registrar una cartilla.')
        return lectura

    @staticmethod
    def _participacion(c, entrada):
        simulacro = c.execute(text('SELECT id_simulacro FROM examenes WHERE id_examen=:id FOR UPDATE'), {'id': entrada['examen_id']}).scalar_one()
        parametros = {'estudiante': entrada['estudiante_id'], 'simulacro': simulacro, 'examen': entrada['examen_id']}
        c.execute(text('INSERT INTO participaciones(id_estudiante,id_simulacro,id_examen) VALUES (:estudiante,:simulacro,:examen) ON DUPLICATE KEY UPDATE id_participacion=LAST_INSERT_ID(id_participacion)'), parametros)
        participacion = c.execute(text('SELECT id_participacion,id_examen FROM participaciones WHERE id_estudiante=:estudiante AND id_simulacro=:simulacro FOR UPDATE'), parametros).mappings().one()
        Participacion.exigir_mismo_examen(participacion['id_examen'], entrada['examen_id'])
        return participacion['id_participacion']

    @staticmethod
    def _insertar_cartilla(c, entrada, participacion, usuario, motivo):
        anterior = c.execute(text('SELECT id_cartilla,numero_recepcion FROM cartillas WHERE id_participacion=:id ORDER BY numero_recepcion DESC LIMIT 1 FOR UPDATE'), {'id': participacion}).mappings().first()
        Participacion.exigir_motivo_reemplazo(anterior is not None, motivo)
        c.execute(text('UPDATE cartillas SET vigente=0 WHERE id_participacion=:id AND vigente=1'), {'id': participacion})
        params = {'participacion': participacion, 'numero': anterior['numero_recepcion'] + 1 if anterior else 1,
                  'anterior': anterior['id_cartilla'] if anterior else None, 'motivo': motivo if anterior else None,
                  'estudiante': entrada['estudiante_id'], 'examen': entrada['examen_id'], 'version': entrada['version_id'],
                  'archivo': entrada['ruta_imagen'], 'usuario': usuario}
        return c.execute(text('INSERT INTO cartillas(id_participacion,numero_recepcion,reemplaza_cartilla,motivo_reemplazo,id_estudiante,id_examen,id_version,archivo_imagen,fecha_recepcion,operador_recepcion) VALUES (:participacion,:numero,:anterior,:motivo,:estudiante,:examen,:version,:archivo,CURRENT_DATE,:usuario)'), params).lastrowid

    @staticmethod
    def _insertar_lectura(c, cartilla, usuario, lectura):
        procesamiento = c.execute(text("INSERT INTO procesamiento_cartilla(id_cartilla,numero_intento,metodo,usuario_proceso,resultado,observacion) VALUES (:cartilla,1,'OPEN_CV',:usuario,'REQUIERE_REVISION','Confianza cualitativa; revisión manual pendiente')"), {'cartilla': cartilla, 'usuario': usuario}).lastrowid
        for respuesta in lectura.get('respuestas', []):
            marca = respuesta.get('respuesta') if respuesta.get('estado') == 'VALIDA' else None
            c.execute(text('INSERT INTO respuestas_detectadas(id_cartilla,id_procesamiento,numero_pregunta,respuesta_detectada,nivel_confianza) VALUES (:cartilla,:procesamiento,:numero,:marca,NULL)'), {'cartilla': cartilla, 'procesamiento': procesamiento, 'numero': respuesta['pregunta'], 'marca': marca})

    def crear(self, datos):
        with self.motor.begin() as c:
            # Misma página y contenido en el mismo examen se conserva una sola vez.
            c.execute(text('SELECT id_examen FROM examenes WHERE id_examen=:examen FOR UPDATE'), {'examen': datos['examen']}).scalar_one()
            duplicada = c.execute(text("SELECT id FROM cargas_omr WHERE examen_id=:examen AND huella=:huella AND estado <> 'DESCARTADA' LIMIT 1"), datos).scalar_one_or_none()
            if duplicada:
                return None
            return c.execute(text('INSERT INTO cargas_omr(examen_id,usuario_id,operacion_id,nombre_archivo,pagina,huella,ruta_imagen,ruta_original) VALUES (:examen,:usuario,:operacion,:nombre,:pagina,:huella,:ruta,:original)'), datos).lastrowid

    def actualizar_lectura(self, id, estado, lectura=None, error=None):
        with self.motor.begin() as c:
            c.execute(text("UPDATE cargas_omr SET estado=:estado,lectura_json=:lectura,error_texto=:error WHERE id=:id AND estado='PENDIENTE'"), {'id': id, 'estado': str(estado), 'lectura': json.dumps(lectura, ensure_ascii=False) if lectura else None, 'error': error})

    def descartar(self, id, motivo):
        with self.motor.begin() as c:
            return c.execute(text("UPDATE cargas_omr SET estado='DESCARTADA',motivo_descarte=:motivo WHERE id=:id AND estado IN ('PENDIENTE','REVISAR','ERROR')"), {'id': id, 'motivo': motivo}).rowcount
