"""Objeciones del DPO a las respuestas del diagnóstico, con RLS (DIAG-07). ¤diagnostico ¤dpo-independencia

Tabla append-only salvo `resuelta_en`, que el servidor fija cuando el respondiente vuelve a guardar la
pregunta. Una objeción abierta (resuelta_en nulo) impide sellar. `lopdp_app` lee, inserta y solo actualiza
esa columna.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_diag_objeciones"
down_revision = "20261109_inventario_activos"
branch_labels = None
depends_on = None

TABLA = "diagnostico_objeciones"


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("pregunta_id", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("objetado_por", sa.String(), nullable=False),
        sa.Column("objetado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resuelta_en", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("pregunta_id BETWEEN 1 AND 80", name="ck_diag_obj_pregunta"),
        sa.CheckConstraint("length(trim(motivo)) >= 20", name="ck_diag_obj_motivo"),
    )
    op.create_index("ix_diag_obj_tenant_pregunta", TABLA, ["tenant_id", "pregunta_id", sa.text("objetado_en DESC")])
    op.execute(f"ALTER TABLE {TABLA} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLA} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation_{TABLA} ON {TABLA} "
        "USING (tenant_id = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))"
    )
    op.execute(f"GRANT SELECT, INSERT ON {TABLA} TO lopdp_app")
    op.execute(f"GRANT UPDATE (resuelta_en) ON {TABLA} TO lopdp_app")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{TABLA} ON {TABLA}")
    op.drop_table(TABLA)
