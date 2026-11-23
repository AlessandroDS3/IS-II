"""Casos de uso del coordinador para revisar lecturas, validar cartillas y revisar resultados."""
from dominio.banco_preguntas.letra import LETRAS
from dominio.evaluacion.estado_respuesta import EstadoRespuesta
from dominio.evaluacion.i_revision_lecturas_repositorio import IRevisionLecturasRepositorio

RESOLUCIONES = tuple(r.value for r in EstadoRespuesta)


class RevisionLecturasAppService:
    def __init__(self, repositorio: IRevisionLecturasRepositorio):
        self.repositorio = repositorio

    def corregir(self, respuesta, resolucion, marca, motivo, usuario):
        motivo = (motivo or '').strip()
        marca = (marca or '').strip().upper()
        if resolucion not in RESOLUCIONES:
            raise ValueError('Selecciona una resolución válida.')
        es_marca_unica = resolucion == EstadoRespuesta.MARCA_UNICA
        if es_marca_unica and marca not in LETRAS:
            raise ValueError('Selecciona una respuesta de A a E.')
        if not motivo:
            raise ValueError('Indica el motivo de la corrección.')
        self.repositorio.corregir(respuesta, resolucion, marca if es_marca_unica else None, motivo, usuario)

    def examenes(self):
        return self.repositorio.examenes()

    def lecturas(self, examen):
        return self.repositorio.lecturas(examen)

    def historial_lecturas(self, examen):
        return self.repositorio.historial_lecturas(examen)

    def validar_cartilla(self, cartilla):
        return self.repositorio.validar_cartilla(cartilla)

    def imagen_cartilla(self, cartilla):
        return self.repositorio.imagen_cartilla(cartilla)

    def resultados(self, examen):
        return self.repositorio.resultados(examen)

    def resultado(self, examen, resultado):
        return self.repositorio.resultado(examen, resultado)

    def detalle_coordinador(self, resultado):
        return self.repositorio.detalle_coordinador(resultado)

    def revisar_resultado(self, resultado, usuario):
        return self.repositorio.revisar_resultado(resultado, usuario)
