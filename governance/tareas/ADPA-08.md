+++
id = "ADPA-08"
titulo = "Restaurar migración base de terceros_encargados y transferencias_terceros con RLS y separar salas"
ola = "C"
estado = "pendiente"
sala = "terceros, transferencias"
depende_de = ["SEC-09", "ADPA-01", "ADPA-05", "ADPA-06"]
propiedad = ["alembic/versions/20260420_01_restaurar_terceros_transferencias_rls.py", "db/models/terceros.py#ADPA-08", "features/terceros/models.py#ADPA-08", "features/transferencias/models.py", "tests/test_adpa08_terceros_transferencias_schema.py"]
arbitro = "pytest tests/test_adpa08_terceros_transferencias_schema.py against rama Neon de revisión con lopdp_app"
rastros = ["¤adpa", "¤transferencias", "¤seguridad-tenant"]
+++
# ADPA-08 · Restaurar migración base de `terceros_encargados` y `transferencias_terceros` con RLS y separar salas

## Entrega
- Migración idempotente `alembic/versions/20260420_01_restaurar_terceros_transferencias_rls.py` que crea `terceros_encargados` y `transferencias_terceros` (eliminada accidentalmente en `9369ce2c67fd`), aplica `ENABLE/FORCE ROW LEVEL SECURITY` con política `tenant_isolation` y otorga permisos `SELECT, INSERT, UPDATE` a `lopdp_app`.
- `features/transferencias/models.py` propio de la sala `transferencias` para desacoplarla de `features/terceros/models.py`.

## Pruebas
- `pytest tests/test_adpa08_terceros_transferencias_schema.py` verifica la existencia de ambas tablas, sus políticas RLS y la ausencia de acoplamiento entre `features/terceros` y `features/transferencias`.
