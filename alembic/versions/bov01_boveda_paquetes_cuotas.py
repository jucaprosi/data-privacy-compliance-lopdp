# ¤¤backend-developer
"""BOV-01: catálogo de paquetes de Bóveda Cloud y suscripción por organización. ¤boveda-cloud ¤seguridad-tenant

Revision ID: bov01_boveda_paquetes_cuotas
Revises: rat07_consentimientos

`boveda_paquetes` es dato global del operador (sin tenant_id ni RLS). `lopdp_app` solo lee; lo edita el rol
`lopdp_operador_boveda` (NOLOGIN), que el brief del propietario concede al inicio de sesión del operador.
Siembra los cuatro paquetes del PRD §2.2 (espacio y descargas) y §2.3 (techos de uso). Base binaria: 1 GB = 1024^3
bytes, la misma que formatea la pantalla (ESTIMADO: el Arquitecto no la confirma; la confirma el CTO). ENTERPRISE es personalizado: sus cuotas y techos van en NULL y el alta
exige cuotas explícitas.

`boveda_suscripciones_tenant`: una por organización, RLS ENABLE y FORCE por `app.current_tenant_id`. `lopdp_app`
no borra; solo actualiza los usos y el estado.
"""
from alembic import op

revision = "bov01_boveda_paquetes_cuotas"
down_revision = "rat07_consentimientos"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE boveda_paquetes (
            codigo VARCHAR(32) PRIMARY KEY CHECK (codigo ~ '^[A-Z][A-Z0-9_]{1,31}$'),
            nombre VARCHAR(120) NOT NULL CHECK (length(trim(nombre)) >= 1),
            cuota_almacenamiento_bytes BIGINT CHECK (cuota_almacenamiento_bytes IS NULL OR cuota_almacenamiento_bytes > 0),
            cuota_egress_mensual_bytes BIGINT CHECK (cuota_egress_mensual_bytes IS NULL OR cuota_egress_mensual_bytes > 0),
            peticiones_api_minuto INTEGER CHECK (peticiones_api_minuto IS NULL OR peticiones_api_minuto > 0),
            tokens_ia_mes BIGINT CHECK (tokens_ia_mes IS NULL OR tokens_ia_mes > 0),
            max_claves_integracion INTEGER CHECK (max_claves_integracion IS NULL OR max_claves_integracion > 0),
            max_webhooks INTEGER CHECK (max_webhooks IS NULL OR max_webhooks > 0)
        );
        """
    )
    # Bytes literales (sin f-string: test_sin_sql_interpolado). 50 GB = 53687091200; 1 TB = 1099511627776.
    op.execute(
        """
        INSERT INTO boveda_paquetes (codigo, nombre, cuota_almacenamiento_bytes, cuota_egress_mensual_bytes,
                                     peticiones_api_minuto, tokens_ia_mes, max_claves_integracion, max_webhooks)
        VALUES
            ('INICIAL', 'Inicial', 53687091200, 107374182400, 300, 2000000, 2, 2),
            ('PROFESIONAL', 'Profesional', 268435456000, 536870912000, 1200, 10000000, 10, 10),
            ('CORPORATIVO', 'Corporativo', 1099511627776, 2199023255552, 5000, 50000000, 50, 50),
            ('ENTERPRISE', 'Enterprise Custom', NULL, NULL, NULL, NULL, NULL, NULL);
        """
    )
    op.execute(
        """
        CREATE TABLE boveda_suscripciones_tenant (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL UNIQUE REFERENCES tenants(id),
            paquete_codigo VARCHAR(32) NOT NULL REFERENCES boveda_paquetes(codigo),
            cuota_almacenamiento_bytes BIGINT NOT NULL CHECK (cuota_almacenamiento_bytes > 0),
            uso_almacenamiento_bytes BIGINT NOT NULL DEFAULT 0 CHECK (uso_almacenamiento_bytes >= 0),
            cuota_egress_mensual_bytes BIGINT NOT NULL CHECK (cuota_egress_mensual_bytes > 0),
            uso_egress_mensual_bytes BIGINT NOT NULL DEFAULT 0 CHECK (uso_egress_mensual_bytes >= 0),
            certificaciones_heredadas JSONB NOT NULL
                DEFAULT '["ISO 27001", "ISO 27701", "SOC 2"]'::jsonb
                CHECK (jsonb_typeof(certificaciones_heredadas) = 'array'),
            estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
                CHECK (estado IN ('ACTIVA', 'CUOTA_EXCEDIDA', 'SUSPENDIDA')),
            creado_por VARCHAR,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        ALTER TABLE boveda_suscripciones_tenant ENABLE ROW LEVEL SECURITY;
        ALTER TABLE boveda_suscripciones_tenant FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_boveda_suscripciones_tenant ON boveda_suscripciones_tenant
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON boveda_paquetes, boveda_suscripciones_tenant FROM lopdp_app;
        GRANT SELECT ON boveda_paquetes TO lopdp_app;
        GRANT SELECT, INSERT ON boveda_suscripciones_tenant TO lopdp_app;
        GRANT UPDATE (uso_almacenamiento_bytes, uso_egress_mensual_bytes, estado, actualizado_en)
            ON boveda_suscripciones_tenant TO lopdp_app;
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_operador_boveda') THEN
                CREATE ROLE lopdp_operador_boveda NOLOGIN;
            END IF;
        END
        $$;
        GRANT SELECT, INSERT, UPDATE ON boveda_paquetes TO lopdp_operador_boveda;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS boveda_suscripciones_tenant")
    op.execute("DROP TABLE IF EXISTS boveda_paquetes")
