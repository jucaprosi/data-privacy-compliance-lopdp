"""RLS efectivo: rol de aplicación sin BYPASSRLS y FORCE ROW LEVEL SECURITY.

Revision ID: 20261008_app_role_rls
Revises: 20261008_rbac_sod
Create Date: 2026-10-08 18:00:00.000000

El rol dueño (lopdp_beta_owner) tiene BYPASSRLS y es dueño de las tablas, así
que las políticas tenant_isolation_* nunca se le aplicaban. Esta migración:

- Crea el rol 'lopdp_app' (NOLOGIN, NOBYPASSRLS, no dueño de nada). La
  contraseña y el atributo LOGIN se fijan a mano en la consola SQL de Neon
  (nunca en el código):  ALTER ROLE lopdp_app WITH LOGIN PASSWORD '<secreto>';
- Concede los privilegios mínimos: DML en las tablas de negocio, solo
  SELECT/INSERT en las bitácoras de auditoría (append-only).
- Concede al rol que migra la membresía con SET (sin INHERIT), para que los
  tests puedan hacer SET ROLE lopdp_app sin conocer la contraseña.
- Activa FORCE ROW LEVEL SECURITY en las tablas con políticas: no afecta a
  roles con BYPASSRLS (el dueño y el trigger SECURITY DEFINER fn_utr_dpo_sod
  siguen igual), pero cierra el hueco si la propiedad pasa a un rol sin él.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20261008_app_role_rls"
down_revision: Union[str, None] = "20261008_rbac_sod"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"

RLS_TABLES = (
    "areas",
    "roadmaps",
    "roadmap_waves",
    "roadmap_tasks",
    "task_evidence",
    "task_audit_log",
    "user_tenant_roles",
)

# Tablas con DML completo para la app.
DML_TABLES = (
    "areas",
    "roadmaps",
    "roadmap_waves",
    "roadmap_tasks",
    "task_evidence",
    "task_dependencies",
    "user_tenant_roles",
    "tenants",
    "users",
    "tareas_mitigacion",
)

# Bitácoras append-only.
APPEND_ONLY_TABLES = ("task_audit_log", "registro_auditoria")


def upgrade() -> None:
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} NOLOGIN NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
            ELSE
                ALTER ROLE {APP_ROLE} NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
            END IF;
        END $$;
    """)
    op.execute(f"GRANT {APP_ROLE} TO CURRENT_USER WITH INHERIT FALSE, SET TRUE")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(DML_TABLES)} TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON {', '.join(APPEND_ONLY_TABLES)} TO {APP_ROLE}")
    for tabla in RLS_TABLES:
        op.execute(f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for tabla in RLS_TABLES:
        op.execute(f"ALTER TABLE {tabla} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON {', '.join(DML_TABLES + APPEND_ONLY_TABLES)} FROM {APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}")
    op.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
