# ¤¤security-engineer
"""DIAG-12: estados del diagnóstico, cortes sellados que parten del diagnóstico real. ¤diagnostico ¤rbac-tenant

Después del diagnóstico real (DIAG-11) no se repite el diagnóstico: el DPO emite estados. Cada estado
guarda la fecha de corte, quién lo emitió, los niveles por control y por dimensión, las tareas cerradas
con evidencia validada que sumó y una huella SHA-256 encadenada por organización (secuencia 1, 2, 3...).
La aplicación (lopdp_app) solo puede leer e insertar: un estado sellado no se edita ni se borra, y esta
tabla no toca `diagnostico_resultados`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261107_diagnostico_estados"
down_revision = "20261109_inventario_activos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostico_estados",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("secuencia", sa.Integer(), nullable=False),
        sa.Column("emitido_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fecha_corte", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resultado_real_id", sa.String(), nullable=False),
        sa.Column("escala", sa.String(length=32), nullable=False),
        sa.Column("respuestas", postgresql.JSONB(), nullable=False),
        sa.Column("tareas", postgresql.JSONB(), nullable=False),
        sa.Column("indicadores", postgresql.JSONB(), nullable=False),
        sa.Column("huella_anterior", sa.String(length=64), nullable=False),
        sa.Column("huella", sa.String(length=64), nullable=False),
        sa.CheckConstraint("secuencia >= 1", name="ck_diagnostico_estados_secuencia"),
        # Una cadena lineal por organización: dos estados no pueden colgar del mismo eslabón.
        sa.UniqueConstraint("tenant_id", "secuencia", name="uq_diagnostico_estados_secuencia"),
        sa.UniqueConstraint("tenant_id", "huella_anterior", name="uq_diagnostico_estados_eslabon"),
    )
    op.create_index("ix_diagnostico_estados_tenant", "diagnostico_estados", ["tenant_id"])
    op.execute("ALTER TABLE diagnostico_estados ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE diagnostico_estados FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_diagnostico_estados ON diagnostico_estados "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON diagnostico_estados FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON diagnostico_estados TO lopdp_app")


def downgrade() -> None:
    op.drop_table("diagnostico_estados")
