"""Casos de uso de la organización académica (catálogos y asignación de docentes a materias)."""
from dominio.organizacion_academica.i_organizacion_repositorio import IOrganizacionRepositorio
from dominio.organizacion_academica.reglas_organizacion import identificador, validar_datos, validar_estado, validar_tipo


class OrganizacionAppService:
    def __init__(self, repositorio: IOrganizacionRepositorio):
        self.repositorio = repositorio
        # Cada acción del formulario se atiende con un caso de uso propio.
        self._acciones = {
            'asignar': lambda tipo, datos: self.asignar(datos, activo=True),
            'desasignar': lambda tipo, datos: self.asignar(datos, activo=False),
            'crear': self.crear,
            'editar': self.editar,
            'estado': self.cambiar_estado,
        }

    def listar(self):
        return self.repositorio.listar()

    def ejecutar(self, accion, tipo, datos):
        caso_de_uso = self._acciones.get(accion)
        if caso_de_uso is None:
            validar_tipo(tipo)
            raise ValueError('Acción no válida.')
        return caso_de_uso(tipo, datos)

    def asignar(self, datos, activo):
        docente = identificador(datos.get('docente'), 'un docente')
        materia = identificador(datos.get('materia'), 'una materia')
        return self.repositorio.asignar(docente, materia, activo)

    def crear(self, tipo, datos):
        return self.repositorio.crear(tipo, validar_datos(tipo, datos))

    def editar(self, tipo, datos):
        valores = validar_datos(tipo, datos)
        return self.repositorio.actualizar(tipo, identificador(datos.get('id'), 'un elemento'), valores)

    def cambiar_estado(self, tipo, datos):
        validar_tipo(tipo)
        elemento = identificador(datos.get('id'), 'un elemento')
        return self.repositorio.estado(tipo, elemento, validar_estado(tipo, datos.get('estado')))
