"""Pruebas de las rutas web con servicios falsos (sin base de datos)."""
import io
from types import SimpleNamespace

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError, OperationalError

from presentacion.controllers.rutas_web import registrar_rutas
from presentacion.controllers.servicios_web import ServiciosWeb

VISTAS = str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'presentacion' / 'vistas')


class ServicioFalso:
    """Servicio que registra llamadas; cada método devuelve el valor configurado o lanza la excepción indicada."""

    def __init__(self, **valores):
        self.valores = valores
        self.llamadas = []

    def __getattr__(self, nombre):
        def metodo(*args, **kwargs):
            self.llamadas.append(nombre)
            valor = self.valores.get(nombre)
            if isinstance(valor, Exception):
                raise valor
            return valor(*args) if callable(valor) else valor
        return metodo


def _error_bd():
    return OperationalError('stmt', {}, Exception('fallo'))


ENTRADA = {'id': 1, 'examen_id': 3, 'ruta_imagen': 'no-existe.img', 'nombre_archivo': 'x.jpg', 'estado': 'REVISAR',
           'pagina': 1, 'creada_en': None, 'lectura_json': None, 'error_texto': None, 'estudiante_id': None,
           'version_id': None, 'cartilla_id': None, 'motivo_descarte': None}


ROLES = ['COORDINADOR', 'DIRECTOR', 'DOCENTE', 'ESTUDIANTE']
RESUMEN_DIRECTOR = {'estudiantes': 0, 'promedio': 0, 'maximo': 0, 'minimo': 0}
CONTEXTO = {'id_examen': 3, 'id_simulacro': 1, 'id_area': 1, 'estado': 'APROBADO', 'admite_preguntas': 1, 'area': 'Área',
            'nombre': 'Simulacro', 'fecha': None, 'ciclo': 'Ciclo', 'estado_aplicacion': 'ABIERTO', 'areas': []}


def _servicios(**reemplazos):
    base = {
        'acceso': ServicioFalso(consultar_cuenta_activa={'id': 1, 'roles': ROLES},
                                iniciar_sesion={'id': 1, 'usuario': 'u', 'nombre': 'U', 'roles': ['DOCENTE']}),
        'usuarios': ServicioFalso(listar=[]),
        'estudiantes': ServicioFalso(buscar_por_id={'id_estudiante': 1}, listar=[], cambiar_estado=1,
                                     consultar_asignaciones=([], [], [], [])),
        'organizacion': ServicioFalso(listar={}),
        'panel': ServicioFalso(consultar_pendientes=_error_bd()),
        'simulacros': ServicioFalso(listar=([], [], [], []), contexto_examen=CONTEXTO),
        'diseno': ServicioFalso(consultar=SimpleNamespace(examenes=[], actual=None, preguntas=[], versiones=[], claves=[])),
        'preguntas': ServicioFalso(consultar_banco=([], [], [], [])),
        'autoria': ServicioFalso(preguntas=[], catalogos=([], [], []), examenes=[], obtener=None, estadisticas=[]),
        'imagenes_preguntas': SimpleNamespace(directorio='.', guardar=lambda archivo: ('no-existe.png', 1)),
        'cartillas': ServicioFalso(obtener=ENTRADA, historial=[], registrar_cartilla=9, importar_lote=2, examenes=[]),
        'revision_lecturas': ServicioFalso(examenes=[], lecturas=[], historial_lecturas=[], resultados=[], resultado=None),
        'calculo': ServicioFalso(calcular_resultados=3),
        'publicacion': ServicioFalso(examenes=[], ranking=[{'posicion': 1, 'codigo_estudiante': '=X', 'estudiante': 'Ana',
                                                            'puntaje': 10, 'porcentaje': 50, 'aciertos': 1, 'errores': 0, 'en_blanco': 0}],
                                     estadisticas_director=SimpleNamespace(ciclos=[], filas=[], resumen=RESUMEN_DIRECTOR)),
        'resultados_estudiante': ServicioFalso(mis_resultados=[], mi_resultado=None),
    }
    base['cartillas'].preparador = SimpleNamespace(MAX_BYTES=100)
    base.update(reemplazos)
    return ServiciosWeb(**base)


def _cliente(servicios):
    app = Flask('prueba', root_path=str(__import__('pathlib').Path(VISTAS).parents[1]), template_folder=VISTAS,
                static_folder=VISTAS + '/recursos', static_url_path='/recursos')
    app.config.update(SECRET_KEY='x', WTF_CSRF_ENABLED=False)
    app.jinja_env.globals['csrf_token'] = lambda: 'token'
    registrar_rutas(app, servicios)
    cliente = app.test_client()
    with cliente.session_transaction() as sesion:
        sesion.update(usuario='u', usuario_id=1, nombre='U', roles=ROLES)
    return cliente


@pytest.fixture
def servicios():
    return _servicios()


@pytest.fixture
def cliente(servicios):
    return _cliente(servicios)


