"""Pruebas de publicación y ranking (Elyud)."""
from datetime import datetime
from decimal import Decimal

import pytest

from aplicacion.servicios.publicacion_examen_app_service import PublicacionExamenAppService
from dominio.publicacion_ranking.clasificador_ranking import ClasificadorRanking
from dominio.publicacion_ranking.entrada_publicada import EntradaPublicada
from dominio.publicacion_ranking.publicacion_examen import PublicacionExamen
from tests.conftest import RepositorioFalso


def _entradas(*puntajes):
    return [EntradaPublicada(estudiante_id=i, participacion_id=None, calculo_id=i, puntaje=Decimal(p))
            for i, p in enumerate(puntajes, 1)]


def test_ranking_de_competicion_con_empates_igual_que_rank_sql():
    clasificadas = ClasificadorRanking().clasificar(_entradas('10', '18', '18', '7'))
    assert [(e.estudiante_id, e.puesto) for e in clasificadas] == [(2, 1), (3, 1), (1, 3), (4, 4)]


def test_republicar_exige_motivo():
    publicacion = PublicacionExamen(examen_id=1)
    publicacion.actualizar_resultados_vigentes(_entradas('5'), datetime(2026, 1, 1), None)
    assert publicacion.version_publicacion == 1
    nuevas, fecha = _entradas('6'), datetime(2026, 1, 2)
    with pytest.raises(ValueError, match='motivo'):
        publicacion.actualizar_resultados_vigentes(nuevas, fecha, '')
    vacia, fecha_vacia = PublicacionExamen(examen_id=2), datetime(2026, 1, 1)
    with pytest.raises(ValueError):
        vacia.actualizar_resultados_vigentes([], fecha_vacia, 'x')


def test_servicio_publicacion():
    repo = RepositorioFalso(ranking=['fila'])
    servicio = PublicacionExamenAppService(repo)
    with pytest.raises(ValueError, match='examen'):
        servicio.publicar(0, 1)
    assert servicio.ranking(0) == []
    assert servicio.ranking(3) == ['fila']
