"""Persistencia de exámenes: contexto de trabajo, resumen de avance y habilitación de preguntas."""
from sqlalchemy import text

from dominio.diseno_evaluaciones.estado_examen import ESTADOS_CONFIGURABLES
from dominio.diseno_evaluaciones.estado_simulacro import EstadoSimulacro
from infraestructura.persistencia.repositories.simulacro_orm_repositorio import SQL_INSERTAR_EXAMEN


class ExamenORMRepositorio:
    """Implementa IExamenRepositorio."""

    def __init__(self, motor):
        self.motor = motor

    def contexto_examen(self, examen):
        with self.motor.connect() as c:
            fila = c.execute(text('''SELECT e.id_examen,e.id_simulacro,e.id_area,e.estado,e.admite_preguntas,
                a.nombre area,s.nombre nombre,s.fecha,cp.nombre ciclo,s.estado estado_aplicacion
                FROM examenes e JOIN simulacros s ON s.id_simulacro=e.id_simulacro
                JOIN areas a ON a.id_area=e.id_area JOIN ciclos_preparacion cp ON cp.id_ciclo=s.id_ciclo
                WHERE e.id_examen=:id'''), {'id': examen}).mappings().first()
            if not fila:
                return None
            areas = c.execute(text('''SELECT e.id_examen,a.nombre area FROM examenes e
                JOIN areas a ON a.id_area=e.id_area WHERE e.id_simulacro=:id ORDER BY a.nombre'''), {'id': fila['id_simulacro']}).mappings().all()
            return dict(fila, areas=areas)

    def abrir_aplicacion(self, simulacro, examen=0):
        with self.motor.connect() as c:
            ids = c.execute(text('SELECT id_examen FROM examenes WHERE id_simulacro=:id ORDER BY id_examen'), {'id': simulacro}).scalars().all()
        if not ids or (examen and examen not in ids):
            return None
        return self.contexto_examen(examen or ids[0])

    def resumen_examen(self, examen):
        with self.motor.connect() as c:
            return dict(c.execute(text('''SELECT
                (SELECT COUNT(*) FROM preguntas p WHERE p.id_examen_destino=:id AND p.estado='REVISION') preguntas_revision,
                (SELECT COUNT(*) FROM versiones_examen WHERE id_examen=:id AND estado='ACTIVA') versiones,
                (SELECT COUNT(*) FROM cargas_omr WHERE examen_id=:id AND estado IN ('PENDIENTE','REVISAR','ERROR')) cargas_pendientes,
                (SELECT COUNT(*) FROM cartillas WHERE id_examen=:id AND vigente=1) cartillas,
                (SELECT COUNT(*) FROM cartillas WHERE id_examen=:id AND vigente=1 AND estado NOT IN ('VALIDADA','ANULADA')) cartillas_revision,
                (SELECT COUNT(*) FROM resultados_examen r JOIN cartillas ca ON ca.id_cartilla=r.id_cartilla
                    WHERE r.id_examen=:id AND r.vigente=1 AND ca.vigente=1) resultados,
                (SELECT COUNT(*) FROM resultados_examen r JOIN cartillas ca ON ca.id_cartilla=r.id_cartilla
                    WHERE r.id_examen=:id AND r.vigente=1 AND ca.vigente=1 AND r.estado='CALCULADO') calculos_revision,
                (SELECT COUNT(*) FROM resultados_examen r JOIN cartillas ca ON ca.id_cartilla=r.id_cartilla
                    WHERE r.id_examen=:id AND r.vigente=1 AND ca.vigente=1 AND r.estado='REVISADO') por_publicar,
                (SELECT COUNT(*) FROM publicaciones_examen WHERE id_examen=:id AND vigente=1) publicado
                '''), {'id': examen}).mappings().one())

    def crear_examen(self, datos, usuario_id):
        with self.motor.begin() as c:
            if not c.execute(text("SELECT id_simulacro FROM simulacros WHERE id_simulacro=:id AND estado='ABIERTO' FOR UPDATE"), {'id': datos['simulacro']}).scalar_one_or_none():
                raise ValueError('El simulacro no está abierto.')
            if not c.execute(text("SELECT id_area FROM areas WHERE id_area=:id AND estado='ACTIVO' FOR UPDATE"), {'id': datos['area']}).scalar_one_or_none():
                raise ValueError('El área no está activa.')
            c.execute(SQL_INSERTAR_EXAMEN, {**datos, 'usuario': usuario_id})

    def habilitar_preguntas(self, examen, habilitar):
        with self.motor.begin() as c:
            fila = c.execute(text("SELECT e.estado,s.estado simulacro FROM examenes e JOIN simulacros s ON s.id_simulacro=e.id_simulacro WHERE e.id_examen=:id FOR UPDATE"), {'id': examen}).mappings().first()
            if not fila:
                raise ValueError('El examen no existe.')
            if habilitar and (fila['estado'] not in ESTADOS_CONFIGURABLES or fila['simulacro'] != EstadoSimulacro.ABIERTO):
                raise ValueError('Solo se puede habilitar un examen en configuración de un simulacro abierto.')
            c.execute(text('UPDATE examenes SET admite_preguntas=:habilitar WHERE id_examen=:id'), {'habilitar': habilitar, 'id': examen})
