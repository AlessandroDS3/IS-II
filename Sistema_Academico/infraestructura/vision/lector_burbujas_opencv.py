"""Adaptador del puerto ILectorCartillas sobre el motor ADDISON OMR."""
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from infraestructura.vision.addison_omr import RECURSOS_PLANTILLA, VERSION, procesar

CARPETA_PLANTILLA = Path(__file__).parent / 'addison_omr'


class LectorBurbujasOpenCV:
    """Implementa ILectorCartillas. La confianza del lector es cualitativa, no porcentual."""

    version_algoritmo = f'ADDISON OMR {VERSION}'

    def leer(self, imagen_ref, plantilla_ref=None):
        imagen = Path(imagen_ref).resolve(strict=True)
        plantilla = Path(plantilla_ref).resolve(strict=True) if plantilla_ref else CARPETA_PLANTILLA
        if not imagen.is_file() or not plantilla.is_dir():
            raise ValueError('La imagen o la carpeta de plantilla no son válidas.')

        # El motor escribe imágenes intermedias en su carpeta de trabajo.
        # Cada lectura recibe una copia aislada para evitar colisiones entre cargas.
        with TemporaryDirectory(prefix='addison_omr_') as temporal:
            trabajo = Path(temporal)
            for nombre in RECURSOS_PLANTILLA:
                origen = plantilla / nombre
                if not origen.is_file():
                    raise FileNotFoundError(f'Falta el recurso de plantilla: {nombre}')
                copy2(origen, trabajo / nombre)
            resultado = procesar(imagen, trabajo, salida=trabajo / 'lectura', alineacion=True, alineacion_local=True)
            if resultado.get('exito') is False:
                return {'exito': False, 'version_lector': self.version_algoritmo, 'error': resultado.get('error', 'Lectura rechazada'), 'detalle': resultado}
            return {
                'exito': True,
                'version_lector': self.version_algoritmo,
                'dni': resultado.get('dni'),
                'controles': resultado.get('controles', {}),
                'respuestas': resultado.get('respuestas', []),
                'resumen': resultado.get('resumen', {}),
                'detalle': resultado,
            }
