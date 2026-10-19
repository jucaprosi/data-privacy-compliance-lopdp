"""DPO sin roles operativos: actualiza trigger fn_utr_dpo_sod para abarcar todos los roles.

Revision ID: 20261019_dpo_sin_roles_operativos
Revises: 20261019_rol_coordinador
Create Date: 2026-10-19 15:40:00.000000

ORG-01: El DPO no puede tener ningún otro rol en la plataforma en el mismo tenant
(coordinador, implementador, responsable_area, admin_organizacion).
Base legal:
- Arts. 49 y 50 LOPDP.
- Arts. 48, 49 y 56 del Reglamento General (Decreto Ejecutivo 904).
- Arts. 3, 15, 16, 17 y 18 del Reglamento del Delegado (Resolución SPDP-SPD-2025-0028-R).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261019_dpo_sin_operativos"
down_revision: Union[str, None] = "20261019_rol_coordinador"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_ASCENDENTE: tuple[str, ...] = (
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
                  AND role IN ('implementador', 'coordinador', 'responsable_area', 'admin_organizacion')
                  AND (valid_to IS NULL OR valid_to > now())
            ) THEN
                RAISE EXCEPTION 'SoD DPO: el usuario % ya tiene rol operativo en el tenant %', NEW.user_id, NEW.tenant_id
                    USING ERRCODE = 'check_violation';
            END IF;
        ELSIF NEW.role IN ('implementador', 'coordinador', 'responsable_area', 'admin_organizacion') THEN
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
)

SQL_DESCENDENTE: tuple[str, ...] = (
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
)


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
