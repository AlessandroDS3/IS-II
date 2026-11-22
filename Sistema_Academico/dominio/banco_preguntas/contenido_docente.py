"""Reglas de integridad para el contenido que registra el docente."""
from dataclasses import dataclass, field

from dominio.banco_preguntas.letra import LETRAS

MAX_ENUNCIADO = 20000
MAX_ALTERNATIVA = 10000
MIN_ALTERNATIVAS = 2


def validar_contenido(datos):
    enunciado = (datos.get('enunciado') or '').strip()
    respuesta = (datos.get('respuesta') or '').strip().upper()
    alternativas = {letra: (datos.get('alternativa_' + letra) or '').strip() for letra in LETRAS}
    if not enunciado or len(enunciado) > MAX_ENUNCIADO:
        raise ValueError('Escribe un enunciado de hasta 20 000 caracteres.')
    if any(len(valor) > MAX_ALTERNATIVA for valor in alternativas.values()):
        raise ValueError('Cada alternativa admite hasta 10 000 caracteres.')
    if sum(bool(valor) for valor in alternativas.values()) < MIN_ALTERNATIVAS:
        raise ValueError('Registra al menos dos alternativas con texto.')
    if respuesta not in alternativas or not alternativas[respuesta]:
        raise ValueError('Selecciona como correcta una alternativa registrada.')
    return enunciado, respuesta, alternativas


@dataclass(frozen=True)
class ContenidoPregunta:
    """Comando con los datos para guardar una pregunta (sustituye la lista de 13 parámetros)."""
    pregunta: int | None
    version: int
    materia: int
    tema: int
    areas: list
    enunciado: str
    respuesta: str
    alternativas: dict
    imagenes: dict = field(default_factory=dict)
    enviar: bool = False
    examen: int = 0
    tema_nuevo: str = ''
