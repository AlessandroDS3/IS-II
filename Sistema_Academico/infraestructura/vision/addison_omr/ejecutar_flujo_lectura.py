"""Flujo de procesamiento completo desde imagen hasta reporte (paso 1.2 de SECUENCIA.md)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import cv2

from .alinear_fotografia import alinear, mejora_ecc
from .cargar_plantilla_referencia import _leer_imagen, leer_datos
from .consolidar_resultados_omr import leer_v4
from .definir_parametros_omr import Diccionario, UMBRAL_ERROR_ALINEACION
from .exportar_json_csv import _guardar_resultados
from .validar_cuadricula_respuestas import verificar_cuadricula

LONGITUD_IDENTIFICADOR = 12


def _alinear(ruta: Path, carpeta: Path, alineacion_local: bool) -> tuple[Diccionario, Path]:
    """3.1 — Alinea la fotografía; devuelve el reporte y la ruta de la imagen alineada."""
    identificador = hashlib.sha256(str(ruta.resolve()).encode("utf-8")).hexdigest()[:LONGITUD_IDENTIFICADOR]
    prefijo_alineacion = f"temp_v4_{identificador}"
    reporte = alinear(ruta, carpeta, prefijo=prefijo_alineacion, alineacion_local=alineacion_local)
    return reporte, carpeta / f"{prefijo_alineacion}_alineada.png"


def _refinar(gris, referencia, datos, reporte, refinar: bool):
    """3.6 — Refinamiento ECC opcional, salvo que la alineación ya lo aplicara (o aplicara corrección local)."""
    metricas = (reporte or {}).get("metricas", {})
    if refinar and not (metricas.get("ecc_automatico") or metricas.get("alineacion_local")):
        return mejora_ecc(gris, referencia, datos)
    if metricas.get("ecc_automatico"):
        informacion = dict(metricas["ecc_automatico"])
        informacion["motivo"] = "Refinamiento ECC automático durante la alineación"
        return gris, informacion
    return gris, {"aplicado": False, "motivo": "No solicitado"}


def _marcar_revision_global(resumen: Diccionario) -> None:
    resumen["requiere_revision"] = True
    resumen["revision_global_alineacion"] = True
    # Evita el estado contradictorio de la versión original.
    resumen["lectura_apta_para_calificar"] = False


def _alineacion_dudosa(reporte) -> bool:
    if not reporte or not reporte.get("valido"):
        return False
    error_mediano = reporte.get("metricas", {}).get("error_mediano_px", 0)
    return error_mediano > UMBRAL_ERROR_ALINEACION or reporte.get("revision_geometrica_recomendada", False)


def _comparar_agrupamientos(resultado: Diccionario, prefijo_salida: Path) -> None:
    """Etapa 9.2 — Diagnóstico experimental (opcional); NO cambia estados OMR."""
    from .diagnostico.comparar_agrupamientos import comparar_agrupamientos, guardar_comparacion_csv

    resultado["comparador_clusters"] = comparar_agrupamientos(resultado)
    guardar_comparacion_csv(str(prefijo_salida) + "_comparacion_clusters.csv", resultado["comparador_clusters"])


# PASO 1.2 — Coordinador principal: plantilla, alineación opcional, lectura y archivos.
def procesar(
    ruta: str | Path,
    carpeta: str | Path,
    salida: str | Path | None = None,
    alineacion: bool = False,
    refinar: bool = False,
    rescatar_tenues: bool = True,
    comparar_clusters: bool = False,
    alineacion_local: bool = False,
) -> Diccionario:
    """Ejecuta el flujo OMR y guarda archivos compatibles con el formato 0.5."""
    ruta = Path(ruta)
    carpeta = Path(carpeta)
    # 2.1 — Cargar plantilla validada y coordenadas.
    datos, referencia = leer_datos(carpeta)
    reporte = None
    ruta_procesada = ruta
    if alineacion:
        reporte, ruta_procesada = _alinear(ruta, carpeta, alineacion_local)
        if not reporte.get("valido", False):
            return {
                "exito": False,
                "error": "Alineacion rechazada: " + reporte.get("motivo", "sin diagnostico"),
                "reporte_alineacion": reporte,
            }

    gris = _leer_imagen(ruta_procesada, cv2.IMREAD_GRAYSCALE)
    if gris.shape != referencia.shape:
        raise ValueError(f"Tamaño de imagen {gris.shape[::-1]} no coincide con plantilla {referencia.shape[::-1]}")
    gris, informacion_ecc = _refinar(gris, referencia, datos, reporte, refinar)

    # PASO 3.9 — También controlar las hojas proporcionadas YA alineadas y
    # repetir el control tras un ECC opcional: una imagen de tamaño correcto
    # no implica que el centro de las burbujas sea correcto.
    if datos.get("marcadores_px"):
        verificacion = verificar_cuadricula(gris, referencia, datos)
        if not verificacion["valido"]:
            return {"exito": False, "error": "Desalineacion de burbujas: " + verificacion["motivo"],
                    "verificacion_geometrica": verificacion, "reporte_alineacion": reporte}
    else:
        verificacion = {"valido": False,
                        "motivo": "Sin marcadores en las coordenadas: lectura sin verificacion geometrica"}

    # 9.1 — Entrar al lector que orquesta las etapas 4, 5, 6, 7, 8 y 9.
    resultado = leer_v4(gris, datos, referencia, rescatar_tenues=rescatar_tenues)
    if _alineacion_dudosa(reporte) or not verificacion["valido"]:
        _marcar_revision_global(resultado["resumen"])
    resultado["verificacion_geometrica"] = verificacion
    resultado["imagen_fuente"] = ruta.name
    resultado["reporte_alineacion"] = reporte
    resultado["refinamiento_ecc"] = informacion_ecc
    prefijo_salida = Path(salida) if salida is not None else carpeta / f"{ruta.stem}_omr_v4"
    if comparar_clusters:
        _comparar_agrupamientos(resultado, prefijo_salida)
    # 10.1 — Guardar resultados y revisión visual.
    _guardar_resultados(prefijo_salida, gris, datos, resultado)
    return resultado
