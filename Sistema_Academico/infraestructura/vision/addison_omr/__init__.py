"""API pública del lector ADDISON OMR (versión experimental).

El orden de las etapas del algoritmo está documentado en SECUENCIA.md.
"""
from .alinear_fotografia import alinear, extraer_coincidencias, medidas_homografia, mejora_ecc
from .auditar_marcas_con_plantilla import auditar_opciones_con_plantilla, medir_evidencia_plantilla, rescatar_marca_tenue
from .cargar_plantilla_referencia import RECURSOS_PLANTILLA, guardar_json, leer_datos
from .clasificar_respuestas_dni_area import kmeans_umbral, leer, resolver_controles, resolver_opciones
from .consensuar_lecturas import combinar_opciones, consenso_item
from .consolidar_resultados_omr import leer_v4
from .definir_parametros_omr import ESTADOS, SECCIONES_CONTROL, TOTAL_COLUMNAS_DNI, TOTAL_PREGUNTAS, VERSION
from .dibujar_imagen_revision import anotacion
from .ejecutar_flujo_lectura import procesar
from .medir_tinta_burbujas import medir_circulo
from .normalizar_luz_fotografia import evaluar_calidad, normalizar_luz, tratamientos
from .recibir_argumentos_cli import main

__all__ = [
    'VERSION', 'TOTAL_PREGUNTAS', 'TOTAL_COLUMNAS_DNI', 'SECCIONES_CONTROL', 'ESTADOS', 'RECURSOS_PLANTILLA',
    'leer_datos', 'guardar_json', 'alinear', 'mejora_ecc', 'medidas_homografia', 'extraer_coincidencias',
    'medir_circulo', 'kmeans_umbral', 'resolver_opciones', 'resolver_controles', 'leer', 'consenso_item',
    'combinar_opciones', 'medir_evidencia_plantilla', 'rescatar_marca_tenue', 'auditar_opciones_con_plantilla',
    'leer_v4', 'normalizar_luz', 'tratamientos', 'evaluar_calidad', 'procesar', 'anotacion', 'main',
]
