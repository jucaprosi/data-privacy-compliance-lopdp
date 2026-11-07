+++
id = "SEC-18"
titulo = "lopdp_app puede usar las secuencias de las tablas donde inserta (identity sin permission denied)"
ola = "indep"
estado = "pendiente"
sala = "pasillo_central"
depende_de = []
propiedad = ["alembic/versions/20261122_sec18_secuencias_lopdp_app.py", "tests/test_sec18_secuencias_lopdp_app.py"]
arbitro = "pytest tests/test_sec18_secuencias_lopdp_app.py contra PostgreSQL 16 local en contenedor + tests/test_alembic_una_cabeza.py + suite completa; prueba de mutación documentada (sin la migración, la prueba falla con permission denied for sequence)"
rastros = ["¤seguridad", "¤arbitro"]
+++

# SEC-18 · Permiso de lopdp_app sobre secuencias

**Origen.** Una prueba de humo en producción (`evydentia_prod`, con el backend como `lopdp_app`), hecha el 2026-11-07 con Antigravity, salió bien: `/health` en 200, 401 sin token y una lectura real de la base. Pero ninguna migración le da a `lopdp_app` permiso sobre secuencias. `20261008_app_role_rls.py` solo da USAGE sobre el esquema y permisos sobre tablas.

**Confirmado en el código (Tech Lead, 2026-11-07).** Hay dos tablas con columna identity en las que `lopdp_app` tiene INSERT; un INSERT en ellas fallaría con «permission denied for sequence»:
- `biblioteca_importaciones` (`id bigint GENERATED ALWAYS AS IDENTITY`, en `20261026_biblioteca_catalogo.py`, con `GRANT SELECT, INSERT`).
- `biblioteca_verificaciones` (`secuencia bigint GENERATED ALWAYS AS IDENTITY`, en `20261114_biblioteca_verificaciones.py`, con `GRANT SELECT, INSERT`).

Las tablas de auditoría de la biblioteca también usan identity, pero se escriben desde funciones `SECURITY DEFINER`; las demás usan identificadores UUID o texto generados por la aplicación.

## Entrega
- Una migración `20261122_sec18_secuencias_lopdp_app.py`:
  - `GRANT USAGE, SELECT` sobre las secuencias de las tablas donde `lopdp_app` tiene INSERT. Se calculan en la migración desde `information_schema.role_table_grants` y `pg_depend`; no se usa una lista fija.
  - `ALTER DEFAULT PRIVILEGES FOR ROLE current_user IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO lopdp_app` para las secuencias futuras, porque en todos los entornos migra el mismo rol que crea las tablas.
  - `downgrade` que revoca ambos permisos.
- Antes de fusionar: traer `main`, correr `alembic heads` y aplicar `governance/operaciones/FUSION_ALEMBIC.md` si hay más de una cabeza.

## Pruebas
- `tests/test_sec18_secuencias_lopdp_app.py`: con `SET LOCAL ROLE lopdp_app` y el contexto RLS de una organización de prueba, inserta en `biblioteca_importaciones` y comprueba que se generó el id. Una segunda prueba comprueba que una tabla nueva creada por el rol que migra le da `USAGE` a `lopdp_app` sobre su secuencia (privilegios por defecto).
- Mutación: sin la migración (en `downgrade`), la primera prueba falla con «permission denied for sequence».

## Límites
- La migración a producción la hace el propietario después de fusionar, con el job `evydentia-migrate` (`governance/operaciones/entornos/produccion/MIGRAR_PRODUCCION.md`). Ninguna sesión de IA migra producción.
- No da DELETE ni DDL a `lopdp_app`.
