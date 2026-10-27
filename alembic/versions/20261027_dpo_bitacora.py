# ¤¤security-engineer
"""DPO-01: bitácora del DPO persistida en PostgreSQL con cadena SHA-256 y RLS por organización. ¤dpo ¤rbac-tenant"""
from alembic import op
import sqlalchemy as sa

revision = "20261027_dpo_bitacora"
down_revision = "20261025_gran_escala_obligacion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dpo_dictamenes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("dpo_id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(length=64), nullable=False),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("referencia_normativa", sa.Text(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("fecha_emision", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "es_vinculante",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "acuse_recibo_alta_direccion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("acuse_por", sa.String(), nullable=True),
        sa.Column("fecha_acuse", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dpo_dictamenes_tenant_id", "dpo_dictamenes", ["tenant_id"])
    op.execute("ALTER TABLE dpo_dictamenes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dpo_dictamenes FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_dpo_dictamenes ON dpo_dictamenes "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON dpo_dictamenes FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON dpo_dictamenes TO lopdp_app")


def downgrade() -> None:
    op.drop_index("ix_dpo_dictamenes_tenant_id", table_name="dpo_dictamenes")
    op.drop_table("dpo_dictamenes")
