# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤developer-architect
"""API-02b: Suscripciones a webhooks firmados HMAC-SHA256 con RLS forzada. ¤api-integraciones ¤seguridad-tenant

Revision ID: api02b_webhooks_suscripciones
Revises: api02_claves_integracion
Create Date: 2026-11-19

Tabla `webhooks_suscripciones` con RLS ENABLE + FORCE por `tenant_id`.
Permisos para `lopdp_app`: SELECT, INSERT, UPDATE (sin DELETE).
"""
from alembic import op

revision = "api02b_webhooks_suscripciones"
down_revision = "api02_claves_integracion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE webhooks_suscripciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            url TEXT NOT NULL CHECK (url LIKE 'https://%'),
            eventos TEXT[] NOT NULL CHECK (cardinality(eventos) >= 1),
            secreto_cifrado TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            rotada_en TIMESTAMPTZ NULL
        );

        CREATE INDEX ix_webhooks_suscripciones_tenant_activo
            ON webhooks_suscripciones (tenant_id, activo);

        ALTER TABLE webhooks_suscripciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE webhooks_suscripciones FORCE ROW LEVEL SECURITY;

        CREATE POLICY webhooks_suscripciones_tenant_isolation ON webhooks_suscripciones
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        REVOKE ALL ON webhooks_suscripciones FROM lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON webhooks_suscripciones TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS webhooks_suscripciones_tenant_isolation ON webhooks_suscripciones;
        DROP TABLE IF EXISTS webhooks_suscripciones CASCADE;
        """
    )
