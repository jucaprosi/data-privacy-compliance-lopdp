# CON-01 · Sala Conservación y Bloqueo (Art. 10 y 20 LOPDP)
`¤sdd` `¤conservacion` `¤rat` `¤adpa`

## 1. Datos

Tabla `politicas_conservacion` (con RLS forzado por `tenant_id`):
- `id` (UUID PK), `tenant_id` (VARCHAR(64) NOT NULL), `actividad_rat_id` (VARCHAR(64) NOT NULL), `plazo_meses` (INTEGER NOT NULL > 0), `accion_vencimiento` (`'BLOQUEO' | 'ANONIMIZACION' | 'SUPRESION'`), `fecha_proxima_revision` (DATE NOT NULL), `estado` (`'ACTIVA' | 'BLOQUEADA' | 'EJECUTADA'`), `acta_ejecucion_hash` (VARCHAR(64) NULL), `creado_en` (TIMESTAMPTZ).

## 2. API

- `GET /api/v1/conservacion/politicas` -> `200 OK`
- `POST /api/v1/conservacion/politicas` -> `201 Created`
- `POST /api/v1/conservacion/politicas/{politica_id}/ejecutar` -> `200 OK`

## 3. Reglas

- **R1 · Vinculación con RAT vía pasillo.** Al registrar una política, `conservacion_service` verifica la existencia de `actividad_rat_id` mediante `app_core/pasillo/rat.py#CON-01`.
- **R2 · Ejecución idempotente y acta inmutable.** Ejecutar una política en estado `EJECUTADA` lanza `ErrorNegocio("CONSERVACION_YA_EJECUTADA")` (409). Al ejecutarse por primera vez, calcula `acta_ejecucion_hash` (SHA-256) y cambia `estado` a `BLOQUEADA` o `EJECUTADA`.
- **R3 · Alertas de vencimiento en DPO Cockpit.** Las políticas con `fecha_proxima_revision <= hoy` se exponen al DPO Cockpit vía `app_core/pasillo/conservacion.py#CON-01` y `app_core/pasillo/dpo_cockpit.py#CON-01`.

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/CON-01.tsx` accesible desde el menú lateral (`menus/index.ts#CON-01`), con listado de políticas de retención por actividad RAT, semáforo de vencimiento y botón de ejecución de bloqueo/anonimización.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un tratamiento activo en el RAT, **cuando** se crea una política con `plazo_meses = 24` y `accion_vencimiento = 'BLOQUEO'` y luego se ejecuta, **entonces** queda registrada con `acta_ejecucion_hash` no nulo y un segundo intento devuelve 409 `CONSERVACION_YA_EJECUTADA`. | `test_ciclo_politica_conservacion_y_bloqueo` |
| **Dado** dos inquilinos A y B, **cuando** B consulta `/api/v1/conservacion/politicas`, **entonces** RLS impide ver las políticas de A. | `test_conservacion_rls_aislamiento_tenant` |

## 6. Trazabilidad

- PRD §7.1 (`conservacion` — Políticas de conservación, bloqueo y purga/anonimización) y Art. 10 / Art. 20 LOPDP.
