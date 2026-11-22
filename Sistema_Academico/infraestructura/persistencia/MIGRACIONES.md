# Scripts de base de datos

## Instalación nueva

1. `nueva_base_de_datos.sql` (raíz del repositorio): esquema completo, vistas, triggers y procedimientos.
   Ya incluye los cambios de los scripts de actualización listados abajo.
2. `datos_iniciales.sql` (raíz): catálogos y datos de prueba.

## Actualizar una base existente

Ejecutar **una sola vez** solo los que aún no se hayan aplicado
(no todos son idempotentes: `ALTER TABLE ... ADD COLUMN` falla si la columna ya existe).
El historial de Git no conserva el orden original de creación; el orden siguiente respeta las
dependencias verificadas (`historial_cargas_omr` tiene una clave foránea hacia `cargas_omr`):

| Orden | Script | Cambio |
|---|---|---|
| 1 | `preguntas_examen_destino.sql` | Columna `preguntas.id_examen_destino` (no idempotente) |
| 2 | `habilitar_preguntas_examen.sql` | Columna `examenes.admite_preguntas` (no idempotente) |
| 3 | `cargas_cartillas.sql` | Tabla `cargas_omr` (idempotente) |
| 4 | `historial_cargas_omr.sql` | Tabla `historial_cargas_omr` (idempotente) |
| 5 | `posiciones_cartilla.sql` | Redefine triggers de resultados (idempotente) |
| 6 | `actualizar_permisos_director.sql` | Permisos del director, trigger de aprobación de preguntas y procedimientos `sp_registrar_cartilla` y `sp_publicar_examen` (idempotente) |

## Pendiente

No existe una tabla que registre qué scripts se aplicaron. Se recomienda adoptar una herramienta de
migraciones versionadas (Alembic o Flyway) y generar el esquema base a partir de ellas.