@pytest.mark.parametrize('url', [
    '/', '/elegir-rol', '/coordinador', '/coordinador/usuarios', '/coordinador/estudiantes', '/coordinador/estudiantes/1/editar',
    '/coordinador/estudiantes/1/asignaciones', '/coordinador/organizacion', '/coordinador/simulacros', '/coordinador/preguntas',
    '/coordinador/configurar-examen', '/coordinador/cartillas', '/coordinador/cargas/1', '/coordinador/lecturas',
    '/coordinador/resultados', '/coordinador/reportes', '/director', '/docente', '/docente/preguntas/nueva',
    '/docente/estadisticas', '/estudiante',
])
def test_paginas_se_renderizan(cliente, url):
    assert cliente.get(url).status_code == 200


@pytest.mark.parametrize('url, datos', [
    ('/coordinador/usuarios/2/estado', {'estado': 'ACTIVO'}),
    ('/coordinador/usuarios/2/roles', {'roles': ['DOCENTE']}),
    ('/coordinador/estudiantes', {'codigo': 'E'}),
    ('/coordinador/estudiantes/1/editar', {'codigo': 'E'}),
    ('/coordinador/estudiantes/1/estado', {'estado': 'ACTIVO'}),
    ('/coordinador/estudiantes/1/cuenta', {'usuario': 'u'}),
    ('/coordinador/estudiantes/1/asignaciones', {'grupo': '1'}),
    ('/coordinador/organizacion', {'accion': 'crear'}),
    ('/coordinador/simulacros', {'accion': 'simulacro', 'areas': ['1']}),
    ('/coordinador/simulacros', {'accion': 'agregar_areas'}),
    ('/coordinador/simulacros', {'accion': 'examen'}),
    ('/coordinador/simulacros', {'accion': 'habilitar'}),
    ('/coordinador/preguntas/1/revision', {'version': '1', 'accion': 'aprobar'}),
    ('/coordinador/configurar-examen?examen=2', {'puntaje_1': '5', 'preguntas': ['1']}),
    ('/coordinador/versiones/1/clave?examen=2', {'respuesta_1': 'A', 'motivo': 'm'}),
    ('/coordinador/cartillas/1/identificar', {'estudiante': '1'}),
    ('/coordinador/cartillas/1/registrar', {'motivo': ''}),
    ('/coordinador/cartillas/1/descartar', {'motivo': 'm'}),
    ('/coordinador/cargas/1/resolver', {'accion': 'reintentar'}),
    ('/coordinador/lecturas/1/corregir', {'resolucion': 'BLANCO'}),
    ('/coordinador/cartillas/1/validar', {}),
    ('/coordinador/resultados/1/revisar', {}),
    ('/coordinador/resultados/calcular', {'examen': '2'}),
    ('/coordinador/resultados/publicar', {'examen': '2'}),
    ('/docente/temas', {'materia': '1'}),
    ('/salir', {}),
])
def test_acciones_redirigen(cliente, url, datos):
    assert cliente.post(url, data=datos).status_code == 302


def test_errores_de_validacion_y_de_base_de_datos_se_informan():
    errores = {'crear': ValueError('x'), 'registrar_estudiante': IntegrityError('s', {}, Exception()),
               'actualizar': IntegrityError('s', {}, Exception()), 'vincular_cuenta': IntegrityError('s', {}, Exception()),
               'cambiar_asignacion': IntegrityError('s', {}, Exception()), 'ejecutar': IntegrityError('s', {}, Exception()),
               'crear_simulacro': _error_bd(), 'revisar_pregunta': _error_bd(), 'configurar': _error_bd(), 'crear_clave': _error_bd(),
               'registrar_cartilla': _error_bd(), 'reintentar_lectura': _error_bd(), 'corregir': _error_bd(),
               'revisar_resultado': _error_bd(), 'calcular_resultados': _error_bd(), 'publicar': _error_bd(),
               'cambiar_roles': _error_bd(), 'listar': _error_bd()}
    falsos = {nombre: ServicioFalso(**errores) for nombre in ('usuarios', 'estudiantes', 'organizacion', 'simulacros', 'preguntas',
                                                                'diseno', 'cartillas', 'revision_lecturas', 'calculo', 'publicacion')}
    falsos['cartillas'].valores['obtener'] = ENTRADA
    falsos['estudiantes'].valores.update(buscar_por_id={'id_estudiante': 1}, consultar_asignaciones=([], [], [], []))
    falsos['cartillas'].preparador = SimpleNamespace(MAX_BYTES=100)
    falsos['organizacion'].valores['listar'] = {}
    falsos['diseno'].valores['consultar'] = SimpleNamespace(examenes=[], actual=None, preguntas=[], versiones=[], claves=[])
    cliente = _cliente(_servicios(**falsos))
    assert cliente.post('/coordinador/usuarios', data={'username': 'x'}).status_code == 503
    for url in ('/coordinador/estudiantes/1/editar', '/coordinador/estudiantes/1/asignaciones', '/coordinador/organizacion'):
        assert cliente.post(url, data={}).status_code == 200
    falsos['simulacros'].valores.update(listar=([], [], [], []), contexto_examen=CONTEXTO)
    assert cliente.post('/coordinador/simulacros', data={'accion': 'simulacro'}).status_code == 200
    for url in ('/coordinador/estudiantes/1/cuenta', '/coordinador/preguntas/1/revision',
                '/coordinador/versiones/1/clave', '/coordinador/cartillas/1/registrar', '/coordinador/cargas/1/resolver',
                '/coordinador/lecturas/1/corregir', '/coordinador/resultados/1/revisar', '/coordinador/resultados/calcular',
                '/coordinador/resultados/publicar', '/coordinador/usuarios/2/roles'):
        assert cliente.post(url, data={'accion': 'reintentar', 'examen': '2', 'version': '1'}).status_code == 302
    assert cliente.post('/coordinador/configurar-examen?examen=2', data={}).status_code == 200


