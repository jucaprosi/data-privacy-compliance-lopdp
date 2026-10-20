"""Tabla designaciones_formales con RLS, sin DELETE, y GRANT a lopdp_app.

Revision ID: 20261019_org06_designaciones
Revises: 20261019_org07_estructura
Create Date: 2026-10-19 23:50:00.000000

ORG-06:
1. Crea la tabla `designaciones_formales`:
   - id (VARCHAR PK)
   - tenant_id (VARCHAR NOT NULL REFERENCES tenants(id))
   - tipo (VARCHAR(20) NOT NULL, 'dpd' o 'coordinador')
   - user_id (VARCHAR NOT NULL REFERENCES users(id))
   - representante_nombre (VARCHAR(255) NOT NULL)
   - representante_identificacion (VARCHAR(50) NOT NULL)
   - representante_cargo (VARCHAR(255) NOT NULL)
   - fecha_designacion DATE NOT NULL
   - doc_referencia (VARCHAR(255) NOT NULL)
   - valid_from (TIMESTAMPTZ NOT NULL DEFAULT now())
   - valid_to (TIMESTAMPTZ NULL)
   - vinculo (VARCHAR(30) NULL, 'relacion_dependencia' o 'prestacion_servicios')
   - aceptacion_at (TIMESTAMPTZ NULL)
   - inscripcion_spdp_fecha (DATE NULL)
   - inscripcion_spdp_ref (VARCHAR(255) NULL)
   - declaracion_at (TIMESTAMPTZ NULL)
   - declaracion_texto (TEXT NULL)
   - declaracion_tiene_conflicto (BOOLEAN NOT NULL DEFAULT FALSE)
   - declaracion_es_socio_accionista (BOOLEAN NOT NULL DEFAULT FALSE)
   - declaracion_es_pariente_admin (BOOLEAN NOT NULL DEFAULT FALSE)
   - revocada_at (TIMESTAMPTZ NULL)
   - revocada_motivo (VARCHAR(255) NULL)
   - revocada_por_user_id (VARCHAR NULL REFERENCES users(id))
   - created_at (TIMESTAMPTZ NOT NULL DEFAULT now())
   - updated_at (TIMESTAMPTZ NOT NULL DEFAULT now())
2. Índices y Constraints:
   - ck_designaciones_tipo ('dpd', 'coordinador')
   - ck_designaciones_vinculo ('relacion_dependencia', 'prestacion_servicios')
   - ix_designaciones_tenant (tenant_id)
   - ix_designaciones_user (user_id)
   - uq_designaciones_formales_activa (un solo DPD o Coordinador sin revocar y sin valid_to por tenant)
   - Trigger trg_designaciones_unica_activa para verificar que no coexistan designaciones vigentes.
3. RLS:
   - ENABLE y FORCE ROW LEVEL SECURITY.
   - Política tenant_isolation_designaciones_formales.
4. Permisos:
   - GRANT SELECT, INSERT, UPDATE a lopdp_app (sin DELETE).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261019_org06_designaciones"
down_revision: Union[str, None] = "20261020_sod_exceptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"

SQL_ASCENDENTE: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS designaciones_formales (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        tipo VARCHAR(20) NOT NULL,
        user_id VARCHAR NOT NULL REFERENCES users(id),
        representante_nombre VARCHAR(255) NOT NULL,
        representante_identificacion VARCHAR(50) NOT NULL,
        representante_cargo VARCHAR(255) NOT NULL,
        fecha_designacion DATE NOT NULL,
        doc_referencia VARCHAR(255) NOT NULL,
        valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
        valid_to TIMESTAMPTZ NULL,
        vinculo VARCHAR(30) NULL,
        aceptacion_at TIMESTAMPTZ NULL,
        inscripcion_spdp_fecha DATE NULL,
        inscripcion_spdp_ref VARCHAR(255) NULL,
        declaracion_at TIMESTAMPTZ NULL,
        declaracion_texto TEXT NULL,
        declaracion_tiene_conflicto BOOLEAN NOT NULL DEFAULT FALSE,
        declaracion_es_socio_accionista BOOLEAN NOT NULL DEFAULT FALSE,
        declaracion_es_pariente_admin BOOLEAN NOT NULL DEFAULT FALSE,
        revocada_at TIMESTAMPTZ NULL,
        revocada_motivo VARCHAR(255) NULL,
        revocada_por_user_id VARCHAR NULL REFERENCES users(id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT ck_designaciones_tipo CHECK (tipo IN ('dpd', 'coordinador')),
        CONSTRAINT ck_designaciones_vinculo CHECK (
            vinculo IS NULL OR vinculo IN ('relacion_dependencia', 'prestacion_servicios')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_designaciones_formales_tenant ON designaciones_formales(tenant_id)",
    "CREATE INDEX IF NOT EXISTS ix_designaciones_formales_user ON designaciones_formales(user_id)",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_designaciones_formales_activa
    ON designaciones_formales (tenant_id, tipo)
    WHERE revocada_at IS NULL AND valid_to IS NULL
    """,
    """
    CREATE OR REPLACE FUNCTION fn_designaciones_unica_activa() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
    BEGIN
        IF NEW.revocada_at IS NOT NULL OR (NEW.valid_to IS NOT NULL AND NEW.valid_to <= now()) THEN
            RETURN NEW;
        END IF;
        IF EXISTS (
            SELECT 1 FROM designaciones_formales
            WHERE tenant_id = NEW.tenant_id
              AND tipo = NEW.tipo
              AND id <> NEW.id
              AND revocada_at IS NULL
              AND (valid_to IS NULL OR valid_to > now())
        ) THEN
            RAISE EXCEPTION 'Ya existe una designación formal activa para este tipo en el tenant'
                USING ERRCODE = 'check_violation';
        END IF;
        RETURN NEW;
    END;
    $$;
    """,
    """
    DROP TRIGGER IF EXISTS trg_designaciones_unica_activa ON designaciones_formales;
    CREATE TRIGGER trg_designaciones_unica_activa
    BEFORE INSERT OR UPDATE ON designaciones_formales
    FOR EACH ROW EXECUTE FUNCTION fn_designaciones_unica_activa();
    """,
    "ALTER TABLE designaciones_formales ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE designaciones_formales FORCE ROW LEVEL SECURITY",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE tablename = 'designaciones_formales' AND policyname = 'tenant_isolation_designaciones_formales'
        ) THEN
            CREATE POLICY tenant_isolation_designaciones_formales ON designaciones_formales
            USING (tenant_id = current_setting('app.current_tenant_id', true));
        END IF;
    END $$;
    """,
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            GRANT SELECT, INSERT, UPDATE ON designaciones_formales TO {APP_ROLE};
        END IF;
    END $$;
    """,
)

SQL_DESCENDENTE: tuple[str, ...] = (
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            REVOKE ALL ON designaciones_formales FROM {APP_ROLE};
        END IF;
    END $$;
    """,
    "DROP TRIGGER IF EXISTS trg_designaciones_unica_activa ON designaciones_formales",
    "DROP FUNCTION IF EXISTS fn_designaciones_unica_activa()",
    "DROP TABLE IF EXISTS designaciones_formales CASCADE",
)


def upgrade() -> None:
    for sql in SQL_ASCENDENTE:
        op.execute(sql)


def downgrade() -> None:
    for sql in SQL_DESCENDENTE:
        op.execute(sql)
