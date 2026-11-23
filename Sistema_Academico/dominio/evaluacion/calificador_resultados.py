"""Reglas de puntuación de una cartilla resuelta."""
from decimal import Decimal

from dominio.evaluacion.desglose_calificacion import DesgloseCalificacion
from dominio.evaluacion.estado_respuesta import EstadoRespuesta
from dominio.evaluacion.tipo_resultado import TipoResultado

UNICA = TipoResultado.UNICA.value
BLANCO = TipoResultado.BLANCO.value
CERO = Decimal(0)


def _tipo_y_marca(fila):
    """Tipo efectivo de la respuesta y letra marcada, considerando la corrección manual si existe."""
    if fila['resolucion']:
        tipo = UNICA if fila['resolucion'] == EstadoRespuesta.MARCA_UNICA else fila['resolucion']
        return tipo, fila['corregida']
    return (UNICA if fila['lectura'] else BLANCO), fila['lectura']


def _puntaje(fila, tipo, correcta, penalizacion):
    if correcta:
        return fila['puntaje']
    return penalizacion if tipo == UNICA else CERO


def _acumular(contador, correcta, tipo, puntaje):
    contador['correctas'] += int(correcta)
    contador['incorrectas'] += int(tipo == UNICA and not correcta)
    contador['blancos'] += int(tipo != UNICA)
    contador['puntaje'] += puntaje


def calificar(filas, penalizacion):
    """Califica las respuestas de una cartilla y devuelve el desglose por pregunta y por materia."""
    detalles = []
    materias = {}
    totales = {'correctas': 0, 'incorrectas': 0, 'blancos': 0, 'puntaje': CERO}
    for fila in filas:
        tipo, marcada = _tipo_y_marca(fila)
        correcta = tipo == UNICA and marcada == fila['clave']
        puntaje = _puntaje(fila, tipo, correcta, penalizacion)
        detalles.append(dict(fila, tipo=tipo, marcada=marcada, correcta=correcta, obtenido=puntaje))
        materia = materias.setdefault(fila['id_materia'], {'total': 0, 'correctas': 0, 'incorrectas': 0, 'blancos': 0, 'puntaje': CERO})
        materia['total'] += 1
        _acumular(materia, correcta, tipo, puntaje)
        _acumular(totales, correcta, tipo, puntaje)
    puntaje_total = max(CERO, sum((detalle['obtenido'] for detalle in detalles), CERO))
    return DesgloseCalificacion(detalles, materias, totales['correctas'], totales['incorrectas'], totales['blancos'], puntaje_total)
