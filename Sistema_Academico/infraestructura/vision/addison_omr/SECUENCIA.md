# Secuencia del lector ADDISON OMR

Orden en que se ejecutan las etapas del algoritmo. Los antiguos prefijos numéricos de archivo
(`00_`, `01_1_`...) se sustituyeron por nombres importables; este documento conserva el orden.

| Paso | Módulo | Responsabilidad |
|---|---|---|
| 0 | `definir_parametros_omr.py` | Constantes, umbrales experimentales y tipos compartidos |
| 1.1 | `recibir_argumentos_cli.py` | Entrada por línea de comandos (`python -m addison_omr`) |
| 1.2 | `ejecutar_flujo_lectura.py` | Coordinador: plantilla, alineación opcional, lectura y archivos |
| 2.1 | `cargar_plantilla_referencia.py` | Plantilla maestra y mapa de coordenadas |
| 2.2 | `02_2_mapa_coordenadas_burbujas.json` | Coordenadas de cada burbuja (recurso) |
| 2.3 | `02_3_plantilla_maestra_sin_marcas.png` | Plantilla sin marcas (recurso) |
| 2.4 | `localizar_burbujas.py` | Recorrido de burbujas y centros |
| 3.1 | `alinear_fotografia.py` | Alineación por características (ORB/SIFT) y ECC |
| 3.2 | `detectar_marcadores_esquinas.py` | Refinamiento con los marcadores de las esquinas |
| 3.3 | `validar_cuadricula_respuestas.py` | Verificación geométrica de la cuadrícula |
| 3.4 | `corregir_alineacion_local.py` | Corrección local experimental (exige revisión manual) |
| 4 | `normalizar_luz_fotografia.py` | Normalización de iluminación y calidad de imagen |
| 5 | `medir_tinta_burbujas.py` | Medición de tinta por burbuja |
| 6 | `clasificar_respuestas_dni_area.py` | Clasificación de respuestas, DNI y controles |
| 7 | `consensuar_lecturas.py` | Consenso entre tratamientos |
| 8 | `auditar_marcas_con_plantilla.py` | Auditoría de marcas contra la plantilla |
| 9.1 | `consolidar_resultados_omr.py` | Consolidación del resultado final |
| 10.1 | `exportar_json_csv.py` | Exportación a JSON y CSV |
| 10.2 | `dibujar_imagen_revision.py` | Imagen anotada para revisión |
| — | `diagnostico/comparar_agrupamientos.py` | Experimental: K-Means, Fuzzy C-Means y DBSCAN |
| — | `diagnostico/comparar_varias_fotos.py` | Experimental: varias fotos de una misma cartilla |

Los umbrales proceden del prototipo original y no están calibrados con una muestra etiquetada:
cualquier cambio requiere ejecutar la prueba de regresión del lector sobre cartillas de respuesta conocida.
