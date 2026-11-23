"""Página recibida en una importación de cartillas, antes de registrarse como cartilla."""
from dataclasses import dataclass
from datetime import datetime

from dominio.evaluacion.estado_entrada import EstadoEntrada


@dataclass
class EntradaImportacion:
    archivo_fuente: str
    huella_contenido: str
    pagina_opcional: int | None = None
    estado: EstadoEntrada = EstadoEntrada.PENDIENTE
    error_opcional: str | None = None
    motivo_resolucion_opcional: str | None = None
    resuelta_por_opcional: int | None = None
    resuelta_en_opcional: datetime | None = None
    sustituida_por_entrada_id_opcional: int | None = None
    estudiante_identificado_id_opcional: int | None = None
    cuadernillo_identificado_id_opcional: int | None = None
    cartilla_registrada_id_opcional: int | None = None
    id: int | None = None
