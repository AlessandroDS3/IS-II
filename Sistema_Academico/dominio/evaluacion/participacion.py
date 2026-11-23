"""Agregado Participacion: un estudiante rinde un único examen por simulacro con una cartilla vigente."""
from dataclasses import dataclass, field

from dominio.evaluacion.cartilla import Cartilla
from dominio.evaluacion.lectura_cartilla import LecturaCartilla
from dominio.evaluacion.estado_lectura import EstadoLectura


@dataclass
class Participacion:
    estudiante_id: int
    simulacro_id: int
    examen_id: int
    cartillas: list = field(default_factory=list)
    lecturas: list = field(default_factory=list)
    id: int | None = None

    @staticmethod
    def exigir_mismo_examen(examen_participacion, examen_entrada):
        if examen_participacion != examen_entrada:
            raise ValueError('El estudiante ya participa en otra área del simulacro.')

    @staticmethod
    def exigir_motivo_reemplazo(hay_cartilla_anterior, motivo):
        if hay_cartilla_anterior and not motivo:
            raise ValueError('Para reemplazar una cartilla existente debes indicar el motivo.')

    @property
    def cartilla_vigente(self):
        return next((c for c in reversed(self.cartillas) if c.vigente), None)

    def validar_simulacro_del_examen(self, simulacro_examen_id):
        if simulacro_examen_id != self.simulacro_id:
            raise ValueError('El examen no pertenece al simulacro de la participación.')

    def recibir_cartilla(self, imagen, cuadernillo_id, recibida_por=None):
        if self.cartilla_vigente:
            raise ValueError('Para reemplazar una cartilla existente debes indicar el motivo.')
        return self._agregar(Cartilla(numero_recepcion=1, cuadernillo_id=cuadernillo_id, imagen=imagen, recibida_por=recibida_por))

    def reemplazar_cartilla(self, imagen, cuadernillo_id, motivo, recibida_por=None):
        anterior = self.cartilla_vigente
        self.exigir_motivo_reemplazo(anterior is not None, (motivo or '').strip())
        numero = self.cartillas[-1].numero_recepcion + 1 if self.cartillas else 1
        if anterior:
            anterior.vigente = False
        cartilla = Cartilla(numero_recepcion=numero, cuadernillo_id=cuadernillo_id, imagen=imagen, recibida_por=recibida_por,
                            motivo_reemplazo_opcional=motivo, cartilla_origen_id_opcional=anterior.id if anterior else None)
        return self._agregar(cartilla)

    def _agregar(self, cartilla):
        self.cartillas.append(cartilla)
        return cartilla

    def registrar_lectura(self, cartilla_id):
        vigente = self.cartilla_vigente
        if not vigente or vigente.id != cartilla_id:
            raise ValueError('Solo se registran lecturas de la cartilla vigente.')
        lectura = LecturaCartilla(cartilla_id=cartilla_id)
        self.lecturas.append(lectura)
        return lectura

    def confirmar_lectura(self, lectura_id):
        lectura = next((x for x in self.lecturas if x.id == lectura_id), None)
        if lectura is None:
            raise ValueError('La lectura no existe.')
        lectura.estado = EstadoLectura.EXITOSO
        vigente = self.cartilla_vigente
        if vigente and vigente.id == lectura.cartilla_id:
            vigente.lectura_confirmada_id_opcional = lectura_id
        return lectura

    def invalidar_cartilla(self, cartilla_id, rectificacion_id):
        cartilla = next((c for c in self.cartillas if c.id == cartilla_id), None)
        if cartilla is None or not cartilla.vigente:
            raise ValueError('La cartilla no está vigente.')
        cartilla.vigente = False
        cartilla.invalidada_por_rectificacion_id_opcional = rectificacion_id
