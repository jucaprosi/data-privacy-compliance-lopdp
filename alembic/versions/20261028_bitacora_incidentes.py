# ¤¤security-engineer
"""INC-01: bitácora de incidentes por organización, sin edición ni borrado. ¤incidentes ¤rbac-tenant

La huella SHA-256 se encadena por organización (secuencia 1, 2, 3...). La aplicación (lopdp_app)
solo puede leer e insertar: un incidente registrado no se edita ni se borra.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261028_bitacora_incidentes"
down_revision = "20261028_diagnostico_resultados"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidentes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("secuencia", sa.Integer(), nullable=False),
        sa.Column("fecha_deteccion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("severidad", sa.String(length=16), nullable=False),
        sa.Column("afecta_datos_personales", sa.Boolean(), nullable=False),
        sa.Column("categorias_datos", postgresql.JSONB(), nullable=False),
        sa.Column("medidas_inmediatas", sa.Text(), nullable=False),
        sa.Column("registrado_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("huella_anterior", sa.String(length=64), nullable=False),
        sa.Column("huella", sa.String(length=64), nullable=False),
        sa.CheckConstraint("secuencia >= 1", name="ck_incidentes_secuencia"),
        sa.CheckConstraint(
            "severidad IN ('Baja', 'Media', 'Alta', 'Crítica')", name="ck_incidentes_severidad"
        ),
        # Una cadena lineal por organización: dos registros no pueden colgar del mismo eslabón.
        sa.UniqueConstraint("tenant_id", "secuencia", name="uq_incidentes_secuencia"),
        sa.UniqueConstraint("tenant_id", "huella_anterior", name="uq_incidentes_eslabon"),
    )
    op.execute("ALTER TABLE incidentes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE incidentes FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_incidentes ON incidentes "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON incidentes FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON incidentes TO lopdp_app")


def downgrade() -> None:
    op.drop_table("incidentes")
