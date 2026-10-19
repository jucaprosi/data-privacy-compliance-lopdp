"""Renombrar el rol encargado a coordinador (datos, check constraint y triggers).

Revision ID: 20261019_rol_coordinador
Revises: 20261018_responsable_requests
Create Date: 2026-10-19 00:00:00.000000

ORG-00: el rol que se llamaba 'encargado' pasa a llamarse 'coordinador' (PRD §5.2 y §5.3).
1. Actualiza los datos: UPDATE user_tenant_roles SET role = 'coordinador' WHERE role = 'encargado'.
2. Reemplaza la restricción ck_utr_role para admitir 'coordinador' en lugar de 'encargado'.
3. Reescribe fn_utr_dpo_sod para nombrar 'coordinador'.
4. Reemplaza el trigger y función trg_utr_encargado_responsable / fn_utr_encargado_responsable por
   trg_utr_coordinador_responsable / fn_utr_coordinador_responsable nombrando 'coordinador'.
El downgrade revierte exactamente estos cambios.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261019_rol_coordinador"
down_revision: Union[str, None] = "20261018_responsable_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_ASCENDENTE: tuple[str, ...] = (
    # 1. Dropear restricción vieja temporalmente para actualizar datos sin conflicto
    "ALTER TABLE user_tenant_roles DROP CONSTRAINT IF EXISTS ck_utr_role",
    # 2. Actualizar datos históricos
    "UPDATE user_tenant_roles SET role = 'coordinador' WHERE role = 'encargado'",
    # 3. Crear restricción nueva con 'coordinador'
    """
    ALTER TABLE user_tenant_roles ADD CONSTRAINT ck_utr_role
    CHECK (role IN ('responsable_area', 'coordinador', 'dpo', 'implementador', 'admin_organizacion'))
    """,
    # 4. Reescribir fn_utr_dpo_sod
    """
    CREATE OR REPLACE FUNCTION fn_utr_dpo_sod() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
    BEGIN
        IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
            RETURN NEW;
        END IF;
        IF NEW.role = 'dpo' THEN
            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role IN ('implementador', 'coordinador')
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'SoD DPO: el usuario % ya tiene rol operativo en el tenant %', NEW.user_id, NEW.tenant_id
                    USING ERRCODE = 'check_violation';
            END IF;
        ELSIF NEW.role IN ('implementador', 'coordinador') THEN
            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role = 'dpo'
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'SoD DPO: el usuario % es DPO en el tenant %', NEW.user_id, NEW.tenant_id
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$;
    """,
    # 5. Dropear trigger y función viejos de encargado_responsable
    "DROP TRIGGER IF EXISTS trg_utr_encargado_responsable ON user_tenant_roles",
    "DROP FUNCTION IF EXISTS fn_utr_encargado_responsable()",
    # 6. Crear función y trigger nuevos coordinador_responsable
    """
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
    """,
    """
    CREATE TRIGGER trg_utr_coordinador_responsable
    BEFORE INSERT OR UPDATE ON user_tenant_roles
    FOR EACH ROW EXECUTE FUNCTION fn_utr_coordinador_responsable();
    """,
)

SQL_DESCENDENTE: tuple[str, ...] = (
    # 1. Dropear trigger y función de coordinador_responsable
    "DROP TRIGGER IF EXISTS trg_utr_coordinador_responsable ON user_tenant_roles",
    "DROP FUNCTION IF EXISTS fn_utr_coordinador_responsable()",
    # 2. Restaurar función y trigger fn_utr_encargado_responsable
    """
    CREATE OR REPLACE FUNCTION fn_utr_encargado_responsable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
    DECLARE
        contraparte text;
        tam text;
    BEGIN
        IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
            RETURN NEW;
        END IF;
        IF NEW.role = 'encargado' THEN
            contraparte := 'responsable_area';
        ELSIF NEW.role = 'responsable_area' THEN
            contraparte := 'encargado';
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
                RAISE EXCEPTION 'SOD_VIOLATION: encargado y responsable_area en la misma persona (tamano %)', tam
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$;
    """,
    """
    CREATE TRIGGER trg_utr_encargado_responsable
    BEFORE INSERT OR UPDATE ON user_tenant_roles
    FOR EACH ROW EXECUTE FUNCTION fn_utr_encargado_responsable();
    """,
    # 3. Restaurar fn_utr_dpo_sod con 'encargado'
    """
    CREATE OR REPLACE FUNCTION fn_utr_dpo_sod() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
    BEGIN
        IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
            RETURN NEW;
        END IF;
        IF NEW.role = 'dpo' THEN
            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role IN ('implementador', 'encargado')
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'SoD DPO: el usuario % ya tiene rol operativo en el tenant %', NEW.user_id, NEW.tenant_id
                    USING ERRCODE = 'check_violation';
            END IF;
        ELSIF NEW.role IN ('implementador', 'encargado') THEN
            IF EXISTS (
                SELECT 1 FROM user_tenant_roles
                WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
                  AND id <> NEW.id
                  AND role = 'dpo'
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'SoD DPO: el usuario % es DPO en el tenant %', NEW.user_id, NEW.tenant_id
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$;
    """,
    # 4. Dropear ck_utr_role
    "ALTER TABLE user_tenant_roles DROP CONSTRAINT IF EXISTS ck_utr_role",
    # 5. Revertir datos a 'encargado'
    "UPDATE user_tenant_roles SET role = 'encargado' WHERE role = 'coordinador'",
    # 6. Recrear ck_utr_role con 'encargado'
    """
    ALTER TABLE user_tenant_roles ADD CONSTRAINT ck_utr_role
    CHECK (role IN ('responsable_area', 'encargado', 'dpo', 'implementador', 'admin_organizacion'))
    """,
)


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
