# ¤¤backend-developer
"""FOR-01: Formación, contenidos, acciones formativas con examen y seguimiento. ¤evidencias ¤rbac-tenant

Revision ID: for01_formacion
Revises: ret02_clave_objeto
Create Date: 2026-11-16

Primera migración de la sala formacion en el esquema CI-28 (cuelga de BASE_COMUN).
Tablas:
- formacion_contenidos (id, tenant_id, titulo, tipo, referencia, creado_por, creado_en)
- formacion_preguntas (id, tenant_id, contenido_id, orden, enunciado, opciones, correcta)
- formacion_acciones (id, tenant_id, contenido_id, nombre, inicio, fin, nota_minima, creado_por)
- formacion_participaciones (id, tenant_id, accion_id, persona_id, enviado_en, iniciado_en, terminado_en, nota, diploma_sha256)

RLS ENABLE + FORCE en todas.
lopdp_app: SELECT, INSERT en contenidos, preguntas, acciones y participaciones; UPDATE en participaciones y contenidos/acciones; sin DELETE.
"""
from alembic import op

revision = "for01_formacion"
down_revision = "ret02_clave_objeto"
branch_labels = ("formacion",)
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE formacion_contenidos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            titulo VARCHAR(120) NOT NULL CHECK (length(trim(titulo)) >= 1),
            tipo VARCHAR(8) NOT NULL CHECK (tipo IN ('pdf', 'video')),
            referencia TEXT NOT NULL CHECK (length(trim(referencia)) >= 1),
            creado_por VARCHAR(64) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE formacion_preguntas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            contenido_id UUID NOT NULL REFERENCES formacion_contenidos(id) ON DELETE CASCADE,
            orden SMALLINT NOT NULL CHECK (orden >= 0),
            enunciado TEXT NOT NULL CHECK (length(trim(enunciado)) >= 1),
            opciones JSONB NOT NULL CHECK (jsonb_array_length(opciones) BETWEEN 2 AND 6),
            correcta SMALLINT NOT NULL CHECK (correcta >= 0),
            UNIQUE (contenido_id, orden)
        );

        CREATE TABLE formacion_acciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            contenido_id UUID NOT NULL REFERENCES formacion_contenidos(id),
            nombre VARCHAR(120) NOT NULL CHECK (length(trim(nombre)) >= 1),
            inicio DATE NOT NULL,
            fin DATE NOT NULL,
            nota_minima NUMERIC(4, 1) NOT NULL DEFAULT 70.0 CHECK (nota_minima BETWEEN 0 AND 100),
            creado_por VARCHAR(64) NOT NULL,
            CHECK (fin >= inicio)
        );

        CREATE TABLE formacion_participaciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            accion_id UUID NOT NULL REFERENCES formacion_acciones(id) ON DELETE CASCADE,
            persona_id VARCHAR(64) NOT NULL,
            enviado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            iniciado_en TIMESTAMPTZ NULL,
            terminado_en TIMESTAMPTZ NULL,
            nota NUMERIC(4, 1) NULL CHECK (nota IS NULL OR (nota BETWEEN 0 AND 100)),
            diploma_sha256 VARCHAR(64) NULL,
            UNIQUE (accion_id, persona_id)
        );

        -- RLS
        ALTER TABLE formacion_contenidos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE formacion_contenidos FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_formacion_contenidos_tenant ON formacion_contenidos
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE formacion_preguntas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE formacion_preguntas FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_formacion_preguntas_tenant ON formacion_preguntas
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE formacion_acciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE formacion_acciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_formacion_acciones_tenant ON formacion_acciones
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        ALTER TABLE formacion_participaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE formacion_participaciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY p_formacion_participaciones_tenant ON formacion_participaciones
            FOR ALL USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

        -- Permisos lopdp_app
        GRANT SELECT, INSERT, UPDATE ON formacion_contenidos TO lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON formacion_preguntas TO lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON formacion_acciones TO lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON formacion_participaciones TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS formacion_participaciones CASCADE;
        DROP TABLE IF EXISTS formacion_acciones CASCADE;
        DROP TABLE IF EXISTS formacion_preguntas CASCADE;
        DROP TABLE IF EXISTS formacion_contenidos CASCADE;
        """
    )
