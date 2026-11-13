# ¤¤backend-developer
"""Tabla trazas_ia de IA-10: una fila por cada resultado de IA (invariante 64). ¤gemini-vertex ¤seguridad-tenant

Revision ID: 20261112_ia10_trazas_ia
Revises: rm25a_evidencia_doble_validacion

Solo se agrega: `lopdp_app` con SELECT e INSERT, sin UPDATE ni DELETE. RLS forzada por tenant_id.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261112_ia10_trazas_ia"
down_revision: Union[str, Sequence[str], None] = "rm25a_evidencia_doble_validacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE trazas_ia (
            id VARCHAR PRIMARY KEY,
            tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
            sala VARCHAR NOT NULL,
            entidad VARCHAR NOT NULL,
            entidad_id VARCHAR NOT NULL,
            modelo_version VARCHAR NOT NULL,
            modelo_solicitado VARCHAR NOT NULL,
            prompt_id VARCHAR NOT NULL,
            prompt_version INTEGER NOT NULL CHECK (prompt_version >= 1),
            corpus_sha256 VARCHAR(64) NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_trazas_ia_entidad ON trazas_ia (tenant_id, entidad, entidad_id);
        ALTER TABLE trazas_ia ENABLE ROW LEVEL SECURITY;
        ALTER TABLE trazas_ia FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_trazas_ia ON trazas_ia
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON trazas_ia FROM lopdp_app;
        GRANT SELECT, INSERT ON trazas_ia TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS trazas_ia")
