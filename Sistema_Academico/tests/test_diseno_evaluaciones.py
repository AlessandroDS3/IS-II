"""Pruebas del diseño de evaluaciones (Diego)."""
from datetime import date
from decimal import Decimal

import pytest

from aplicacion.servicios.diseno_examen_app_service import DisenoExamenAppService, respuestas_desde_csv
from aplicacion.servicios.simulacro_app_service import SimulacroAppService
from dominio.diseno_evaluaciones.conjunto_calificacion import ConjuntoCalificacion
from dominio.diseno_evaluaciones.distribucion_materia import DistribucionMateria
from dominio.diseno_evaluaciones.estado_simulacro import EstadoSimulacro
from dominio.diseno_evaluaciones.examen import Examen
from dominio.diseno_evaluaciones.revision_clave import RevisionClave
from dominio.diseno_evaluaciones.simulacro import Simulacro
from tests.conftest import RepositorioFalso

RESUMEN_VACIO = {'preguntas_revision': 0, 'cargas_pendientes': 0, 'cartillas_revision': 0, 'cartillas': 0,
                 'resultados': 0, 'calculos_revision': 0, 'por_publicar': 0, 'publicado': 0}


def test_simulacro_un_examen_por_area_y_cierre():
    simulacro = Simulacro(ciclo_id=1, nombre='S', fecha_aplicacion=date(2026, 1, 1))
    with pytest.raises(ValueError):
        simulacro.confirmar()
    simulacro.registrar_examen(1, 10)
    with pytest.raises(ValueError, match='ya pertenece'):
        simulacro.registrar_examen(1, 11)
    simulacro.confirmar()
    assert simulacro.estado == EstadoSimulacro.CERRADO
    with pytest.raises(ValueError):
        simulacro.registrar_examen(2, 12)
    simulacro.desactivar('motivo')
    assert simulacro.estado == EstadoSimulacro.INACTIVO


def test_ordenar_versiones_y_validaciones_de_estado():
    assert Examen.ordenar_versiones([1, 2, 3], 'B') == [3, 2, 1]
    with pytest.raises(ValueError):
        Examen.ordenar_versiones([1], 'Z')
    with pytest.raises(ValueError):
        Examen.validar_configuracion('APROBADO', 0)
    Examen.validar_revision_clave('APLICADO', 0)


def test_revision_clave_y_conjunto_y_distribucion():
    clave = RevisionClave(1, 1, 1, {1: 'A', 2: 'E'}, 1, 'Inicial')
    clave.confirmar()
    assert clave.confirmada
    with pytest.raises(ValueError):
        clave.confirmar()
    conjunto = ConjuntoCalificacion(1, clave_id=3)
    with pytest.raises(ValueError, match='política'):
        conjunto.validar_claves_y_politica()
    assert DistribucionMateria(1, 4, Decimal('2.5')).puntaje_materia_derivado() == Decimal('10.0')


def test_respuestas_desde_csv():
    assert respuestas_desde_csv('pregunta,respuesta\n1,A\n2,b\n'.encode('utf-8-sig')) == {'1': 'A', '2': 'b'}
    with pytest.raises(ValueError, match='únicos'):
        respuestas_desde_csv(b'1,A\n1,B\n')
    latin1 = '1,Á'.encode('latin-1')
    with pytest.raises(ValueError, match='UTF-8'):
        respuestas_desde_csv(latin1)
    with pytest.raises(ValueError, match='tamaño'):
        respuestas_desde_csv(b'x' * 100001)


def test_configurar_valida_puntajes_y_versiones():
    servicio = DisenoExamenAppService(RepositorioFalso())
    with pytest.raises(ValueError, match='versión'):
        servicio.configurar(1, ['1'], {'1': '10'}, ['C'], '0', 1)
    with pytest.raises(ValueError, match='penalización'):
        servicio.configurar(1, ['1'], {'1': '10'}, ['A'], '1', 1)
    with pytest.raises(ValueError, match='puntaje'):
        servicio.configurar(1, ['1'], {'1': '0.0000000001'}, ['A'], '0', 1)


@pytest.mark.parametrize('cambios, esperado', [
    ({'preguntas_revision': 1}, 'banco_preguntas'),
    ({}, 'cartillas'),
    ({'cargas_pendientes': 2}, 'cartillas'),
    ({'cartillas_revision': 1}, 'lecturas'),
    ({'cartillas': 3, 'resultados': 1}, 'resultados_coordinador'),
    ({'publicado': 1}, 'reportes'),
])
def test_siguiente_etapa(cambios, esperado):
    assert SimulacroAppService.siguiente_etapa({'estado': 'APROBADO'}, dict(RESUMEN_VACIO, **cambios))[0] == esperado
    assert SimulacroAppService.siguiente_etapa({'estado': 'CONFIGURACION'}, RESUMEN_VACIO)[0] == 'configurar_examen'
