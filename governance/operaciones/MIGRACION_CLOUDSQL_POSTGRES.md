# Migración de Neon a Cloud SQL PostgreSQL 16 (GCP-04)
`¤cloud-run-perf` `¤seguridad-tenant` `¤ci-cd`

Procedimiento para el propietario. Lo ejecuta una persona con Antigravity; ninguna sesión de IA
escribe en Google Cloud ni en la base. El PMV sigue congelado en Neon y Vercel: este corte afecta
solo a EVYDENTIA.

## Estado de destino

- Instancia `evydentia-production`, PostgreSQL 16, base `evydentia_prod` (`cloud_sql_instance.yaml`).
- Sin IP pública: red privada VPC y conector de Cloud SQL desde Cloud Run. SSL obligatorio.
- Backups automáticos diarios, recuperación a un punto en el tiempo y protección contra borrado.
- Dos roles: `lopdp_beta_owner` migra y es dueño de las tablas; `lopdp_app` es el rol de la
  aplicación (`NOSUPERUSER`, `NOBYPASSRLS`, sin propiedad). Toda tabla con políticas tiene RLS
  activa y forzada.
- Un dominio y una IP: `/api/*` va al backend y el resto al frontend (`cloud_load_balancer.yaml`),
  con Cloud Armor y certificado administrado.

## Pasos

1. **Crear la instancia** según `cloud_sql_instance.yaml`, crear la base `evydentia_prod` y el usuario
   `lopdp_beta_owner`. Guardar su contraseña en Secret Manager.
2. **Esquema por Alembic, no por copia de DDL.** Desde `main`, con `MIGRATION_DATABASE_URL` apuntando a
   la instancia: `python -m alembic upgrade head`. La migración `20261008_app_role_rls` crea
   `lopdp_app` y fuerza RLS en las tablas con políticas.
3. **Activar el rol de la aplicación:** `ALTER ROLE lopdp_app WITH LOGIN PASSWORD '<secreto>';` en la
   consola SQL. La contraseña va solo a Secret Manager, dentro del secreto `DATABASE_URL`.
4. **Datos (si se migran desde Neon).** Con escritura detenida en el origen:
   `pg_dump --data-only --no-owner --no-privileges` desde Neon y `pg_restore --data-only
   --disable-triggers` con el rol dueño. Comparar el número de filas por tabla en origen y destino.
5. **Verificación notarial**, antes de abrir el tráfico:
   `python scripts/verificar_cloudsql_conexion.py` con `CLOUDSQL_DATABASE_URL` del rol `lopdp_app`.
   Debe salir con código 0. También `python scripts/verificar_revision_alembic.py`.
6. **Corte.** Apuntar el secreto `DATABASE_URL` del backend a la instancia, publicar una revisión de
   Cloud Run y luego crear el balanceador. Comprobar `/api/v1/health` a través del dominio.
7. **Vuelta atrás.** Mientras no haya escrituras nuevas en Cloud SQL, basta con devolver
   `DATABASE_URL` a su valor anterior y publicar la revisión previa. Después del corte, la vuelta
   atrás exige volcar Cloud SQL hacia el origen.

## Qué no se hace

- No se copia el DDL a mano: el esquema sale siempre de Alembic en `main`.
- No se usa `lopdp_beta_owner` en la aplicación.
- No se abre IP pública ni se desactiva SSL para «probar».
