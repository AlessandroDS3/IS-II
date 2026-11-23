"""Agregado ImportacionCartillas: lote de páginas recibidas para un examen."""
from dataclasses import dataclass, field
from datetime import datetime

from dominio.evaluacion.entrada_importacion import EntradaImportacion
from dominio.evaluacion.estado_entrada import ESTADOS_DESCARTABLES, ESTADOS_REINTENTABLES, EstadoEntrada


@dataclass
class ImportacionCartillas:
    examen_destino_id: int
    operacion_id: str
    responsable_id: int
    entradas: dict = field(default_factory=dict)
    creada_en: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def _entrada(self, entrada_id):
        entrada = self.entradas.get(entrada_id)
        if entrada is None:
            raise ValueError('La entrada no existe.')
        return entrada

    def agregar_entrada(self, fuente, pagina, huella=None, entrada_id=None):
        """Registra una página; el mismo contenido no se conserva dos veces en el examen (devuelve None)."""
        huella = huella or fuente
        if any(e.huella_contenido == huella and e.estado != EstadoEntrada.DESCARTADA for e in self.entradas.values()):
            return None
        entrada = EntradaImportacion(archivo_fuente=fuente, huella_contenido=huella, pagina_opcional=pagina, id=entrada_id)
        self.entradas[entrada_id if entrada_id is not None else len(self.entradas) + 1] = entrada
        return entrada

    def resolver_identificacion(self, entrada_id, estudiante_id, cuadernillo_id):
        entrada = self._entrada(entrada_id)
        if entrada.estado != EstadoEntrada.REVISAR:
            raise ValueError('La entrada no está disponible para identificar.')
        if entrada.estudiante_identificado_id_opcional is not None or entrada.cuadernillo_identificado_id_opcional is not None:
            raise ValueError('La identificación ya fue guardada; su rectificación requiere un proceso con historial.')
        entrada.estudiante_identificado_id_opcional = estudiante_id
        entrada.cuadernillo_identificado_id_opcional = cuadernillo_id

    def _preparar_reintento(self, entrada_id):
        entrada = self._entrada(entrada_id)
        if entrada.estado not in ESTADOS_REINTENTABLES or entrada.cartilla_registrada_id_opcional:
            raise ValueError('Solo puedes reintentar o reemplazar una entrada que aún no originó una cartilla.')
        return entrada

    @staticmethod
    def _reiniciar(entrada):
        entrada.estado = EstadoEntrada.PENDIENTE
        entrada.error_opcional = None
        entrada.estudiante_identificado_id_opcional = None
        entrada.cuadernillo_identificado_id_opcional = None

    def reintentar_entrada(self, entrada_id, operacion_id):
        entrada = self._preparar_reintento(entrada_id)
        if not entrada.pagina_opcional or entrada.pagina_opcional <= 0:
            raise ValueError('Este archivo no pudo convertirse a imagen. Adjunta una imagen legible de reemplazo.')
        self.operacion_id = operacion_id
        self._reiniciar(entrada)

    def aportar_reemplazo_legible(self, entrada_id, archivo):
        entrada = self._preparar_reintento(entrada_id)
        if any(e is not entrada and e.huella_contenido == archivo['huella'] and e.estado != EstadoEntrada.DESCARTADA
               for e in self.entradas.values()):
            raise ValueError('Esta imagen ya está cargada en el mismo examen.')
        entrada.archivo_fuente = archivo['ruta']
        entrada.huella_contenido = archivo['huella']
        entrada.pagina_opcional = 1
        self._reiniciar(entrada)

    def descartar_entrada(self, entrada_id, motivo, responsable_id):
        motivo = (motivo or '').strip()
        if not motivo:
            raise ValueError('Indica el motivo del descarte.')
        entrada = self._entrada(entrada_id)
        if entrada.estado not in ESTADOS_DESCARTABLES:
            raise ValueError('La entrada no existe o ya fue descartada.')
        entrada.estado = EstadoEntrada.DESCARTADA
        entrada.motivo_resolucion_opcional = motivo
        entrada.resuelta_por_opcional = responsable_id
        entrada.resuelta_en_opcional = datetime.now()
