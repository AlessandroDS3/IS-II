"""Rutas HTTP: adaptan formularios y respuestas a los servicios de aplicación."""
import csv
import io
import json
from pathlib import Path
from functools import wraps

from flask import Response, abort, flash, redirect, render_template, request, send_file, session, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dominio.identidad_acceso.autorizacion import Autorizacion
from presentacion.controllers.servicios_web import ServiciosWeb


LOGIN_TEMPLATE = 'comun/login.html'
MIMETYPE_PNG = 'image/png'

ETAPAS_EXAMEN = {
    'espacio_examen': 'Resumen', 'banco_preguntas': 'Preguntas',
    'configurar_examen': 'Configuración', 'cartillas': 'Cartillas',
    'lecturas': 'Lecturas', 'resultados_coordinador': 'Resultados', 'reportes': 'Reportes',
}

# Conserva los nombres de endpoint usados en las plantillas y redirecciones.
RUTAS_WEB = (
    ('login', '/', ('GET', 'POST'), None),
    ('elegir_rol', '/elegir-rol', ('GET',), None),
    ('coordinador', '/coordinador', ('GET',), 'COORDINADOR'),
    ('director', '/director', ('GET',), 'DIRECTOR'),
    ('director_reporte', '/director/reporte.csv', ('GET',), 'DIRECTOR'),
    ('estudiantes', '/coordinador/estudiantes', ('GET', 'POST'), 'COORDINADOR'),
    ('editar_estudiante', '/coordinador/estudiantes/<int:id>/editar', ('GET', 'POST'), 'COORDINADOR'),
    ('estado_estudiante', '/coordinador/estudiantes/<int:id>/estado', ('POST',), 'COORDINADOR'),
    ('vincular_estudiante', '/coordinador/estudiantes/<int:id>/cuenta', ('POST',), 'COORDINADOR'),
    ('asignaciones_estudiante', '/coordinador/estudiantes/<int:id>/asignaciones', ('GET', 'POST'), 'COORDINADOR'),
    ('usuarios', '/coordinador/usuarios', ('GET', 'POST'), 'COORDINADOR'),
    ('estado_usuario', '/coordinador/usuarios/<int:id>/estado', ('POST',), 'COORDINADOR'),
    ('cambiar_roles_usuario', '/coordinador/usuarios/<int:id>/roles', ('POST',), 'COORDINADOR'),
    ('organizacion', '/coordinador/organizacion', ('GET', 'POST'), 'COORDINADOR'),
    ('simulacros', '/coordinador/simulacros', ('GET', 'POST'), 'COORDINADOR'),
    ('banco_preguntas', '/coordinador/preguntas', ('GET',), 'COORDINADOR'),
    ('espacio_examen', '/coordinador/examenes/<int:simulacro_id>', ('GET',), 'COORDINADOR'),
    ('revisar_pregunta', '/coordinador/preguntas/<int:id>/revision', ('POST',), 'COORDINADOR'),
    ('cartillas', '/coordinador/cartillas', ('GET', 'POST'), 'COORDINADOR'),
    ('identificar_cartilla', '/coordinador/cartillas/<int:id>/identificar', ('POST',), 'COORDINADOR'),
    ('detalle_carga', '/coordinador/cargas/<int:id>', ('GET',), 'COORDINADOR'),
    ('imagen_entrada', '/coordinador/cargas/<int:id>/imagen', ('GET',), 'COORDINADOR'),
    ('resolver_carga', '/coordinador/cargas/<int:id>/resolver', ('POST',), 'COORDINADOR'),
    ('registrar_cartilla', '/coordinador/cartillas/<int:id>/registrar', ('POST',), 'COORDINADOR'),
    ('descartar_cartilla', '/coordinador/cartillas/<int:id>/descartar', ('POST',), 'COORDINADOR'),
    ('lecturas', '/coordinador/lecturas', ('GET',), 'COORDINADOR'),
    ('imagen_cartilla', '/coordinador/cartillas/<int:id>/imagen', ('GET',), 'COORDINADOR'),
    ('corregir_lectura', '/coordinador/lecturas/<int:id>/corregir', ('POST',), 'COORDINADOR'),
    ('validar_cartilla', '/coordinador/cartillas/<int:id>/validar', ('POST',), 'COORDINADOR'),
    ('resultados_coordinador', '/coordinador/resultados', ('GET',), 'COORDINADOR'),
    ('detalle_resultado_coordinador', '/coordinador/resultados/<int:id>/detalle', ('GET',), 'COORDINADOR'),
    ('revisar_resultado', '/coordinador/resultados/<int:id>/revisar', ('POST',), 'COORDINADOR'),
    ('calcular_resultados', '/coordinador/resultados/calcular', ('POST',), 'COORDINADOR'),
    ('publicar_resultados', '/coordinador/resultados/publicar', ('POST',), 'COORDINADOR'),
    ('reportes', '/coordinador/reportes', ('GET',), 'COORDINADOR'),
    ('descargar_reporte', '/coordinador/reportes/descargar', ('GET',), 'COORDINADOR'),
    ('descargar_reporte_excel', '/coordinador/reportes/excel', ('GET',), 'COORDINADOR'),
    ('estudiante', '/estudiante', ('GET',), 'ESTUDIANTE'),
    ('mi_detalle', '/estudiante/resultados/<int:id>', ('GET',), 'ESTUDIANTE'),
    ('docente', '/docente', ('GET',), 'DOCENTE'),
    ('docente_tema', '/docente/temas', ('POST',), 'DOCENTE'),
    ('docente_detalle', '/docente/preguntas/<int:id>', ('GET',), 'DOCENTE'),
    ('docente_crear', '/docente/preguntas/nueva', ('GET', 'POST'), 'DOCENTE'),
    ('docente_editar', '/docente/preguntas/<int:id>/editar', ('GET', 'POST'), 'DOCENTE'),
    ('docente_imagen', '/docente/imagenes/<int:id>', ('GET',), 'DOCENTE'),
    ('coordinador_imagen_pregunta', '/coordinador/preguntas/imagenes/<int:id>', ('GET',), 'COORDINADOR'),
    ('docente_estadisticas', '/docente/estadisticas', ('GET',), 'DOCENTE'),
    ('configurar_examen', '/coordinador/configurar-examen', ('GET', 'POST'), 'COORDINADOR'),
    ('guardar_clave', '/coordinador/versiones/<int:id>/clave', ('POST',), 'COORDINADOR'),
    ('salir', '/salir', ('POST',), None),
)


