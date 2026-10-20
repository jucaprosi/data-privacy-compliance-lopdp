"""Crear tabla sod_exceptions, trigger de verificacion de excepcion y migracion de datos.

Revision ID: 20261020_sod_exceptions
Revises: 20261019_org07_estructura
Create Date: 2026-10-20 00:00:00.000000

ORG-02: Excepciones de separacion de funciones (SoD) explicitas y con fin.
- Tabla sod_exceptions con RLS y GRANT a lopdp_app (sin DELETE).
- Trigger fn_utr_coordinador_responsable que verifica excepcion activa.
- Migracion de datos idempotente de conjunto para usuarios con coordinador + responsable_area
  en organizaciones micro o pequena con origen 'migracion'.
"""
import time
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261020_sod_exceptions"
down_revision: Union[str, None] = "20261019_org07_estructura"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"


def upgrade() -> None:
    # 1. Crear tabla sod_exceptions
    op.execute("""
        CREATE TABLE IF NOT EXISTS sod_exceptions (
            id VARCHAR PRIMARY KEY,
            tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
            user_id VARCHAR NOT NULL REFERENCES users(id),
            rol_existente VARCHAR(50) NOT NULL,
            rol_solicitado VARCHAR(50) NOT NULL,
            motivo TEXT NOT NULL,
            control_compensatorio_tipo VARCHAR(100) NOT NULL,
            control_compensatorio_detalle TEXT NOT NULL,
            origen VARCHAR(50) NOT NULL DEFAULT 'solicitud',
            estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
            requested_by VARCHAR NOT NULL REFERENCES users(id),
            requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            approved_by VARCHAR NULL REFERENCES users(id),
            approved_at TIMESTAMPTZ NULL,
            resolucion_referencia VARCHAR(255) NULL,
            revoked_by VARCHAR NULL REFERENCES users(id),
            revoked_at TIMESTAMPTZ NULL,
            motivo_revocacion TEXT NULL,
            observaciones_dpo TEXT NULL,
            observaciones_dpo_by VARCHAR NULL REFERENCES users(id),
            observaciones_dpo_at TIMESTAMPTZ NULL,
            valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
            valid_to TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_sod_exceptions_roles CHECK (
                (rol_existente = 'coordinador' AND rol_solicitado = 'responsable_area') OR
                (rol_existente = 'responsable_area' AND rol_solicitado = 'coordinador')
            ),
            CONSTRAINT ck_sod_exceptions_control CHECK (
                control_compensatorio_tipo IN (
                    'observaciones_periodicas_delegado',
                    'verificacion_tercero_externo',
                    'aprobacion_decisiones_alta_direccion'
                )
            ),
            CONSTRAINT ck_sod_exceptions_origen CHECK (
                origen IN ('solicitud', 'migracion')
            ),
            CONSTRAINT ck_sod_exceptions_estado CHECK (
                estado IN ('pendiente', 'activa', 'vencida', 'revocada')
            )
        );
    """)

    # Índices
    op.execute("CREATE INDEX IF NOT EXISTS ix_sod_exceptions_tenant ON sod_exceptions(tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sod_exceptions_user ON sod_exceptions(user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sod_exceptions_estado ON sod_exceptions(estado);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sod_exceptions_vigencia ON sod_exceptions(tenant_id, user_id, estado, valid_from, valid_to);")

    # RLS
    op.execute("ALTER TABLE sod_exceptions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE sod_exceptions FORCE ROW LEVEL SECURITY;")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'sod_exceptions' AND policyname = 'tenant_isolation_sod_exceptions'
            ) THEN
                CREATE POLICY tenant_isolation_sod_exceptions ON sod_exceptions
                USING (tenant_id = current_setting('app.current_tenant_id', true));
            END IF;
        END $$;
    """)

    # Privilegios a lopdp_app (sin DELETE, solo SELECT, INSERT, UPDATE)
    op.execute(f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                GRANT SELECT, INSERT, UPDATE ON sod_exceptions TO {APP_ROLE};
            END IF;
        END $$;
    """)

    # 2. Migración de datos IDEMPOTENTE y DE CONJUNTO
    # Quienes ya acumulan ambos roles en organizaciones micro o pequena reciben excepcion de origen 'migracion'
    # vigencia: 1 año por defecto.
    t0 = time.perf_counter()
    res = op.get_bind().execute(sa.text("""
        WITH pares_existentes AS (
            SELECT DISTINCT
                c.tenant_id,
                c.user_id,
                t.tamano,
                COALESCE(c.granted_by, r.granted_by, c.user_id) AS admin_id
            FROM user_tenant_roles c
            JOIN user_tenant_roles r ON c.user_id = r.user_id AND c.tenant_id = r.tenant_id
            JOIN tenants t ON t.id = c.tenant_id
            WHERE c.role = 'coordinador' AND r.role = 'responsable_area'
              AND (c.valid_to IS NULL OR c.valid_to > now())
              AND (r.valid_to IS NULL OR r.valid_to > now())
              AND t.tamano IN ('micro', 'pequena')
        ),
        a_insertar AS (
            SELECT
                p.tenant_id,
                p.user_id,
                p.admin_id
            FROM pares_existentes p
            WHERE NOT EXISTS (
                SELECT 1 FROM sod_exceptions e
                WHERE e.tenant_id = p.tenant_id
                  AND e.user_id = p.user_id
                  AND e.estado = 'activa'
                  AND e.valid_to > now()
            )
        )
        INSERT INTO sod_exceptions (
            id,
            tenant_id,
            user_id,
            rol_existente,
            rol_solicitado,
            motivo,
            control_compensatorio_tipo,
            control_compensatorio_detalle,
            origen,
            estado,
            requested_by,
            requested_at,
            approved_by,
            approved_at,
            valid_from,
            valid_to,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid()::text,
            ai.tenant_id,
            ai.user_id,
            'coordinador',
            'responsable_area',
            'Excepción generada automáticamente por migración desde RM-16 (organización micro/pequeña)',
            'aprobacion_decisiones_alta_direccion',
            'Control compensatorio de transición asignado por migración de datos histórica',
            'migracion',
            'activa',
            ai.admin_id,
            now(),
            ai.admin_id,
            now(),
            now(),
            now() + INTERVAL '1 year',
            now(),
            now()
        FROM a_insertar ai;
    """))
    t1 = time.perf_counter()
    filas_creadas = res.rowcount if hasattr(res, "rowcount") else 0
    print(f"[MIGRACION ORG-02] Excepciones SoD creadas por migracion: {filas_creadas} en {(t1 - t0):.4f}s")

    # 3. Reemplazar la función del trigger trg_utr_coordinador_responsable
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_utr_coordinador_responsable() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
        DECLARE
            contraparte text;
            tam text;
            tiene_excepcion boolean;
        BEGIN
            IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
                RETURN NEW;
            END IF;
            IF NEW.role = 'coordinador' THEN
                contraparte := 'responsable_area';
            ELSIF NEW.role = 'responsable_area' THEN
                contraparte := 'coordinador';
            ELSE
                RETURN NEW;
            END IF;

            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role = contraparte
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                SELECT tamano INTO tam FROM tenants WHERE id = NEW.tenant_id;
                IF tam IS NULL OR tam NOT IN ('micro', 'pequena', 'mediana', 'corporativo') THEN
                    RAISE EXCEPTION 'TENANT_SIZE_NOT_CONFIGURED: tamano no configurado en el tenant %', NEW.tenant_id
                        USING ERRCODE = 'check_violation';
                END IF;

                SELECT EXISTS (
                    SELECT 1 FROM sod_exceptions
                    WHERE tenant_id = NEW.tenant_id
                      AND user_id = NEW.user_id
                      AND estado = 'activa'
                      AND valid_from <= now()
                      AND valid_to > now()
                ) INTO tiene_excepcion;

                IF NOT tiene_excepcion THEN
                    RAISE EXCEPTION 'SOD_VIOLATION: coordinador y responsable_area en la misma persona requiere excepcion SoD activa (tamano %)', tam
                        USING ERRCODE = 'check_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_utr_coordinador_responsable ON user_tenant_roles;
        CREATE TRIGGER trg_utr_coordinador_responsable
        BEFORE INSERT OR UPDATE ON user_tenant_roles
        FOR EACH ROW EXECUTE FUNCTION fn_utr_coordinador_responsable();
    """)


def downgrade() -> None:
    # Restaurar función basada en tamaño de RM-16 / ORG-00
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_utr_coordinador_responsable() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
        DECLARE
            contraparte text;
            tam text;
        BEGIN
            IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
                RETURN NEW;
            END IF;
            IF NEW.role = 'coordinador' THEN
                contraparte := 'responsable_area';
            ELSIF NEW.role = 'responsable_area' THEN
                contraparte := 'coordinador';
            ELSE
                RETURN NEW;
            END IF;
            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role = contraparte
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                SELECT tamano INTO tam FROM tenants WHERE id = NEW.tenant_id;
                IF tam IS NULL OR tam NOT IN ('micro', 'pequena', 'mediana', 'corporativo') THEN
                    RAISE EXCEPTION 'TENANT_SIZE_NOT_CONFIGURED: tamano no configurado en el tenant %', NEW.tenant_id
                        USING ERRCODE = 'check_violation';
                END IF;
                IF tam NOT IN ('micro', 'pequena') THEN
                    RAISE EXCEPTION 'SOD_VIOLATION: coordinador y responsable_area en la misma persona (tamano %)', tam
                        USING ERRCODE = 'check_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_utr_coordinador_responsable ON user_tenant_roles;
        CREATE TRIGGER trg_utr_coordinador_responsable
        BEFORE INSERT OR UPDATE ON user_tenant_roles
        FOR EACH ROW EXECUTE FUNCTION fn_utr_coordinador_responsable();
    """)

    op.execute("DROP TABLE IF EXISTS sod_exceptions CASCADE;")
