"""Identificación de una cartilla a partir de marcas y coincidencias inequívocas."""
import json
import re
import unicodedata

COLUMNAS_DNI = 8
PATRON_DNI = re.compile(r'\d{8}', re.ASCII)  # solo dígitos 0-9, como en la versión original
AREAS_POR_MARCA = {'I': 'Ingenierías', 'B': 'Biomédicas', 'S': 'Sociales'}


def decodificar_lectura(valor):
    """La lectura OMR se guarda como JSON; algunos conectores ya la devuelven decodificada."""
    return json.loads(valor) if isinstance(valor, str) else valor


def _normalizar(valor):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(valor)) if not unicodedata.combining(c)).casefold().strip()


def _control_valido(control):
    return (isinstance(control, dict) and control.get('estado') == 'VALIDA'
            and control.get('requiere_revision_manual') is not True
            and control.get('confianza') != 'baja' and bool(control.get('respuesta')))


def _dni_valido(lectura, resumen, detalle):
    dni = str(lectura.get('dni') or '').strip()
    valido = (bool(PATRON_DNI.fullmatch(dni)) and resumen.get('dni_completo') is True
              and not resumen.get('dni_columnas_revision') and not resumen.get('dni_faltantes_o_invalidos'))
    columnas = lectura.get('detalle_dni') or detalle.get('detalle_dni') or []
    if columnas:
        valido = valido and len(columnas) == COLUMNAS_DNI and all(_control_valido(c) for c in columnas)
    return dni if valido else None


def _unico(candidatos):
    return candidatos[0] if len(candidatos) == 1 else None


def _identificar_estudiante(resultado, lectura, resumen, detalle, estudiantes):
    dni = _dni_valido(lectura, resumen, detalle)
    if dni:
        resultado['estudiante'] = _unico([e for e in estudiantes if str(e.get('dni') or '').strip() == dni])


def _control_confirmado(controles, nombre, resumen):
    control = controles.get(nombre) or {}
    if _control_valido(control) and nombre not in (resumen.get('controles_revision') or []):
        return control
    return None


def _identificar_area(resultado, controles, resumen, area_actual):
    area = _control_confirmado(controles, 'area', resumen)
    nombre = AREAS_POR_MARCA.get(str(area['respuesta']).upper()) if area else None
    if not nombre:
        return
    resultado['area_detectada'] = nombre
    resultado['area_coincide'] = _normalizar(nombre) == _normalizar(area_actual)
    if not resultado['area_coincide']:
        resultado['bloqueo'] = f'La cartilla indica {nombre}, pero la carga pertenece a {area_actual}. Cárgala en el área correspondiente o revisa la imagen.'


def _identificar_version(resultado, controles, resumen, versiones):
    tema = _control_confirmado(controles, 'tema', resumen)
    if not tema:
        if len(versiones) == 1:
            resultado['version'] = versiones[0]
        return
    codigo = str(tema['respuesta']).strip().upper()
    version = _unico([v for v in versiones if str(v['codigo_version']).strip().upper() == codigo])
    if version:
        resultado['version'] = version
    else:
        resultado['bloqueo'] = f'La cartilla indica la versión {codigo}, que no está activa en este examen. Revisa la imagen o la configuración.'


def identificar_cartilla(lectura, estudiantes, versiones, area_actual):
    resultado = {'estudiante': None, 'version': None, 'area_detectada': None,
                 'area_coincide': False, 'bloqueo': None, 'completa': False}
    if not lectura or not lectura.get('exito'):
        return resultado
    resumen = lectura.get('resumen') or {}
    detalle = lectura.get('detalle') or {}
    controles = lectura.get('controles') or {}
    _identificar_estudiante(resultado, lectura, resumen, detalle, estudiantes)
    _identificar_area(resultado, controles, resumen, area_actual)
    _identificar_version(resultado, controles, resumen, versiones)
    resultado['completa'] = bool(resultado['estudiante'] and resultado['version']
                                 and resultado['area_coincide'] and not resultado['bloqueo'])
    return resultado
