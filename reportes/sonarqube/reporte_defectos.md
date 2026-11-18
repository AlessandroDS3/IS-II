# Laboratorio 02: reporte de defectos de SonarQube

Proyecto: **Sistema-Academico-FINAL**. Exportado el 2026-11-18T11:21:32-05:00 (America/Lima).

[Abrir resultados en SonarQube](http://localhost:9000/dashboard?id=Sistema-Academico-FINAL). El enlace requiere el servidor local encendido.

## Evidencia y alcance

Resultados exportados de la API de SonarQube Community Build 26.9.0.129388, tras ejecutar SonarScanner CLI 8.1.0.6389.

Tarea: `1cdea50f-ca9e-410c-98e4-543597b2e0eb`. Analisis: `d5b5336e-ef13-4fee-96d1-56d168ce637f`. Estado de procesamiento: **SUCCESS**.

Commit de referencia: `ab99472a15a3e944aba542017c72d4e0bda06a4b`. Se analizo la copia de trabajo, incluidos cambios locales sin commit; este informe no certifica que todos esos cambios esten en GitHub.

Fuentes: `Sistema_Academico`. Pruebas: `tests/**/*.py`. Se excluyeron datos privados, la clave local de MySQL y archivos generados de Python.

## Metricas generales

| Metrica | Valor |
| --- | --- |
| Archivos de produccion | 219 |
| Lineas de codigo sin comentarios | 6690 |
| Incidencias | 333 |
| Bugs (clasificacion tradicional) | 4 |
| Vulnerabilidades (clasificacion tradicional) | 0 |
| Code smells (clasificacion tradicional) | 329 |
| Security Hotspots (requieren revision) | 0 |
| Cobertura (%) | 0.0 |
| Duplicacion (%) | 0.0 |
| Deuda tecnica estimada (minutos) | 1830 |

Quality Gate informado por SonarQube: **ERROR**.

Las siguientes condiciones se aplican al codigo nuevo segun la referencia del servidor, no a todas las incidencias del proyecto.

| Condicion | Valor | Umbral de fallo | Estado |
| --- | --- | --- | --- |
| new_coverage | 0.0 | LT 80 | ERROR |
| new_duplicated_lines_density | 0.0 | GT 3 | OK |
| new_violations | 2 | GT 0 | ERROR |

Referencia de codigo nuevo: `PREVIOUS_VERSION`, desde `2026-11-18T11:18:02-0500`.

El servidor esta en modo MQR. Las categorias tradicionales de bugs, vulnerabilidades y code smells se muestran como referencia; los impactos por calidad estan conservados en el CSV y JSON.

No se ejecuto la suite de pruebas ni se importo un informe de cobertura en esta actividad. Una cobertura del 0% no significa que el repositorio carezca de pruebas.

El scanner aviso que no pudo obtener atribucion Git (blame) para cuatro archivos modificados o sin seguimiento: app.py, rutas_web.py, servicios_web.py y test_rutas_web.py. Esto puede limitar la atribucion de autor y la clasificacion de codigo nuevo.

## Incidencias por severidad tradicional

| Severidad | Cantidad |
| --- | --- |
| BLOCKER | 0 |
| CRITICAL | 314 |
| MAJOR | 12 |
| MINOR | 7 |
| INFO | 0 |

## Reglas con mas incidencias

| Regla | Cantidad |
| --- | --- |
| python:S1186 | 295 |
| python:S3776 | 18 |
| Web:S6819 | 4 |
| Web:InputWithoutLabelCheck | 4 |
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
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_protector_credenciales.py | 5 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_protector_credenciales.py | 8 | Add a nested comment explaining why this method is empty, or complete the implementation. |
| CRITICAL | python:S1186 | Sistema_Academico/aplicacion/puertos/i_protector_credenciales.py | 11 | Add a nested comment explaining why this method is empty, or complete the implementation. |
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

## Seguimiento

1. Revisar las incidencias de seguridad y confiabilidad de mayor impacto en Issues.
2. Revisar manualmente los Security Hotspots; no equivalen por si mismos a vulnerabilidades confirmadas.
3. Corregir incidencias acordadas por el equipo y repetir SonarScanner para comprobar el resultado.
4. Incorporar un informe de cobertura de las pruebas si se desea evaluar esa metrica.

## Limites de la exportacion

El token permite analizar y exportar incidencias, pero el servidor denego el detalle de Security Hotspots (HTTP 403). El resumen conserva su cantidad medida; deben revisarse en el panel con una cuenta autorizada.
