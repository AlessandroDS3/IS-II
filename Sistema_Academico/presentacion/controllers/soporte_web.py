"""Utilidades compartidas por los módulos de rutas."""
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

from flask import abort, redirect, render_template, request, send_file, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from dominio.identidad_acceso.autorizacion import Autorizacion
from infraestructura.archivos.validador_imagenes import tipo_mime_por_firma

ROL_COORDINADOR = 'Coordinador'
ROL_DIRECTOR = 'Director'
ROL_DOCENTE = 'Docente'
ROL_ESTUDIANTE = 'Estudiante'
CABECERA_LOTE = 'X-Carga-Lote'
BYTES_FIRMA = 8

# Etapas del espacio de trabajo de un examen: endpoint -> etiqueta del menú.
ETAPAS_EXAMEN = {
    'espacio_examen': 'Resumen', 'banco_preguntas': 'Preguntas',
    'configurar_examen': 'Configuración', 'cartillas': 'Cartillas',
    'lecturas': 'Lecturas', 'resultados_coordinador': 'Resultados', 'reportes': 'Reportes',
}


@dataclass(frozen=True)
class Ruta:
    """Declaración de una ruta: URL, endpoint (mismo nombre que usan las plantillas), vista, métodos,
    rol exigido (None = pública) y servicios que deben estar disponibles."""
    url: str
    endpoint: str
    vista: Callable
    metodos: tuple = ('GET',)
    rol: str | None = None
    servicios: tuple = ()


def registrar_vistas(app, proteger, rutas):
    """Registra las rutas aplicando primero la sesión/rol y después la disponibilidad de servicios."""
    for ruta in rutas:
        vista = ruta.vista
        for servicio in ruta.servicios:
            vista = requiere(servicio)(vista)
        if ruta.rol:
            vista = proteger(ruta.rol)(vista)
        app.add_url_rule(ruta.url, ruta.endpoint, vista, methods=list(ruta.metodos))


def pagina(plantilla, rol, **contexto):
    """Renderiza una página de un panel con el rol y el nombre del usuario en sesión."""
    return render_template(plantilla, rol=rol, nombre=session['nombre'], **contexto)


def requiere(servicio):
    """Responde 503 si el servicio no está disponible (base de datos sin configurar)."""
    def decorador(funcion):
        @wraps(funcion)
        def vista(*args, **kwargs):
            if servicio is None:
                abort(503)
            return funcion(*args, **kwargs)
        return vista
    return decorador


def crear_proteger(app, acceso):
    """Decorador que exige sesión válida, cuenta activa y el rol indicado."""
    def proteger(rol):
        def decorador(funcion):
            @wraps(funcion)
            def vista(*args, **kwargs):
                if not session.get('usuario'):
                    return redirect(url_for('login'))
                if not acceso:
                    abort(503)
                try:
                    cuenta = acceso.consultar_cuenta_activa(session['usuario'])
                except SQLAlchemyError:
                    app.logger.exception('No se pudo verificar la sesión')
                    abort(503)
                if not cuenta or cuenta['id'] != session.get('usuario_id'):
                    session.clear()
                    return redirect(url_for('login'))
                session['roles'] = cuenta['roles']
                if not Autorizacion.puede_acceder(cuenta['roles'], rol):
                    abort(403)
                return funcion(*args, **kwargs)
            return vista
        return decorador
    return proteger


def seleccionar_examen():
    try:
        return max(0, int(request.values.get('examen', 0)))
    except ValueError:
        return 0


def numero_pagina(fuente):
    return max(1, fuente.get('pagina', default=1, type=int) or 1)


def es_carga_por_lotes():
    return request.method == 'POST' and request.headers.get(CABECERA_LOTE) == '1'


def enviar_imagen_privada(ruta, raiz, nombre_descarga=None):
    """Envía un archivo de la carpeta privada indicada; 404 si está fuera de ella o no existe.

    El tipo se determina por la firma del archivo; si no es PNG ni JPEG se ofrece como descarga.
    """
    if not ruta:
        abort(404)
    archivo = Path(ruta).resolve()
    if not archivo.is_relative_to(Path(raiz).resolve()) or not archivo.is_file():
        abort(404)
    with archivo.open('rb') as datos:
        tipo = tipo_mime_por_firma(datos.read(BYTES_FIRMA))
    if tipo is None:
        return send_file(archivo, mimetype='application/octet-stream', as_attachment=True, download_name=nombre_descarga or archivo.name)
    return send_file(archivo, mimetype=tipo, conditional=True)
