"""Pruebas del banco de preguntas (Estrella)."""
import pytest
from werkzeug.datastructures import MultiDict

from aplicacion.servicios.autoria_preguntas_app_service import AutoriaPreguntasAppService
from aplicacion.servicios.pregunta_app_service import PreguntaAppService
from dominio.banco_preguntas.contenido_docente import ContenidoPregunta, validar_contenido
from dominio.banco_preguntas.estado_pregunta import EstadoPregunta
from dominio.banco_preguntas.pregunta import Pregunta
from tests.conftest import RepositorioFalso

CONTENIDO = {'enunciado': '¿2+2?', 'respuesta': 'B'}


def _pregunta_en_revision():
    pregunta = Pregunta(autor_id=1, materia_id=1, area_ids=[2])
    pregunta.editar_creando_version(dict(CONTENIDO, id=10), responsable_id=1)
    pregunta.enviar_a_revision()
    return pregunta


def test_estados_coinciden_con_la_base_de_datos():
    assert [e.value for e in EstadoPregunta] == ['BORRADOR', 'REVISION', 'APROBADA', 'INACTIVA']


def test_ciclo_de_vida_aprobacion():
    pregunta = _pregunta_en_revision()
    assert pregunta.estado == EstadoPregunta.REVISION
    assert pregunta.version_activa.sellada
    revision = pregunta.aprobar_inicialmente(coordinador_id=5, version_vista_id=10)
    assert pregunta.estado == EstadoPregunta.APROBADA
    assert revision.decision == 'APROBADA'
    assert pregunta.es_elegible_para_area(2)
    assert not pregunta.es_elegible_para_area(3)


def test_devolver_exige_observacion_y_version_vigente():
    pregunta = _pregunta_en_revision()
    with pytest.raises(ValueError, match='observación'):
        pregunta.devolver_a_borrador('', 10)
    with pytest.raises(ValueError, match='cambió'):
        pregunta.devolver_a_borrador('Corrige', 99)
    pregunta.devolver_a_borrador('Corrige', 10)
    assert pregunta.estado == EstadoPregunta.BORRADOR


def test_solo_se_edita_en_borrador_y_se_numeran_versiones():
    pregunta = Pregunta(area_ids=[1])
    assert pregunta.editar_creando_version(CONTENIDO, 1).numero == 1
    assert pregunta.editar_creando_version(CONTENIDO, 1).numero == 2
    pregunta.enviar_a_revision()
    with pytest.raises(ValueError):
        pregunta.editar_creando_version(CONTENIDO, 1)
    pregunta.desactivar()
    with pytest.raises(ValueError):
        pregunta.desactivar()


def test_validar_contenido_exige_dos_alternativas_y_respuesta_registrada():
    with pytest.raises(ValueError, match='dos alternativas'):
        validar_contenido({'enunciado': 'x', 'respuesta': 'A', 'alternativa_A': 'a'})
    with pytest.raises(ValueError, match='correcta'):
        validar_contenido({'enunciado': 'x', 'respuesta': 'C', 'alternativa_A': 'a', 'alternativa_B': 'b'})
    assert validar_contenido({'enunciado': ' x ', 'respuesta': 'b', 'alternativa_A': 'a', 'alternativa_B': 'b'})[:2] == ('x', 'B')


def test_autoria_construye_un_comando_contenido():
    repo = RepositorioFalso(guardar=7)
    datos = MultiDict({'accion': 'enviar', 'enunciado': 'E', 'respuesta': 'A', 'alternativa_A': 'a', 'alternativa_B': 'b',
                       'materia': '1', 'tema': '2', 'examen': '3'})
    datos.setlist('areas', ['2', '2'])
    assert AutoriaPreguntasAppService(repo).guardar(9, datos, {}) == 7
    _, (usuario, contenido), _ = repo.llamadas[0]
    assert usuario == 9
    assert isinstance(contenido, ContenidoPregunta)
    assert contenido.areas == [2]
    assert contenido.enviar
    assert contenido.examen == 3


def test_filtros_de_banco_invalidos():
    servicio = PreguntaAppService(RepositorioFalso())
    with pytest.raises(ValueError, match='Estado'):
        servicio.consultar_banco({'estado': 'X'})
    with pytest.raises(ValueError, match='Filtros'):
        servicio.consultar_banco({'materia': 'x'})
