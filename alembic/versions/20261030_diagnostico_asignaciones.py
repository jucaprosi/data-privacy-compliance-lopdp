"""Asignación de dominios del assessment a encargados del diagnóstico, con RLS (DIAG-04). ¤diagnostico-asignacion

Tabla append-only: la asignación vigente de una dimensión es su última fila (R2); un responsable nulo la
desasigna. Los dominios asignables son las diez dimensiones D01-D10. `lopdp_app` solo lee e inserta.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_diag_asignaciones"
down_revision = "20261029_evidencias_documentales"
branch_labels = None
depends_on = None

TABLA = "diagnostico_asignaciones"


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("dimension", sa.String(3), nullable=False),
        sa.Column("responsable_user_id", sa.String(), nullable=True),
        sa.Column("asignado_por", sa.String(), nullable=False),
        sa.Column("asignado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("dimension ~ '^D(0[1-9]|10)$'", name="ck_diag_asig_dimension"),
    )
    op.create_index("ix_diag_asig_tenant_dim", TABLA, ["tenant_id", "dimension", sa.text("asignado_en DESC")])
    op.execute(f"ALTER TABLE {TABLA} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLA} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation_{TABLA} ON {TABLA} "
        "USING (tenant_id = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))"
    )
    op.execute(f"GRANT SELECT, INSERT ON {TABLA} TO lopdp_app")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{TABLA} ON {TABLA}")
    op.drop_table(TABLA)
