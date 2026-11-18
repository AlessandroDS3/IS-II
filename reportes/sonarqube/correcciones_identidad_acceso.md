# Correcciones de identidad y acceso

Se corrigieron exclusivamente los hallazgos del listado original relacionados con identidad y acceso, sus contratos, repositorio de autenticación, controlador y mensajes de la vista compartida.

SonarQube confirmó la desaparición de **23 incidencias**: 22 de la regla `python:S1186` y una de `Web:S6819`. No se introdujeron incidencias nuevas. El total pasó de **333 a 310**; las incidencias ajenas a este alcance conservan sus identificadores.

Análisis verificado: `c2898e88-e932-499b-b121-34ba5e71ea42`. Tarea: `885a03ae-3a9a-440f-bdbb-da0e70b90e5d`, estado **SUCCESS**.

## Archivos corregidos

| Archivo | Antes | Después |
| --- | --- | --- |
| `Sistema_Academico/aplicacion/puertos/i_protector_credenciales.py` | 3 | 0 |
| `Sistema_Academico/dominio/identidad_acceso/autorizacion.py` | 3 | 0 |
| `Sistema_Academico/dominio/identidad_acceso/cuenta_usuario.py` | 2 | 0 |
| `Sistema_Academico/dominio/identidad_acceso/i_cuenta_repositorio.py` | 5 | 0 |
| `Sistema_Academico/infraestructura/persistencia/repositories/cuenta_usuario_orm_repositorio.py` | 3 | 0 |
| `Sistema_Academico/infraestructura/seguridad/protector_credenciales_werkzeug.py` | 1 | 0 |
| `Sistema_Academico/presentacion/controllers/cuenta_usuario_controller.py` | 5 | 0 |
| `Sistema_Academico/presentacion/vistas/comun/base.html` | 1 | 0 |

## Cambios realizados

- Se retiraron constructores vacíos que no inicializaban estado.
- Los contratos de repositorio y protección de credenciales son clases abstractas: no se pueden instanciar implementaciones incompletas.
- `CuentaUsuario.asignar_roles` aplica las reglas existentes de roles y copia la colección para evitar modificaciones externas; asignar DIRECTOR exige autorización explícita. `cambiar_credencial` rechaza hashes vacíos antes de modificar la cuenta.
- `CuentaUsuarioController` recibe el servicio por constructor y delega sus operaciones, incluido el inicio de sesión.
- Las operaciones heredadas pendientes del repositorio y de autorización lanzan `NotImplementedError`, en lugar de devolver silenciosamente `None`. No se inventaron políticas de permisos ni un flujo de recuperación de contraseña.
- El protector rechaza hashes o contraseñas de tipos inválidos sin provocar errores durante la autenticación.
- Los mensajes de la plantilla base usan `<output>`, manteniendo el contenedor y sus estilos; se verificó el escape de HTML.

## Alcance preservado y límites

Los servicios de cuenta y gestión de usuarios no tenían hallazgos en este CSV y mantuvieron su implementación. El hallazgo de `rutas_web.py` corresponde al listado de cartillas y el de `app.py` a la composición global de servicios; ambos permanecen fuera de esta corrección.

Los métodos pendientes ahora fallan explícitamente; esto no equivale a implementar nuevas funciones de recuperación de acceso, autorización por operación o consultas de repositorio sin requisitos definidos. La creación, los cambios de estado y de roles continúan en los servicios y repositorios de gestión existentes.

## Validación

| Conjunto | Pruebas | Resultado |
| --- | --- | --- |
| Identidad y acceso: unidad, integración y vista | 43 | OK |
| Rutas HTTP y regresiones de sesión | 16 | OK |
| Funcionales con Selenium | 11 | OK |

Las pruebas usan SQLite temporal y cuentas de prueba; no modifican MySQL. La cobertura del conjunto de seis archivos configurado en `tests/identidad_acceso/.coveragerc` fue 84%; no es la cobertura global del proyecto.

Comandos ejecutados desde la raíz:

```powershell
.\.venv-1\Scripts\python.exe -X utf8 -B tests/identidad_acceso/ejecutar_pruebas.py
.\.venv-1\Scripts\python.exe -X utf8 -B -m unittest discover -s tests/presentacion -p "test_*.py" -v
.\.venv-1\Scripts\python.exe -X utf8 -B tests/funcionales/ejecutar.py
& "C:\sonar-scanner\bin\sonar-scanner.bat"
```

La autenticación del scanner se suministró mediante `SONAR_TOKEN` en el entorno, sin guardarla en el repositorio. No se importó cobertura en este análisis de SonarQube, por lo que su 0% continúa siendo independiente de la cobertura local indicada arriba.

## Evidencias

- [Reporte posterior](despues_identidad_acceso/reporte_defectos.md).
- [Incidencias restantes](despues_identidad_acceso/defectos.csv).
- [Las 23 incidencias corregidas](despues_identidad_acceso/corregidos_identidad_acceso.csv).
- [Datos de la API](despues_identidad_acceso/resultados.json).
- [Ejecución de SonarScanner](despues_identidad_acceso/ejecucion.txt).

El CSV original y el primer reporte permanecen como evidencia anterior a las correcciones. Se analizó la copia de trabajo con cambios sin commit; no se publicaron cambios en GitHub.
