# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""TER-02 · Cuestionario de garantías del encargado por portal externo. ¤seguridad ¤evidencias

Revision ID: 20261107_terceros_cuestionario
Revises: ret02_clave_objeto
Create Date: 2026-11-16

Tabla terceros_cuestionarios y función SECURITY DEFINER para resolución de token.
"""
from alembic import op

revision = "20261107_terceros_cuestionario"
down_revision = "ret02_clave_objeto"
branch_labels = ("terceros",)
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE terceros_cuestionarios (
            id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            tercero_id VARCHAR(64) NOT NULL,
            version_cuestionario VARCHAR(32) NOT NULL DEFAULT 'TER-02.1',
            token_hash VARCHAR(64) UNIQUE NOT NULL,
            caduca_en TIMESTAMPTZ NOT NULL,
            estado VARCHAR(12) NOT NULL CHECK (estado IN ('enviado', 'respondido', 'conforme', 'correccion', 'rechazado')),
            respuestas JSONB NULL,
            evidencias JSONB NULL,
            revisado_por VARCHAR(64) NULL,
            revisado_en TIMESTAMPTZ NULL,
            comentario_revision TEXT NULL,
            informe_sha256 VARCHAR(64) NULL,
            proxima_revision DATE NULL,
            creado_por VARCHAR(64) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX ix_terceros_cuestionarios_tenant ON terceros_cuestionarios (tenant_id);
        CREATE INDEX ix_terceros_cuestionarios_tercero ON terceros_cuestionarios (tenant_id, tercero_id);

        ALTER TABLE terceros_cuestionarios ENABLE ROW LEVEL SECURITY;
        ALTER TABLE terceros_cuestionarios FORCE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation_terceros_cuestionarios ON terceros_cuestionarios
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app') THEN
                GRANT SELECT, INSERT, UPDATE ON terceros_cuestionarios TO lopdp_app;
            END IF;
        END $$;

        CREATE OR REPLACE FUNCTION terceros_cuestionario_por_token(p_token_hash VARCHAR)
        RETURNS TABLE (
            id VARCHAR,
            tenant_id VARCHAR,
            organizacion VARCHAR,
            version_cuestionario VARCHAR,
            caduca_en TIMESTAMPTZ,
            estado VARCHAR
        )
        SECURITY DEFINER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                c.id,
                c.tenant_id,
                CAST(COALESCE(t.nombre_comercial, t.razon_social, 'Organización') AS VARCHAR) AS organizacion,
                c.version_cuestionario,
                c.caduca_en,
                c.estado
            FROM terceros_cuestionarios c
            JOIN tenants t ON t.id = c.tenant_id
            WHERE c.token_hash = p_token_hash;
        END;
        $$;

        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app') THEN
                GRANT EXECUTE ON FUNCTION terceros_cuestionario_por_token(VARCHAR) TO lopdp_app;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DROP FUNCTION IF EXISTS terceros_cuestionario_por_token(VARCHAR);
        DROP TABLE IF EXISTS terceros_cuestionarios;
    """)
