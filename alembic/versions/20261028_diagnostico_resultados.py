# ¤¤security-engineer
"""DIAG-03: resultados sellados del diagnóstico, por organización, sin edición ni borrado. ¤diagnostico ¤rbac-tenant

El DPO sella; la huella SHA-256 se encadena por organización (secuencia 1, 2, 3...). La aplicación
(lopdp_app) solo puede leer e insertar: un resultado sellado no se edita ni se borra.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261028_diagnostico_resultados"
down_revision = "20261027_capa_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostico_resultados",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("secuencia", sa.Integer(), nullable=False),
        sa.Column("sellado_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sellado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("normativa", sa.String(length=32), nullable=False),
        sa.Column("version_normativa", sa.String(length=64), nullable=False),
        sa.Column("tamano", sa.String(length=32), nullable=False),
        sa.Column("perfil", postgresql.JSONB(), nullable=False),
        sa.Column("respuestas", postgresql.JSONB(), nullable=False),
        sa.Column("indicadores", postgresql.JSONB(), nullable=False),
        sa.Column("huella_anterior", sa.String(length=64), nullable=False),
        sa.Column("huella", sa.String(length=64), nullable=False),
        sa.CheckConstraint("secuencia >= 1", name="ck_diagnostico_resultados_secuencia"),
        # Una cadena lineal por organización: dos sellados no pueden colgar del mismo eslabón.
        sa.UniqueConstraint("tenant_id", "secuencia", name="uq_diagnostico_resultados_secuencia"),
        sa.UniqueConstraint("tenant_id", "huella_anterior", name="uq_diagnostico_resultados_eslabon"),
    )
    op.execute("ALTER TABLE diagnostico_resultados ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE diagnostico_resultados FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_diagnostico_resultados ON diagnostico_resultados "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON diagnostico_resultados FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON diagnostico_resultados TO lopdp_app")


def downgrade() -> None:
    op.drop_table("diagnostico_resultados")
