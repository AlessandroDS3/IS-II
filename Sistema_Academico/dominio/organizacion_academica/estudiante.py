"""Estudiante y reglas de validación de sus datos."""
from dataclasses import dataclass, field
from datetime import date

from dominio.organizacion_academica.asignacion_academica import AsignacionAcademica
from dominio.organizacion_academica.estado_registro import ESTADOS_BASICOS, EstadoRegistro

CAMPOS = ('codigo', 'nombres', 'apellidos', 'dni', 'email', 'telefono')
CAMPOS_OBLIGATORIOS = ('codigo', 'nombres', 'apellidos')
CAMPOS_OPCIONALES = ('dni', 'email', 'telefono')


@dataclass
class Estudiante:
    codigo: str
    nombres: str
    cuenta_id_opcional: int | None = None
    estado: EstadoRegistro = EstadoRegistro.ACTIVO
    asignacion_area: dict | None = None
    asignacion_grupo: dict | None = None
    historial: list = field(default_factory=list)
    id: int | None = None

    @staticmethod
    def validar_datos(datos):
        valores = {campo: str(datos.get(campo) or '').strip() for campo in CAMPOS}
        if not all(valores[campo] for campo in CAMPOS_OBLIGATORIOS):
            raise ValueError('Código, nombres y apellidos son obligatorios.')
        for campo in CAMPOS_OPCIONALES:
            valores[campo] = valores[campo] or None
        return valores

    @staticmethod
    def validar_estado(estado):
        if estado not in ESTADOS_BASICOS:
            raise ValueError('Estado no válido.')
        return estado

    @staticmethod
    def validar_cambio(fecha, area_id, grupo_id):
        try:
            fecha_valida = date.fromisoformat(fecha)
            area_id, grupo_id = int(area_id), int(grupo_id)
        except (TypeError, ValueError):
            raise ValueError('Selecciona una fecha, un área y un grupo válidos.') from None
        if area_id <= 0 or grupo_id <= 0:
            raise ValueError('Selecciona un área y un grupo válidos.')
        if fecha_valida > date.today():
            raise ValueError('La fecha del cambio no puede ser futura.')
        return fecha_valida, area_id, grupo_id

    @property
    def activo(self):
        return self.estado == EstadoRegistro.ACTIVO

    def cambiar_asignacion(self, grupo_id, area_id, fecha):
        """Cierra la asignación vigente y abre una nueva solo si cambia (conserva el historial)."""
        if not self.activo:
            raise ValueError('El estudiante no existe o está inactivo.')
        for atributo, valor in (('asignacion_area', area_id), ('asignacion_grupo', grupo_id)):
            actual = getattr(self, atributo)
            if AsignacionAcademica.requiere_cambio(actual, valor, fecha):
                if actual:
                    self.historial.append(dict(actual, fecha_fin=fecha))
                setattr(self, atributo, {'valor': valor, 'fecha_inicio': fecha})

    def vincular_cuenta(self, cuenta_id):
        if self.cuenta_id_opcional is not None:
            raise ValueError('El estudiante ya tiene una cuenta vinculada.')
        self.cuenta_id_opcional = cuenta_id

    def desactivar(self):
        self.estado = EstadoRegistro.INACTIVO

    def activar(self):
        self.estado = EstadoRegistro.ACTIVO
