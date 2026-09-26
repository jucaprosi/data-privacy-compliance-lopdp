"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-09-16 23:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Crear tabla derechos_arco_solicitudes
    op.create_table(
        'derechos_arco_solicitudes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('titular_id', sa.String(length=100), nullable=False),
        sa.Column('tipo_derecho', sa.String(length=50), nullable=False),
        sa.Column('estado', sa.String(length=50), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Crear tabla transferencias_terceros
    op.create_table(
        'transferencias_terceros',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tercero_nombre', sa.String(length=255), nullable=False),
        sa.Column('pais_destino', sa.String(length=100), nullable=False),
        sa.Column('nivel_adecuacion', sa.String(length=50), nullable=False),
        sa.Column('fecha_registro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Activar RLS en derechos_arco_solicitudes (CRITICO)
    op.execute("ALTER TABLE derechos_arco_solicitudes ENABLE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY tenant_isolation_policy ON derechos_arco_solicitudes USING (tenant_id = current_setting('app.current_tenant_id')::uuid);")
    
    # Activar RLS en transferencias_terceros para mantener consistencia
    op.execute("ALTER TABLE transferencias_terceros ENABLE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY tenant_isolation_policy_terceros ON transferencias_terceros USING (tenant_id = current_setting('app.current_tenant_id')::uuid);")

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy_terceros ON transferencias_terceros;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON derechos_arco_solicitudes;")
    op.drop_table('transferencias_terceros')
    op.drop_table('derechos_arco_solicitudes')
