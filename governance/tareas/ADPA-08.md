+++
id = "ADPA-08"
titulo = "Restaurar migración base de terceros_encargados y transferencias_terceros con RLS y separar salas"
ola = "C"
estado = "en_curso"
sala = "terceros, transferencias"
depende_de = ["SEC-09", "ADPA-01", "ADPA-05", "ADPA-06", "ADPA-10"]
propiedad = ["alembic/versions/20260420_01_restaurar_terceros_transferencias_rls.py", "features/terceros/domain/models.py#ADPA-08", "features/transferencias/models.py", "tests/test_adpa08_terceros_transferencias_schema.py", "features/transferencias/services/encargados_service.py", "governance/tareas/_exenciones_propiedad.txt#ADPA-08"]
arbitro = "pytest tests/test_adpa08_terceros_transferencias_schema.py against PostgreSQL 16 local en contenedor con lopdp_app"
rastros = ["¤adpa", "¤transferencias", "¤seguridad-tenant"]
+++
# ADPA-08 · Restaurar migración base de `terceros_encargados` y `transferencias_terceros` con RLS y separar salas

## Entrega
- Migración idempotente `alembic/versions/20260420_01_restaurar_terceros_transferencias_rls.py` que crea `terceros_encargados` y `transferencias_terceros` (eliminada accidentalmente en `9369ce2c67fd`), aplica `ENABLE/FORCE ROW LEVEL SECURITY` con política `tenant_isolation` y otorga permisos `SELECT, INSERT, UPDATE` a `lopdp_app`.
- `features/transferencias/models.py` propio de la sala `transferencias` para desacoplarla de `features/terceros/domain/models.py`.

## Pruebas
- `pytest tests/test_adpa08_terceros_transferencias_schema.py` verifica la existencia de ambas tablas, sus políticas RLS y la ausencia de acoplamiento entre `features/terceros` y `features/transferencias`.

**Ampliación (Tech Lead, 2026-11-09, a pedido del ingeniero).** (1) El PR siembra la marca `#ADPA-08` en `features/terceros/domain/models.py` y, en el mismo cambio, retira su línea de la sección `#ADPA-08` de `_exenciones_propiedad.txt`. (2) El modelo `TerceroEncargado` se mueve de `features/transferencias/services/encargados_service.py` (de RM-02 y SEC-09, hechas) a `features/transferencias/models.py`, y el servicio pasa a importarlo de ahí.
