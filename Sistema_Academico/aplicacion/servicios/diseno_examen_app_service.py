"""Casos de uso de configuración de exámenes y claves."""
import csv
import io
from decimal import Decimal, InvalidOperation

from dominio.banco_preguntas.letra import LETRAS
from dominio.diseno_evaluaciones.examen import CODIGOS_VERSION
from dominio.diseno_evaluaciones.i_diseno_examen_repositorio import IDisenoExamenRepositorio

MAX_BYTES_CSV_CLAVE = 100000
MAX_DECIMALES = 9
ENCABEZADOS_CSV = ('pregunta', 'numero')


def _decimales_validos(valor):
    return valor.is_finite() and valor.as_tuple().exponent >= -MAX_DECIMALES


def respuestas_desde_csv(contenido):
    """Convierte el CSV de una clave (número,respuesta) en un diccionario; valida tamaño, codificación y unicidad."""
    if len(contenido) > MAX_BYTES_CSV_CLAVE:
        raise ValueError('El CSV supera el tamaño permitido.')
    try:
        texto = contenido.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('El CSV debe estar codificado en UTF-8.') from None
    respuestas = {}
    for fila in csv.reader(io.StringIO(texto)):
        if not fila or (len(fila) == 2 and fila[0].strip().lower() in ENCABEZADOS_CSV):
            continue
        if len(fila) != 2 or fila[0].strip() in respuestas:
            raise ValueError('El CSV debe contener número y respuesta únicos en cada fila.')
        respuestas[fila[0].strip()] = fila[1].strip()
    return respuestas


class DisenoExamenAppService:
    def __init__(self, repositorio: IDisenoExamenRepositorio):
        self.repositorio = repositorio

    def consultar(self, examen):
        return self.repositorio.consultar(examen)

    def distribucion(self, examen):
        return self.repositorio.distribucion(examen)

    def configurar(self, examen, ids, puntajes, versiones, penalizacion, usuario):
        try:
            preguntas = list(dict.fromkeys(int(x) for x in ids))
            importes = {int(k): Decimal(v) for k, v in puntajes.items()}
            penalizacion = Decimal(penalizacion or '0')
        except (ValueError, InvalidOperation):
            raise ValueError('Revisa los identificadores y puntajes.') from None
        if not preguntas or not versiones or any(v not in CODIGOS_VERSION for v in versiones):
            raise ValueError('Selecciona preguntas y al menos una versión.')
        if not _decimales_validos(penalizacion) or penalizacion > 0:
            raise ValueError('La penalización debe ser cero o negativa, con hasta 9 decimales.')
        if any(not _decimales_validos(v) or v <= 0 for v in importes.values()):
            raise ValueError('Cada puntaje debe ser positivo y tener hasta 9 decimales.')
        self.repositorio.configurar(examen, preguntas, importes, versiones, penalizacion, usuario)

    def crear_clave(self, version, valores, motivo, usuario):
        motivo = (motivo or '').strip()
        if not motivo:
            raise ValueError('Indica el motivo de la nueva revisión de clave.')
        try:
            respuestas = {int(k): str(v).strip().upper() for k, v in valores.items()}
        except ValueError:
            raise ValueError('La numeración no es válida.') from None
        if not respuestas or any(v not in LETRAS for v in respuestas.values()):
            raise ValueError('Cada respuesta debe estar entre A y E.')
        self.repositorio.crear_clave(version, respuestas, motivo, usuario)
