"""Respuestas del diagnóstico aisladas por tenant."""
from alembic import op
import sqlalchemy as sa

revision = "20261024_diag_respuestas"
down_revision = "20261023_rls_pendientes"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("diagnostico_respuestas", sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("pregunta_id", sa.Integer(), nullable=False), sa.Column("control_ref", sa.String(3), nullable=False), sa.Column("dimension", sa.String(3), nullable=False), sa.Column("estado", sa.String(20), nullable=False), sa.Column("nivel_evidencia", sa.Integer(), nullable=False), sa.Column("criticidad", sa.Integer(), nullable=False), sa.Column("respondido_por", sa.String(), sa.ForeignKey("users.id"), nullable=False), sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("tenant_id", "pregunta_id"))
    op.execute("ALTER TABLE diagnostico_respuestas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE diagnostico_respuestas FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_diagnostico_respuestas ON diagnostico_respuestas USING (tenant_id::text = current_setting('app.current_tenant_id', true))")
    op.execute("GRANT SELECT, INSERT, UPDATE ON diagnostico_respuestas TO lopdp_app")

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_diagnostico_respuestas ON diagnostico_respuestas")
    op.execute("ALTER TABLE diagnostico_respuestas NO FORCE ROW LEVEL SECURITY")
    op.drop_table("diagnostico_respuestas")
