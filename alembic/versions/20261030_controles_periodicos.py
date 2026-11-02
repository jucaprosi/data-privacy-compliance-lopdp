# ¤¤security-engineer
"""CAPA-02: controles periódicos y sus verificaciones. ¤controles-periodicos ¤auditoria-capa ¤rbac-tenant

- `controles_periodicos` por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por tenant_id).
  La aplicación (lopdp_app) lee, inserta y actualiza; no borra.
- `verificaciones_control`, append-only: lopdp_app solo lee e inserta.

Contrato: governance/especificaciones/CAPA-02.md §1.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_controles_periodicos"
down_revision = "20261030_hallazgos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "controles_periodicos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("control_ref", sa.String(length=5), nullable=True),
        sa.Column("frecuencia", sa.String(length=10), nullable=False),
        sa.Column("responsable_user_id", sa.String(), nullable=False),
        sa.Column("proxima_verificacion", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(length=10), server_default="vigente", nullable=False),
        sa.Column("hallazgo_vigente_id", sa.String(), sa.ForeignKey("hallazgos.id"), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(nombre) BETWEEN 1 AND 200", name="ck_controles_periodicos_nombre"),
        sa.CheckConstraint("control_ref ~ '^P([1-9]|[1-7][0-9]|80)$'", name="ck_controles_periodicos_control_ref"),
        sa.CheckConstraint(
            "frecuencia IN ('mensual','trimestral','semestral','anual')", name="ck_controles_periodicos_frecuencia"
        ),
        sa.CheckConstraint("estado IN ('vigente','vencido','retirado')", name="ck_controles_periodicos_estado"),
    )
    op.create_index("ix_controles_periodicos_tenant_estado", "controles_periodicos", ["tenant_id", "estado"])
    op.create_index(
        "ix_controles_periodicos_responsable", "controles_periodicos", ["tenant_id", "responsable_user_id"]
    )

    op.create_table(
        "verificaciones_control",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("control_id", sa.String(), sa.ForeignKey("controles_periodicos.id"), nullable=False),
        sa.Column("verificado_por", sa.String(), nullable=False),
        sa.Column("verificado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("evidencia_sha256", sa.String(length=64), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
    )
    op.create_index("ix_verificaciones_control_control", "verificaciones_control", ["tenant_id", "control_id"])

    op.execute("ALTER TABLE controles_periodicos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE controles_periodicos FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_controles_periodicos ON controles_periodicos "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON controles_periodicos FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON controles_periodicos TO lopdp_app")

    op.execute("ALTER TABLE verificaciones_control ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE verificaciones_control FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_verificaciones_control ON verificaciones_control "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON verificaciones_control FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON verificaciones_control TO lopdp_app")


def downgrade() -> None:
    op.drop_table("verificaciones_control")
    op.drop_table("controles_periodicos")
