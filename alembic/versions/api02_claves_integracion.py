# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""API-02: Claves de integración por organización con techo del paquete. ¤api-integraciones ¤seguridad-tenant

Revision ID: api02_claves_integracion
Revises: bov02_boveda_objetos_custodia
Create Date: 2026-11-16

Tabla `claves_integracion` con RLS forzada (tenant_id, nombre, prefijo, hash_sha256, alcances[], creada_en, rotada_en, revocada_en).
Trigger que impide modificar hash_sha256 y prefijo en UPDATE.
Permisos: SELECT, INSERT y UPDATE (rotada_en, revocada_en) a lopdp_app, sin DELETE.
"""
from alembic import op

revision = "api02_claves_integracion"
down_revision = "bov02_boveda_objetos_custodia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE claves_integracion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            nombre VARCHAR(120) NOT NULL CHECK (length(trim(nombre)) >= 1),
            prefijo VARCHAR(16) NOT NULL,
            hash_sha256 VARCHAR(64) NOT NULL UNIQUE,
            alcances TEXT[] NOT NULL DEFAULT '{}',
            creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            rotada_en TIMESTAMPTZ NULL,
            revocada_en TIMESTAMPTZ NULL
        );

        CREATE INDEX ix_claves_integracion_tenant_hash ON claves_integracion (tenant_id, hash_sha256);

        ALTER TABLE claves_integracion ENABLE ROW LEVEL SECURITY;
        ALTER TABLE claves_integracion FORCE ROW LEVEL SECURITY;

        CREATE POLICY claves_integracion_tenant_isolation ON claves_integracion
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        CREATE OR REPLACE FUNCTION fn_claves_integracion_inmutables()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.hash_sha256 IS DISTINCT FROM OLD.hash_sha256 THEN
                RAISE EXCEPTION 'No se permite modificar el hash_sha256 de una clave de integracion';
            END IF;
            IF NEW.prefijo IS DISTINCT FROM OLD.prefijo THEN
                RAISE EXCEPTION 'No se permite modificar el prefijo de una clave de integracion';
            END IF;
            IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id THEN
                RAISE EXCEPTION 'No se permite modificar el tenant_id de una clave de integracion';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id THEN
                RAISE EXCEPTION 'No se permite modificar el id de una clave de integracion';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_claves_integracion_inmutables
        BEFORE UPDATE ON claves_integracion
        FOR EACH ROW
        EXECUTE FUNCTION fn_claves_integracion_inmutables();

        GRANT SELECT, INSERT ON claves_integracion TO lopdp_app;
        GRANT UPDATE (rotada_en, revocada_en) ON claves_integracion TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_claves_integracion_inmutables ON claves_integracion;
        DROP FUNCTION IF EXISTS fn_claves_integracion_inmutables();
        DROP TABLE IF EXISTS claves_integracion CASCADE;
        """
    )
