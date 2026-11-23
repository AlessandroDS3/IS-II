"""Casos de uso de simulacros y exámenes por área."""
from datetime import date

from dominio.diseno_evaluaciones.estado_examen import ESTADOS_CONFIGURABLES
from dominio.diseno_evaluaciones.i_examen_repositorio import IExamenRepositorio
from dominio.diseno_evaluaciones.i_simulacro_repositorio import ISimulacroRepositorio
from dominio.diseno_evaluaciones.simulacro import validar_nombre

MSG_EXAMEN_INVALIDO = 'Selecciona un examen válido.'
ACCIONES_PREGUNTAS = ('habilitar', 'cerrar')


def _entero_positivo(valor, mensaje):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(mensaje) from None
    if numero <= 0:
        raise ValueError(mensaje)
    return numero


class SimulacroAppService:
    def __init__(self, simulacros: ISimulacroRepositorio, examenes: IExamenRepositorio):
        self.simulacros = simulacros
        self.examenes = examenes

    @staticmethod
    def _validar_areas(valores):
        try:
            areas = [int(valor) for valor in valores]
        except (TypeError, ValueError):
            raise ValueError('Selecciona áreas válidas.') from None
        if not areas or any(area <= 0 for area in areas) or len(set(areas)) != len(areas):
            raise ValueError('Selecciona una o más áreas diferentes.')
        return areas

    def crear_simulacro(self, datos, usuario_id):
        nombre = validar_nombre(datos.get('nombre', ''))
        try:
            fecha = date.fromisoformat(datos.get('fecha', ''))
            ciclo = int(datos.get('ciclo', ''))
        except ValueError:
            raise ValueError('Selecciona un ciclo y una fecha válidos.') from None
        areas = self._validar_areas(datos.get('areas', []))
        if ciclo <= 0:
            raise ValueError('Selecciona un ciclo válido.')
        self.simulacros.crear_simulacro({'nombre': nombre, 'fecha': fecha, 'ciclo': ciclo, 'areas': areas}, usuario_id)

    def agregar_areas(self, simulacro, valores, usuario_id):
        simulacro = _entero_positivo(simulacro, MSG_EXAMEN_INVALIDO)
        self.simulacros.agregar_areas(simulacro, self._validar_areas(valores), usuario_id)

    def crear_examen(self, datos, usuario_id):
        nombre = validar_nombre(datos.get('nombre', ''))
        try:
            fecha = date.fromisoformat(datos.get('fecha', ''))
            simulacro = int(datos.get('simulacro', ''))
            area = int(datos.get('area', ''))
        except ValueError:
            raise ValueError('Selecciona simulacro, área y fecha válidos.') from None
        self.examenes.crear_examen({'nombre': nombre, 'fecha': fecha, 'simulacro': simulacro, 'area': area}, usuario_id)

    def listar(self):
        return self.simulacros.simulacros()

    def contexto_examen(self, examen):
        return self.examenes.contexto_examen(examen)

    def abrir_aplicacion(self, simulacro, examen=0):
        return self.examenes.abrir_aplicacion(simulacro, examen)

    def resumen_examen(self, examen):
        return self.examenes.resumen_examen(examen)

    def habilitar_preguntas(self, examen, accion):
        try:
            examen = int(examen)
        except (TypeError, ValueError):
            raise ValueError(MSG_EXAMEN_INVALIDO) from None
        if examen <= 0 or accion not in ACCIONES_PREGUNTAS:
            raise ValueError('Acción no válida.')
        self.examenes.habilitar_preguntas(examen, accion == 'habilitar')

    @staticmethod
    def siguiente_etapa(contexto, resumen):
        """Decide la etapa del flujo del examen que el coordinador debe atender a continuación."""
        if resumen['preguntas_revision']:
            return 'banco_preguntas', 'Revisar preguntas pendientes'
        if contexto['estado'] in ESTADOS_CONFIGURABLES:
            return 'configurar_examen', 'Preparar configuración y clave'
        if resumen['cargas_pendientes']:
            return 'cartillas', 'Resolver cargas pendientes'
        if resumen['cartillas_revision']:
            return 'lecturas', 'Revisar lecturas'
        if resumen['cartillas'] > resumen['resultados'] or resumen['calculos_revision'] or resumen['por_publicar']:
            return 'resultados_coordinador', 'Revisar resultados y publicación'
        if resumen['publicado']:
            return 'reportes', 'Consultar resultados publicados'
        return 'cartillas', 'Cargar cartillas'
