"""ETAPA 11.1 — Comparación CONSERVADORA de varias capturas de una misma cartilla.

Modo expresamente solicitado. No altera decisiones OMR ni calibra confianzas.
Las fotos de una misma hoja pueden ser dependientes (recortes/giro), y el
acuerdo entre tratamientos de una misma imagen tampoco es independencia.

Se agrupan solo lecturas con coincidencia fuerte de DNI parcial y respuestas.
Cada propuesta requiere verificación humana antes de calificar.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import csv
import json

from ..ejecutar_flujo_lectura import procesar


def _respuesta_misma_hoja(a: dict, b: dict) -> dict:
    """Criterio conservador: DNI parcial + coincidencia de respuestas válidas."""
    da, db = a['dni'], b['dni']
    posiciones = [(x, y) for x, y in zip(da, db) if x.isdigit() and y.isdigit()]
    coincidencia_dni = sum(x == y for x, y in posiciones)
    dif_dni = len(posiciones) - coincidencia_dni
    aa = a['controles']['area']
    ab = b['controles']['area']
    area_compatible = not (aa['estado'] == ab['estado'] == 'VALIDA'
                           and aa['respuesta'] != ab['respuesta'])
    parejas = [(x['respuesta'], y['respuesta'])
              for x, y in zip(a['respuestas'], b['respuestas'])
              if x['estado'] == y['estado'] == 'VALIDA']
    total_validas = len(parejas)
    iguales = sum(x == y for x, y in parejas)
    compatible = (dif_dni == 0 and coincidencia_dni >= 5 and
                  area_compatible and total_validas >= 60 and
                  iguales / total_validas >= .98)
    return {'compatible': compatible, 'digitos_dni_comparados': len(posiciones),
            'digitos_dni_iguales': coincidencia_dni,
            'respuestas_validas_comparadas': total_validas,
            'respuestas_validas_coincidentes': iguales,
            'area_compatible': area_compatible}


def _grupos_compatibles(resultados: list[dict]) -> tuple[list[list[int]], list[dict]]:
    """Agrupación completa: todos los pares del grupo deben ser compatibles."""
    pares = {}
    comparaciones = []
    for i in range(len(resultados)):
        for j in range(i + 1, len(resultados)):
            c = _respuesta_misma_hoja(resultados[i], resultados[j])
            pares[i, j] = c['compatible']
            comparaciones.append(dict(imagen_a=resultados[i]['imagen_fuente'],
                                      imagen_b=resultados[j]['imagen_fuente'], **c))
    grupos = []
    for indice in range(len(resultados)):
        asignado = False
        for grupo in grupos:
            if all(pares[min(indice, j), max(indice, j)] for j in grupo):
                grupo.append(indice)
                asignado = True
                break
        if not asignado:
            grupos.append([indice])
    return grupos, comparaciones


COLUMNAS_SUGERENCIAS = ['imagen', 'campo', 'indice', 'estado_original', 'candidatas_originales',
                        'respuesta_sugerida', 'imagenes_con_respuesta_valida',
                        'confirmacion_manual_obligatoria', 'observacion']
FILA_SIN_LECTURA = {'dni': '', 'area': '', 'validas': '', 'dudosas': '', 'dobles': '', 'sin_respuesta': '',
                    'requiere_revision': True}


def _items(registros: list[dict], campo: str, indice: int | str) -> list[dict]:
    if campo == 'pregunta':
        return [r['respuestas'][int(indice) - 1] for r in registros]
    if campo == 'dni':
        return [r['detalle_dni'][int(indice) - 1] for r in registros]
    return [r['controles'][str(indice)] for r in registros]


def _admite_sugerencia(item: dict, candidata, items: list[dict]) -> bool:
    """Nunca ignorar una doble marca. Para una duda, exigir que la candidata sea la única alternativa
    detectada; un vacío necesita revisión visual."""
    if item['estado'] in ('VALIDA', 'DOBLE_MARCA'):
        return False
    candidatas = item.get('candidatas') or []
    if item['estado'] == 'DUDOSA' and (not candidatas or any(op != candidata for op in candidatas)):
        return False
    return all(x['estado'] != 'DUDOSA' or not x.get('candidatas') or candidata in x['candidatas'] for x in items)


def _evaluar_campos(registros: list[dict], campo: str, indice: int | str,
                    archivos: list[str]) -> list[dict]:
    """Sugerencias para registros DUDOSA/SIN_RESPUESTA, nunca cambios oficiales."""
    items = _items(registros, campo, indice)
    fuertes = [(a, item['respuesta']) for a, item in zip(archivos, items)
               if item['estado'] == 'VALIDA' and item['respuesta'] is not None]
    alternativas = {respuesta for _, respuesta in fuertes}
    if len(alternativas) != 1:
        return []
    candidata = next(iter(alternativas))
    return [{
        'imagen': archivo, 'campo': campo, 'indice': indice,
        'estado_original': item['estado'],
        'candidatas_originales': item.get('candidatas') or [],
        'respuesta_sugerida': candidata,
        'imagenes_con_respuesta_valida': [nombre for nombre, _ in fuertes],
        'confirmacion_manual_obligatoria': True,
        'observacion': ('Marca dudosa coherente con otra captura' if item['estado'] == 'DUDOSA'
                        else 'No detectada en esta captura; revisar visualmente'),
    } for archivo, item in zip(archivos, items) if _admite_sugerencia(item, candidata, items)]


def _procesar_imagen(numero: int, imagen: Path, carpeta, salida: Path):
    """Lee una captura; devuelve (resultado o None, rechazo o None, fila del resumen)."""
    prefijo = salida / 'individual' / f'{numero:02d}_{imagen.stem}'
    try:
        r = procesar(imagen, carpeta, salida=prefijo, alineacion=True, alineacion_local=True)
    except Exception as error:  # cualquier fallo de una captura se registra y no detiene el lote
        fila = {'archivo': imagen.name, 'resultado': 'ERROR', **FILA_SIN_LECTURA}
        return None, {'imagen': imagen.name, 'error': str(error)}, fila
    if r.get('exito', True) is False:
        fila = {'archivo': imagen.name, 'resultado': 'RECHAZADA', **FILA_SIN_LECTURA}
        return None, {'imagen': imagen.name, 'error': r['error']}, fila
    s = r['resumen']
    return r, None, {'archivo': imagen.name, 'resultado': 'LEIDA',
                     'dni': r['dni'], 'area': r['controles']['area']['respuesta'] or '',
                     'validas': s['VALIDA'], 'dudosas': s['DUDOSA'],
                     'dobles': s['DOBLE_MARCA'], 'sin_respuesta': s['SIN_RESPUESTA'],
                     'requiere_revision': s['requiere_revision']}


def _sugerencias_grupo(registros: list[dict], archivos: list[str]) -> list[dict]:
    sugerencias = []
    for pregunta in range(1, 91):
        sugerencias.extend(_evaluar_campos(registros, 'pregunta', pregunta, archivos))
    for columna in range(1, 9):
        sugerencias.extend(_evaluar_campos(registros, 'dni', columna, archivos))
    for control in ('turno', 'area', 'tema'):
        sugerencias.extend(_evaluar_campos(registros, 'control', control, archivos))
    return sugerencias


def _escribir_reportes(salida: Path, reporte: dict, resumen: list[dict], sugerencias: list[dict]) -> None:
    (salida / 'reporte_recuperacion.json').write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding='utf-8')
    with (salida / 'resumen.csv').open('w', newline='', encoding='utf-8-sig') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resumen[0]))
        escritor.writeheader()
        escritor.writerows(resumen)
    with (salida / 'sugerencias_revision.csv').open('w', newline='', encoding='utf-8-sig') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_SUGERENCIAS)
        escritor.writeheader()
        for s in sugerencias:
            escritor.writerow({**s,
                               'candidatas_originales': '/'.join(s['candidatas_originales']),
                               'imagenes_con_respuesta_valida': ' / '.join(s['imagenes_con_respuesta_valida'])})


def analizar_lote(imagenes: Sequence[str | Path], carpeta: str | Path,
                  salida: str | Path) -> dict:
    """Procesa capturas y guarda comparaciones sin modificar el resultado individual.

    Las imágenes con error se registran como rechazadas y no participan en
    propuestas. Las sugerencias NO rellenan datos ni otorgan % de confianza.
    """
    imagenes = [Path(x) for x in imagenes]
    if not imagenes:
        raise ValueError('Se necesita al menos una fotografía')
    if len({str(x.resolve()) for x in imagenes}) != len(imagenes):
        raise ValueError('Hay rutas duplicadas en el lote')
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    resultados, rechazadas, resumen = [], [], []
    for n, imagen in enumerate(imagenes, 1):
        resultado, rechazo, fila = _procesar_imagen(n, imagen, carpeta, salida)
        resumen.append(fila)
        if resultado is not None:
            resultados.append(resultado)
        else:
            rechazadas.append(rechazo)
    grupos, comparaciones = _grupos_compatibles(resultados)
    agrupaciones = []
    sugerencias = []
    for i, indices in enumerate(grupos, 1):
        registros = [resultados[j] for j in indices]
        archivos = [x['imagen_fuente'] for x in registros]
        agrupaciones.append({'grupo': i, 'imagenes': archivos, 'mismo_original_confirmado': False,
                             'advertencia': 'Solo grupo probable; verificar que sea la misma hoja física'})
        if len(indices) >= 2:
            sugerencias.extend(_sugerencias_grupo(registros, archivos))
    salida_reporte = {
        'modo': 'recuperacion_especial_multifoto',
        'advertencia': ('Los resultados OMR originales no se alteran. Todas las propuestas '
                        'requieren comprobación humana y mismo original físico confirmado. '
                        'Las categorias alta/media/baja NO son porcentajes de acierto.'),
        'agrupaciones_probables': agrupaciones,
        'comparaciones': comparaciones,
        'sugerencias_pendientes_confirmacion': sugerencias,
        'rechazadas': rechazadas,
        'resumen': resumen,
    }
    _escribir_reportes(salida, salida_reporte, resumen, sugerencias)
    return salida_reporte
