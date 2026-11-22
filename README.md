# Sistema académico

Aplicación Flask con MySQL organizada por capas (presentación, aplicación, dominio e infraestructura).
El programa está en la carpeta `Sistema_Academico`.

## Ejecutar

1. Instala Python 3.11 o superior y MySQL 8. Para una instalación nueva, ejecuta `nueva_base_de_datos.sql`
   y después `datos_iniciales.sql` en MySQL.
2. Crea el entorno virtual e instala las dependencias desde la raíz del repositorio:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r .\Sistema_Academico\requirements.txt
   ```

3. Configura la conexión con variables de entorno (o guarda la contraseña en `Sistema_Academico\mysql_clave.local`,
   archivo local que **no se versiona**):

   | Variable | Uso | Valor por defecto |
   |---|---|---|
   | `SISTEMA_MYSQL_PASSWORD` | Contraseña de MySQL | (obligatoria o `mysql_clave.local`) |
   | `SISTEMA_MYSQL_USER` / `SISTEMA_MYSQL_HOST` / `SISTEMA_MYSQL_PORT` / `SISTEMA_MYSQL_DB` | Conexión | `root` / `localhost` / `3306` / `sistema_evaluacion` |
   | `SISTEMA_SECRET_KEY` | Clave de sesión de Flask | Temporal (se pierde al reiniciar; defínela siempre en producción) |
   | `SISTEMA_COOKIE_SECURE` | `1` para enviar la cookie de sesión solo por HTTPS | desactivado |
   | `SISTEMA_DATABASE_URL` | URL completa de SQLAlchemy (alternativa a las anteriores al usar `app.py`) | — |

4. Inicia la aplicación y abre http://127.0.0.1:5000/:

   ```powershell
   .\.venv\Scripts\python.exe .\Sistema_Academico\run.py
   ```

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\Sistema_Academico\requirements-dev.txt
cd Sistema_Academico
..\.venv\Scripts\python.exe -m pytest tests
```

## Datos privados y credenciales

Las imágenes de cartillas y preguntas se guardan en `Sistema_Academico/datos_privados/` y las credenciales en
`*.local`; ambos están excluidos por `.gitignore` y no deben subirse al repositorio.

## Base de datos

El orden de los scripts de actualización está en `Sistema_Academico/infraestructura/persistencia/MIGRACIONES.md`.
El motor de lectura de cartillas está documentado en `Sistema_Academico/infraestructura/vision/addison_omr/SECUENCIA.md`.
