# ¤¤backend-developer
"""ORG-16: perfil ampliado de la organización y personas clave del paso 6, por organización. ¤rbac-tenant ¤alta-organizacion"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_org16_perfil_alta"
down_revision = "20261030_dpo_inscripcion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("naturaleza", sa.String(length=20), nullable=True))
    op.add_column("tenants", sa.Column("rol_datos", sa.String(length=20), nullable=True))
    op.add_column(
        "tenants",
        sa.Column("actividades_riesgo", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.add_column("tenants", sa.Column("provincia", sa.String(length=120), nullable=True))
    op.create_check_constraint(
        "ck_tenants_naturaleza", "tenants",
        "naturaleza IS NULL OR naturaleza IN ('publica', 'privada', 'mixta')",
    )
    op.create_check_constraint(
        "ck_tenants_rol_datos", "tenants",
        "rol_datos IS NULL OR rol_datos IN ('responsable', 'encargado', 'ambos')",
    )

    op.create_table(
        "invitaciones_personas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("cargo", sa.String(length=150), nullable=False),
        sa.Column("area_id", sa.String(), sa.ForeignKey("areas.id"), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("rol_propuesto", sa.String(length=32), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="pendiente"),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "rol_propuesto IN ('coordinador', 'responsable_area', 'dpo')",
            name="ck_invitaciones_personas_rol",
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'aceptada', 'revocada')",
            name="ck_invitaciones_personas_estado",
        ),
    )
    op.create_index(
        "uq_invitaciones_personas_email", "invitaciones_personas",
        ["tenant_id", sa.text("lower(email)")], unique=True,
    )
    op.execute("ALTER TABLE invitaciones_personas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE invitaciones_personas FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_invitaciones_personas ON invitaciones_personas "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    # Permisos mínimos: alta y relectura; el paso 6 repetido actualiza (R3) y nunca borra.
    op.execute("REVOKE ALL ON invitaciones_personas FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON invitaciones_personas TO lopdp_app")


def downgrade() -> None:
    op.drop_index("uq_invitaciones_personas_email", table_name="invitaciones_personas")
    op.drop_table("invitaciones_personas")
    op.drop_constraint("ck_tenants_rol_datos", "tenants", type_="check")
    op.drop_constraint("ck_tenants_naturaleza", "tenants", type_="check")
    op.drop_column("tenants", "provincia")
    op.drop_column("tenants", "actividades_riesgo")
    op.drop_column("tenants", "rol_datos")
    op.drop_column("tenants", "naturaleza")
