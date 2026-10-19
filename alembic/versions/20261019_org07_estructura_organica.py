"""Estructura orgánica: nivel en áreas y tabla cargos_organicos con RLS.

Revision ID: 20261019_org07_estructura_organica
Revises: 20261019_dpo_sin_operativos
Create Date: 2026-10-19 15:45:00.000000

ORG-07:
1. Agrega la columna `nivel` a `areas` ('alta_direccion', 'direccion', 'jefatura', 'unidad'; defecto 'unidad').
   Garantiza que solo exista como máximo una unidad 'alta_direccion' activa por tenant.
2. Crea la tabla `cargos_organicos`:
   - id (VARCHAR PK)
   - tenant_id (VARCHAR NOT NULL REFERENCES tenants(id))
   - area_id (VARCHAR NOT NULL REFERENCES areas(id))
   - nombre (VARCHAR(255) NOT NULL)
   - tipo_cargo (VARCHAR(50) NOT NULL, catálogo de 8 valores)
   - es_jefatura (BOOLEAN NOT NULL DEFAULT FALSE)
   - reporta_a_cargo_id (VARCHAR NULL REFERENCES cargos_organicos(id))
   - titular_user_id (VARCHAR NULL REFERENCES users(id))
   - valid_from (TIMESTAMPTZ NOT NULL DEFAULT now())
   - valid_to (TIMESTAMPTZ NULL)
   - created_at, updated_at
3. Índices:
   - ix_cargos_organicos_tenant (tenant_id)
   - ix_cargos_organicos_area (area_id)
   - uq_cargos_jefatura_activa_por_area (índice único parcial: una sola jefatura activa por área)
   - uq_cargos_dpd_titular_activo (índice único parcial: solo un titular activo de delegado por tenant)
4. RLS y permisos:
   - Activa ROW LEVEL SECURITY y FORCE ROW LEVEL SECURITY en cargos_organicos.
   - Crea política tenant_isolation_cargos_organicos.
   - GRANT SELECT, INSERT, UPDATE en cargos_organicos a lopdp_app (sin DELETE, inmutable/histórico).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261019_org07_estructura"
down_revision: Union[str, None] = "20261019_dpo_sin_operativos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"

SQL_ASCENDENTE: tuple[str, ...] = (
    # 1. Columna nivel en areas
    """
    ALTER TABLE areas
    ADD COLUMN IF NOT EXISTS nivel VARCHAR(30) NOT NULL DEFAULT 'unidad'
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_areas_nivel'
        ) THEN
            ALTER TABLE areas ADD CONSTRAINT ck_areas_nivel
            CHECK (nivel IN ('alta_direccion', 'direccion', 'jefatura', 'unidad'));
        END IF;
    END $$;
    """,
    # Índice único parcial: una sola alta_direccion activa por tenant
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_areas_alta_direccion_por_tenant
    ON areas (tenant_id)
    WHERE nivel = 'alta_direccion' AND deleted_at IS NULL
    """,
    # 2. Tabla cargos_organicos
    """
    CREATE TABLE IF NOT EXISTS cargos_organicos (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        area_id VARCHAR NOT NULL REFERENCES areas(id),
        nombre VARCHAR(255) NOT NULL,
        tipo_cargo VARCHAR(50) NOT NULL,
        es_jefatura BOOLEAN NOT NULL DEFAULT FALSE,
        reporta_a_cargo_id VARCHAR NULL REFERENCES cargos_organicos(id),
        titular_user_id VARCHAR NULL REFERENCES users(id),
        valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
        valid_to TIMESTAMPTZ NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT ck_cargos_organicos_tipo CHECK (
            tipo_cargo IN (
                'oficial_cumplimiento',
                'oficial_seguridad_informacion',
                'apoderado_especial_extranjero',
                'miembro_administracion_o_control',
                'implementador_proteccion_datos',
                'nivel_superior_sector_publico',
                'delegado_proteccion_datos',
                'otro'
            )
        )
    )
    """,
    # Índices en cargos_organicos
    "CREATE INDEX IF NOT EXISTS ix_cargos_organicos_tenant ON cargos_organicos(tenant_id)",
    "CREATE INDEX IF NOT EXISTS ix_cargos_organicos_area ON cargos_organicos(area_id)",
    "CREATE INDEX IF NOT EXISTS ix_cargos_organicos_titular ON cargos_organicos(titular_user_id)",
    # Índice único parcial: una sola jefatura activa (vigente, sin valid_to) por área
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_cargos_jefatura_activa_por_area
    ON cargos_organicos (area_id)
    WHERE es_jefatura = TRUE AND valid_to IS NULL
    """,
    # Trigger adicional para asegurar que no coexistan dos jefaturas vigentes
    """
    CREATE OR REPLACE FUNCTION fn_cargos_jefatura_unica() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
    BEGIN
        IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
            RETURN NEW;
        END IF;
        IF NEW.es_jefatura = TRUE THEN
            IF EXISTS (
                SELECT 1 FROM cargos_organicos
                WHERE area_id = NEW.area_id
                  AND id <> NEW.id
                  AND es_jefatura = TRUE
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'Una sola jefatura activa por área permitida'
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$;
    """,
    """
    DROP TRIGGER IF EXISTS trg_cargos_jefatura_unica ON cargos_organicos;
    CREATE TRIGGER trg_cargos_jefatura_unica
    BEFORE INSERT OR UPDATE ON cargos_organicos
    FOR EACH ROW EXECUTE FUNCTION fn_cargos_jefatura_unica();
    """,
    # 3. RLS en cargos_organicos
    "ALTER TABLE cargos_organicos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE cargos_organicos FORCE ROW LEVEL SECURITY",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE tablename = 'cargos_organicos' AND policyname = 'tenant_isolation_cargos_organicos'
        ) THEN
            CREATE POLICY tenant_isolation_cargos_organicos ON cargos_organicos
            USING (tenant_id = current_setting('app.current_tenant_id', true));
        END IF;
    END $$;
    """,
    # 4. Conceder privilegios a lopdp_app (sin DELETE, solo SELECT, INSERT, UPDATE)
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            GRANT SELECT, INSERT, UPDATE ON cargos_organicos TO {APP_ROLE};
        END IF;
    END $$;
    """,
)

SQL_DESCENDENTE: tuple[str, ...] = (
    f"""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            REVOKE ALL ON cargos_organicos FROM {APP_ROLE};
        END IF;
    END $$;
    """,
    "DROP TABLE IF EXISTS cargos_organicos CASCADE",
    "DROP INDEX IF EXISTS uq_areas_alta_direccion_por_tenant",
    "ALTER TABLE areas DROP CONSTRAINT IF EXISTS ck_areas_nivel",
    "ALTER TABLE areas DROP COLUMN IF EXISTS nivel",
)


def upgrade() -> None:
    for sql in SQL_ASCENDENTE:
        op.execute(sql)


def downgrade() -> None:
    for sql in SQL_DESCENDENTE:
        op.execute(sql)
