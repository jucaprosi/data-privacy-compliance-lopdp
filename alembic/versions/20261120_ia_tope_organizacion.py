# ¤¤backend-developer
"""Tabla ia_tope_organizacion de SEC-13a: tope total de generaciones de IA por tenant. ¤seguridad-tenant

Revision ID: 20261120_ia_tope_org
Revises: 20261122_merge_sec13_bib106

`tope` nulo, o sin fila, significa sin tope. RLS forzada por tenant_id. `lopdp_app` con SELECT,
INSERT y UPDATE, sin DELETE.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261120_ia_tope_org"
down_revision: Union[str, Sequence[str], None] = "20261122_merge_sec13_bib106"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ia_tope_organizacion (
            tenant_id VARCHAR PRIMARY KEY REFERENCES tenants(id),
            tope INTEGER NULL CHECK (tope IS NULL OR tope >= 0),
            usadas INTEGER NOT NULL DEFAULT 0 CHECK (usadas >= 0)
        );
        ALTER TABLE ia_tope_organizacion ENABLE ROW LEVEL SECURITY;
        ALTER TABLE ia_tope_organizacion FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_ia_tope_organizacion ON ia_tope_organizacion
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON ia_tope_organizacion FROM lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON ia_tope_organizacion TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ia_tope_organizacion")
