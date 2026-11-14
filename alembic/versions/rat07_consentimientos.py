# ¤¤security-engineer
"""RAT-07: colectivos de titulares y registro agregado de consentimientos. ¤rat ¤evidencias ¤rbac-tenant

- `colectivos_titulares`: grupo de titulares por tratamiento (clientes, empleados...). Sin identidad de personas.
- `consentimientos_registro`: evento agregado (fecha, colectivo, canal, cantidad). Append-only: `lopdp_app` solo
  lee e inserta. `colectivos_titulares` admite además UPDATE.
- RLS ENABLE y FORCE, USING y WITH CHECK por tenant_id.

Contrato: governance/especificaciones/RAT-07.md §1.
"""
from alembic import op
import sqlalchemy as sa

revision = "rat07_consentimientos"
down_revision = "dlp01_escaneos_muestreados"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "colectivos_titulares",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("tratamiento_id", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("base_legitimacion", sa.String(32), nullable=False),
        sa.Column("texto_version", sa.String(16), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_colectivos_titulares_tenant_tratamiento", "colectivos_titulares",
                    ["tenant_id", "tratamiento_id"])
    op.create_table(
        "consentimientos_registro",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("colectivo_id", sa.String(), sa.ForeignKey("colectivos_titulares.id"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("canal", sa.String(16), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("texto_version", sa.String(16), nullable=True),
        sa.Column("registrado_por", sa.String(), nullable=True),
        sa.Column("registrado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("canal IN ('web','presencial','telefono','otro')", name="ck_consentimientos_canal"),
        sa.CheckConstraint("cantidad > 0", name="ck_consentimientos_cantidad"),
    )
    op.create_index("ix_consentimientos_registro_colectivo_fecha", "consentimientos_registro",
                    ["tenant_id", "colectivo_id", "fecha"])
    op.execute("ALTER TABLE colectivos_titulares ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE colectivos_titulares FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_colectivos_titulares ON colectivos_titulares "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON colectivos_titulares FROM lopdp_app")
    op.execute("ALTER TABLE consentimientos_registro ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE consentimientos_registro FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_consentimientos_registro ON consentimientos_registro "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON consentimientos_registro FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON colectivos_titulares TO lopdp_app")
    op.execute("GRANT SELECT, INSERT ON consentimientos_registro TO lopdp_app")


def downgrade() -> None:
    op.drop_table("consentimientos_registro")
    op.drop_table("colectivos_titulares")
