+++
id = "CON-01"
titulo = "Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit"
ola = "D"
estado = "pendiente"
sala = "conservacion"
depende_de = ["ADPA-07", "ADPA-09", "RAT-07"]
propiedad = ["alembic/versions/20260429_01_con01_politicas_conservacion.py", "features/conservacion/models.py", "features/conservacion/schemas.py", "features/conservacion/conservacion_service.py#CON-01", "features/conservacion/domain/errores.py#CON-01", "features/conservacion/routes/__init__.py", "features/conservacion/routes/conservacion_routes.py", "app_core/pasillo/conservacion.py#CON-01", "app_core/pasillo/rat.py#CON-01", "app_core/pasillo/dpo_cockpit.py#CON-01", "main.py#CON-01", "frontend/src/components/layout/menus/index.ts#CON-01", "frontend/src/components/layout/pantallas/index.tsx#CON-01", "frontend/src/components/layout/pantallas/CON-01.tsx", "tests/test_con01_conservacion.py"]
arbitro = "pytest tests/test_con01_conservacion.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + vigilantes"
rastros = ["¤conservacion", "¤rat", "¤adpa"]
+++
# CON-01 · Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit

## Entrega
- Tabla `politicas_conservacion` con RLS por `tenant_id` (`ENABLE/FORCE ROW LEVEL SECURITY`, permisos `SELECT, INSERT, UPDATE` a `lopdp_app`) vinculada a las actividades del RAT (`actividad_rat_id`, `plazo_meses`, `accion_vencimiento` en `{BLOQUEO, ANONIMIZACION, SUPRESION}`, `fecha_proxima_revision`, `estado` en `{ACTIVA, BLOQUEADA, EJECUTADA}`, `acta_ejecucion_hash`).
- Servicio `features/conservacion/conservacion_service.py#CON-01` que consulta las actividades del RAT exclusivamente vía `app_core/pasillo/rat.py#CON-01` y publica alertas de vencimiento de retención en el DPO Cockpit vía `app_core/pasillo/dpo_cockpit.py#CON-01`.
- Códigos de error en `features/conservacion/domain/errores.py#CON-01` (`CONSERVACION_POLITICA_NO_ENCONTRADA`, `CONSERVACION_PLAZO_INVALIDO`, `CONSERVACION_YA_EJECUTADA`).
- Router `/api/v1/conservacion` y pantalla `frontend/src/components/layout/pantallas/CON-01.tsx` registrada en `menus/index.ts#CON-01` y `pantallas/index.tsx#CON-01`.

## Pruebas
- `pytest tests/test_con01_conservacion.py` valida el ciclo completo de creación de política de retención, detección de vencimiento, generación de acta de bloqueo/anonimización con hash SHA-256 y aislamiento RLS entre inquilinos.