def registrar_rutas(app, servicios: ServiciosWeb):
    """Registra las vistas con sus métodos HTTP y permisos originales."""
    controlador = ControladorWeb(app, servicios)
    app.context_processor(controlador.contexto_navegacion)
    for nombre, regla, metodos, rol in RUTAS_WEB:
        vista = getattr(controlador, nombre)
        if rol:
            vista = controlador.proteger(rol)(vista)
        app.add_url_rule(regla, endpoint=nombre, view_func=vista, methods=metodos)


class ControladorWeb:
    """Adapta las peticiones HTTP usando las dependencias de cada aplicación."""

    def __init__(self, app, servicios: ServiciosWeb):
        self.app = app
        self.servicios = servicios

    def contexto_navegacion(self):
        etapa = {'detalle_resultado_coordinador': 'resultados_coordinador', 'detalle_carga': 'cartillas'}.get(request.endpoint, request.endpoint)
        if (etapa not in ETAPAS_EXAMEN or request.endpoint == 'espacio_examen'
                or not self.servicios.simulacros_servicio or not session.get('usuario')
                or not Autorizacion.puede_acceder(session.get('roles', []), 'COORDINADOR')):
            return {}
        examen = request.values.get('examen', type=int)
        if request.endpoint == 'detalle_carga' and self.servicios.cartillas_servicio:
            entrada = self.servicios.cartillas_servicio.obtener(request.view_args['id'])
            examen = entrada['examen_id'] if entrada else 0
        if not examen:
            return {}
        contexto = self.servicios.simulacros_servicio.contexto_examen(examen)
        if not contexto:
            abort(404)
        return {'contexto_examen': contexto, 'etapas_examen': ETAPAS_EXAMEN, 'etapa_examen': etapa}

    def proteger(self, rol):
        def decorador(funcion):
            @wraps(funcion)
            def vista(*args, **kwargs):
                if not session.get('usuario'):
                    return redirect(url_for('login'))
                if not self.servicios.servicio:
                    abort(503)
                try:
                    cuenta = self.servicios.servicio.consultar_cuenta_activa(session['usuario'])
                except SQLAlchemyError:
                    self.app.logger.exception('No se pudo verificar la sesión')
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

    def login(self):
        if request.method == 'POST':
            if self.servicios.servicio is None:
                flash('Configure la conexión a la base de datos para iniciar sesión.', 'error')
                return render_template(LOGIN_TEMPLATE), 503
            try:
                cuenta = self.servicios.servicio.iniciar_sesion(request.form.get('usuario', ''), request.form.get('contrasena', ''))
            except SQLAlchemyError:
                self.app.logger.exception('Error de conexión al consultar la cuenta')
                flash('No se pudo consultar la base de datos. Revise la conexión.', 'error')
                return render_template(LOGIN_TEMPLATE), 503
            if not cuenta:
                flash('Usuario o contraseña incorrectos, o cuenta inactiva.', 'error')
                return render_template(LOGIN_TEMPLATE), 401
            roles = [r for r in cuenta['roles'] if r in ('COORDINADOR', 'DIRECTOR', 'ESTUDIANTE', 'DOCENTE')]
            if not roles:
                flash('Esta cuenta no tiene acceso a los paneles disponibles.', 'error')
                return render_template(LOGIN_TEMPLATE), 403
            session.clear()
            session.update(usuario=cuenta['usuario'], usuario_id=cuenta['id'], nombre=cuenta['nombre'], roles=roles)
            return redirect(url_for('elegir_rol') if len(roles) > 1 else url_for(roles[0].lower()))
        return render_template(LOGIN_TEMPLATE)

    def elegir_rol(self):
        if not session.get('usuario'):
            return redirect(url_for('login'))
        return render_template('comun/elegir_rol.html', roles=session['roles'])

    def coordinador(self):
        pendientes = None
        if self.servicios.panel_servicio:
            try:
                pendientes = self.servicios.panel_servicio.consultar_pendientes()
            except SQLAlchemyError:
                self.app.logger.exception('No se pudieron consultar los pendientes')
        return render_template('coordinador/inicio.html', rol='Coordinador', nombre=session['nombre'], pendientes=pendientes)

    def director(self):
        ciclo = request.args.get('ciclo', default=0, type=int)
        ciclos, filas, resumen = self.servicios.resultados_servicio.datos_director(ciclo)
        return render_template('director/director.html', rol='Director', nombre=session['nombre'], ciclo=ciclo, ciclos=ciclos, filas=filas, resumen=resumen)

    def director_reporte(self):
        ciclo = request.args.get('ciclo', default=0, type=int)
        _, filas, _ = self.servicios.resultados_servicio.datos_director(ciclo)
        salida = io.StringIO(newline='')
        escritor = csv.writer(salida)
        escritor.writerow(['Examen','Fecha','Área','Participantes','Promedio %','Máximo %','Mínimo %'])
        for fila in filas:
            valores = [fila[k] for k in ('examen','fecha_programada','area','participantes','promedio','maximo','minimo')]
            escritor.writerow(["'" + x if isinstance(x, str) and x.lstrip().startswith(('=', '+', '-', '@')) else x for x in valores])
        return Response('\ufeff' + salida.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename="reporte_director.csv"'})

    def estudiantes(self):
        if not self.servicios.estudiantes_servicio:
            abort(503)
        if request.method == 'POST':
            try:
                self.servicios.estudiantes_servicio.registrar_estudiante(request.form.to_dict())
                flash('Estudiante registrado correctamente.', 'ok')
                return redirect(url_for('estudiantes'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('El código del estudiante ya está registrado.', 'error')
        try:
            lista = self.servicios.estudiantes_servicio.listar(request.args.get('q', ''))
        except SQLAlchemyError:
            self.app.logger.exception('Error al consultar estudiantes')
            abort(503)
        return render_template('coordinador/estudiantes.html', rol='Coordinador', nombre=session['nombre'], estudiantes=lista, busqueda=request.args.get('q', ''))

    def editar_estudiante(self, id):
        if not self.servicios.estudiantes_servicio:
            abort(503)
        registro = self.servicios.estudiantes_servicio.buscar_por_id(id)
        if not registro:
            abort(404)
        if request.method == 'POST':
            try:
                self.servicios.estudiantes_servicio.actualizar(id, request.form.to_dict())
                flash('Estudiante actualizado correctamente.', 'ok')
                return redirect(url_for('estudiantes'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('El código del estudiante ya está registrado.', 'error')
        return render_template('coordinador/editar_estudiante.html', rol='Coordinador', nombre=session['nombre'], estudiante=registro)

    def estado_estudiante(self, id):
        if not self.servicios.estudiantes_servicio:
            abort(503)
        try:
            if not self.servicios.estudiantes_servicio.cambiar_estado(id, request.form.get('estado', '')):
                abort(404)
            flash('Estado actualizado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('estudiantes'))

    def vincular_estudiante(self, id):
        if not self.servicios.estudiantes_servicio:
            abort(503)
        try:
            self.servicios.estudiantes_servicio.vincular_cuenta(id, request.form.get('usuario', ''))
            flash('Cuenta vinculada correctamente.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except IntegrityError:
            flash('Esa cuenta ya está vinculada a otro estudiante.', 'error')
        return redirect(url_for('editar_estudiante', id=id))

    def asignaciones_estudiante(self, id):
        if not self.servicios.estudiantes_servicio:
            abort(503)
        estudiante = self.servicios.estudiantes_servicio.buscar_por_id(id)
        if not estudiante:
            abort(404)
        if request.method == 'POST':
            try:
                self.servicios.estudiantes_servicio.cambiar_asignacion(id, request.form.get('grupo'), request.form.get('area'), request.form.get('fecha'))
                flash('Asignación actualizada conservando el historial.', 'ok')
                return redirect(url_for('asignaciones_estudiante', id=id))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('No se pudo guardar la asignación: revisa los periodos y datos seleccionados.', 'error')
        areas, grupos, opciones_areas, opciones_grupos = self.servicios.estudiantes_servicio.consultar_asignaciones(id)
        return render_template('coordinador/asignaciones.html', rol='Coordinador', nombre=session['nombre'], estudiante=estudiante, areas=areas, grupos=grupos, opciones_areas=opciones_areas, opciones_grupos=opciones_grupos)

    def usuarios(self):
        if not self.servicios.usuarios_servicio:
            abort(503)
        es_director = 'DIRECTOR' in session['roles']
        if request.method == 'POST':
            try:
                datos = request.form.to_dict()
                datos['roles'] = request.form.getlist('roles')
                self.servicios.usuarios_servicio.crear(datos, es_director)
                flash('Cuenta creada correctamente.', 'ok')
                return redirect(url_for('usuarios'))
            except (ValueError, PermissionError) as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('El nombre de usuario ya está registrado.', 'error')
        try:
            lista = self.servicios.usuarios_servicio.listar()
        except SQLAlchemyError:
            self.app.logger.exception('Error al consultar usuarios')
            abort(503)
        return render_template('coordinador/usuarios.html', rol='Coordinador', nombre=session['nombre'], usuarios=lista, es_director=es_director)

    def estado_usuario(self, id):
        if not self.servicios.usuarios_servicio:
            abort(503)
        try:
            self.servicios.usuarios_servicio.cambiar_estado(id, request.form.get('estado', ''), 'DIRECTOR' in session['roles'])
            flash('Estado actualizado.', 'ok')
        except (ValueError, PermissionError) as error:
            flash(str(error), 'error')
        return redirect(url_for('usuarios'))

    def cambiar_roles_usuario(self, id):
        try:
            self.servicios.usuarios_servicio.cambiar_roles(id, request.form.getlist('roles'), 'DIRECTOR' in session['roles'], session['usuario_id'])
            flash('Roles actualizados.', 'ok')
        except (ValueError, PermissionError) as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('Error al modificar roles')
            flash('No se pudieron actualizar los roles.', 'error')
        return redirect(url_for('usuarios'))

    def organizacion(self):
        if not self.servicios.organizacion_servicio:
            abort(503)
        if request.method == 'POST':
            try:
                self.servicios.organizacion_servicio.ejecutar(request.form.get('accion'), request.form.get('tipo', ''), request.form.to_dict())
                flash('Operación realizada correctamente.', 'ok')
                return redirect(url_for('organizacion'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('No se pudo guardar: comprueba el código o el elemento seleccionado.', 'error')
        return render_template('coordinador/organizacion.html', rol='Coordinador', nombre=session['nombre'], catalogos=self.servicios.organizacion_servicio.listar())

    def simulacros(self):
        if not self.servicios.simulacros_servicio:
            abort(503)
        if request.method == 'POST':
            try:
                if request.form.get('accion') == 'simulacro':
                    datos = request.form.to_dict()
                    datos['areas'] = request.form.getlist('areas')
                    self.servicios.simulacros_servicio.crear_simulacro(datos, session['usuario_id'])
                elif request.form.get('accion') == 'agregar_areas':
                    self.servicios.simulacros_servicio.agregar_areas(request.form.get('simulacro'), request.form.getlist('areas'), session['usuario_id'])
                elif request.form.get('accion') == 'examen':
                    self.servicios.simulacros_servicio.crear_examen(request.form.to_dict(), session['usuario_id'])
                elif request.form.get('accion') in ('habilitar', 'cerrar'):
                    self.servicios.simulacros_servicio.habilitar_preguntas(request.form.get('examen'), request.form.get('accion'))
                else:
                    raise ValueError('Acción no válida.')
                flash('Registro guardado.', 'ok')
                return redirect(url_for('simulacros'))
            except ValueError as error:
                flash(str(error), 'error')
            except IntegrityError:
                flash('No se pudo guardar: verifica la fecha y que no exista otro examen para esa área.', 'error')
        sims, examenes, ciclos, areas = self.servicios.simulacros_servicio.listar()
        return render_template('coordinador/simulacros.html', rol='Coordinador', nombre=session['nombre'], simulacros=sims, examenes=examenes, ciclos=ciclos, areas=areas)

    def banco_preguntas(self):
        if not self.servicios.preguntas_servicio:
            abort(503)
        try:
            filas, materias, areas, ejes = self.servicios.preguntas_servicio.consultar_banco(request.args.to_dict())
        except ValueError as error:
            flash(str(error), 'error')
            return redirect(url_for('banco_preguntas'))
        return render_template('coordinador/banco_preguntas.html', rol='Coordinador', nombre=session['nombre'], preguntas=filas, materias=materias, areas=areas, ejes=ejes, filtros=request.args)

    def espacio_examen(self, simulacro_id):
        if not self.servicios.simulacros_servicio:
            abort(503)
        contexto = self.servicios.simulacros_servicio.abrir_aplicacion(simulacro_id, request.args.get('examen', default=0, type=int) or 0)
        if not contexto:
            abort(404)
        resumen = self.servicios.simulacros_servicio.resumen_examen(contexto['id_examen'])
        if resumen['preguntas_revision']:
            siguiente = ('banco_preguntas', 'Revisar preguntas pendientes')
        elif contexto['estado'] in ('BORRADOR', 'CONFIGURACION'):
            siguiente = ('configurar_examen', 'Preparar configuración y clave')
        elif resumen['cargas_pendientes']:
            siguiente = ('cartillas', 'Resolver cargas pendientes')
        elif resumen['cartillas_revision']:
            siguiente = ('lecturas', 'Revisar lecturas')
        elif resumen['cartillas'] > resumen['resultados'] or resumen['calculos_revision'] or resumen['por_publicar']:
            siguiente = ('resultados_coordinador', 'Revisar resultados y publicación')
        elif resumen['publicado']:
            siguiente = ('reportes', 'Consultar resultados publicados')
        else:
            siguiente = ('cartillas', 'Cargar cartillas')
        return render_template('coordinador/espacio_examen.html', rol='Coordinador', nombre=session['nombre'],
                               contexto_examen=contexto, etapas_examen=ETAPAS_EXAMEN, resumen=resumen, siguiente=siguiente)

    def revisar_pregunta(self, id):
        if not self.servicios.preguntas_servicio:
            abort(503)
        try:
            self.servicios.preguntas_servicio.revisar_pregunta(id, int(request.form.get('version', '0')), request.form.get('accion'), request.form.get('observacion'), session['usuario_id'])
            flash('Revisión guardada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudo revisar la pregunta')
            flash('No se pudo completar la revisión. Verifica que tenga área y versión válida.', 'error')
        filtros = {clave: request.form.get(clave, '') for clave in ('estado', 'examen', 'materia', 'area', 'eje')}
        return redirect(url_for('banco_preguntas', **filtros))

    def cartillas(self):
        if not self.servicios.cartillas_servicio:
            abort(503)
        try:
            examen_id = int(request.values.get('examen', '0'))
            if request.method == 'POST':
                return self.importar_cartillas(examen_id)
            datos = self.datos_cartillas(examen_id)
        except ValueError as error:
            if request.method == 'POST' and request.headers.get('X-Carga-Lote') == '1':
                return {'error': str(error)}, 400
            flash(str(error), 'error')
            return redirect(url_for('cartillas'))
        except SQLAlchemyError:
            self.app.logger.exception('Error al gestionar cartillas')
            if request.method == 'POST' and request.headers.get('X-Carga-Lote') == '1':
                return {'error': 'No se pudo acceder a la base de datos.'}, 503
            flash('No se pudo acceder a las cargas. Comprueba la conexión y la actualización de la base.', 'error')
            return render_template('coordinador/cartillas.html', rol='Coordinador', nombre=session['nombre'], examenes=[], entradas=[], examen_id=0), 503
        return render_template('coordinador/cartillas.html', rol='Coordinador', nombre=session['nombre'], **datos)

    def importar_cartillas(self, examen_id):
        if examen_id <= 0:
            raise ValueError('Selecciona un examen.')
        servicio = self.servicios.cartillas_servicio
        archivos = request.files.getlist('archivos')
        datos = [
            (Path(archivo.filename.replace('\\', '/')).name, archivo.read(servicio.preparador.MAX_BYTES + 1))
            for archivo in archivos if archivo.filename
        ]
        creadas = servicio.importar_lote(examen_id, datos, session['usuario_id'])
        if request.headers.get('X-Carga-Lote') == '1':
            return {'creadas': creadas}
        flash(f'Se registraron {creadas} páginas nuevas. Las duplicadas se omitieron.', 'ok')
        return redirect(url_for('cartillas', examen=examen_id))

    def datos_cartillas(self, examen_id):
        servicio = self.servicios.cartillas_servicio
        examenes = servicio.examenes()
        pagina = max(1, request.args.get('pagina', default=1, type=int) or 1)
        estado = request.args.get('estado', '')
        filas = servicio.listar(examen_id, pagina, estado) if examen_id else []
        resumen = servicio.resumen(examen_id) if examen_id else {}
        hay_siguiente = len(filas) > 200
        entradas = [dict(entrada) for entrada in filas[:200]]
        estudiantes, versiones = servicio.opciones_identificacion(examen_id) if examen_id else ([], [])
        area_actual = next((e['area'] for e in examenes if e['id_examen'] == examen_id), '')
        for entrada in entradas:
            lectura = entrada['lectura_json']
            entrada['lectura'] = json.loads(lectura) if isinstance(lectura, str) else lectura
            entrada['identificacion'] = servicio.identificar_para_vista(entrada, estudiantes, versiones, area_actual)
        return dict(examenes=examenes, entradas=entradas, examen_id=examen_id,
                    estudiantes=estudiantes, versiones=versiones, pagina=pagina,
                    hay_siguiente=hay_siguiente, estado=estado, resumen=resumen, area_actual=area_actual)

    def identificar_cartilla(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        try:
            self.servicios.cartillas_servicio.resolver_identificacion(id, request.form.get('estudiante'), request.form.get('version'))
            flash('Identificación guardada. La cartilla todavía está pendiente de registro.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return self.volver_cartillas()

    def volver_cartillas(self):
        return redirect(url_for('cartillas', examen=request.form.get('examen', ''),
                                pagina=max(1, request.form.get('pagina', default=1, type=int) or 1),
                                estado=request.form.get('estado', '')))

    def detalle_carga(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        entrada = self.servicios.cartillas_servicio.obtener(id)
        if not entrada:
            abort(404)
        return render_template('coordinador/detalle_carga.html', rol='Coordinador', nombre=session['nombre'],
                               entrada=entrada, historial=self.servicios.cartillas_servicio.historial(id))

    def imagen_entrada(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        entrada = self.servicios.cartillas_servicio.obtener(id)
        if not entrada:
            abort(404)
        historial_id = request.args.get('historial', type=int)
        if historial_id:
            entrada = self.servicios.cartillas_servicio.archivo_anterior(id, historial_id)
            if not entrada:
                abort(404)
        ruta = Path(entrada['ruta_imagen']).resolve()
        raiz = (Path(self.app.root_path) / 'datos_privados' / 'cartillas').resolve()
        if not ruta.is_relative_to(raiz) or not ruta.is_file():
            abort(404)
        with ruta.open('rb') as archivo:
            firma = archivo.read(8)
        if firma.startswith(b'\x89PNG'):
            tipo = MIMETYPE_PNG
        elif firma.startswith(b'\xff\xd8'):
            tipo = 'image/jpeg'
        else:
            return send_file(ruta, mimetype='application/octet-stream', as_attachment=True, download_name=entrada['nombre_archivo'])
        return send_file(ruta, mimetype=tipo, conditional=True)

    def resolver_carga(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        entrada = self.servicios.cartillas_servicio.obtener(id)
        if not entrada:
            abort(404)
        try:
            accion = request.form.get('accion')
            if accion == 'reintentar':
                self.servicios.cartillas_servicio.reintentar_lectura(id, session['usuario_id'], request.form.get('motivo'))
            elif accion == 'reemplazar':
                archivo = request.files.get('imagen')
                if not archivo or not archivo.filename:
                    raise ValueError('Selecciona la imagen de reemplazo.')
                self.servicios.cartillas_servicio.reemplazar_imagen(id, session['usuario_id'], request.form.get('motivo'), archivo.filename,
                                                    archivo.read(self.servicios.cartillas_servicio.preparador.MAX_BYTES + 1))
            else:
                raise ValueError('Acción no válida.')
            flash('Intento registrado. Revisa el nuevo estado y confirma de nuevo la identificación.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudo resolver la carga %s', id)
            flash('No se pudo guardar la operación. Comprueba la conexión.', 'error')
        return redirect(url_for('detalle_carga', id=id, examen=entrada['examen_id'],
                                pagina=max(1, request.form.get('pagina', default=1, type=int) or 1), estado=request.form.get('estado', '')))

    def registrar_cartilla(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        try:
            cartilla_id = self.servicios.cartillas_servicio.registrar_cartilla(id, session['usuario_id'], request.form.get('motivo'))
            flash(f'Cartilla {cartilla_id} registrada; las lecturas requieren revisión.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('Error registrando cartilla %s', id)
            flash('No se pudo registrar la cartilla; verifica el examen y su versión.', 'error')
        return self.volver_cartillas()

    def descartar_cartilla(self, id):
        if not self.servicios.cartillas_servicio:
            abort(503)
        try:
            self.servicios.cartillas_servicio.descartar_entrada(id, request.form.get('motivo'))
            flash('Entrada descartada y conservada para consulta.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return self.volver_cartillas()

    def seleccionar_examen(self):
        try:
            return max(0, int(request.values.get('examen', 0)))
        except ValueError:
            return 0

    def lecturas(self):
        if not self.servicios.resultados_servicio:
            abort(503)
        examen = self.seleccionar_examen()
        return render_template('coordinador/lecturas.html', rol='Coordinador', nombre=session['nombre'], examenes=self.servicios.resultados_servicio.examenes(), examen=examen, lecturas=self.servicios.resultados_servicio.lecturas(examen) if examen else [], historial=self.servicios.resultados_servicio.historial_lecturas(examen) if examen else [])

    def imagen_cartilla(self, id):
        ruta = self.servicios.resultados_servicio.imagen_cartilla(id)
        if not ruta:
            abort(404)
        raiz = (Path(self.app.root_path) / 'datos_privados' / 'cartillas').resolve()
        imagen = Path(ruta).resolve()
        if not imagen.is_relative_to(raiz) or not imagen.is_file():
            abort(404)
        with imagen.open('rb') as archivo:
            es_png = archivo.read(8) == b'\x89PNG\r\n\x1a\n'
        return send_file(imagen, mimetype=MIMETYPE_PNG if es_png else 'image/jpeg', conditional=True)

    def corregir_lectura(self, id):
        try:
            self.servicios.resultados_servicio.corregir(id, request.form.get('resolucion'), request.form.get('marca'), request.form.get('motivo'), session['usuario_id'])
            flash('Corrección guardada conservando la lectura original.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('Error al guardar la corrección')
            flash('No se pudo guardar la corrección.', 'error')
        return redirect(url_for('lecturas', examen=self.seleccionar_examen()))

    def validar_cartilla(self, id):
        try:
            self.servicios.resultados_servicio.validar_cartilla(id)
            flash('Cartilla validada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('lecturas', examen=self.seleccionar_examen()))

    def resultados_coordinador(self):
        if not self.servicios.resultados_servicio:
            abort(503)
        examen = self.seleccionar_examen()
        return render_template('coordinador/resultados_coordinador.html', rol='Coordinador', nombre=session['nombre'], examenes=self.servicios.resultados_servicio.examenes(), examen=examen, resultados=self.servicios.resultados_servicio.resultados(examen) if examen else [], ranking=self.servicios.resultados_servicio.ranking(examen) if examen else [])

    def detalle_resultado_coordinador(self, id):
        examen = self.seleccionar_examen()
        resultado = next((r for r in self.servicios.resultados_servicio.resultados(examen) if r['id_resultado'] == id), None)
        if not resultado:
            abort(404)
        return render_template('coordinador/detalle_resultado_coordinador.html', rol='Coordinador', nombre=session['nombre'], resultado=resultado, examen=examen, detalle=self.servicios.resultados_servicio.detalle_coordinador(id))

    def revisar_resultado(self, id):
        try:
            self.servicios.resultados_servicio.revisar_resultado(id, session['usuario_id'])
            flash('Resultado marcado como revisado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudo revisar el resultado')
            flash('No se pudo revisar: el detalle debe coincidir con los totales.', 'error')
        return redirect(url_for('resultados_coordinador', examen=self.seleccionar_examen()))

    def calcular_resultados(self):
        examen = self.seleccionar_examen()
        try:
            cantidad = self.servicios.calculo_servicio.calcular_resultados(examen, session['usuario_id'])
            flash(f'Se calcularon {cantidad} resultados nuevos; revísalos antes de publicar.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudieron calcular los resultados')
            flash('No se pudo calcular. Comprueba las cartillas, claves y política de puntaje.', 'error')
        return redirect(url_for('resultados_coordinador', examen=examen))

    def publicar_resultados(self):
        try:
            self.servicios.resultados_servicio.publicar(self.seleccionar_examen(), session['usuario_id'])
            flash('Resultados publicados.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudo publicar el examen')
            flash('No se pudo publicar. Todas las cartillas vigentes deben estar validadas y sus resultados revisados.', 'error')
        return redirect(url_for('resultados_coordinador', examen=self.seleccionar_examen()))

    def reportes(self):
        examen = self.seleccionar_examen()
        ranking = self.servicios.resultados_servicio.ranking(examen) if examen else []
        return render_template('coordinador/reportes.html', rol='Coordinador', nombre=session['nombre'], examenes=self.servicios.resultados_servicio.examenes(), examen=examen, ranking=ranking)

    def descargar_reporte(self):
        examen = self.seleccionar_examen()
        if not examen:
            abort(400)
        salida = io.StringIO(newline='')
        escritor = csv.writer(salida)
        escritor.writerow(['Posición', 'Código', 'Estudiante', 'Puntaje', 'Porcentaje', 'Aciertos', 'Errores', 'En blanco'])
        for fila in self.servicios.resultados_servicio.ranking(examen):
            # Evita que un nombre o código se interprete como fórmula en hojas de cálculo.
            seguro = lambda valor: "'" + valor if isinstance(valor, str) and valor.lstrip().startswith(('=', '+', '-', '@')) else valor
            escritor.writerow([seguro(fila[k]) for k in ('posicion','codigo_estudiante','estudiante','puntaje','porcentaje','aciertos','errores','en_blanco')])
        return Response('﻿' + salida.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="reporte_examen_{examen}.csv"'})

    def descargar_reporte_excel(self):
        from openpyxl import Workbook
        examen = self.seleccionar_examen()
        if not examen:
            abort(400)
        libro = Workbook()
        hoja = libro.active
        hoja.title = 'Ranking publicado'
        hoja.append(['Posición', 'Código', 'Estudiante', 'Puntaje', 'Porcentaje', 'Aciertos', 'Errores', 'En blanco'])
        for fila in self.servicios.resultados_servicio.ranking(examen):
            valores = [fila[k] for k in ('posicion','codigo_estudiante','estudiante','puntaje','porcentaje','aciertos','errores','en_blanco')]
            hoja.append(["'" + x if isinstance(x, str) and x.lstrip().startswith(('=', '+', '-', '@')) else x for x in valores])
        contenido = io.BytesIO()
        libro.save(contenido)
        contenido.seek(0)
        return send_file(contenido, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'reporte_examen_{examen}.xlsx')

    def estudiante(self):
        if not self.servicios.resultados_servicio:
            abort(503)
        return render_template('estudiante/mis_resultados.html', rol='Estudiante', nombre=session['nombre'], resultados=self.servicios.resultados_servicio.mis_resultados(session['usuario_id']))

    def mi_detalle(self, id):
        resultados = self.servicios.resultados_servicio.mis_resultados(session['usuario_id'])
        resultado = next((r for r in resultados if r['id_resultado'] == id), None)
        if not resultado:
            abort(404)
        return render_template('estudiante/mi_detalle.html', rol='Estudiante', nombre=session['nombre'], resultado=resultado, materias=self.servicios.resultados_servicio.materias(session['usuario_id'], id), detalle=self.servicios.resultados_servicio.detalle(session['usuario_id'], id))

    def docente(self):
        if not self.servicios.docente_servicio:
            abort(503)
        try:
            preguntas = self.servicios.docente_servicio.preguntas(session['usuario_id'], request.args)
        except ValueError as error:
            flash(str(error), 'error')
            return redirect(url_for('docente'))
        materias, _, _ = self.servicios.docente_servicio.catalogos(session['usuario_id'])
        return render_template('docente/docente_preguntas.html', rol='Docente', nombre=session['nombre'], preguntas=preguntas, materias=materias, examenes=self.servicios.docente_servicio.examenes(), filtros=request.args)

    def docente_tema(self):
        try:
            self.servicios.docente_servicio.crear_tema(session['usuario_id'], request.form.get('materia'), request.form.get('nombre'))
            flash('Tema registrado.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        return redirect(url_for('docente_crear'))

    def formulario_docente(self, pregunta_id=None):
        if not self.servicios.docente_servicio:
            abort(503)
        pregunta = self.servicios.docente_servicio.obtener(session['usuario_id'], pregunta_id) if pregunta_id else None
        if pregunta_id and not pregunta:
            abort(404)
        if pregunta and pregunta['estado'] != 'BORRADOR':
            flash('Solo se pueden editar preguntas en borrador.', 'error')
            return redirect(url_for('docente'))
        materias, temas, areas = self.servicios.docente_servicio.catalogos(session['usuario_id'])
        if request.method == 'POST':
            respuesta = self.guardar_pregunta_docente(pregunta_id, pregunta)
            if respuesta is not None:
                return respuesta
        return render_template('docente/docente_formulario.html', rol='Docente', nombre=session['nombre'], pregunta=pregunta, materias=materias, temas=temas, areas=areas, examenes=self.servicios.docente_servicio.examenes(), datos=request.form if request.method == 'POST' else request.args)

    def guardar_pregunta_docente(self, pregunta_id, pregunta):
        guardadas = {}
        try:
            self.guardar_imagenes_pregunta(guardadas)
            self.servicios.docente_servicio.guardar(session['usuario_id'], request.form, guardadas, pregunta_id)
            flash('Pregunta guardada.' if request.form.get('accion') == 'guardar' else 'Pregunta enviada a revisión.', 'ok')
            examen = request.form.get('examen') or (pregunta['id_examen_destino'] if pregunta else '') or ''
            return redirect(url_for('docente', examen=examen))
        except (ValueError, SQLAlchemyError) as error:
            for ruta, _ in guardadas.values():
                Path(ruta).unlink(missing_ok=True)
            if isinstance(error, SQLAlchemyError):
                self.app.logger.exception('No se pudo guardar la pregunta')
                flash('No se pudo guardar la pregunta. Revisa los datos y la conexión.', 'error')
            else:
                flash(str(error), 'error')
        return None

    def guardar_imagenes_pregunta(self, guardadas):
        for clave in ('ENUNCIADO', 'A', 'B', 'C', 'D', 'E'):
            archivo = request.files.get('imagen_' + clave)
            if archivo and archivo.filename:
                guardadas[clave] = self.servicios.imagenes_preguntas.guardar(archivo)

    def docente_detalle(self, id):
        version = request.args.get('version', type=int)
        pregunta = self.servicios.docente_servicio.obtener(session['usuario_id'], id, version)
        if not pregunta:
            abort(404)
        return render_template('docente/docente_detalle.html', rol='Docente', nombre=session['nombre'], pregunta=pregunta)

    def docente_crear(self):
        return self.formulario_docente()

    def docente_editar(self, id):
        return self.formulario_docente(id)

    def devolver_imagen_pregunta(self, id, coordinador=False):
        ruta = self.servicios.docente_servicio.imagen(session['usuario_id'], id, coordinador)
        if not ruta:
            abort(404)
        raiz = self.servicios.imagenes_preguntas.directorio
        imagen = Path(ruta).resolve()
        if not imagen.is_relative_to(raiz) or not imagen.is_file():
            abort(404)
        return send_file(imagen, mimetype=MIMETYPE_PNG, conditional=True)

    def docente_imagen(self, id):
        return self.devolver_imagen_pregunta(id)

    def coordinador_imagen_pregunta(self, id):
        return self.devolver_imagen_pregunta(id, True)

    def docente_estadisticas(self):
        if not self.servicios.docente_servicio:
            abort(503)
        return render_template('docente/docente_estadisticas.html', rol='Docente', nombre=session['nombre'], estadisticas=self.servicios.docente_servicio.estadisticas(session['usuario_id']))

    def configurar_examen(self):
        if not self.servicios.diseno_servicio:
            abort(503)
        examen = self.seleccionar_examen()
        if request.method == 'POST':
            try:
                if not examen:
                    raise ValueError('Selecciona un examen.')
                puntajes = {clave.removeprefix('puntaje_'): valor for clave, valor in request.form.items() if clave.startswith('puntaje_') and valor.strip()}
                self.servicios.diseno_servicio.configurar(examen, request.form.getlist('preguntas'), puntajes, request.form.getlist('versiones'), request.form.get('penalizacion'), session['usuario_id'])
                flash('Examen configurado y aprobado. Ahora revisa las claves de cada versión.', 'ok')
                return redirect(url_for('configurar_examen', examen=examen))
            except ValueError as error:
                flash(str(error), 'error')
            except SQLAlchemyError:
                self.app.logger.exception('No se pudo configurar el examen')
                flash('No se pudo guardar la configuración; verifica que las preguntas y el examen sigan disponibles.', 'error')
        examenes, actual, preguntas, versiones, claves = self.servicios.diseno_servicio.consultar(examen)
        distribucion = self.servicios.diseno_servicio.distribucion(examen) if actual else []
        return render_template('coordinador/configurar_examen.html', rol='Coordinador', nombre=session['nombre'], examen=examen, examenes=examenes, actual=actual, preguntas=preguntas, versiones=versiones, claves=claves, distribucion=distribucion)

    def guardar_clave(self, id):
        examen = self.seleccionar_examen()
        try:
            respuestas = {k.removeprefix('respuesta_'): v for k, v in request.form.items() if k.startswith('respuesta_')}
            archivo = request.files.get('archivo')
            if archivo and archivo.filename:
                respuestas = leer_clave_csv(archivo)
            self.servicios.diseno_servicio.crear_clave(id, respuestas, request.form.get('motivo'), session['usuario_id'])
            flash('Nueva revisión de clave confirmada.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            self.app.logger.exception('No se pudo confirmar la clave')
            flash('No se pudo confirmar la clave; comprueba que cada respuesta sea una alternativa de la pregunta.', 'error')
        return redirect(url_for('configurar_examen', examen=examen))

    def salir(self):
        session.clear()
        return redirect(url_for('login'))


def leer_clave_csv(archivo):
    """Lee respuestas únicas de un CSV UTF-8 con tamaño limitado."""
    contenido = archivo.read(100001)
    if len(contenido) > 100000:
        raise ValueError('El CSV supera el tamaño permitido.')
    try:
        filas = csv.reader(io.StringIO(contenido.decode('utf-8-sig')))
    except UnicodeDecodeError:
        raise ValueError('El CSV debe estar codificado en UTF-8.') from None
    respuestas = {}
    for fila in filas:
        if not fila or (fila[0].strip().lower() in ('pregunta', 'numero') and len(fila) == 2):
            continue
        if len(fila) != 2 or fila[0].strip() in respuestas:
            raise ValueError('El CSV debe contener número y respuesta únicos en cada fila.')
        respuestas[fila[0].strip()] = fila[1].strip()
    return respuestas
