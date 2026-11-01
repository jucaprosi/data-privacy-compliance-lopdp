# ¤¤security-engineer
"""RM-23: recordatorios de vencimiento enviados, para no repetirlos. ¤roadmap ¤rbac-tenant

- `recordatorios_enviados` por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por tenant_id).
  La aplicación (lopdp_app) solo lee e inserta. Sin clave foránea a la tarea: es un registro de envíos.

Contrato: governance/especificaciones/RM-23.md §1.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261107_recordatorios"
down_revision = "20261102_rat_versiones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recordatorios_enviados",
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("tarea_id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(length=8), nullable=False),
        sa.Column("dia", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "tarea_id", "tipo", "dia"),
        sa.CheckConstraint("tipo IN ('7dias','hoy','vencida')", name="ck_recordatorios_enviados_tipo"),
    )
    op.execute("ALTER TABLE recordatorios_enviados ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE recordatorios_enviados FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_recordatorios_enviados ON recordatorios_enviados "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON recordatorios_enviados FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON recordatorios_enviados TO lopdp_app")


def downgrade() -> None:
    op.drop_table("recordatorios_enviados")
