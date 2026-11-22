"""Consulta de los pendientes que el coordinador debe atender."""
from aplicacion.puertos.i_panel_pendientes import IPanelPendientes


class PanelPendientesAppService:
    def __init__(self, repositorio: IPanelPendientes):
        self.repositorio = repositorio

    def consultar_pendientes(self):
        return self.repositorio.consultar()
