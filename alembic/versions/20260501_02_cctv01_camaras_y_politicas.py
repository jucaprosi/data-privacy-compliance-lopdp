"""CCTV-01: inventario de cámaras de videovigilancia. ¤videovigilancia-cctv ¤seguridad-tenant

Revision ID: cctv01_camaras_y_politicas
Revises: ret02_clave_objeto

Primera migración de la sala `videovigilancia` (CI-28): cuelga de BASE_COMUN y abre su rama.
La base rechaza por sí misma una cámara no conforme (códec, modo de grabación, audio ambiental,
máscara de privacidad) y un plazo de retención fuera de 1 a 30 días. RLS ENABLE y FORCE por tenant_id;
lopdp_app sin DELETE ni UPDATE: una cámara no se edita, se da de alta de nuevo.
"""
from alembic import op

revision = "cctv01_camaras_y_politicas"
down_revision = "ret02_clave_objeto"
branch_labels = ("videovigilancia",)
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE cctv_camaras_inventario (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            nombre_ubicacion VARCHAR(160) NOT NULL
                CONSTRAINT ck_cctv_nombre_ubicacion CHECK (length(trim(nombre_ubicacion)) >= 1),
            codec VARCHAR(16) NOT NULL
                CONSTRAINT ck_cctv_codec CHECK (codec IN ('H265', 'H265_PLUS')),
            modo_grabacion VARCHAR(32) NOT NULL
                CONSTRAINT ck_cctv_modo_grabacion CHECK (modo_grabacion IN ('EVENTO_MOVIMIENTO')),
            audio_ambiental_activo BOOLEAN NOT NULL DEFAULT FALSE
                CONSTRAINT ck_cctv_sin_audio CHECK (audio_ambiental_activo = FALSE),
            mascara_privacidad_activa BOOLEAN NOT NULL DEFAULT TRUE
                CONSTRAINT ck_cctv_con_mascara CHECK (mascara_privacidad_activa = TRUE),
            plazo_retencion_dias INTEGER NOT NULL DEFAULT 15
                CONSTRAINT ck_cctv_plazo_retencion CHECK (plazo_retencion_dias BETWEEN 1 AND 30),
            estado_conformidad VARCHAR(32) NOT NULL DEFAULT 'CONFORME'
                CONSTRAINT ck_cctv_estado_conformidad CHECK (estado_conformidad IN ('CONFORME', 'BLOQUEADA_POR_CONFIG')),
            actividad_rat_id VARCHAR(64),
            creado_por VARCHAR NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_cctv_camaras_tenant_creado ON cctv_camaras_inventario (tenant_id, creado_en DESC);
        ALTER TABLE cctv_camaras_inventario ENABLE ROW LEVEL SECURITY;
        ALTER TABLE cctv_camaras_inventario FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_cctv_camaras_inventario ON cctv_camaras_inventario
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON cctv_camaras_inventario FROM lopdp_app;
        GRANT SELECT, INSERT ON cctv_camaras_inventario TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cctv_camaras_inventario")
