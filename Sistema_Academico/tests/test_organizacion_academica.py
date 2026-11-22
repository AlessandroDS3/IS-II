"""Pruebas de organización académica (Stefano)."""
from datetime import date

import pytest

from aplicacion.servicios.organizacion_app_service import OrganizacionAppService
from dominio.organizacion_academica.ciclo import Ciclo
from dominio.organizacion_academica.docente import Docente
from dominio.organizacion_academica.eje_tematico import EjeTematico
from dominio.organizacion_academica.estado_registro import EstadoRegistro
from dominio.organizacion_academica.estudiante import Estudiante
from dominio.organizacion_academica.reglas_organizacion import validar_datos, validar_estado, validar_transicion_estado
from tests.conftest import RepositorioFalso


def test_validar_datos_por_tipo():
    assert validar_datos('materias', {'nombre': ' M ', 'id_eje': '3'}) == {'nombre': 'M', 'codigo': '', 'id_eje': 3}
    grupo = validar_datos('grupos', {'nombre': 'G', 'id_ciclo': '1', 'aula': ''})
    assert grupo['aula'] is None
    assert grupo['horario'] is None
    with pytest.raises(ValueError, match='código del área'):
        validar_datos('areas', {'nombre': 'A'})
    with pytest.raises(ValueError, match='anterior'):
        validar_datos('ciclos', {'nombre': 'C', 'fecha_inicio': '2026-05-01', 'fecha_fin': '2026-01-01'})
    with pytest.raises(ValueError, match='Tipo'):
        validar_datos('otros', {'nombre': 'x'})


def test_estados():
    assert validar_estado('ciclos', 'FINALIZADO') == 'FINALIZADO'
    with pytest.raises(ValueError, match='Solo se pueden finalizar'):
        validar_estado('areas', 'FINALIZADO')
    with pytest.raises(ValueError, match='reactivarse'):
        validar_transicion_estado('ciclos', 'FINALIZADO', 'ACTIVO')


def test_servicio_despacha_acciones():
    repo = RepositorioFalso(crear='ok')
    servicio = OrganizacionAppService(repo)
    assert servicio.ejecutar('crear', 'ejes', {'nombre': 'Eje'}) == 'ok'
    servicio.ejecutar('desasignar', '', {'docente': '1', 'materia': '2'})
    assert repo.llamadas[-1] == ('asignar', (1, 2, False), {})
    with pytest.raises(ValueError, match='Tipo'):
        servicio.ejecutar('borrar', 'x', {})
    with pytest.raises(ValueError, match='Acción'):
        servicio.ejecutar('borrar', 'areas', {})


def test_estudiante_conserva_historial_de_asignaciones():
    estudiante = Estudiante(codigo='E1', nombres='Ana')
    estudiante.cambiar_asignacion(grupo_id=1, area_id=2, fecha=date(2026, 1, 1))
    estudiante.cambiar_asignacion(grupo_id=1, area_id=3, fecha=date(2026, 2, 1))
    assert estudiante.asignacion_area['valor'] == 3
    assert estudiante.historial[0]['fecha_fin'] == date(2026, 2, 1)
    fecha_anterior = date(2026, 1, 15)
    with pytest.raises(ValueError, match='posterior'):
        estudiante.cambiar_asignacion(grupo_id=1, area_id=4, fecha=fecha_anterior)
    estudiante.vincular_cuenta(5)
    with pytest.raises(ValueError, match='ya tiene'):
        estudiante.vincular_cuenta(6)


def test_ciclo_eje_y_docente():
    ciclo = Ciclo(nombre='C')
    ciclo.agregar_grupo('G1').id = 1
    ciclo.desactivar_grupo(1)
    assert ciclo.grupos[0].estado == EstadoRegistro.INACTIVO
    ciclo.finalizar()
    with pytest.raises(ValueError):
        ciclo.activar()
    eje = EjeTematico(nombre='E')
    eje.desactivar()
    with pytest.raises(ValueError, match='activo'):
        eje.agregar_materia('M')
    docente = Docente(cuenta_id=1)
    docente.asignar_materia(4)
    with pytest.raises(ValueError):
        docente.retirar_materia(5)
