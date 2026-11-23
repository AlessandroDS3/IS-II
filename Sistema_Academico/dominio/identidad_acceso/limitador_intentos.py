"""Límite por usuario y proceso: los fallos se pierden al reiniciar la aplicación."""
import time
from threading import Lock


class LimitadorIntentos:
    def __init__(self, max_intentos=5, ventana_segundos=300, reloj=time.monotonic):
        self.max_intentos = max_intentos
        self.ventana = ventana_segundos
        self.reloj = reloj
        self._fallos = {}
        self._bloqueo = Lock()

    def _recientes(self, usuario):
        limite = self.reloj() - self.ventana
        fallos = [t for t in self._fallos.get(usuario, []) if t > limite]
        if fallos:
            self._fallos[usuario] = fallos
        else:
            self._fallos.pop(usuario, None)
        return fallos

    def bloqueado(self, usuario):
        with self._bloqueo:
            return len(self._recientes(usuario)) >= self.max_intentos

    def registrar_fallo(self, usuario):
        with self._bloqueo:
            fallos = self._recientes(usuario)
            fallos.append(self.reloj())
            self._fallos[usuario] = fallos[-self.max_intentos:]

    def reiniciar(self, usuario):
        with self._bloqueo:
            self._fallos.pop(usuario, None)
