# ¤¤security-engineer
"""DLP-01: escaneos muestreados de datos personales. ¤dlp-muestreo ¤seguridad-tenant

Revision ID: dlp01_escaneos_muestreados
Revises: dpo03_consultas

Solo guarda el tipo de hallazgo y su conteo (INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10): un CHECK exige que
`infotypes_detectados` sea un objeto con claves de la lista blanca y valores numéricos, de modo que la base
rechaza cualquier valor de texto, como una cédula. RLS ENABLE y FORCE por tenant_id; lopdp_app sin DELETE y
solo puede actualizar la actividad vinculada.
"""
from alembic import op

revision = "dlp01_escaneos_muestreados"
down_revision = "dpo03_consultas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE dlp_escaneos_muestreados (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            fuente_nombre VARCHAR(160) NOT NULL CHECK (length(trim(fuente_nombre)) >= 1),
            limite_muestra INTEGER NOT NULL DEFAULT 250
                CONSTRAINT ck_dlp_limite_muestra CHECK (limite_muestra BETWEEN 1 AND 1000),
            infotypes_detectados JSONB NOT NULL
                CONSTRAINT ck_dlp_infotypes_lista_blanca CHECK (
                    jsonb_typeof(infotypes_detectados) = 'object'
                    AND (infotypes_detectados - ARRAY['EC_CEDULA_MOD10', 'EC_RUC', 'EMAIL', 'PHONE', 'SALUD']) = '{}'::jsonb
                    AND NOT jsonb_path_exists(infotypes_detectados, '$.* ? (@.type() != "number" || @ < 0)')
                ),
            contiene_datos_sensibles BOOLEAN NOT NULL,
            actividad_rat_id VARCHAR(64),
            creado_por VARCHAR NOT NULL CHECK (length(trim(creado_por)) >= 1),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_dlp_escaneos_tenant_creado ON dlp_escaneos_muestreados (tenant_id, creado_en DESC);
        ALTER TABLE dlp_escaneos_muestreados ENABLE ROW LEVEL SECURITY;
        ALTER TABLE dlp_escaneos_muestreados FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_dlp_escaneos_muestreados ON dlp_escaneos_muestreados
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON dlp_escaneos_muestreados FROM lopdp_app;
        GRANT SELECT, INSERT ON dlp_escaneos_muestreados TO lopdp_app;
        GRANT UPDATE (actividad_rat_id) ON dlp_escaneos_muestreados TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dlp_escaneos_muestreados")
