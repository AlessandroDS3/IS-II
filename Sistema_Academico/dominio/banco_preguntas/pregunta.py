"""Agregado Pregunta: ciclo de vida BORRADOR -> REVISION -> APROBADA/BORRADOR -> INACTIVA."""
from dataclasses import dataclass, field

from dominio.banco_preguntas.estado_pregunta import EstadoPregunta
from dominio.banco_preguntas.revision_pregunta import RevisionPregunta
from dominio.banco_preguntas.version_pregunta import VersionPregunta

ACCION_APROBAR = 'aprobar'
ACCION_DEVOLVER = 'devolver'
MENSAJE_VERSION_CAMBIADA = 'La pregunta o su versión cambió; vuelve a consultar antes de revisarla.'


@dataclass
class Pregunta:
    autor_id: int | None = None
    materia_id: int | None = None
    area_ids: list[int] = field(default_factory=list)
    estado: EstadoPregunta = EstadoPregunta.BORRADOR
    version_activa_id: int | None = None
    versiones: list[VersionPregunta] = field(default_factory=list)
    id: int | None = None

    @staticmethod
    def validar_revision(accion, observacion):
        if accion not in (ACCION_APROBAR, ACCION_DEVOLVER):
            raise ValueError('Acción de revisión no válida.')
        observacion = (observacion or '').strip()
        if accion == ACCION_DEVOLVER and not observacion:
            raise ValueError('Indica una observación para devolver la pregunta.')
        return accion == ACCION_APROBAR, observacion

    @property
    def version_activa(self):
        return self.versiones[-1] if self.versiones else None

    def _exigir_estado(self, estado, mensaje):
        if self.estado != estado:
            raise ValueError(mensaje)

    def _exigir_version_vista(self, version_vista_id):
        if version_vista_id != self.version_activa_id:
            raise ValueError(MENSAJE_VERSION_CAMBIADA)

    def editar_creando_version(self, contenido, responsable_id):
        """Crea una versión nueva; solo se editan preguntas en borrador."""
        self._exigir_estado(EstadoPregunta.BORRADOR, 'La pregunta no es editable o cambió; vuelve a abrirla.')
        numero = self.version_activa.numero + 1 if self.version_activa else 1
        version = VersionPregunta(numero=numero, enunciado=contenido['enunciado'],
                                  alternativa_correcta=contenido['respuesta'], creada_por=responsable_id,
                                  tema=contenido.get('tema'), id=contenido.get('id'))
        self.versiones.append(version)
        self.version_activa_id = version.id
        return version

    def enviar_a_revision(self):
        self._exigir_estado(EstadoPregunta.BORRADOR, 'Solo se envían a revisión preguntas en borrador.')
        if not self.area_ids or not self.version_activa:
            raise ValueError('La pregunta necesita una versión y al menos un área.')
        self.version_activa.sellar()
        self.estado = EstadoPregunta.REVISION

    def aprobar_inicialmente(self, coordinador_id, version_vista_id):
        self._exigir_estado(EstadoPregunta.REVISION, MENSAJE_VERSION_CAMBIADA)
        self._exigir_version_vista(version_vista_id)
        self.estado = EstadoPregunta.APROBADA
        return RevisionPregunta(version_vista_id, coordinador_id, EstadoPregunta.APROBADA)

    def devolver_a_borrador(self, motivo, version_vista_id, responsable_id=None):
        _, motivo = self.validar_revision(ACCION_DEVOLVER, motivo)
        self._exigir_estado(EstadoPregunta.REVISION, MENSAJE_VERSION_CAMBIADA)
        self._exigir_version_vista(version_vista_id)
        self.estado = EstadoPregunta.BORRADOR
        return RevisionPregunta(version_vista_id, responsable_id, EstadoPregunta.BORRADOR, motivo)

    def desactivar(self):
        if self.estado == EstadoPregunta.INACTIVA:
            raise ValueError('La pregunta ya está inactiva.')
        self.estado = EstadoPregunta.INACTIVA

    def es_elegible_para_area(self, area_id):
        return self.estado == EstadoPregunta.APROBADA and area_id in self.area_ids
