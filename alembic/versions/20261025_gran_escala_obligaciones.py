"""MTGE-02: Tablas de obligaciones de tratamiento a gran escala.

Res. SPDP-SPD-2026-0005-R:
- Art. 17: auditorías al menos cada 12 meses, informes conservados 5 años.
- Art. 18: informes anuales de cumplimiento conservados 5 años; política de privacidad.
- Disposición transitoria: 90 días desde vigencia para DPO.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261025_gran_escala_obligacion"
down_revision = "20261024_rat_eipd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Tabla de configuración de vigencia MTGE por tenant (para el cómputo de la disposición transitoria)
    op.create_table(
        "mtge_configuracion_vigencia",
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), primary_key=True),
        sa.Column("fecha_vigencia_norma", sa.Date(), nullable=False),
        sa.Column("registrado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("ALTER TABLE mtge_configuracion_vigencia ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mtge_configuracion_vigencia FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_mtge_configuracion_vigencia ON mtge_configuracion_vigencia "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON mtge_configuracion_vigencia TO lopdp_app")

    # 2. Tabla de auditorías de gran escala (Art. 17)
    op.create_table(
        "mtge_auditorias",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("fecha_auditoria", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(32), nullable=False),
        sa.Column("alcance", sa.Text(), nullable=False),
        sa.Column("auditor", sa.String(255), nullable=False),
        sa.Column("archivo_informe", sa.String(512), nullable=True),
        sa.Column("es_certificacion_equivalente", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("certificacion_nombre", sa.String(255), nullable=True),
        sa.Column("certificacion_vigente_hasta", sa.Date(), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=False),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tipo IN ('interna', 'externa')", name="ck_mtge_auditorias_tipo"),
    )
    op.create_index("ix_mtge_auditorias_tenant", "mtge_auditorias", ["tenant_id", "fecha_auditoria"])
    op.execute("ALTER TABLE mtge_auditorias ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mtge_auditorias FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_mtge_auditorias ON mtge_auditorias "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mtge_auditorias TO lopdp_app")

    # 3. Tabla de informes anuales de cumplimiento (Art. 18)
    op.create_table(
        "mtge_informes_anuales",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("fecha_aprobacion", sa.Date(), nullable=False),
        sa.Column("archivo_informe", sa.String(512), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("anio >= 2020 AND anio <= 2100", name="ck_mtge_informes_anio"),
    )
    op.create_index("ix_mtge_informes_anuales_tenant", "mtge_informes_anuales", ["tenant_id", "anio"])
    op.execute("ALTER TABLE mtge_informes_anuales ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mtge_informes_anuales FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_mtge_informes_anuales ON mtge_informes_anuales "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mtge_informes_anuales TO lopdp_app")

    # 4. Tabla de constancia de política de privacidad (Art. 18)
    op.create_table(
        "mtge_politica_privacidad",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("fecha_emision", sa.Date(), nullable=False),
        sa.Column("enlace_o_archivo", sa.String(512), nullable=False),
        sa.Column("identifica_gran_escala", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mtge_politica_privacidad_tenant", "mtge_politica_privacidad", ["tenant_id", "fecha_emision"])
    op.execute("ALTER TABLE mtge_politica_privacidad ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE mtge_politica_privacidad FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_mtge_politica_privacidad ON mtge_politica_privacidad "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON mtge_politica_privacidad TO lopdp_app")


def downgrade() -> None:
    op.drop_table("mtge_politica_privacidad")
    op.drop_table("mtge_informes_anuales")
    op.drop_table("mtge_auditorias")
    op.drop_table("mtge_configuracion_vigencia")
