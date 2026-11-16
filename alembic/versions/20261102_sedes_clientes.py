# ¤¤backend-developer
"""ORG-18: sedes de la organización y clientes cuando actúa como encargada, por organización. ¤rbac-tenant ¤inventario"""
from alembic import op
import sqlalchemy as sa

revision = "20261102_sedes_clientes"
down_revision = "20261107_diagnostico_estados"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sedes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("direccion", sa.String(length=300), nullable=False),
        sa.Column("ciudad", sa.String(length=120), nullable=False),
        sa.Column("provincia", sa.String(length=120), nullable=False),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("contacto_spdp", sa.Text(), nullable=True),
        sa.Column("contacto_titulares", sa.Text(), nullable=True),
        sa.Column("medidas", sa.Text(), nullable=True),
        sa.Column("retirada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # R1: una sola sede principal vigente por organización.
    op.create_index(
        "uq_sedes_principal", "sedes", ["tenant_id"], unique=True,
        postgresql_where=sa.text("es_principal AND retirada_en IS NULL"),
    )

    op.create_table(
        "clientes_encargo",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("razon_social", sa.String(length=200), nullable=False),
        sa.Column("ruc", sa.String(length=13), nullable=False),
        sa.Column("contrato_sha256", sa.String(length=64), nullable=True),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("retirado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "uq_clientes_encargo_ruc", "clientes_encargo", ["tenant_id", "ruc"], unique=True,
        postgresql_where=sa.text("retirado_en IS NULL"),
    )

    op.execute("ALTER TABLE sedes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sedes FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_sedes ON sedes "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("ALTER TABLE clientes_encargo ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE clientes_encargo FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_clientes_encargo ON clientes_encargo "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )

    # Permisos mínimos: nada se borra, se retira.
    op.execute("REVOKE ALL ON sedes FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON sedes TO lopdp_app")
    op.execute("REVOKE ALL ON clientes_encargo FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON clientes_encargo TO lopdp_app")


def downgrade() -> None:
    op.drop_index("uq_clientes_encargo_ruc", table_name="clientes_encargo")
    op.drop_table("clientes_encargo")
    op.drop_index("uq_sedes_principal", table_name="sedes")
    op.drop_table("sedes")
