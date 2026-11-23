"""Pruebas de evaluación (Jesus)."""
from decimal import Decimal

import pytest

from aplicacion.servicios.importacion_cartillas_app_service import ImportacionCartillasAppService
from aplicacion.servicios.revision_lecturas_app_service import RevisionLecturasAppService
from dominio.evaluacion.calculo_resultado import CalculoResultado
from dominio.evaluacion.calificador_resultados import calificar
from dominio.evaluacion.estado_calculo import EstadoCalculo
from dominio.evaluacion.estado_entrada import EstadoEntrada
from dominio.evaluacion.identificacion_cartilla import identificar_cartilla
from dominio.evaluacion.importacion_cartillas import ImportacionCartillas
from dominio.evaluacion.participacion import Participacion
from tests.conftest import RepositorioFalso


def _fila(lectura, clave, resolucion=None, corregida=None, materia=1):
    return {'lectura': lectura, 'clave': clave, 'resolucion': resolucion, 'corregida': corregida,
            'puntaje': Decimal('5'), 'id_materia': materia}


def test_calificar_con_penalizacion_blancos_y_correcciones():
    filas = [_fila('A', 'A'), _fila('B', 'A'), _fila(None, 'A'), _fila('C', 'C', 'MARCA_UNICA', 'C', 2),
             _fila('A', 'A', 'MULTIPLE_CONFIRMADA', None, 2)]
    desglose = calificar(filas, Decimal('-1'))
    assert (desglose.correctas, desglose.incorrectas, desglose.blancos) == (2, 1, 2)
    assert desglose.puntaje_total == Decimal('9')
    assert desglose.materias[2]['blancos'] == 1
    assert desglose.detalles[4]['tipo'] == 'MULTIPLE_CONFIRMADA'


def test_calificar_no_devuelve_puntaje_negativo():
    assert calificar([_fila('B', 'A')], Decimal('-2')).puntaje_total == Decimal(0)


def _lectura(dni='12345678', area='B', tema='A'):
    control = {'estado': 'VALIDA', 'confianza': 'alta'}
    return {'exito': True, 'dni': dni, 'resumen': {'dni_completo': True},
            'controles': {'area': dict(control, respuesta=area), 'tema': dict(control, respuesta=tema)}}


def test_identificar_cartilla_completa_y_bloqueos():
    estudiantes = [{'id_estudiante': 1, 'dni': '12345678'}]
    versiones = [{'id_version': 7, 'codigo_version': 'A'}, {'id_version': 8, 'codigo_version': 'B'}]
    completa = identificar_cartilla(_lectura(), estudiantes, versiones, 'Biomédicas')
    assert completa['completa']
    assert completa['version']['id_version'] == 7
    otra_area = identificar_cartilla(_lectura(area='I'), estudiantes, versiones, 'Biomédicas')
    assert not otra_area['completa']
    assert 'Ingenierías' in otra_area['bloqueo']
    sin_version = identificar_cartilla(_lectura(tema='C'), estudiantes, versiones, 'Biomedicas')
    assert sin_version['bloqueo'].startswith('La cartilla indica la versión C')
    dni_no_ascii = identificar_cartilla(_lectura(dni='١٢٣٤٥٦٧٨'), estudiantes, versiones, 'Biomédicas')
    assert dni_no_ascii['estudiante'] is None


def test_importacion_reglas_de_entradas():
    importacion = ImportacionCartillas(examen_destino_id=1, operacion_id='op', responsable_id=1)
    entrada = importacion.agregar_entrada('a.img', 1, huella='h1', entrada_id=1)
    assert importacion.agregar_entrada('b.img', 1, huella='h1', entrada_id=2) is None
    with pytest.raises(ValueError, match='identificar'):
        importacion.resolver_identificacion(1, 5, 6)
    entrada.estado = EstadoEntrada.REVISAR
    importacion.resolver_identificacion(1, 5, 6)
    with pytest.raises(ValueError, match='ya fue guardada'):
        importacion.resolver_identificacion(1, 5, 6)
    importacion.reintentar_entrada(1, 'op2')
    assert entrada.estado == EstadoEntrada.PENDIENTE
    assert entrada.estudiante_identificado_id_opcional is None
    with pytest.raises(ValueError, match='motivo'):
        importacion.descartar_entrada(1, ' ', 1)
    importacion.descartar_entrada(1, 'duplicada', 1)
    with pytest.raises(ValueError):
        importacion.descartar_entrada(1, 'otra vez', 1)


def test_participacion_reemplazo_exige_motivo():
    participacion = Participacion(estudiante_id=1, simulacro_id=1, examen_id=2)
    primera = participacion.recibir_cartilla('a.img', 1)
    primera.id = 10
    with pytest.raises(ValueError, match='motivo'):
        participacion.reemplazar_cartilla('b.img', 1, '')
    segunda = participacion.reemplazar_cartilla('b.img', 1, 'ilegible')
    assert not primera.vigente
    assert segunda.numero_recepcion == 2
    assert segunda.cartilla_origen_id_opcional == 10
    with pytest.raises(ValueError, match='otra área'):
        Participacion.exigir_mismo_examen(2, 3)


def test_calculo_solo_se_revisa_una_vez():
    calculo = CalculoResultado(1, 1, 1, 1, 1, 1)
    calculo.marcar_revisado(9)
    assert calculo.estado_revision == EstadoCalculo.REVISADO
    assert calculo.revisado_por_opcional == 9
    with pytest.raises(ValueError):
        calculo.marcar_revisado(9)


def test_corregir_valida_resolucion_y_marca():
    repo = RepositorioFalso()
    servicio = RevisionLecturasAppService(repo)
    with pytest.raises(ValueError, match='resolución'):
        servicio.corregir(1, 'X', 'A', 'm', 1)
    with pytest.raises(ValueError, match='A a E'):
        servicio.corregir(1, 'MARCA_UNICA', 'Z', 'm', 1)
    servicio.corregir(1, 'BLANCO', 'z', ' motivo ', 1)
    assert repo.llamadas[-1][1] == (1, 'BLANCO', None, 'motivo', 1)


class PreparadorFalso:
    MAX_BYTES = 100

    def __init__(self):
        self.guardados = []

    def guardar_pagina(self, contenido):
        self.guardados.append(contenido)
        return f'ruta{len(self.guardados)}', 'huella'

    def paginas(self, nombre, contenido):
        raise ValueError('Solo se admiten imágenes JPG, PNG o archivos PDF.')

    def descartar_archivo_temporal(self, ruta):
        raise AssertionError('no debe descartarse el original')


def test_archivo_ilegible_se_registra_en_error_sin_volver_a_guardarse():
    repo = RepositorioFalso(crear=3)
    preparador = PreparadorFalso()
    servicio = ImportacionCartillasAppService(repo, preparador, lector=None)
    assert servicio.importar_lote(1, [('x.txt', b'hola')], 9) == 1
    assert len(preparador.guardados) == 1
    crear = next(llamada for llamada in repo.llamadas if llamada[0] == 'crear')
    assert crear[1][0]['ruta'] == 'ruta1'
    assert crear[1][0]['pagina'] == 0
    assert repo.llamadas[-1][0] == 'actualizar_lectura'
    assert repo.llamadas[-1][1][1] == EstadoEntrada.ERROR
