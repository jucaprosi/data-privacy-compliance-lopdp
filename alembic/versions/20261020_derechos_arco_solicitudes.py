"""Crear tabla derechos_arco_solicitudes con RLS y GRANT a lopdp_app.

Revision ID: 20261020_arco_solicitudes
Revises: ef238d956830
Create Date: 2026-10-20 11:05:00.000000

SEC-09:
1. Crea tipos ENUM tiposolicitud y estadosolicitud si no existen.
2. Crea tabla derechos_arco_solicitudes:
   - id UUID PK gen_random_uuid()
   - tenant_id UUID NOT NULL
   - tipo_solicitud tiposolicitud NOT NULL
   - estado estadosolicitud NOT NULL DEFAULT 'RECIBIDA'
   - cedula_solicitante VARCHAR(20) NOT NULL
   - nombre_solicitante VARCHAR(200) NOT NULL
   - fecha_recepcion TIMESTAMPTZ NOT NULL DEFAULT now()
   - fecha_vencimiento TIMESTAMPTZ NOT NULL
   - evidencia_respuesta_hash VARCHAR(64) NULL
3. Índices:
   - ix_derechos_arco_solicitudes_tenant_id ON derechos_arco_solicitudes(tenant_id)
4. RLS:
   - ENABLE ROW LEVEL SECURITY
   - FORCE ROW LEVEL SECURITY
   - tenant_isolation_derechos_arco_solicitudes USING (tenant_id::text = current_setting('app.current_tenant_id', true))
5. Permisos:
   - GRANT SELECT, INSERT, UPDATE ON derechos_arco_solicitudes TO lopdp_app (sin DELETE).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261020_arco_solicitudes"
down_revision: Union[str, None] = "ef238d956830"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"

SQL_ASCENDENTE: tuple[str, ...] = (
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tiposolicitud') THEN
            CREATE TYPE tiposolicitud AS ENUM (
                'ACCESO', 'RECTIFICACION', 'CANCELACION', 'OPOSICION', 'PORTABILIDAD'
            );
        END IF;
    END $$;
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estadosolicitud') THEN
            CREATE TYPE estadosolicitud AS ENUM (
                'RECIBIDA', 'EN_ANALISIS', 'EN_REQUERIMIENTO', 'CONTESTADA', 'VENCIDA'
            );
        END IF;
    END $$;
    """,
    """
    CREATE TABLE IF NOT EXISTS derechos_arco_solicitudes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        tipo_solicitud tiposolicitud NOT NULL,
        estado estadosolicitud NOT NULL DEFAULT 'RECIBIDA',
        cedula_solicitante VARCHAR(20) NOT NULL,
        nombre_solicitante VARCHAR(200) NOT NULL,
        fecha_recepcion TIMESTAMPTZ NOT NULL DEFAULT now(),
        fecha_vencimiento TIMESTAMPTZ NOT NULL,
        evidencia_respuesta_hash VARCHAR(64) NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_derechos_arco_solicitudes_tenant_id
    ON derechos_arco_solicitudes(tenant_id);
    """,
    "ALTER TABLE derechos_arco_solicitudes ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE derechos_arco_solicitudes FORCE ROW LEVEL SECURITY;",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE tablename = 'derechos_arco_solicitudes'
              AND policyname = 'tenant_isolation_derechos_arco_solicitudes'
        ) THEN
            CREATE POLICY tenant_isolation_derechos_arco_solicitudes ON derechos_arco_solicitudes
            USING (tenant_id::text = current_setting('app.current_tenant_id', true));
        END IF;
    END $$;
    """,
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            GRANT SELECT, INSERT, UPDATE ON derechos_arco_solicitudes TO {APP_ROLE};
        END IF;
    END $$;
    """,
)

SQL_DESCENDENTE: tuple[str, ...] = (
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            REVOKE ALL ON derechos_arco_solicitudes FROM {APP_ROLE};
        END IF;
    END $$;
    """,
    "DROP TABLE IF EXISTS derechos_arco_solicitudes CASCADE;",
    """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tiposolicitud') THEN
            DROP TYPE tiposolicitud;
        END IF;
    END $$;
    """,
    """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estadosolicitud') THEN
            DROP TYPE estadosolicitud;
        END IF;
    END $$;
    """,
)


def upgrade() -> None:
    for sql in SQL_ASCENDENTE:
        op.execute(sql)


def downgrade() -> None:
    for sql in SQL_DESCENDENTE:
        op.execute(sql)
