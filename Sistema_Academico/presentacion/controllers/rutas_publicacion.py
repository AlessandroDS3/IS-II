"""Rutas de publicación y ranking: publicación, reportes, resultados del estudiante y panel del director."""
from flask import abort, current_app, flash, redirect, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from presentacion.controllers.exportacion import respuesta_csv, respuesta_xlsx
from presentacion.controllers.soporte_web import (ROL_COORDINADOR, ROL_DIRECTOR, ROL_ESTUDIANTE, Ruta, pagina,
                                                  registrar_vistas, seleccionar_examen)

ENCABEZADOS_RANKING = ['Posición', 'Código', 'Estudiante', 'Puntaje', 'Porcentaje', 'Aciertos', 'Errores', 'En blanco']
CLAVES_RANKING = ('posicion', 'codigo_estudiante', 'estudiante', 'puntaje', 'porcentaje', 'aciertos', 'errores', 'en_blanco')
ENCABEZADOS_DIRECTOR = ['Examen', 'Fecha', 'Área', 'Participantes', 'Promedio %', 'Máximo %', 'Mínimo %']
CLAVES_DIRECTOR = ('examen', 'fecha_programada', 'area', 'participantes', 'promedio', 'maximo', 'minimo')
COORDINADOR = 'COORDINADOR'


def _examen_obligatorio():
    examen = seleccionar_examen()
    if not examen:
        abort(400)
    return examen


class RutasPublicacion:
    def __init__(self, servicios):
        self.publicacion = servicios.publicacion
        self.resultados_estudiante = servicios.resultados_estudiante

    def rutas(self):
        pub = (self.publicacion,)
        est = (self.resultados_estudiante,)
        return [
            Ruta('/coordinador/resultados/publicar', 'publicar_resultados', self.publicar_resultados, ('POST',), COORDINADOR, pub),
            Ruta('/coordinador/reportes', 'reportes', self.reportes, rol=COORDINADOR, servicios=pub),
            Ruta('/coordinador/reportes/descargar', 'descargar_reporte', self.descargar_reporte, rol=COORDINADOR, servicios=pub),
            Ruta('/coordinador/reportes/excel', 'descargar_reporte_excel', self.descargar_reporte_excel, rol=COORDINADOR, servicios=pub),
            Ruta('/director', 'director', self.director, rol='DIRECTOR', servicios=pub),
            Ruta('/director/reporte.csv', 'director_reporte', self.director_reporte, rol='DIRECTOR', servicios=pub),
            Ruta('/estudiante', 'estudiante', self.estudiante, rol='ESTUDIANTE', servicios=est),
            Ruta('/estudiante/resultados/<int:id>', 'mi_detalle', self.mi_detalle, rol='ESTUDIANTE', servicios=est),
        ]

    def publicar_resultados(self):
        try:
            self.publicacion.publicar(seleccionar_examen(), session['usuario_id'])
            flash('Resultados publicados.', 'ok')
        except ValueError as error:
            flash(str(error), 'error')
        except SQLAlchemyError:
            current_app.logger.exception('No se pudo publicar el examen')
            flash('No se pudo publicar. Todas las cartillas vigentes deben estar validadas y sus resultados revisados.', 'error')
        return redirect(url_for('resultados_coordinador', examen=seleccionar_examen()))

    def reportes(self):
        examen = seleccionar_examen()
        return pagina('coordinador/reportes.html', ROL_COORDINADOR, examenes=self.publicacion.examenes(), examen=examen,
                      ranking=self.publicacion.ranking(examen))

    def descargar_reporte(self):
        examen = _examen_obligatorio()
        return respuesta_csv(ENCABEZADOS_RANKING, self.publicacion.ranking(examen), CLAVES_RANKING, f'reporte_examen_{examen}.csv')

    def descargar_reporte_excel(self):
        examen = _examen_obligatorio()
        return respuesta_xlsx('Ranking publicado', ENCABEZADOS_RANKING, self.publicacion.ranking(examen), CLAVES_RANKING,
                              f'reporte_examen_{examen}.xlsx')

    def director(self):
        ciclo = request.args.get('ciclo', default=0, type=int)
        datos = self.publicacion.estadisticas_director(ciclo)
        return pagina('director/director.html', ROL_DIRECTOR, ciclo=ciclo, ciclos=datos.ciclos, filas=datos.filas, resumen=datos.resumen)

    def director_reporte(self):
        datos = self.publicacion.estadisticas_director(request.args.get('ciclo', default=0, type=int))
        return respuesta_csv(ENCABEZADOS_DIRECTOR, datos.filas, CLAVES_DIRECTOR, 'reporte_director.csv')

    def estudiante(self):
        return pagina('estudiante/mis_resultados.html', ROL_ESTUDIANTE, resultados=self.resultados_estudiante.mis_resultados(session['usuario_id']))

    def mi_detalle(self, id):
        usuario = session['usuario_id']
        resultado = self.resultados_estudiante.mi_resultado(usuario, id)
        if not resultado:
            abort(404)
        return pagina('estudiante/mi_detalle.html', ROL_ESTUDIANTE, resultado=resultado,
                      materias=self.resultados_estudiante.materias(usuario, id), detalle=self.resultados_estudiante.detalle(usuario, id))


def registrar(app, proteger, servicios):
    registrar_vistas(app, proteger, RutasPublicacion(servicios).rutas())
