# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""CAPA-04: Auditoría con grilla de verificación por dominio y acta por área. ¤auditoria-capa ¤hallazgos

Revision ID: capa04_auditoria_grilla
Revises: ret02_clave_objeto
Create Date: 2026-11-16

Primera migración de la sala auditoria_capa en el esquema CI-28 (cuelga de BASE_COMUN).
Tablas:
- auditorias (id, tenant_id, nombre, alcance JSONB, equipo JSONB, estado, creado_por, creado_en, cerrada_en)
- auditoria_filas (id, tenant_id, auditoria_id, area_id, control_ref, declarado, riesgo_inicial, verificado, evidencia_sha256, riesgo_final, revisado_por, hallazgo_id)
- auditoria_actas (id, tenant_id, auditoria_id, area_id, evidencia_id, acta_sha256, firmada_por, firmada_en)
- auditoria_verificaciones_cierre (id, tenant_id, hallazgo_id, accion_ref, verificado_por, resultado, motivo, registrado_en)

RLS ENABLE + FORCE en todas.
lopdp_app: SELECT, INSERT en auditorias, actas y verificaciones; UPDATE en filas y (estado, cerrada_en) en auditorias; sin DELETE.
"""
from alembic import op

revision = "capa04_auditoria_grilla"
down_revision = "ret02_clave_objeto"
branch_labels = ("auditoria_capa",)
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE auditorias (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            nombre VARCHAR(120) NOT NULL CHECK (length(trim(nombre)) >= 1),
            alcance JSONB NOT NULL DEFAULT '[]'::jsonb,
            equipo JSONB NOT NULL DEFAULT '[]'::jsonb,
            estado VARCHAR(10) NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
            creado_por VARCHAR(64) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            cerrada_en TIMESTAMPTZ NULL
        );

        CREATE TABLE auditoria_filas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            auditoria_id UUID NOT NULL REFERENCES auditorias(id) ON DELETE CASCADE,
            area_id VARCHAR(64) NOT NULL,
            control_ref VARCHAR(64) NOT NULL,
            declarado SMALLINT NOT NULL CHECK (declarado BETWEEN 1 AND 5),
            riesgo_inicial SMALLINT NOT NULL,
            verificado SMALLINT NULL CHECK (verificado IS NULL OR verificado BETWEEN 1 AND 5),
            evidencia_sha256 VARCHAR(64) NULL,
            riesgo_final SMALLINT NULL,
            revisado_por VARCHAR(64) NULL,
            hallazgo_id VARCHAR(64) NULL,
            UNIQUE (auditoria_id, control_ref)
        );

        CREATE TABLE auditoria_actas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            auditoria_id UUID NOT NULL REFERENCES auditorias(id) ON DELETE CASCADE,
            area_id VARCHAR(64) NOT NULL,
            evidencia_id VARCHAR(64) NOT NULL,
            acta_sha256 VARCHAR(64) NOT NULL,
            firmada_por VARCHAR(64) NOT NULL,
            firmada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (auditoria_id, area_id)
        );

        CREATE TABLE auditoria_verificaciones_cierre (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            hallazgo_id VARCHAR(64) NOT NULL,
            accion_ref VARCHAR(64) NOT NULL,
            verificado_por VARCHAR(64) NOT NULL,
            resultado VARCHAR(15) NOT NULL CHECK (resultado IN ('conforme', 'no_conforme')),
            motivo TEXT NOT NULL CHECK (length(trim(motivo)) >= 10),
            registrado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        -- RLS
        ALTER TABLE auditorias ENABLE ROW LEVEL SECURITY;
        ALTER TABLE auditorias FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_auditorias_tenant ON auditorias
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE auditoria_filas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE auditoria_filas FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_auditoria_filas_tenant ON auditoria_filas
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE auditoria_actas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE auditoria_actas FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_auditoria_actas_tenant ON auditoria_actas
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE auditoria_verificaciones_cierre ENABLE ROW LEVEL SECURITY;
        ALTER TABLE auditoria_verificaciones_cierre FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_auditoria_verificaciones_cierre_tenant ON auditoria_verificaciones_cierre
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        -- Permisos lopdp_app
        GRANT SELECT, INSERT ON auditorias, auditoria_actas, auditoria_verificaciones_cierre TO lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON auditoria_filas TO lopdp_app;
        GRANT UPDATE (estado, cerrada_en) ON auditorias TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS auditoria_verificaciones_cierre CASCADE;
        DROP TABLE IF EXISTS auditoria_actas CASCADE;
        DROP TABLE IF EXISTS auditoria_filas CASCADE;
        DROP TABLE IF EXISTS auditorias CASCADE;
        """
    )
