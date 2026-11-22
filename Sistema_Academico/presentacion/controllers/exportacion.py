"""Exportación de tablas a CSV y XLSX protegida contra inyección de fórmulas."""
import csv
import io

from flask import Response, send_file
from openpyxl import Workbook

PREFIJOS_FORMULA = ('=', '+', '-', '@')
BOM_UTF8 = '﻿'
MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def celda_segura(valor):
    """Evita que un texto se interprete como fórmula en una hoja de cálculo."""
    if isinstance(valor, str) and valor.lstrip().startswith(PREFIJOS_FORMULA):
        return "'" + valor
    return valor


def _filas_seguras(filas, claves):
    for fila in filas:
        yield [celda_segura(fila[clave]) for clave in claves]


def respuesta_csv(encabezados, filas, claves, nombre_archivo):
    salida = io.StringIO(newline='')
    escritor = csv.writer(salida)
    escritor.writerow(encabezados)
    escritor.writerows(_filas_seguras(filas, claves))
    return Response(BOM_UTF8 + salida.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{nombre_archivo}"'})


def respuesta_xlsx(titulo, encabezados, filas, claves, nombre_archivo):
    libro = Workbook()
    hoja = libro.active
    hoja.title = titulo
    hoja.append(encabezados)
    for fila in _filas_seguras(filas, claves):
        hoja.append(fila)
    contenido = io.BytesIO()
    libro.save(contenido)
    contenido.seek(0)
    return send_file(contenido, mimetype=MIME_XLSX, as_attachment=True, download_name=nombre_archivo)
