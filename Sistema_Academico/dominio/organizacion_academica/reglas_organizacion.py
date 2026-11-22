"""Reglas compartidas para administrar la organización académica."""
from datetime import date

from dominio.organizacion_academica.estado_registro import ESTADOS_BASICOS, EstadoRegistro

TIPOS = ('areas', 'ejes', 'materias', 'ciclos', 'grupos')
MAX_NOMBRE = 100
MAX_CODIGO_AREA = 50
LIMITES_GRUPO = (('horario', 100), ('aula', 50))
ESTADOS_ADMITIDOS = tuple(estado.value for estado in EstadoRegistro)


def identificador(valor, nombre):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'Selecciona {nombre} válido.') from None
    if numero <= 0:
        raise ValueError(f'Selecciona {nombre} válido.')
    return numero


def _validar_area(datos, valores):
    if not valores['codigo'] or len(valores['codigo']) > MAX_CODIGO_AREA:
        raise ValueError('El código del área es obligatorio y admite hasta 50 caracteres.')


def _validar_materia(datos, valores):
    valores['id_eje'] = identificador(datos.get('id_eje'), 'un eje')


def _validar_grupo(datos, valores):
    valores['id_ciclo'] = identificador(datos.get('id_ciclo'), 'un ciclo')
    for campo, maximo in LIMITES_GRUPO:
        valor = (datos.get(campo) or '').strip()
        if len(valor) > maximo:
            raise ValueError(f'{campo.capitalize()} admite hasta {maximo} caracteres.')
        valores[campo] = valor or None


def _fecha_opcional(datos, campo):
    return date.fromisoformat(datos[campo]) if datos.get(campo) else None


def _validar_ciclo(datos, valores):
    try:
        inicio = _fecha_opcional(datos, 'fecha_inicio')
        fin = _fecha_opcional(datos, 'fecha_fin')
    except ValueError:
        raise ValueError('Las fechas del ciclo no son válidas.') from None
    if inicio and fin and fin < inicio:
        raise ValueError('La fecha final no puede ser anterior a la inicial.')
    valores.update(fecha_inicio=inicio, fecha_fin=fin)


# Validación específica por tipo de catálogo: añadir un catálogo solo requiere registrar aquí su regla.
VALIDADORES_POR_TIPO = {
    'areas': _validar_area,
    'materias': _validar_materia,
    'grupos': _validar_grupo,
    'ciclos': _validar_ciclo,
}


def validar_tipo(tipo):
    if tipo not in TIPOS:
        raise ValueError('Tipo de elemento no válido.')
    return tipo


def validar_datos(tipo, datos):
    validar_tipo(tipo)
    nombre = (datos.get('nombre') or '').strip()
    if not nombre or len(nombre) > MAX_NOMBRE:
        raise ValueError('El nombre es obligatorio y admite hasta 100 caracteres.')
    valores = {'nombre': nombre, 'codigo': (datos.get('codigo') or '').strip()}
    validador = VALIDADORES_POR_TIPO.get(tipo)
    if validador:
        validador(datos, valores)
    return valores


def validar_estado(tipo, estado):
    if tipo not in TIPOS or estado not in ESTADOS_ADMITIDOS:
        raise ValueError('Estado no válido.')
    if estado == EstadoRegistro.FINALIZADO and tipo != 'ciclos':
        raise ValueError('Solo se pueden finalizar ciclos.')
    return estado


def validar_transicion_estado(tipo, actual, nuevo):
    validar_estado(tipo, nuevo)
    if actual == EstadoRegistro.FINALIZADO:
        raise ValueError('Un ciclo finalizado no puede reactivarse.')
    if actual not in ESTADOS_BASICOS:
        raise ValueError('Estado actual no válido.')
