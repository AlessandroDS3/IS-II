"""Etapa 03.2: localización OBSERVADA de los cuatro cuadrados negros.

Se buscan primero en una foto rectificada por ORB/SIFT. A diferencia de
proyectar coordenadas, esta función comprueba la existencia de tinta cuadrada.
No acepta formas difusas ni inventa puntos para las esquinas ausentes.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import cv2
import numpy as np

from .definir_parametros_omr import Imagen

UMBRALES_BINARIZACION = (90, 115, 140, 165, 190, 215)
DISTANCIA_MAXIMA_PX = 26
CLAVES_MARCADORES = ("tl", "tr", "bl", "br")
NOMBRES_MARCADORES = {
    "tl": "superior_izquierda", "tr": "superior_derecha",
    "bl": "inferior_izquierda", "br": "inferior_derecha",
}
MITAD_PATRON, MARGEN_PATRON = 12, 23
CORRELACION_RESPALDO_MINIMA = .80
ESCALA_MINIMA_AFIN, ESCALA_MAXIMA_AFIN = .94, 1.06
CORRECCION_MAXIMA_PX = 30


def _es_cuadrado_compacto(ancho: int, alto: int, area: int) -> bool:
    return (12 <= ancho <= 32 and 12 <= alto <= 32
            and 110 <= area <= 850 and 0.77 <= ancho / alto <= 1.30
            and area / (ancho * alto) > 0.62)


def _candidatos(region: Imagen, origen: tuple[int, int], esperado: tuple[int, int]) -> list[tuple]:
    """Componentes cuadradas compactas cerca de la posición esperada, para varios umbrales."""
    x0, y0 = origen
    x, y = esperado
    candidatos = []
    for umbral in UMBRALES_BINARIZACION:
        _, mascara = cv2.threshold(region, umbral, 255, cv2.THRESH_BINARY_INV)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        total, _, componentes, centros = cv2.connectedComponentsWithStats(mascara)
        for indice in range(1, total):
            _, _, ancho, alto, area = (int(v) for v in componentes[indice])
            if not _es_cuadrado_compacto(ancho, alto, area):
                continue
            cx, cy = centros[indice] + [x0, y0]
            distancia = float(np.hypot(cx - x, cy - y))
            if distancia > DISTANCIA_MAXIMA_PX:
                continue
            compacidad = area / (ancho * alto)
            puntuacion = (distancia/8 + abs(ancho-20)/7 + abs(alto-20)/7
                          + max(0, .80-compacidad)*4)
            candidatos.append((puntuacion, float(cx), float(cy), umbral))
    return candidatos


# ETAPA 03.2 — Detecta realmente los cuadrados negros, con varios umbrales.
def detectar_marcadores(
    gris: Imagen, coordenadas: Mapping[str, Any], radio_busqueda: int = 39,
) -> tuple[dict[str, list[float]], dict[str, Any]]:
    """Encuentra centros por componentes compactas próximas a cada ancla.

    Devuelve (centros_observados, diagnóstico). Solo se usa para registros
    de hoja ya aproximados; la detección no es una búsqueda global arbitraria.
    """
    encontrados: dict[str, list[float]] = {}
    detalles: dict[str, Any] = {}
    for nombre, posicion in coordenadas.items():
        x, y = (int(round(float(valor))) for valor in posicion)
        x0, y0 = max(0, x-radio_busqueda), max(0, y-radio_busqueda)
        x1 = min(gris.shape[1], x + radio_busqueda + 1)
        y1 = min(gris.shape[0], y + radio_busqueda + 1)
        if x1 <= x0 or y1 <= y0:
            detalles[nombre] = {"encontrado": False, "motivo": "fuera_de_imagen"}
            continue
        region = cv2.GaussianBlur(gris[y0:y1, x0:x1], (3, 3), 0)
        candidatos = _candidatos(region, (x0, y0), (x, y))
        if not candidatos:
            detalles[nombre] = {
                "encontrado": False, "motivo": "cuadrado_no_localizado",
                "posicion_esperada_px": [x, y],
            }
            continue
        _, cx, cy, umbral = min(candidatos)
        encontrados[nombre] = [round(cx, 3), round(cy, 3)]
        detalles[nombre] = {
            "encontrado": True, "centro_observado_px": encontrados[nombre],
            "distancia_a_estimacion_px": round(float(np.hypot(cx-x, cy-y)), 2),
            "umbral_utilizado": umbral,
        }
    return encontrados, detalles


def _normalizar_nombres(coordenadas: Mapping[str, Any]) -> dict[str, Any]:
    """Las plantillas ADDISON usan nombres descriptivos; las rutinas de refinamiento emplean tl/tr/bl/br."""
    return {
        corto: coordenadas[corto] if corto in coordenadas else coordenadas[largo]
        for corto, largo in NOMBRES_MARCADORES.items()
        if corto in coordenadas or largo in coordenadas
    }


def _respaldo_por_correlacion(clave, coordenadas, plantilla_gris, aproximada, esperados, observados, info) -> None:
    """Si un cuadrado se fusiona con el borde impreso, la segmentación por componentes falla.
    Se correlaciona entonces la impresión del propio cuadrado físico (+/-23 px), sin inventar
    coordenadas, y solo se acepta una coincidencia fuerte con el dibujo real de la plantilla."""
    h, w = plantilla_gris.shape
    px, py = [int(round(float(v))) for v in coordenadas[clave]]
    mitad, margen = MITAD_PATRON, MARGEN_PATRON
    if (px-mitad-margen < 0 or py-mitad-margen < 0
            or px+mitad+margen >= w or py+mitad+margen >= h):
        return
    patron = plantilla_gris[py-mitad:py+mitad+1, px-mitad:px+mitad+1]
    roi = aproximada[py-mitad-margen:py+mitad+margen+1, px-mitad-margen:px+mitad+margen+1]
    mapa = cv2.matchTemplate(cv2.GaussianBlur(roi, (3, 3), 0), cv2.GaussianBlur(patron, (3, 3), 0), cv2.TM_CCOEFF_NORMED)
    _, puntuacion, _, (xx, yy) = cv2.minMaxLoc(mapa)
    info["marcadores_rectificados"][clave]["correlacion_respaldo"] = round(float(puntuacion), 3)
    if puntuacion < CORRELACION_RESPALDO_MINIMA:
        return
    centro = np.float32(esperados[clave]) + np.float32([xx-margen, yy-margen])
    observados[clave] = np.round(centro, 3).tolist()
    info["marcadores_rectificados"][clave] = {
        "encontrado": True, "centro_observado_px": observados[clave],
        "metodo": "coincidencia_visual_cuadrado",
        "correlacion": round(float(puntuacion), 3),
    }


def _escala_afin_aceptable(afin: Imagen) -> bool:
    singular = np.linalg.svd(afin[:, :2], compute_uv=False)
    return not (singular.min() < ESCALA_MINIMA_AFIN or singular.max() > ESCALA_MAXIMA_AFIN)


def _puntos_control(ancho, alto) -> Imagen:
    return np.float32([[ancho*.1, alto*.1], [ancho*.9, alto*.1], [ancho*.1, alto*.9], [ancho*.9, alto*.9]])


def _correccion(origen: Imagen, destino: Imagen, info: dict[str, Any]) -> Imagen | None:
    """Perspectiva con cuatro marcadores; con tres solo una transformación afín (nunca una perspectiva completa)."""
    if len(origen) == 4:
        info["metodo_correccion"] = "perspectiva_cuatro_marcadores"
        return cv2.getPerspectiveTransform(origen, destino)
    af = cv2.getAffineTransform(origen, destino)
    info["metodo_correccion"] = "afin_tres_marcadores"
    if not _escala_afin_aceptable(af):
        info["motivo"] = "Afin de tres marcadores implica deformación excesiva"
        return None
    return np.vstack([af, [0, 0, 1]])


# PASO 3.8 — Rectifica perspectiva según cuadrados físicos, no esquinas estimadas.
def refinar_con_marcadores(
    foto_gris: Imagen, plantilla_gris: Imagen, homografia: Imagen,
    coordenadas: Mapping[str, Any],
) -> tuple[Imagen | None, dict[str, Any]]:
    """Propone una homografía refinada con 3 o 4 cuadrados observados.

    La corrección nunca debe aceptarse por sí sola: la etapa 3.10 compara
    también la homografía ORB/SIFT original sobre la cuadrícula interior.
    """
    coordenadas = _normalizar_nombres(coordenadas)
    if not all(clave in coordenadas for clave in CLAVES_MARCADORES):
        return None, {"valido": False, "motivo": "Faltan coordenadas de los cuatro marcadores en plantilla"}
    esperados, diag_plantilla = detectar_marcadores(plantilla_gris, coordenadas)
    if len(esperados) != 4:
        return None, {"valido": False, "motivo": "Marcadores no legibles en plantilla maestra",
                      "marcadores_plantilla": diag_plantilla}
    h, w = plantilla_gris.shape
    aproximada = cv2.warpPerspective(
        foto_gris, np.linalg.inv(homografia), (w, h),
        borderMode=cv2.BORDER_CONSTANT, borderValue=255,
    )
    observados, diag_foto = detectar_marcadores(aproximada, coordenadas)
    info: dict[str, Any] = {
        "valido": False, "marcadores_detectados": len(observados),
        "marcadores_rectificados": diag_foto,
        "marcadores_plantilla": esperados,
    }
    for clave in CLAVES_MARCADORES:
        if clave not in observados:
            _respaldo_por_correlacion(clave, coordenadas, plantilla_gris, aproximada, esperados, observados, info)
    info["marcadores_detectados"] = len(observados)
    if len(observados) < 3:
        # ORB/SIFT puede funcionar aun sin cuadrados suficientes.
        # Esta función NO es la verificación final de la alineación.
        info["motivo"] = "Menos de tres marcadores; probar ORB/SIFT sin correccion"
        return None, info
    visibles = [clave for clave in CLAVES_MARCADORES if clave in observados]
    origen = np.float32([observados[clave] for clave in visibles])
    destino = np.float32([esperados[clave] for clave in visibles])
    correccion = _correccion(origen, destino, info)
    if correccion is None:
        return None, info
    puntos = _puntos_control(w, h)
    desplazamientos = cv2.perspectiveTransform(puntos.reshape(-1, 1, 2), correccion).reshape(-1, 2)
    magnitudes = np.linalg.norm(desplazamientos - puntos, axis=1)
    info["correccion_maxima_px"] = round(float(magnitudes.max()), 2)
    # Rechazar cambios geométricos grandes derivados de anclas equivocadas.
    if not np.isfinite(correccion).all() or float(magnitudes.max()) > CORRECCION_MAXIMA_PX:
        info["motivo"] = "La corrección por marcadores excede los límites geométricos"
        return None, info
    homografia_final = homografia @ np.linalg.inv(correccion)
    if not np.isfinite(homografia_final).all():
        info["motivo"] = "Homografía refinada no finita"
        return None, info
    # Transformación de los centros físicamente observados a la fotografía original.
    coords_raw = cv2.perspectiveTransform(origen.reshape(-1, 1, 2), homografia).reshape(-1, 2)
    info["marcadores_foto_original_px"] = {
        clave: np.round(coords_raw[i], 2).tolist() for i, clave in enumerate(visibles)
    }
    info["valido"] = True
    info["motivo"] = "Ajuste propuesto con cuadrados; requiere validar cuadrícula"
    return homografia_final, info


# PASO 3.10 — Hipótesis adicionales al detectar cuatro cuadrados contradictorios.
def hipotesis_tres_de_cuatro(
    homografia: Imagen, info: Mapping[str, Any], ancho: int, alto: int,
) -> list[tuple[str, Imagen]]:
    """Prueba excluir cada ancla; una ancla falsa no arrastra toda la hoja.

    Estas son HIPÓTESIS, no resultados seguros. Cada una requiere superar
    la validación independiente de la cuadrícula interior.
    """
    observaciones = info.get("marcadores_rectificados", {})
    referencia = info.get("marcadores_plantilla", {})
    visibles = [clave for clave in CLAVES_MARCADORES
                if observaciones.get(clave, {}).get("encontrado") and clave in referencia]
    if len(visibles) != 4:
        return []
    salida = []
    puntos_control = _puntos_control(ancho, alto)
    for omitido in visibles:
        claves = [clave for clave in visibles if clave != omitido]
        origen = np.float32([observaciones[c]["centro_observado_px"] for c in claves])
        destino = np.float32([referencia[c] for c in claves])
        afin = cv2.getAffineTransform(origen, destino)
        if not np.isfinite(afin).all() or not _escala_afin_aceptable(afin):
            continue
        cor = np.vstack((afin, [0., 0., 1.]))
        cambiados = cv2.perspectiveTransform(puntos_control.reshape(-1, 1, 2), cor).reshape(-1, 2)
        if float(np.max(np.linalg.norm(cambiados-puntos_control, axis=1))) > 24:
            continue
        try:
            homografia_hipotesis = homografia @ np.linalg.inv(cor)
        except np.linalg.LinAlgError:
            continue
        if np.isfinite(homografia_hipotesis).all():
            salida.append((f"afin_tres_sin_{omitido}", homografia_hipotesis))
    return salida
