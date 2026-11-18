# Laboratorio 02: reporte de defectos de SonarQube

Proyecto: **Sistema-Academico-FINAL**. Exportado el 2026-11-18T11:39:56-05:00 (America/Lima).

[Abrir resultados en SonarQube](http://localhost:9000/dashboard?id=Sistema-Academico-FINAL). El enlace requiere el servidor local encendido.

## Evidencia y alcance

Resultados exportados de la API de SonarQube Community Build 26.9.0.129388, tras ejecutar SonarScanner CLI 8.1.0.6389.

Tarea: `885a03ae-3a9a-440f-bdbb-da0e70b90e5d`. Analisis: `c2898e88-e932-499b-b121-34ba5e71ea42`. Estado de procesamiento: **SUCCESS**.

Commit de referencia: `ab99472a15a3e944aba542017c72d4e0bda06a4b`. Se analizo la copia de trabajo, incluidos cambios locales sin commit; este informe no certifica que todos esos cambios esten en GitHub.

Fuentes: `Sistema_Academico`. Pruebas: `tests/**/*.py`. Se excluyeron datos privados, la clave local de MySQL y archivos generados de Python.

## Metricas generales

| Metrica | Valor |
| --- | --- |
| Archivos de produccion | 219 |
| Lineas de codigo sin comentarios | 6697 |
| Incidencias | 310 |
| Bugs (clasificacion tradicional) | 4 |
| Vulnerabilidades (clasificacion tradicional) | 0 |
| Code smells (clasificacion tradicional) | 306 |
| Security Hotspots (requieren revision) | 0 |
| Cobertura (%) | 0.0 |
| Duplicacion (%) | 0.0 |
| Deuda tecnica estimada (minutos) | 1715 |

Quality Gate informado por SonarQube: **ERROR**.

Las siguientes condiciones se aplican al codigo nuevo segun la referencia del servidor, no a todas las incidencias del proyecto.

| Condicion | Valor | Umbral de fallo | Estado |
| --- | --- | --- | --- |
| new_coverage | 0.0 | LT 80 | ERROR |
| new_duplicated_lines_density | 0.0 | GT 3 | OK |
| new_violations | 2 | GT 0 | ERROR |

Referencia de codigo nuevo: `PREVIOUS_VERSION`, desde `2026-11-18T11:18:02-0500`.

El servidor esta en modo MQR. Las categorias tradicionales de bugs, vulnerabilidades y code smells se muestran como referencia; los impactos por calidad estan conservados en el CSV y JSON.

No se importo un informe de cobertura en este analisis. SonarScanner no ejecuta las pruebas; una cobertura del 0% no significa que el repositorio carezca de ellas. La validacion ejecutada se documenta por separado en los reportes de pruebas.

Consulte ejecucion.txt para los avisos de atribucion Git (blame) de archivos modificados o sin seguimiento. Estos avisos pueden limitar la atribucion de autor y la clasificacion de codigo nuevo.

## Incidencias por severidad tradicional

| Severidad | Cantidad |
| --- | --- |
| BLOCKER | 0 |
| CRITICAL | 292 |
| MAJOR | 11 |
| MINOR | 7 |
| INFO | 0 |

## Reglas con mas incidencias

| Regla | Cantidad |
| --- | --- |
| python:S1186 | 273 |
| python:S3776 | 18 |
| Web:InputWithoutLabelCheck | 4 |
| Web:S6819 | 3 |
| python:S1481 | 3 |
| Web:S6851 | 2 |
| python:S7498 | 2 |
| python:S1192 | 1 |
| python:S1172 | 1 |
| python:S3358 | 1 |

## Primeras 20 incidencias por severidad

Los mensajes se conservan en el idioma devuelto por SonarQube. El listado completo esta en `defectos.csv` y `resultados.json`.

| Severidad | Regla | Archivo | Linea | Mensaje |
| --- | --- | --- | --- | --- |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_almacen_evidencias.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_almacen_evidencias.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_almacen_evidencias.py | 11 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_extractor_paginas.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_extractor_paginas.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_lector_cartillas.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_lector_cartillas.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_unidad_trabajo.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_unidad_trabajo.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_unidad_trabajo.py | 11 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_unidad_trabajo.py | 14 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/area_academica_app_service.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/area_academica_app_service.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/area_academica_app_service.py | 11 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/area_academica_app_service.py | 14 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/ciclo_app_service.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/ciclo_app_service.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/ciclo_app_service.py | 11 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/ciclo_app_service.py | 14 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/servicios/eje_tematico_app_service.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |

## Seguimiento

1. Revisar las incidencias de seguridad y confiabilidad de mayor impacto en Issues.
2. Revisar manualmente los Security Hotspots; no equivalen por si mismos a vulnerabilidades confirmadas.
3. Corregir incidencias acordadas por el equipo y repetir SonarScanner para comprobar el resultado.
4. Incorporar un informe de cobertura de las pruebas si se desea evaluar esa metrica.

## Limites de la exportacion

El token permite analizar y exportar incidencias, pero el servidor denego el detalle de Security Hotspots (HTTP 403). El resumen conserva su cantidad medida; deben revisarse en el panel con una cuenta autorizada.
