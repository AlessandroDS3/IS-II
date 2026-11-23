"""Conjunto que fija la clave y la política de puntaje con que se califica un examen."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConjuntoCalificacion:
    examen_id: int
    clave_id: int | None = None
    politica_id: int | None = None
    confirmado_por: int | None = None
    confirmado_en: datetime | None = None
    id: int | None = None

    def validar_claves_y_politica(self):
        if not self.clave_id:
            raise ValueError('Todas las cartillas necesitan una clave confirmada y lectura validada.')
        if not self.politica_id:
            raise ValueError('Falta una política de puntaje confirmada.')
        return True
