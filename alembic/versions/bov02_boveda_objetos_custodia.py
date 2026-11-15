# ¤¤backend-developer
"""BOV-02: registro de custodia de objetos de la bóveda dual. ¤boveda-cloud ¤conservacion

Revision ID: bov02_boveda_objetos_custodia
Revises: ret02_clave_objeto

Primera migración propia de la sala `boveda_cloud`: cuelga de BASE_COMUN y abre su rama.

`boveda_objetos_custodia`: un registro por objeto que la plataforma entrega a Cloud Storage con URL firmada.
Con `retencion_dias` menor de 30 va al bucket de vida corta (sin Autoclass, sin bloqueo); con 30 o más, al de
retención larga con Autoclass y bloqueo WORM hasta `worm_lock_hasta`. RLS ENABLE y FORCE por tenant; `lopdp_app`
solo lee e inserta: el registro de custodia no se edita ni se borra.
"""
from alembic import op

revision = "bov02_boveda_objetos_custodia"
down_revision = "ret02_clave_objeto"
branch_labels = ("boveda_cloud",)
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE boveda_objetos_custodia (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            categoria VARCHAR(40) NOT NULL CHECK (categoria ~ '^[a-z0-9][a-z0-9_-]{0,39}$'),
            bucket_destino VARCHAR(63) NOT NULL
                CHECK (bucket_destino IN ('lopdp360-vault-short-ttl', 'lopdp360-vault-long-retention')),
            storage_class VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
            autoclass_activo BOOLEAN NOT NULL,
            worm_lock_hasta TIMESTAMPTZ,
            retencion_dias INTEGER NOT NULL CHECK (retencion_dias > 0),
            sha256_original VARCHAR(64) NOT NULL CHECK (sha256_original ~ '^[0-9a-f]{64}$'),
            tamano_bytes BIGINT NOT NULL CHECK (tamano_bytes > 0),
            creado_por VARCHAR,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT boveda_objetos_tier_corto CHECK (
                retencion_dias >= 30 OR (bucket_destino = 'lopdp360-vault-short-ttl'
                    AND autoclass_activo = false AND worm_lock_hasta IS NULL)),
            CONSTRAINT boveda_objetos_tier_largo CHECK (
                retencion_dias < 30 OR (bucket_destino = 'lopdp360-vault-long-retention'
                    AND autoclass_activo = true AND worm_lock_hasta IS NOT NULL))
        );
        CREATE INDEX ix_boveda_objetos_custodia_tenant ON boveda_objetos_custodia (tenant_id, creado_en);
        ALTER TABLE boveda_objetos_custodia ENABLE ROW LEVEL SECURITY;
        ALTER TABLE boveda_objetos_custodia FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_boveda_objetos_custodia ON boveda_objetos_custodia
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON boveda_objetos_custodia FROM lopdp_app;
        GRANT SELECT, INSERT ON boveda_objetos_custodia TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS boveda_objetos_custodia")
