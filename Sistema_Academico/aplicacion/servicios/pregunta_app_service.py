"""Casos de uso del coordinador sobre el banco de preguntas."""
from dominio.banco_preguntas.estado_pregunta import EstadoPregunta
from dominio.banco_preguntas.i_pregunta_repositorio import IPreguntaRepositorio
from dominio.banco_preguntas.pregunta import Pregunta

ESTADOS_FILTRO = ('',) + tuple(estado.value for estado in EstadoPregunta)


def validar_estado_filtro(estado):
    if estado not in ESTADOS_FILTRO:
        raise ValueError('Estado no válido.')
    return estado


class PreguntaAppService:
    def __init__(self, repositorio: IPreguntaRepositorio):
        self.repositorio = repositorio

    def revisar_pregunta(self, pregunta_id, version_vista_id, accion, observacion, usuario_id):
        aprobar, observacion = Pregunta.validar_revision(accion, observacion)
        self.repositorio.revisar(pregunta_id, version_vista_id, aprobar, observacion, usuario_id)

    def consultar_banco(self, filtros):
        estado = validar_estado_filtro(filtros.get('estado', ''))
        try:
            materia = int(filtros.get('materia') or 0)
            area = int(filtros.get('area') or 0)
            eje = int(filtros.get('eje') or 0)
            examen = int(filtros.get('examen') or 0)
        except ValueError:
            raise ValueError('Filtros no válidos.') from None
        return self.repositorio.preguntas(estado, materia, area, eje, examen)
