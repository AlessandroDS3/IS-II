"""Persistencia de simulacros y de sus exámenes por área."""
from sqlalchemy import bindparam, text

from dominio.diseno_evaluaciones.estado_simulacro import EstadoSimulacro

SQL_INSERTAR_EXAMEN = text("INSERT INTO examenes(id_simulacro,id_area,nombre,fecha_programada,creado_por) VALUES (:simulacro,:area,:nombre,:fecha,:usuario)")


class SimulacroORMRepositorio:
    """Implementa ISimulacroRepositorio."""

    def __init__(self, motor):
        self.motor = motor

    def simulacros(self):
        with self.motor.connect() as c:
            sims = c.execute(text("SELECT s.id_simulacro,s.nombre,s.fecha,s.estado,c.nombre AS ciclo FROM simulacros s JOIN ciclos_preparacion c ON c.id_ciclo=s.id_ciclo ORDER BY s.fecha DESC,s.id_simulacro DESC")).mappings().all()
            examenes = c.execute(text("SELECT e.id_examen,e.id_simulacro,e.nombre,e.estado,e.admite_preguntas,a.nombre AS area FROM examenes e JOIN areas a ON a.id_area=e.id_area ORDER BY e.nombre")).mappings().all()
            ciclos = c.execute(text("SELECT id_ciclo,nombre FROM ciclos_preparacion WHERE estado='ACTIVO' ORDER BY nombre")).mappings().all()
            areas = c.execute(text("SELECT id_area,nombre FROM areas WHERE estado='ACTIVO' ORDER BY nombre")).mappings().all()
            return sims, examenes, ciclos, areas

    def crear_simulacro(self, datos, usuario_id):
        with self.motor.begin() as c:
            if not c.execute(text("SELECT id_ciclo FROM ciclos_preparacion WHERE id_ciclo=:id AND estado='ACTIVO' FOR UPDATE"), {'id': datos['ciclo']}).scalar_one_or_none():
                raise ValueError('El ciclo seleccionado no está activo.')
            self._validar_areas(c, datos['areas'])
            simulacro = c.execute(text("INSERT INTO simulacros(id_ciclo,nombre,fecha,creado_por) VALUES (:ciclo,:nombre,:fecha,:usuario)"), {**datos, 'usuario': usuario_id}).lastrowid
            self._insertar_examenes(c, simulacro, datos['nombre'], datos['fecha'], datos['areas'], usuario_id)

    def agregar_areas(self, simulacro, areas, usuario_id):
        with self.motor.begin() as c:
            evento = c.execute(text("SELECT nombre,fecha,estado FROM simulacros WHERE id_simulacro=:id FOR UPDATE"), {'id': simulacro}).mappings().first()
            if not evento or evento['estado'] != EstadoSimulacro.ABIERTO:
                raise ValueError('El examen no existe o está cerrado.')
            self._validar_areas(c, areas)
            existentes = set(c.execute(text('SELECT id_area FROM examenes WHERE id_simulacro=:id'), {'id': simulacro}).scalars())
            if existentes.intersection(areas):
                raise ValueError('Una de las áreas seleccionadas ya pertenece a este examen.')
            self._insertar_examenes(c, simulacro, evento['nombre'], evento['fecha'], areas, usuario_id)

    @staticmethod
    def _validar_areas(c, areas):
        consulta = text("SELECT id_area FROM areas WHERE id_area IN :ids AND estado='ACTIVO' FOR UPDATE").bindparams(bindparam('ids', expanding=True))
        if set(c.execute(consulta, {'ids': areas}).scalars()) != set(areas):
            raise ValueError('Todas las áreas seleccionadas deben estar activas.')

    @staticmethod
    def _insertar_examenes(c, simulacro, nombre, fecha, areas, usuario):
        for area in areas:
            c.execute(SQL_INSERTAR_EXAMEN, {'simulacro': simulacro, 'area': area, 'nombre': nombre, 'fecha': fecha, 'usuario': usuario})
