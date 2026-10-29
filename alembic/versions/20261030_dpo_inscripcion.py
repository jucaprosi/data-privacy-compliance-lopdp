# ¤¤security-engineer
"""DPO-02: historial de inscripción del delegado ante la SPDP, por organización y solo de alta. ¤dpo-informe-anual ¤rbac-tenant"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_dpo_inscripcion"
down_revision = "20261030_hallazgos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dpo_inscripciones",
        sa.Column("orden", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("inscrito", sa.Boolean(), nullable=False),
        sa.Column("fecha_inscripcion", sa.Date(), nullable=True),
        sa.Column("numero_tramite", sa.String(length=60), nullable=True),
        sa.Column("registrado_por", sa.String(), nullable=False),
        sa.Column(
            "registrado_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "(inscrito AND fecha_inscripcion IS NOT NULL AND numero_tramite IS NOT NULL) "
            "OR (NOT inscrito AND fecha_inscripcion IS NULL AND numero_tramite IS NULL)",
            name="ck_dpo_inscripciones_coherente",
        ),
    )
    op.create_index("ix_dpo_inscripciones_tenant_orden", "dpo_inscripciones", ["tenant_id", "orden"])
    op.execute("ALTER TABLE dpo_inscripciones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dpo_inscripciones FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_dpo_inscripciones ON dpo_inscripciones "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    # Historial append-only: lopdp_app solo lee y agrega; nunca edita ni borra (42501).
    op.execute("REVOKE ALL ON dpo_inscripciones FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON dpo_inscripciones TO lopdp_app")


def downgrade() -> None:
    op.drop_index("ix_dpo_inscripciones_tenant_orden", table_name="dpo_inscripciones")
    op.drop_table("dpo_inscripciones")
