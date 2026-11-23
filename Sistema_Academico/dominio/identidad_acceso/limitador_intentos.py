"""Bloqueo temporal tras varios intentos de inicio de sesión fallidos para un mismo usuario."""
import time


class LimitadorIntentos:
    def __init__(self, max_intentos=5, ventana_segundos=300, reloj=time.monotonic):
        self.max_intentos = max_intentos
        self.ventana = ventana_segundos
        self.reloj = reloj
        self._fallos = {}

    def _recientes(self, usuario):
        limite = self.reloj() - self.ventana
        fallos = [t for t in self._fallos.get(usuario, []) if t > limite]
        self._fallos[usuario] = fallos
        return fallos

    def bloqueado(self, usuario):
        return len(self._recientes(usuario)) >= self.max_intentos

    def registrar_fallo(self, usuario):
        self._recientes(usuario).append(self.reloj())

    def reiniciar(self, usuario):
        self._fallos.pop(usuario, None)
