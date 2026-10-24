# ¤¤security-engineer
"""RAT-01: inventario persistido y RLS forzado por organización. ¤rat ¤rbac-tenant"""
from alembic import op
import sqlalchemy as sa

revision = "20261024_rat_actividades"
down_revision = "20261023_rls_pendientes"
branch_labels = None
depends_on = None


# ¤rat
def upgrade() -> None:
    op.create_table(
        "rat_actividades",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        *[sa.Column(c, sa.Text(), nullable=False) for c in (
            "codigo", "nombre", "area_responsable", "finalidad", "base_legal",
            "medio_soporte", "pais_transferencia", "plazo_conservacion",
            "nivel_riesgo", "observaciones_dpo", "origen",
        )],
        *[sa.Column(c, sa.JSON(), nullable=False) for c in (
            "categorias_titulares", "categorias_datos", "encargados",
            "destinatarios", "medidas_seguridad",
        )],
        *[sa.Column(c, sa.Boolean(), nullable=False) for c in (
            "datos_sensibles", "transferencia_internacional", "requiere_eipd",
            "es_gran_escala", "decisiones_automatizadas",
        )],
        sa.Column("volumen_titulares_estimado", sa.Integer(), nullable=False),
        sa.Column("volumen_titulares_12_meses", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("volumen_titulares_estimado >= 0 AND "
                           "volumen_titulares_12_meses >= 0", name="ck_rat_volumen"),
        sa.CheckConstraint("version > 0", name="ck_rat_version"),
        sa.CheckConstraint("origen = 'manual' OR origen ~ '^plantilla:[^:[:space:]]+$'",
                           name="ck_rat_origen"),
    )
    op.create_index("ix_rat_actividades_tenant_id", "rat_actividades", ["tenant_id"])
    op.execute("ALTER TABLE rat_actividades ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rat_actividades FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_rat_actividades ON rat_actividades "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON rat_actividades TO lopdp_app")


# ¤rat
def downgrade() -> None:
    op.drop_index("ix_rat_actividades_tenant_id", table_name="rat_actividades")
    op.drop_table("rat_actividades")