def test_carga_de_cartillas_por_lotes(cliente, servicios):
    archivo = (io.BytesIO(b'img'), 'carpeta\\foto.jpg')
    respuesta = cliente.post('/coordinador/cartillas', data={'examen': '3', 'archivos': [archivo]},
                             headers={'X-Carga-Lote': '1'}, content_type='multipart/form-data')
    assert respuesta.get_json() == {'creadas': 2}
    assert cliente.post('/coordinador/cartillas', data={'examen': '0'}, headers={'X-Carga-Lote': '1'}).status_code == 400
    assert cliente.post('/coordinador/cartillas', data={'examen': '0'}).status_code == 302


def test_carga_de_cartillas_sin_base_de_datos():
    cartillas = ServicioFalso(examenes=_error_bd(), importar_lote=_error_bd())
    cartillas.preparador = SimpleNamespace(MAX_BYTES=100)
    cliente = _cliente(_servicios(cartillas=cartillas))
    assert cliente.get('/coordinador/cartillas').status_code == 503
    assert cliente.post('/coordinador/cartillas', data={'examen': '3'}, headers={'X-Carga-Lote': '1'}).status_code == 503


def test_reemplazo_de_imagen_y_accion_invalida(cliente):
    assert cliente.post('/coordinador/cargas/1/resolver', data={'accion': 'reemplazar'}).status_code == 302
    datos = {'accion': 'reemplazar', 'imagen': (io.BytesIO(b'x'), 'r.jpg')}
    assert cliente.post('/coordinador/cargas/1/resolver', data=datos, content_type='multipart/form-data').status_code == 302
    assert cliente.post('/coordinador/cargas/1/resolver', data={'accion': 'otra'}).status_code == 302


def test_detalles_inexistentes_responden_404(cliente):
    for url in ('/coordinador/resultados/9/detalle?examen=2', '/estudiante/resultados/9', '/docente/preguntas/9',
                '/docente/preguntas/9/editar', '/coordinador/cargas/1/imagen', '/coordinador/cargas/1/imagen?historial=2',
                '/coordinador/cartillas/1/imagen', '/docente/imagenes/1', '/coordinador/preguntas/imagenes/1',
                '/coordinador/examenes/1'):
        assert cliente.get(url).status_code == 404


def test_reportes_csv_y_excel_neutralizan_formulas(cliente):
    csv = cliente.get('/coordinador/reportes/descargar?examen=2').get_data(as_text=True)
    assert "'=X" in csv
    assert cliente.get('/coordinador/reportes/excel?examen=2').mimetype.endswith('sheet')
    assert cliente.get('/coordinador/reportes/descargar').status_code == 400
    assert cliente.get('/director/reporte.csv').status_code == 200


def test_login_correcto_y_errores():
    cliente = _cliente(_servicios())
    assert cliente.post('/', data={'usuario': 'u', 'contrasena': 'c'}).status_code == 302
    sin_roles = ServicioFalso(iniciar_sesion={'id': 1, 'usuario': 'u', 'nombre': 'U', 'roles': ['OTRO']})
    assert _cliente(_servicios(acceso=sin_roles)).post('/', data={'usuario': 'u'}).status_code == 403
    caida = ServicioFalso(iniciar_sesion=_error_bd())
    assert _cliente(_servicios(acceso=caida)).post('/', data={'usuario': 'u'}).status_code == 503


def test_formulario_docente_guarda_y_limpia_imagenes(cliente):
    datos = {'accion': 'guardar', 'examen': '3', 'imagen_A': (io.BytesIO(b'png'), 'a.png')}
    assert cliente.post('/docente/preguntas/nueva', data=datos, content_type='multipart/form-data').status_code == 302
    fallo = ServicioFalso(guardar=ValueError('datos'), catalogos=([], [], []), examenes=[], obtener=None)
    respuesta = _cliente(_servicios(autoria=fallo)).post('/docente/preguntas/nueva', data=dict(datos, imagen_A=(io.BytesIO(b'p'), 'a.png')),
                                                        content_type='multipart/form-data')
    assert respuesta.status_code == 200


def test_pregunta_no_borrador_no_se_edita():
    autoria = ServicioFalso(obtener={'estado': 'REVISION'}, catalogos=([], [], []), examenes=[])
    assert _cliente(_servicios(autoria=autoria)).get('/docente/preguntas/5/editar').status_code == 302
