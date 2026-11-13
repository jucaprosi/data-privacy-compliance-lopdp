# ¤¤backend-developer
"""ORG-20: exportaciones completas de la organización (la papelera no crea tablas: usa `retirado_en`). ¤rbac-tenant ¤seguridad"""
from alembic import op
import sqlalchemy as sa

revision = "org20_papelera"
down_revision = "20261109_der04_contraccion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exportaciones",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("solicitado_por", sa.String(), nullable=False),
        sa.Column("solicitada_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("lista_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("r2_key", sa.String(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("caduca_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("estado", sa.String(length=10), nullable=False, server_default="pendiente"),
        sa.CheckConstraint("estado IN ('pendiente','lista','caducada')", name="ck_exportaciones_estado"),
    )
    # 409 EXPORTACION_EN_CURSO: una sola pendiente por organización, también ante carreras.
    op.create_index(
        "uq_exportaciones_pendiente", "exportaciones", ["tenant_id"], unique=True,
        postgresql_where=sa.text("estado = 'pendiente'"),
    )
    op.execute("ALTER TABLE exportaciones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE exportaciones FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_exportaciones ON exportaciones "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    # Permisos mínimos: nada se borra.
    op.execute("REVOKE ALL ON exportaciones FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON exportaciones TO lopdp_app")


def downgrade() -> None:
    op.drop_index("uq_exportaciones_pendiente", table_name="exportaciones")
    op.drop_table("exportaciones")
