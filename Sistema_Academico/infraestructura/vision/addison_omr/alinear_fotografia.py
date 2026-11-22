"""Registro geométrico ORB/SIFT, validación de homografía y refinamiento ECC."""

# ===================================================================
# MAPA DE REVISIÓN: pasos 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
# Consulta SECUENCIA.md para recorrer el algoritmo en orden.
# La numeración es documental; no cambia llamadas ni nombres Python.
# ===================================================================


from __future__ import annotations

from typing import Any
from collections.abc import Mapping
from pathlib import Path
import json
import logging

import cv2
import numpy as np
from .definir_parametros_omr import Diccionario, ESCALA_ECC, Imagen
from .localizar_burbujas import _centro, _iterar_burbujas
from .cargar_plantilla_referencia import ARCHIVO_PLANTILLA, _leer_imagen, guardar_json, _ruta_coordenadas
from .detectar_marcadores_esquinas import refinar_con_marcadores, hipotesis_tres_de_cuatro
from .validar_cuadricula_respuestas import verificar_cuadricula
from .corregir_alineacion_local import corregir_cuadricula_local

logger = logging.getLogger(__name__)


# PASO 3.6 — Refina una imagen ya alineada; solo con --refinar-ecc.
def mejora_ecc(
    imagen_gris: Imagen, referencia: Imagen, datos: Mapping[str, Any]
) -> tuple[Imagen, Diccionario]:
    """Refina una imagen YA alineada mediante una transformación afín pequeña.

    Se excluyen las burbujas del ajuste para evitar que las marcas modifiquen
    la transformación calculada. Si el ajuste es dudoso, devuelve la imagen
    original junto con una explicación.
    """
    mascara = np.full(referencia.shape, 255, dtype=np.uint8)
    for burbuja in _iterar_burbujas(datos):
        cv2.circle(
            mascara,
            _centro(burbuja),
            round(burbuja["radio_px"] * 1.08),
            0,
            -1,
        )

    mascara[:30, :] = 0
    mascara[-25:, :] = 0

    def reducir(imagen: Imagen) -> Imagen:
        return cv2.resize(
            imagen,
            None,
            fx=ESCALA_ECC,
            fy=ESCALA_ECC,
            interpolation=cv2.INTER_AREA,
        )

    matriz = np.eye(2, 3, dtype=np.float32)
    criterios = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        100,
        1e-5,
    )
    try:
        correlacion, matriz = cv2.findTransformECC(
            reducir(referencia).astype(np.float32) / 255.0,
            reducir(imagen_gris).astype(np.float32) / 255.0,
            matriz,
            cv2.MOTION_AFFINE,
            criterios,
            reducir(mascara),
            5,
        )
    except cv2.error as error:
        return imagen_gris, {"aplicado": False, "motivo": str(error)[:200]}

    matriz[:, 2] /= ESCALA_ECC
    desplazamiento_maximo = float(np.max(np.abs(matriz[:, 2])))
    deformacion_maxima = float(
        np.max(np.abs(matriz[:, :2] - np.eye(2)))
    )
    if (
        correlacion < 0.70
        or desplazamiento_maximo > 10
        or deformacion_maxima > 0.025
    ):
        return imagen_gris, {
            "aplicado": False,
            "correlacion": round(float(correlacion), 4),
            "motivo": "correccion ECC fuera de limites geometricos",
        }

    imagen_corregida = cv2.warpAffine(
        imagen_gris,
        matriz,
        (imagen_gris.shape[1], imagen_gris.shape[0]),
        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    return imagen_corregida, {
        "aplicado": True,
        "correlacion": round(float(correlacion), 4),
        "matriz": np.round(matriz, 5).tolist(),
    }


# PASO 3.4 — Comprueba cobertura, forma y error de homografía.
def medidas_homografia(
    homografia: Imagen | None,
    puntos_plantilla: Imagen,
    buenos: Mapping[str, Imagen],
    inliers: Imagen | None,
    w: int,
    h: int,
    w_img: int,
    h_img: int,
) -> Diccionario | None:
    """Valida geometría y cobertura antes de aceptar una homografía."""
    if homografia is None or inliers is None:
        return None

    mascara = inliers.ravel() != 0
    cantidad = int(mascara.sum())
    if cantidad < 30:
        return None

    esquinas = np.float32(
        [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]
    ).reshape(-1, 1, 2)
    proyectadas = cv2.perspectiveTransform(esquinas, homografia).reshape(-1, 2)
    if not np.isfinite(proyectadas).all():
        return None
    if not cv2.isContourConvex(proyectadas.astype(np.float32)):
        return None

    superficie = abs(cv2.contourArea(proyectadas.astype(np.float32)))
    ratio_superficie = superficie / (w_img * h_img)
    if not 0.12 <= ratio_superficie <= 3.0:
        return None

    longitudes = [
        float(np.linalg.norm(proyectadas[i] - proyectadas[(i + 1) % 4]))
        for i in range(4)
    ]
    if min(longitudes) < min(w_img, h_img) * 0.25:
        return None

    puntos_compatibles = puntos_plantilla[mascara]
    cobertura_ancho = float(
        (puntos_compatibles[:, 0].max() - puntos_compatibles[:, 0].min()) / w
    )
    cobertura_alto = float(
        (puntos_compatibles[:, 1].max() - puntos_compatibles[:, 1].min()) / h
    )
    envolvente = cv2.convexHull(puntos_compatibles.astype(np.float32))
    cobertura_convexa = float(cv2.contourArea(envolvente)) / (w * h)
    if (
        cobertura_ancho < 0.50
        or cobertura_alto < 0.48
        or cobertura_convexa < 0.18
    ):
        return None

    proporcion_inliers = cantidad / len(buenos["src"])
    if proporcion_inliers < 0.25:
        return None

    puntos_foto = buenos["dst"][mascara]
    puntos_proyectados = cv2.perspectiveTransform(
        puntos_compatibles.reshape(-1, 1, 2), homografia
    ).reshape(-1, 2)
    error_mediano = float(
        np.median(np.linalg.norm(puntos_proyectados - puntos_foto, axis=1))
    )
    if error_mediano > 4.0:
        return None

    return {
        "inliers": cantidad,
        "coincidencias_iniciales": len(buenos["src"]),
        "proporcion_inliers": round(proporcion_inliers, 4),
        "cobertura_ancho_plantilla": round(cobertura_ancho, 4),
        "cobertura_alto_plantilla": round(cobertura_alto, 4),
        "cobertura_convexa_plantilla": round(cobertura_convexa, 4),
        "area_documento_respecto_foto": round(ratio_superficie, 4),
        "error_mediano_px": round(error_mediano, 3),
        "esquinas_en_fotografia_px": np.round(proyectadas, 1).tolist(),
    }


# PASO 3.3 — Detecta y empareja rasgos para estimar homografía.
def extraer_coincidencias(
    template: Imagen, foto: Imagen, metodo: str
) -> tuple[Imagen, dict[str, Imagen], Imagen] | None:
    """Calcula coincidencias y una homografía desde la plantilla a la foto."""
    if metodo == "ORB":
        detector = cv2.ORB_create(
            nfeatures=8500, fastThreshold=9, scaleFactor=1.2
        )
        norma, umbral = cv2.NORM_HAMMING, 0.74
    elif metodo == "SIFT":
        detector = cv2.SIFT_create(nfeatures=6500)
        norma, umbral = cv2.NORM_L2, 0.72
    else:
        raise ValueError(f"Método de alineación no soportado: {metodo}")

    puntos_template, descriptores_template = detector.detectAndCompute(
        template, None
    )
    puntos_foto, descriptores_foto = detector.detectAndCompute(foto, None)
    if (
        descriptores_template is None
        or descriptores_foto is None
        or len(puntos_template) < 4
        or len(puntos_foto) < 4
    ):
        return None

    coincidencias_knn = cv2.BFMatcher(norma).knnMatch(
        descriptores_template, descriptores_foto, k=2
    )
    coincidencias = [
        primer
        for pareja in coincidencias_knn
        if len(pareja) == 2
        for primer, segundo in [pareja]
        if primer.distance < umbral * segundo.distance
    ]
    if len(coincidencias) < 40:
        return None

    origen = np.float32(
        [puntos_template[match.queryIdx].pt for match in coincidencias]
    )
    destino = np.float32(
        [puntos_foto[match.trainIdx].pt for match in coincidencias]
    )
    homografia, mascara = cv2.findHomography(
        origen,
        destino,
        cv2.RANSAC,
        4.0,
        maxIters=10000,
        confidence=0.998,
    )
    if homografia is None:
        return None
    return homografia, {"src": origen, "dst": destino}, mascara


# PASO 3.5 — Visualiza esquinas y marcadores detectados.
def _dibujar_deteccion(
    foto: Imagen,
    homografia: Imagen,
    evaluacion: Mapping[str, Any],
    datos: Mapping[str, Any],
) -> Imagen:
    """Marca el borde encontrado y los marcadores de la plantilla."""
    visualizacion = foto.copy()
    esquinas = np.round(
        np.array(evaluacion["esquinas_en_fotografia_px"])
    ).astype(np.int32)
    cv2.polylines(
        visualizacion, [esquinas.reshape(-1, 1, 2)], True, (0, 205, 0), 4
    )
    # VERDE = posición proyectada, NARANJA = centro negro observado.
    for punto in datos["marcadores_px"].values():
        estimado = cv2.perspectiveTransform(
            np.float32(punto).reshape(1, 1, 2), homografia
        )[0, 0]
        cv2.circle(visualizacion, tuple(np.round(estimado).astype(int)),
                   12, (0, 180, 0), 2)
    observados = evaluacion.get("marcadores", {}).get("marcadores_foto_original_px", {})
    for punto in observados.values():
        cv2.circle(visualizacion, tuple(np.round(punto).astype(int)),
                   7, (0, 170, 255), 2)
    return visualizacion


# Penaliza el error máximo y premia la similitud: menor puntaje = mejor registro de la cuadrícula.
PESO_ERROR_MAXIMO = .35
PESO_CORRELACION = .9
PUNTAJE_SIN_MUESTRAS = 1e6
CORRELACION_MINIMA_ECC = 0.27
ERROR_MAXIMO_ECC_PX = 12.0
BLANCO_BGR = (255, 255, 255)


def _puntaje_cuadricula(muestras: list[Mapping[str, Any]]) -> float:
    """Desempate entre hipótesis: menor error local y mayor similitud de cuadrícula."""
    if not muestras:
        return PUNTAJE_SIN_MUESTRAS
    errores = [x["error_px"] for x in muestras]
    return (np.mean(errores) + PESO_ERROR_MAXIMO * max(errores)
            - PESO_CORRELACION * np.mean([x["correlacion"] for x in muestras]))


def _cargar_entrada(carpeta: Path, foto_path: Path) -> tuple[Diccionario, Imagen, Imagen]:
    datos = json.loads(_ruta_coordenadas(carpeta).read_text(encoding="utf-8"))
    ruta_plantilla = carpeta / ARCHIVO_PLANTILLA
    if not ruta_plantilla.exists():
        ruta_plantilla = carpeta / "plantilla_maestra.png"
    return datos, _leer_imagen(ruta_plantilla, cv2.IMREAD_COLOR), _leer_imagen(foto_path, cv2.IMREAD_COLOR)


def _enderezar(foto_gris: Imagen, homografia: Imagen, ancho: int, alto: int) -> Imagen | None:
    try:
        return cv2.warpPerspective(
            foto_gris, np.linalg.inv(homografia), (ancho, alto), flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT, borderValue=255,
        )
    except (cv2.error, np.linalg.LinAlgError):
        return None


def _probar_hipotesis(contexto: Diccionario, opciones, geometria, info_marcadores, validos) -> tuple[list, tuple | None]:
    """Valida cada hipótesis de homografía; devuelve los intentos y la mejor hipótesis fallida recuperable.

    El ECC solo debe aplicarse a la mejor hipótesis inicialmente rechazada de cada detector:
    evita ajustar sobre múltiples variantes y mantiene el coste acotado en fotos difíciles.
    """
    intentos_metodo = []
    mejor_fallida = None
    for nombre_hipotesis, homografia_candidata in opciones:
        corregida = _enderezar(contexto["foto_gris"], homografia_candidata, contexto["ancho"], contexto["alto"])
        if corregida is None:
            continue
        cuadricula = verificar_cuadricula(corregida, contexto["plantilla_gris"], contexto["datos"])
        muestras = cuadricula.get("muestras", [])
        puntaje = _puntaje_cuadricula(muestras)
        intentos_metodo.append({"hipotesis": nombre_hipotesis,
                                "cuadricula_valida": bool(cuadricula["valido"]),
                                "error_maximo_px": cuadricula.get("error_maximo_local_px"),
                                "correlacion_minima": cuadricula.get("correlacion_minima"),
                                "puntaje": round(float(puntaje), 3)})
        if cuadricula["valido"]:
            validos.append((puntaje, nombre_hipotesis, homografia_candidata,
                            geometria, cuadricula, info_marcadores, None, None))
        elif (muestras and cuadricula.get("correlacion_minima", 0) >= CORRELACION_MINIMA_ECC
              and cuadricula.get("error_maximo_local_px", 1e9) <= ERROR_MAXIMO_ECC_PX
              and (mejor_fallida is None or puntaje < mejor_fallida[0])):
            mejor_fallida = (puntaje, nombre_hipotesis, homografia_candidata, corregida)
    return intentos_metodo, mejor_fallida


def _intentar_ecc(contexto: Diccionario, mejor_fallida, geometria, info_marcadores, validos) -> Diccionario:
    """Segunda oportunidad SOLO cuando ninguna hipótesis del detector validó; exige la misma verificación estricta."""
    _, nombre_prev, homografia_prev, imagen_prev = mejor_fallida
    corregida_ecc, informe_ecc = mejora_ecc(imagen_prev, contexto["plantilla_gris"], contexto["datos"])
    intento_ecc = {"hipotesis": f"{nombre_prev}+ECC", "ecc": informe_ecc, "cuadricula_valida": False}
    if not informe_ecc.get("aplicado", False):
        return intento_ecc
    cuadro_ecc = verificar_cuadricula(corregida_ecc, contexto["plantilla_gris"], contexto["datos"])
    intento_ecc["cuadricula_valida"] = bool(cuadro_ecc["valido"])
    intento_ecc["error_maximo_px"] = cuadro_ecc.get("error_maximo_local_px")
    intento_ecc["correlacion_minima"] = cuadro_ecc.get("correlacion_minima")
    if cuadro_ecc["valido"]:
        validos.append((_puntaje_cuadricula(cuadro_ecc["muestras"]), f"{nombre_prev}+ECC",
                        homografia_prev, geometria, cuadro_ecc, info_marcadores, informe_ecc, None))
    return intento_ecc


def _intentar_alineacion_local(contexto: Diccionario, mejor_fallida, geometria, info_marcadores, validos) -> Diccionario:
    """Tercera oportunidad EXPERIMENTAL y opt-in: desplazamiento suave de la zona de respuestas,
    con 24 zonas de validación distintas de las usadas para ajustar la deformación."""
    _, nombre_prev, homografia_prev, imagen_prev = mejor_fallida
    mapa, info_local = corregir_cuadricula_local(imagen_prev, contexto["plantilla_gris"], contexto["datos"])
    if mapa is not None:
        cuadricula_local = info_local["cuadricula"]
        validos.append((_puntaje_cuadricula(cuadricula_local["muestras"]), f"{nombre_prev}+LOCAL",
                        homografia_prev, geometria, cuadricula_local, info_marcadores, None, (mapa, info_local)))
    return {"hipotesis": f"{nombre_prev}+LOCAL", "alineacion_local": info_local}


def _evaluar_detector(contexto: Diccionario, metodo_actual: str, validos: list) -> Diccionario:
    """Estima la homografía con un detector y prueba sus hipótesis (marcadores, tres de cuatro, ECC, local)."""
    matches = extraer_coincidencias(contexto["plantilla_gris"], contexto["foto_gris"], metodo_actual)
    if matches is None:
        return {"metodo": metodo_actual, "motivo": "Sin coincidencias suficientes"}
    h_inicial, puntos, inliers = matches
    geometria = medidas_homografia(h_inicial, puntos["src"], puntos, inliers, contexto["ancho"], contexto["alto"],
                                   contexto["ancho_foto"], contexto["alto_foto"])
    if geometria is None:
        return {"metodo": metodo_actual, "motivo": "Geometría ORB/SIFT inválida"}
    geometria["metodo"] = metodo_actual
    ajuste, info_marcadores = refinar_con_marcadores(contexto["foto_gris"], contexto["plantilla_gris"], h_inicial,
                                                     contexto["datos"].get("marcadores_px", {}))
    opciones = [("sin_refinamiento", h_inicial)]
    if ajuste is not None:
        opciones.append((info_marcadores["metodo_correccion"], ajuste))
    # Si una detección de cuatro cuadrados incluye un falso positivo,
    # contrastar correcciones excluyendo una esquina a la vez.
    opciones.extend(hipotesis_tres_de_cuatro(h_inicial, info_marcadores, contexto["ancho"], contexto["alto"]))
    intentos_metodo, mejor_fallida = _probar_hipotesis(contexto, opciones, geometria, info_marcadores, validos)

    def detector_sin_validar():
        return mejor_fallida is not None and not any(item[3]["metodo"] == metodo_actual for item in validos)

    if detector_sin_validar():
        intentos_metodo.append(_intentar_ecc(contexto, mejor_fallida, geometria, info_marcadores, validos))
    if contexto["alineacion_local"] and detector_sin_validar():
        intentos_metodo.append(_intentar_alineacion_local(contexto, mejor_fallida, geometria, info_marcadores, validos))
    return {"metodo": metodo_actual,
            "marcadores_detectados": info_marcadores.get("marcadores_detectados", 0),
            "hipotesis": intentos_metodo}


def _aplicar_correccion(foto: Imagen, homografia: Imagen, ecc_aplicado, ajuste_local, ancho: int, alto: int) -> Imagen:
    corregida = cv2.warpPerspective(
        foto, np.linalg.inv(homografia), (ancho, alto), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=BLANCO_BGR,
    )
    if ajuste_local is not None:
        mapa_x, mapa_y = ajuste_local[0]
        corregida = cv2.remap(corregida, mapa_x, mapa_y, interpolation=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=BLANCO_BGR)
    if ecc_aplicado is not None and ecc_aplicado.get("aplicado", False):
        corregida = cv2.warpAffine(
            corregida, np.asarray(ecc_aplicado["matriz"], dtype=np.float32), (ancho, alto),
            flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=BLANCO_BGR,
        )
    return corregida


def _escribir_imagen(ruta: Path, imagen: Imagen, parametros=None) -> None:
    if not cv2.imwrite(str(ruta), imagen, parametros or []):
        raise OSError(f"No se pudo guardar la imagen: {ruta}")


def _metricas_seleccionadas(validos: list, intentos: list) -> tuple[Diccionario, Imagen, Any, Any]:
    _, nombre_hipotesis, homografia, evaluacion, cuadricula, marcadores, ecc_aplicado, ajuste_local = min(
        validos, key=lambda item: item[0]
    )
    evaluacion = dict(evaluacion)
    evaluacion["cuadricula"] = cuadricula
    evaluacion["marcadores"] = marcadores
    evaluacion["hipotesis_seleccionada"] = nombre_hipotesis
    evaluacion["ecc_automatico"] = ecc_aplicado
    evaluacion["alineacion_local"] = ajuste_local[1] if ajuste_local else None
    evaluacion["intentos"] = intentos
    metodos_validos = {i[3]["metodo"] for i in validos}
    evaluacion["metodos_alternativos_validos"] = sorted(metodos_validos)
    # Si sólo una familia o pocos marcadores verifican la geometría,
    # permitir lectura diagnosticada pero impedir calificación sin revisión.
    evaluacion["revision_geometrica_recomendada"] = (
        len(metodos_validos) < 2 or marcadores.get("marcadores_detectados", 0) < 3 or ajuste_local is not None
    )
    return evaluacion, homografia, ecc_aplicado, ajuste_local


# PASO 3.1 — Alinea una fotografía y guarda diagnóstico geométrico; si se solicita.
def alinear(
    foto_path: str | Path,
    carpeta: str | Path,
    metodo: str = "AUTO",
    prefijo: str = "cartilla",
    alineacion_local: bool = False,
) -> Diccionario:
    """Alinea la foto y guarda la imagen, visualización y reporte geométrico."""
    carpeta = Path(carpeta)
    foto_path = Path(foto_path)
    datos, plantilla, foto = _cargar_entrada(carpeta, foto_path)
    plantilla_gris = cv2.cvtColor(plantilla, cv2.COLOR_BGR2GRAY)
    foto_gris = cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY)
    alto, ancho = plantilla_gris.shape
    alto_foto, ancho_foto = foto_gris.shape
    contexto = {"datos": datos, "plantilla_gris": plantilla_gris, "foto_gris": foto_gris, "ancho": ancho, "alto": alto,
                "ancho_foto": ancho_foto, "alto_foto": alto_foto, "alineacion_local": alineacion_local}
    ruta_reporte = carpeta / f"{prefijo}_reporte.json"

    # PASO 3.10 — No obligar cuatro cuadrados: comparar ORB, SIFT y
    # correcciones opcionales, conservando el mejor registro interior.
    validos = []
    metodos = ("ORB", "SIFT") if metodo == "AUTO" else (metodo,)
    intentos = [_evaluar_detector(contexto, metodo_actual, validos) for metodo_actual in metodos]

    if not validos:
        reporte = {
            "valido": False,
            "motivo": "Ninguna hipótesis ORB/SIFT, con o sin marcadores, validó la cuadrícula interior",
            "intentos": intentos,
        }
        guardar_json(ruta_reporte, reporte)
        logger.info("RECHAZADA: %s", reporte["motivo"])
        return reporte
    evaluacion, homografia, ecc_aplicado, ajuste_local = _metricas_seleccionadas(validos, intentos)
    corregida = _aplicar_correccion(foto, homografia, ecc_aplicado, ajuste_local, ancho, alto)

    nombre_alineada = f"{prefijo}_alineada.png"
    ruta_alineada = carpeta / nombre_alineada
    _escribir_imagen(ruta_alineada, corregida)
    _escribir_imagen(carpeta / f"{prefijo}_deteccion.jpg", _dibujar_deteccion(foto, homografia, evaluacion, datos),
                     [cv2.IMWRITE_JPEG_QUALITY, 92])

    reporte = {
        "valido": True,
        "imagen_fuente": foto_path.name,
        "imagen_resultado": nombre_alineada,
        "metricas": evaluacion,
        "revision_geometrica_recomendada": evaluacion["revision_geometrica_recomendada"],
        "nota": (
            "Validacion geometrica preliminar; no es garantia "
            "de lectura correcta."
        ),
    }
    guardar_json(ruta_reporte, reporte)
    logger.info("ALINEACION ACEPTADA: %s | inliers %s / coincidencias %s | cobertura %s | error mediano %s px | imagen %s",
                evaluacion["metodo"], evaluacion["inliers"], evaluacion["coincidencias_iniciales"],
                evaluacion["cobertura_convexa_plantilla"], evaluacion["error_mediano_px"], ruta_alineada.resolve())
    return reporte
