# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""DER-02: Portal público de solicitudes de titulares por organización y seguimiento.

Revision ID: 20261105_derechos_portal
Revises: der01_derechos_respuestas
Create Date: 2026-11-16 15:40:00.000000

Contrato: governance/especificaciones/DER-02.md
- Columnas en derechos_arco_solicitudes:
    * canal VARCHAR(12) DEFAULT 'interno'
    * codigo_seguimiento_hash VARCHAR(64) UNIQUE NULL
    * email_solicitante VARCHAR(255) NULL
    * descripcion TEXT NULL
- Tabla portal_config (tenant_id PK, activo, slug UNIQUE, texto_bienvenida)
- Funciones SECURITY DEFINER para consulta pública sin abrir RLS
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20261105_derechos_portal"
down_revision: Union[str, Sequence[str], None] = "der01_derechos_respuestas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"


def upgrade() -> None:
    # 1. Columnas en derechos_arco_solicitudes
    op.execute(
        """
        ALTER TABLE derechos_arco_solicitudes
        ADD COLUMN IF NOT EXISTS canal VARCHAR(12) NOT NULL DEFAULT 'interno',
        ADD COLUMN IF NOT EXISTS codigo_seguimiento_hash VARCHAR(64) UNIQUE NULL,
        ADD COLUMN IF NOT EXISTS email_solicitante VARCHAR(255) NULL,
        ADD COLUMN IF NOT EXISTS descripcion TEXT NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_derechos_arco_codigo_hash
        ON derechos_arco_solicitudes (codigo_seguimiento_hash)
        WHERE codigo_seguimiento_hash IS NOT NULL;
        """
    )

    # 2. Tabla portal_config por organización
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS portal_config (
            tenant_id VARCHAR(64) PRIMARY KEY REFERENCES tenants(id),
            activo BOOLEAN NOT NULL DEFAULT FALSE,
            slug VARCHAR(48) NOT NULL UNIQUE,
            texto_bienvenida TEXT NULL
        );
        """
    )
    op.execute("ALTER TABLE portal_config ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE portal_config FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'portal_config' AND policyname = 'tenant_isolation_portal_config'
            ) THEN
                CREATE POLICY tenant_isolation_portal_config ON portal_config
                USING (tenant_id = current_setting('app.current_tenant_id', true))
                WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
            END IF;
        END $$;
        """
    )
    op.execute(f"REVOKE ALL ON portal_config FROM {APP_ROLE};")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON portal_config TO {APP_ROLE};")

    # 3. Funciones SECURITY DEFINER para rutas públicas
    op.execute(
        """
        CREATE OR REPLACE FUNCTION resolver_portal_por_slug(p_slug VARCHAR(48))
        RETURNS TABLE (
            tenant_id VARCHAR,
            nombre_comercial VARCHAR,
            activo BOOLEAN,
            texto_bienvenida TEXT
        )
        LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
            SELECT p.tenant_id, t.nombre_comercial, p.activo, p.texto_bienvenida
            FROM public.portal_config p
            JOIN public.tenants t ON t.id = p.tenant_id
            WHERE p.slug = p_slug AND p.activo = TRUE;
        $$;
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION resolver_portal_por_slug(VARCHAR) FROM PUBLIC;")
    op.execute(f"GRANT EXECUTE ON FUNCTION resolver_portal_por_slug(VARCHAR) TO {APP_ROLE};")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION consultar_seguimiento_solicitud(p_codigo_hash VARCHAR(64))
        RETURNS TABLE (
            estado VARCHAR,
            recibida_en TIMESTAMPTZ,
            respondida_en TIMESTAMPTZ
        )
        LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
            SELECT s.estado::varchar, s.fecha_recepcion, s.respondida_en
            FROM public.derechos_arco_solicitudes s
            WHERE s.codigo_seguimiento_hash = p_codigo_hash;
        $$;
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION consultar_seguimiento_solicitud(VARCHAR) FROM PUBLIC;")
    op.execute(f"GRANT EXECUTE ON FUNCTION consultar_seguimiento_solicitud(VARCHAR) TO {APP_ROLE};")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION crear_solicitud_portal(
            p_tenant_id VARCHAR,
            p_tipo VARCHAR,
            p_nombre VARCHAR,
            p_email VARCHAR,
            p_descripcion TEXT,
            p_codigo_hash VARCHAR
        )
        RETURNS UUID
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
        DECLARE
            v_id UUID;
            v_tipo tiposolicitud;
            v_plazo_dias INT := 15;
        BEGIN
            v_tipo := p_tipo::tiposolicitud;
            INSERT INTO public.derechos_arco_solicitudes (
                tenant_id_texto,
                tipo_solicitud,
                estado,
                cedula_solicitante,
                nombre_solicitante,
                email_solicitante,
                descripcion,
                canal,
                codigo_seguimiento_hash,
                fecha_recepcion,
                fecha_vencimiento
            ) VALUES (
                p_tenant_id,
                v_tipo,
                'RECIBIDA',
                'PENDIENTE',
                p_nombre,
                p_email,
                p_descripcion,
                'portal',
                p_codigo_hash,
                now(),
                now() + (v_plazo_dias || ' days')::interval
            ) RETURNING id INTO v_id;
            RETURN v_id;
        END;
        $$;
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION crear_solicitud_portal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR) FROM PUBLIC;")
    op.execute(f"GRANT EXECUTE ON FUNCTION crear_solicitud_portal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR) TO {APP_ROLE};")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS crear_solicitud_portal(VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS consultar_seguimiento_solicitud(VARCHAR);")
    op.execute("DROP FUNCTION IF EXISTS resolver_portal_por_slug(VARCHAR);")
    op.execute("DROP TABLE IF EXISTS portal_config;")
    op.execute("ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS descripcion;")
    op.execute("ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS email_solicitante;")
    op.execute("ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS codigo_seguimiento_hash;")
    op.execute("ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS canal;")
