"""Validación compartida de imágenes recibidas (extensión y decodificación real con OpenCV)."""
from pathlib import Path

import cv2
import numpy as np

EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png')
FIRMA_PNG = b'\x89PNG'
FIRMA_JPEG = b'\xff\xd8'


def tiene_extension_imagen(nombre):
    return Path(nombre).suffix.lower() in EXTENSIONES_IMAGEN


def decodificar(contenido, modo=cv2.IMREAD_COLOR):
    """Devuelve la imagen decodificada o None si el contenido no es una imagen legible."""
    return cv2.imdecode(np.frombuffer(contenido, dtype=np.uint8), modo)


def tipo_mime_por_firma(cabecera):
    """Tipo MIME según los primeros bytes del archivo, o None si no es PNG ni JPEG."""
    if cabecera.startswith(FIRMA_PNG):
        return 'image/png'
    if cabecera.startswith(FIRMA_JPEG):
        return 'image/jpeg'
    return None
