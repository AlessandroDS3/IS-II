"""Utilidades compartidas por los repositorios basados en SQLAlchemy Core."""
from sqlalchemy import text

SQL_EXAMENES_CON_AREA = 'SELECT e.id_examen,e.nombre,a.nombre AS area FROM examenes e JOIN areas a ON a.id_area=e.id_area ORDER BY e.id_examen DESC'


class RepositorioSQL:
    """Base con el motor y consultas de solo lectura reutilizables."""

    def __init__(self, motor):
        self.motor = motor

    def _consultar(self, sql, parametros=None):
        with self.motor.connect() as conexion:
            return conexion.execute(text(sql), parametros or {}).mappings().all()

    def examenes(self):
        """Exámenes con el nombre de su área, del más reciente al más antiguo."""
        return self._consultar(SQL_EXAMENES_CON_AREA)
