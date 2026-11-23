"""Casos de uso de importación de cartillas: recepción de archivos, lectura OMR, identificación y registro."""
import logging
from pathlib import Path
from uuid import uuid4

from aplicacion.puertos.i_cargas_omr import ICargasOMR
from aplicacion.puertos.i_lector_cartillas import ILectorCartillas
from aplicacion.puertos.i_preparador_cartillas import IPreparadorCartillas
from dominio.evaluacion.estado_entrada import ESTADOS_FILTRABLES, EstadoEntrada
from dominio.evaluacion.identificacion_cartilla import decodificar_lectura, identificar_cartilla

logger = logging.getLogger(__name__)

MAX_ARCHIVOS_POR_CARGA = 20
MAX_NOMBRE = 255
EXTENSIONES_REEMPLAZO = ('.png', '.jpg', '.jpeg')
MSG_ERROR_LECTURA = 'No fue posible leer la imagen; revisa el archivo y los registros del servidor.'


def _exigir_motivo(motivo, mensaje):
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValueError(mensaje)
    return motivo


class ImportacionCartillasAppService:
    def __init__(self, repositorio: ICargasOMR, preparador: IPreparadorCartillas, lector: ILectorCartillas):
        self.repositorio = repositorio
        self.preparador = preparador
        self.lector = lector

    # ------------------------------------------------------------------ consultas
    def examenes(self):
        return self.repositorio.examenes()

    def listar(self, examen_id, pagina=1, estado=''):
        if estado not in ESTADOS_FILTRABLES:
            raise ValueError('Estado de carga no válido.')
        return self.repositorio.listar(examen_id, pagina, estado)

    def resumen(self, examen_id):
        return self.repositorio.resumen(examen_id)

    def opciones_identificacion(self, examen_id):
        return self.repositorio.opciones_identificacion(examen_id)

    def obtener(self, entrada_id):
        return self.repositorio.obtener(entrada_id)

    def historial(self, entrada_id):
        return self.repositorio.historial(entrada_id)

    def archivo_anterior(self, entrada_id, historial_id):
        return self.repositorio.archivo_anterior(entrada_id, historial_id)

    def identificar_para_vista(self, entrada, estudiantes, versiones, area):
        identificacion = identificar_cartilla(decodificar_lectura(entrada.get('lectura_json')), estudiantes, versiones, area)
        # Una identificación ya guardada se conserva; no se reasigna desde una vista.
        if entrada.get('estudiante_id'):
            identificacion['estudiante'] = next((e for e in estudiantes if e['id_estudiante'] == entrada['estudiante_id']), None)
        if entrada.get('version_id'):
            identificacion['version'] = next((v for v in versiones if v['id_version'] == entrada['version_id']), None)
        return identificacion

    # ------------------------------------------------------------------ importación
    def importar_lote(self, examen_id, archivos, usuario_id):
        if not archivos:
            raise ValueError('Selecciona al menos un archivo.')
        if len(archivos) > MAX_ARCHIVOS_POR_CARGA:
            raise ValueError('Selecciona como máximo 20 archivos por carga.')
        return sum(self._importar_archivo(examen_id, usuario_id, nombre, contenido) for nombre, contenido in archivos)

    def _importar_archivo(self, examen_id, usuario_id, nombre, contenido):
        if not contenido or len(contenido) > self.preparador.MAX_BYTES:
            raise ValueError('Cada archivo debe contener datos y tener un máximo de 20 MB.')
        operacion = str(uuid4())
        original, huella_original = self.preparador.guardar_pagina(contenido)
        datos = {'examen': examen_id, 'usuario': usuario_id, 'operacion': operacion, 'nombre': nombre[:MAX_NOMBRE], 'original': str(original)}
        creadas = 0
        try:
            for pagina, imagen in self.preparador.paginas(nombre, contenido):
                creadas += self._registrar_pagina(datos, pagina, imagen)
        except ValueError as error:
            creadas += self._registrar_archivo_ilegible(datos, original, huella_original, error)
        return creadas

    def _registrar_pagina(self, datos, pagina, imagen):
        ruta, huella = self.preparador.guardar_pagina(imagen)
        try:
            entrada_id = self.repositorio.crear(dict(datos, pagina=pagina, huella=huella, ruta=str(ruta)))
        except Exception:
            # Limpieza del archivo recién escrito; el error se propaga sin alterarse.
            self.preparador.descartar_archivo_temporal(ruta)
            raise
        if entrada_id is None:
            self.preparador.descartar_archivo_temporal(ruta)
            return 0
        self._procesar(entrada_id, ruta)
        return 1

    def _registrar_archivo_ilegible(self, datos, original, huella, error):
        """Conserva el archivo que no pudo convertirse como entrada en ERROR, reutilizando la copia ya guardada."""
        entrada_id = self.repositorio.crear(dict(datos, pagina=0, huella=huella, ruta=str(original)))
        if not entrada_id:
            return 0
        self.repositorio.actualizar_lectura(entrada_id, EstadoEntrada.ERROR, error=str(error))
        return 1

    def _procesar(self, entrada_id, ruta):
        try:
            lectura = self.lector.leer(ruta, None)
            if not lectura['exito']:
                self.repositorio.actualizar_lectura(entrada_id, EstadoEntrada.ERROR, lectura, lectura.get('error'))
            else:
                # La identificación se deriva de la lectura al presentar o registrar la entrada.
                self.repositorio.actualizar_lectura(entrada_id, EstadoEntrada.REVISAR, lectura)
        except Exception:
            # Frontera con el motor OMR: cualquier fallo se registra y la entrada queda en ERROR para reintentarla.
            logger.exception('Error procesando la entrada %s', entrada_id)
            self.repositorio.actualizar_lectura(entrada_id, EstadoEntrada.ERROR, error=MSG_ERROR_LECTURA)

    # ------------------------------------------------------------------ resolución
    def resolver_identificacion(self, entrada_id, estudiante_id, version_id):
        try:
            estudiante_id = int(estudiante_id)
            version_id = int(version_id)
        except (TypeError, ValueError):
            raise ValueError('Selecciona un estudiante y una versión válidos.') from None
        if estudiante_id <= 0 or version_id <= 0:
            raise ValueError('Selecciona un estudiante y una versión válidos.')
        self.repositorio.resolver_identificacion(entrada_id, estudiante_id, version_id)

    def registrar_cartilla(self, entrada_id, usuario_id, motivo):
        return self.repositorio.registrar_cartilla(entrada_id, usuario_id, (motivo or '').strip())

    def descartar_entrada(self, entrada_id, motivo):
        motivo = _exigir_motivo(motivo, 'Indica el motivo del descarte.')
        if not self.repositorio.descartar(entrada_id, motivo):
            raise ValueError('La entrada no existe o ya fue descartada.')

    def reintentar_lectura(self, entrada_id, usuario, motivo):
        motivo = _exigir_motivo(motivo, 'Indica por qué reintentas la lectura.')
        ruta = self.repositorio.preparar_reintento(entrada_id, usuario, motivo)
        self._procesar(entrada_id, ruta)

    def reemplazar_imagen(self, entrada_id, usuario, motivo, nombre, contenido):
        motivo = _exigir_motivo(motivo, 'Indica el motivo del reemplazo.')
        if Path(nombre).suffix.lower() not in EXTENSIONES_REEMPLAZO:
            raise ValueError('Adjunta una imagen PNG o JPG de reemplazo.')
        paginas = list(self.preparador.paginas(nombre, contenido))
        ruta, huella = self.preparador.guardar_pagina(paginas[0][1])
        try:
            self.repositorio.preparar_reintento(entrada_id, usuario, motivo, {'ruta': str(ruta), 'huella': huella, 'nombre': Path(nombre).name[:MAX_NOMBRE]})
        except Exception:
            self.preparador.descartar_archivo_temporal(ruta)
            raise
        self._procesar(entrada_id, ruta)
