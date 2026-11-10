# ¤¤backend-developer
"""ORG-17: inventario de activos y sistemas, soportes y personas mínimas, por organización. ¤rbac-tenant ¤inventario"""
from alembic import op
import sqlalchemy as sa

revision = "20261109_inventario_activos"
down_revision = "20261030_diag_asignaciones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventario_personas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("cargo", sa.String(length=150), nullable=False),
        sa.Column("area_id", sa.String(), sa.ForeignKey("areas.id"), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("cedula_cifrada", sa.Text(), nullable=True),
        sa.Column("archivada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "uq_inventario_personas_email", "inventario_personas",
        ["tenant_id", sa.text("lower(email)")], unique=True,
    )

    op.create_table(
        "inventario_activos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.String(length=1000), nullable=True),
        sa.Column("ubicacion", sa.String(length=200), nullable=True),
        sa.Column("area_id", sa.String(), sa.ForeignKey("areas.id"), nullable=True),
        sa.Column("responsable_id", sa.String(), sa.ForeignKey("inventario_personas.id"), nullable=True),
        sa.Column("archivado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "tipo IN ('sistema', 'soporte_fisico', 'soporte_digital')",
            name="ck_inventario_activos_tipo",
        ),
    )
    op.create_index(
        "uq_inventario_activos_nombre", "inventario_activos",
        ["tenant_id", "tipo", sa.text("lower(nombre)")], unique=True,
    )

    op.create_table(
        "inventario_activos_tratamientos",
        sa.Column("activo_id", sa.String(), sa.ForeignKey("inventario_activos.id"), primary_key=True),
        sa.Column("rat_id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute("ALTER TABLE inventario_personas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inventario_personas FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_inventario_personas ON inventario_personas "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("ALTER TABLE inventario_activos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inventario_activos FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_inventario_activos ON inventario_activos "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("ALTER TABLE inventario_activos_tratamientos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inventario_activos_tratamientos FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_inventario_activos_tratamientos ON inventario_activos_tratamientos "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )

    # Permisos mínimos: personas y activos se archivan, nunca se borran; los vínculos sí se quitan.
    op.execute("REVOKE ALL ON inventario_personas FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON inventario_personas TO lopdp_app")
    op.execute("REVOKE ALL ON inventario_activos FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON inventario_activos TO lopdp_app")
    op.execute("REVOKE ALL ON inventario_activos_tratamientos FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON inventario_activos_tratamientos TO lopdp_app")


def downgrade() -> None:
    op.drop_table("inventario_activos_tratamientos")
    op.drop_index("uq_inventario_activos_nombre", table_name="inventario_activos")
    op.drop_table("inventario_activos")
    op.drop_index("uq_inventario_personas_email", table_name="inventario_personas")
    op.drop_table("inventario_personas")
