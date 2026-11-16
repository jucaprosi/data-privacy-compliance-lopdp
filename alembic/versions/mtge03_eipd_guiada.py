# ¤¤backend-developer
"""MTGE-03: EIPD guiada de ocho pasos y sus puntos por corregir. ¤riesgos-eipd ¤mtge-granescala ¤hallazgos

Revision ID: mtge03_eipd_guiada
Revises: 20261109_der04_contraccion

Tablas por organización con RLS ENABLE y FORCE (USING y WITH CHECK por tenant_id). `lopdp_app` sin DELETE:
`eipd` admite SELECT, INSERT y UPDATE (el UPDATE de una EIPD cerrada lo bloquea la sala); los puntos por
corregir no se editan, solo SELECT e INSERT.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "mtge03_eipd_guiada"
down_revision: Union[str, Sequence[str], None] = "20261109_der04_contraccion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "eipd",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("tratamiento_id", sa.String(), sa.ForeignKey("rat_actividades.id"), nullable=False),
        sa.Column("obligatoria", sa.Boolean(), nullable=False),
        sa.Column("motivo_obligatoriedad", sa.Text(), nullable=False, server_default=""),
        sa.Column("paso_actual", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("consulta_titulares", sa.Text(), nullable=True),
        sa.Column("ciclo_vida", postgresql.JSONB(), nullable=True),
        sa.Column("necesidad", sa.Text(), nullable=True),
        sa.Column("riesgo_inherente", sa.String(8), nullable=True),
        sa.Column("riesgo_residual", sa.String(8), nullable=True),
        sa.Column("decision", sa.String(16), nullable=True),
        sa.Column("decision_texto", sa.Text(), nullable=True),
        sa.Column("informe_sha256", sa.String(64), nullable=True),
        sa.Column("cerrada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("paso_actual BETWEEN 1 AND 8", name="ck_eipd_paso"),
        sa.CheckConstraint("riesgo_inherente IN ('bajo','medio','alto')", name="ck_eipd_inherente"),
        sa.CheckConstraint("riesgo_residual IN ('bajo','medio','alto')", name="ck_eipd_residual"),
        sa.CheckConstraint("decision IN ('aceptar','medidas','consulta_previa')", name="ck_eipd_decision"),
    )
    op.create_index("ix_eipd_tenant_tratamiento", "eipd", ["tenant_id", "tratamiento_id"])
    op.create_table(
        "eipd_incumplimientos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("eipd_id", sa.String(), sa.ForeignKey("eipd.id"), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("hallazgo_id", sa.String(), nullable=True),
    )
    op.create_index("ix_eipd_incumplimientos_eipd", "eipd_incumplimientos", ["tenant_id", "eipd_id"])
    op.execute("ALTER TABLE eipd ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE eipd FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_eipd ON eipd "
               "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
               "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE eipd_incumplimientos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE eipd_incumplimientos FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_eipd_incumplimientos ON eipd_incumplimientos "
               "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
               "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))")
    op.execute("GRANT SELECT, INSERT, UPDATE ON eipd TO lopdp_app")
    op.execute("GRANT SELECT, INSERT ON eipd_incumplimientos TO lopdp_app")


def downgrade() -> None:
    op.drop_table("eipd_incumplimientos")
    op.drop_table("eipd")
