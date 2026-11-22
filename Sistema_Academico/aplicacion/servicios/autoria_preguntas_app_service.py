"""Casos de uso del docente: redactar, consultar y enviar a revisión sus preguntas."""
from aplicacion.servicios.pregunta_app_service import validar_estado_filtro
from dominio.banco_preguntas.contenido_docente import ContenidoPregunta, validar_contenido
from dominio.banco_preguntas.i_autoria_preguntas_repositorio import IAutoriaPreguntasRepositorio

MAX_TEMA = 150
ACCIONES = ('guardar', 'enviar')


class AutoriaPreguntasAppService:
    def __init__(self, repositorio: IAutoriaPreguntasRepositorio):
        self.repositorio = repositorio

    def catalogos(self, usuario):
        return self.repositorio.catalogos(usuario)

    def examenes(self):
        return self.repositorio.examenes()

    def crear_tema(self, usuario, materia, nombre):
        nombre = (nombre or '').strip()
        try:
            materia = int(materia)
        except (TypeError, ValueError):
            raise ValueError('Selecciona una materia válida.') from None
        if not nombre or len(nombre) > MAX_TEMA:
            raise ValueError('El tema debe tener entre 1 y 150 caracteres.')
        self.repositorio.crear_tema(usuario, materia, nombre)

    def preguntas(self, usuario, filtros):
        estado = validar_estado_filtro(filtros.get('estado', ''))
        try:
            materia = int(filtros.get('materia') or 0)
            examen = int(filtros.get('examen') or 0)
        except ValueError:
            raise ValueError('Materia no válida.') from None
        return self.repositorio.preguntas(usuario, estado, materia, examen)

    def obtener(self, usuario, pregunta, version=None):
        return self.repositorio.obtener(usuario, pregunta, version)

    def guardar(self, usuario, datos, archivos, pregunta=None):
        enunciado, respuesta, alternativas = validar_contenido(datos)
        if datos.get('accion') not in ACCIONES:
            raise ValueError('Selecciona una acción válida.')
        try:
            version = int(datos.get('version') or 0)
            materia = int(datos.get('materia') or 0)
            tema = int(datos.get('tema') or 0)
            examen = int(datos.get('examen') or 0)
            areas = list(dict.fromkeys(int(valor) for valor in datos.getlist('areas')))
        except (TypeError, ValueError):
            raise ValueError('Selecciona materia, tema y áreas válidos.') from None
        tema_nuevo = (datos.get('tema_nuevo') or '').strip()
        if len(tema_nuevo) > MAX_TEMA:
            raise ValueError('El tema admite hasta 150 caracteres.')
        if not pregunta and (not materia or not (tema or tema_nuevo) or not areas or not examen):
            raise ValueError('Selecciona un examen, materia, tema y al menos un área.')
        contenido = ContenidoPregunta(pregunta=pregunta, version=version, materia=materia, tema=tema, areas=areas,
                                      enunciado=enunciado, respuesta=respuesta, alternativas=alternativas,
                                      imagenes=archivos, enviar=datos.get('accion') == 'enviar', examen=examen,
                                      tema_nuevo=tema_nuevo)
        return self.repositorio.guardar(usuario, contenido)

    def estadisticas(self, usuario):
        return self.repositorio.estadisticas(usuario)

    def imagen(self, usuario, imagen, coordinador=False):
        return self.repositorio.imagen(usuario, imagen, coordinador)
