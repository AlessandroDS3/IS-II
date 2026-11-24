"""Agregado PublicacionExamen: versión vigente de los resultados publicados de un examen."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from dominio.publicacion_ranking.clasificador_ranking import ClasificadorRanking


@dataclass
class PublicacionExamen:
    examen_id: int
    simulacro_id: int | None = None
    area_id: int | None = None
    ciclo_id: int | None = None
    fecha_aplicacion: datetime | None = None
    puntaje_maximo: Decimal | None = None
    responsable_id: int | None = None
    version_publicacion: int = 0
    entradas: list = field(default_factory=list)
    publicada_en: datetime | None = None
    motivo: str | None = None
    rectificacion_id_opcional: int | None = None
    id: int | None = None

    def actualizar_resultados_vigentes(self, resultados, publicada_en, motivo):
        """Publica una nueva versión del ranking; republicar exige indicar el motivo."""
        if not resultados:
            raise ValueError('Todas las cartillas vigentes requieren resultado validado.')
        if self.version_publicacion and not (motivo or '').strip():
            raise ValueError('Indica el motivo para actualizar una publicación existente.')
        self.entradas = ClasificadorRanking().clasificar(resultados)
        self.version_publicacion += 1
        self.publicada_en = publicada_en
        self.motivo = motivo
        return self.entradas
