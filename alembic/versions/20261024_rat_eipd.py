"""RAT-03: EIPD y riesgos persistentes con aislamiento forzado por tenant."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261024_rat_eipd"
down_revision = "20261024_diag_respuestas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("rat_eipd",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("rat_id", sa.String(), sa.ForeignKey("rat_actividades.id"), nullable=False),
        sa.Column("estado", sa.String(), nullable=False), sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("volumen_titulares_aprobacion", sa.Integer(), nullable=False),
        sa.Column("categorias_datos_aprobacion", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("aprobada_por", sa.String()),
        sa.Column("aprobada_en", sa.DateTime(timezone=True)),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizada_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estado IN ('BORRADOR','APROBADA','REQUIERE_ACTUALIZACION')", name="ck_rat_eipd_estado"),
        sa.CheckConstraint("volumen_titulares_aprobacion >= 0", name="ck_rat_eipd_volumen"))
    op.create_index("ix_rat_eipd_tenant_rat", "rat_eipd", ["tenant_id", "rat_id"])
    op.create_table("rat_eipd_riesgos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("eipd_id", sa.String(), sa.ForeignKey("rat_eipd.id", ondelete="CASCADE"), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False), sa.Column("probabilidad", sa.Integer(), nullable=False),
        sa.Column("impacto", sa.Integer(), nullable=False), sa.Column("puntuacion", sa.Integer(), nullable=False),
        sa.Column("nivel", sa.String(), nullable=False), sa.Column("medida", sa.Text(), nullable=False),
        sa.CheckConstraint("probabilidad BETWEEN 1 AND 5 AND impacto BETWEEN 1 AND 5", name="ck_rat_eipd_riesgo_escalas"),
        sa.CheckConstraint("puntuacion = probabilidad * impacto", name="ck_rat_eipd_riesgo_producto"))
    op.create_index("ix_rat_eipd_riesgos_tenant", "rat_eipd_riesgos", ["tenant_id", "eipd_id"])
    op.execute("ALTER TABLE rat_eipd ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rat_eipd FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_rat_eipd ON rat_eipd USING (tenant_id::text = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))")
    op.execute("GRANT SELECT, INSERT, UPDATE ON rat_eipd TO lopdp_app")
    op.execute("ALTER TABLE rat_eipd_riesgos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rat_eipd_riesgos FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_rat_eipd_riesgos ON rat_eipd_riesgos USING (tenant_id::text = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))")
    op.execute("GRANT SELECT, INSERT, UPDATE ON rat_eipd_riesgos TO lopdp_app")


def downgrade() -> None:
    op.drop_table("rat_eipd_riesgos")
    op.drop_table("rat_eipd")
