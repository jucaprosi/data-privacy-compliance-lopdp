# ¤¤backend-developer
"""NORM-02b: destinatarios del aviso normativo por organización. ¤inteligencia-normativa ¤seguridad-tenant

Revision ID: norm02b_destinatarios_normativos
Revises: ret02_clave_objeto (BASE_COMUN; primera migración de la sala `plataforma`, CI-28)

El operador nunca fija organización (ORG-09) y con `lopdp_app` la RLS de `user_tenant_roles` le oculta
todas las filas. `fn_destinatarios_normativos()`, `SECURITY DEFINER` como `fn_tenant_tiene_admin_activo`
(20261022_invitacion_unica_emitida.py), devuelve por cada organización activa solo su identificador y los
correos de sus usuarios activos con rol vigente `admin_organizacion` y `dpo`. Una organización sin ningún
correo en los dos grupos no sale. Solo `lopdp_app` la ejecuta; no cambia ninguna política ni la RLS.

Va en la sala `plataforma`, donde vive el motor que la lee, y no en `organizacion` aunque lea sus tablas:
abrir la rama de `organizacion` exigiría, por la regla R4 de CI-28, `depends_on` en las migraciones ya
aplicadas de las demás salas que nombran `tenants`, `users` o `user_tenant_roles`.

Dueño: el rol que ejecuta la migración, dueño de las tablas. Con FORCE ROW LEVEL SECURITY la RLS también
se aplica a ese rol si no es superusuario ni tiene BYPASSRLS (Cloud SQL): el brief del propietario
`governance/operaciones/BRIEF_PROPIETARIO_NORM02B.md` lo comprueba en cada base tras migrar (R2b).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm02b_destinatarios_normativos"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"
branch_labels: Union[str, Sequence[str], None] = ("plataforma",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_destinatarios_normativos()
        RETURNS TABLE(tenant_id VARCHAR, correos_admin TEXT[], correos_dpo TEXT[])
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
            SELECT t.id::varchar,
                   COALESCE(
                       array_agg(DISTINCT u.email::text ORDER BY u.email::text)
                           FILTER (WHERE utr.role = 'admin_organizacion'),
                       ARRAY[]::text[]
                   ),
                   COALESCE(
                       array_agg(DISTINCT u.email::text ORDER BY u.email::text)
                           FILTER (WHERE utr.role = 'dpo'),
                       ARRAY[]::text[]
                   )
            FROM public.tenants t
            JOIN public.user_tenant_roles utr ON utr.tenant_id = t.id
            JOIN public.users u ON u.id = utr.user_id
            WHERE t.activo IS TRUE
              AND utr.role IN ('admin_organizacion', 'dpo')
              AND (utr.valid_to IS NULL OR utr.valid_to > now())
              AND u.activo
              AND u.deleted_at IS NULL
            GROUP BY t.id
            ORDER BY t.id
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION fn_destinatarios_normativos() FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION fn_destinatarios_normativos() TO lopdp_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS fn_destinatarios_normativos()")
