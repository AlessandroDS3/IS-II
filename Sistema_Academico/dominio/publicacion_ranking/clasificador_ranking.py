"""Ranking de resultados por puntaje exacto con empates (misma regla que RANK() en sp_publicar_examen)."""
from dominio.publicacion_ranking.entrada_publicada import EntradaPublicada


class ClasificadorRanking:
    @staticmethod
    def ordenar_por_puntaje_exacto(resultados_transferidos):
        """Orden descendente por puntaje; a igual puntaje se conserva el orden recibido (orden estable)."""
        return sorted(resultados_transferidos, key=lambda r: r.puntaje, reverse=True)

    @staticmethod
    def asignar_puestos_con_empates(entradas_ordenadas):
        """Ranking de competición: puntajes iguales comparten puesto y el siguiente salta (1, 1, 3)."""
        puesto_actual = 0
        puntaje_anterior = None
        clasificadas = []
        for posicion, entrada in enumerate(entradas_ordenadas, 1):
            if entrada.puntaje != puntaje_anterior:
                puesto_actual = posicion
                puntaje_anterior = entrada.puntaje
            clasificadas.append(EntradaPublicada(entrada.estudiante_id, entrada.participacion_id, entrada.calculo_id,
                                                 entrada.puntaje, puesto_actual))
        return clasificadas

    def clasificar(self, resultados):
        return self.asignar_puestos_con_empates(self.ordenar_por_puntaje_exacto(resultados))
