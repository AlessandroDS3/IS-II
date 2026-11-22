"""Normaliza imágenes de preguntas a PNG para no conservar archivos que no sean imágenes."""
import uuid
from pathlib import Path

import cv2

from infraestructura.archivos import validador_imagenes


class ImagenesPreguntas:
    MAX_BYTES = 2 * 1024 * 1024
    MAX_PIXELES = 16000000
    BYTES_POR_KB = 1024

    def __init__(self, directorio):
        self.directorio = Path(directorio).resolve()
        self.directorio.mkdir(parents=True, exist_ok=True)

    def guardar(self, archivo):
        contenido = archivo.read(self.MAX_BYTES + 1)
        if not contenido or len(contenido) > self.MAX_BYTES:
            raise ValueError('Cada imagen debe contener datos y pesar como máximo 2 MB.')
        if not validador_imagenes.tiene_extension_imagen(archivo.filename):
            raise ValueError('Solo se aceptan imágenes JPG o PNG.')
        imagen = validador_imagenes.decodificar(contenido)
        if imagen is None or imagen.shape[0] * imagen.shape[1] > self.MAX_PIXELES:
            raise ValueError('La imagen no es válida o supera las dimensiones permitidas.')
        exito, png = cv2.imencode('.png', imagen)
        if not exito:
            raise ValueError('No se pudo preparar la imagen.')
        ruta = self.directorio / (uuid.uuid4().hex + '.png')
        ruta.write_bytes(png.tobytes())
        return str(ruta), len(png) // self.BYTES_POR_KB
