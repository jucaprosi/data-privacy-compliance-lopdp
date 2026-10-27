# ¤¤security-engineer
"""CAPA-01: casos de acciones correctivas (CAPA) persistidos en PostgreSQL con RLS por organización. ¤capa ¤rbac-tenant"""
from alembic import op
import sqlalchemy as sa

revision = "20261027_capa_tickets"
down_revision = "20261025_biblioteca_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capa_tickets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("control_id", sa.String(length=128), nullable=False),
        sa.Column("severidad", sa.String(length=64), nullable=False),
        sa.Column("descripcion_hallazgo", sa.Text(), nullable=False),
        sa.Column(
            "causa_raiz",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("accion_correctiva", sa.Text(), nullable=False),
        sa.Column("responsable_implementacion_id", sa.String(), nullable=False),
        sa.Column(
            "creado_por",
            sa.String(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("auditor_verificador_id", sa.String(), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'ABIERTO'"),
        ),
        sa.Column("evidencia_cierre_id", sa.String(), nullable=True),
        sa.Column(
            "snapshot_normativo",
            sa.String(length=128),
            nullable=False,
            server_default=sa.text("'LOPDP-Ecuador-2021'"),
        ),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_capa_tickets_tenant_id", "capa_tickets", ["tenant_id"])
    op.execute("ALTER TABLE capa_tickets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE capa_tickets FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_capa_tickets ON capa_tickets "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON capa_tickets FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON capa_tickets TO lopdp_app")


def downgrade() -> None:
    op.drop_index("ix_capa_tickets_tenant_id", table_name="capa_tickets")
    op.drop_table("capa_tickets")
