# Registro de migraciones aplicadas a mano en bases compartidas

El CI no ejecuta migraciones: no hay ningún paso `alembic` en `.github/workflows/zero-regression-pipeline.yml`. Cada migración que una tarea necesita en la base de pruebas se aplica a mano antes de que corra su CI. Este registro deja constancia de cada aplicación manual, para que cualquier persona del equipo sepa en qué revisión está cada base y quién la dejó así.

## Reglas

1. **Cada aplicación manual se registra el mismo día**, también un `downgrade`, un `stamp` o un «Reset from parent» en Neon, que borran lo aplicado.
2. **Nunca se anotan credenciales, cadenas de conexión, contraseñas ni nombres de endpoint.** Solo el nombre de la rama de Neon (por ejemplo `test-aleczandra`).
3. **La revisión se confirma con `alembic current`** ejecutado por una sesión o persona con acceso, sin mostrar valores de conexión. Si todavía no se confirmó, la entrada lo dice en la columna «Confirmación».
4. **Solo en bases de pruebas** (`test-<persona>` y sus temporales). Producción la migra la propietaria, desde `main`, tras fusionar, con copia previa y ensayo previo (ver las condiciones de las migraciones que reescriben o borran datos).
5. Una migración que reescribe datos o cuyo `downgrade` pierde información lleva su advertencia en la columna «Nota».

## Registro

| Fecha (UTC) | Base | Revisión (antes → después) | Origen (PR y tarea) | Aplicó | Autorizó | Confirmación | Nota |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 2026-10-30, 01:45 (hora en que se grabó el resultado; alembic no imprime hora) | `test-aleczandra` | `20261030_hallazgos` → `20261031_diag_escala_smartcidi` | #235, DIAG-08 | Sesión de DIAG-08 (`alembic upgrade head` con la URL directa) | La propietaria, con un mensaje directo en el chat de DIAG-08 («Autorizo `alembic upgrade head` solo en `test-aleczandra`…») | `alembic current` en `test-aleczandra` el 2026-10-30, según la sesión de DIAG-08: `20261031_diag_escala_smartcidi`. Antes del `upgrade`, la misma sesión vio `20261030_hallazgos`. La hora exacta de inicio no se conoce: no hay marca de tiempo en la base, que guarda solo la revisión. | Reescribe datos: `nivel_evidencia` sube una unidad donde era mayor que 0 y el CHECK pasa de 0-3 a 0-4; añade `nivel_asignado`. Su `downgrade` pierde `nivel_asignado` y confunde la evidencia 0 con 1. Antes de producción: copia y ensayo previos. |

## Migraciones previstas y todavía sin aplicar

| Migración | Base prevista | Origen | Condición |
| :-- | :-- | :-- | :-- |
| `20261030_dpo_inscripcion` (se re-encadena sobre la de DIAG-08) | `test-aleczandra` o `test-aleczandra-dpo02` | #234, DPO-02 | Esperar a que #235 esté fusionado. Su `downgrade` borra la tabla `dpo_inscripciones` entera, con el historial de inscripciones SPDP de todas las organizaciones, sin copia posible: antes de producción, copia previa, y no ejecutar `downgrade` sin ella. |
