# ¤rbac-tenant
"""ORG-22: fn_utr_dpo_sod hace exclusivos a 'dpo' y 'auditor' (sin trigger nuevo).

Regla de negocio INV_LOPDP_AUDITOR_SOLE_ROLE (PRD EVYDENTIA §3; razón: INV_LOPDP_FOUR_EYES_CLOSURE; decisión del CTO, 2026-11-12; sin artículo vinculante): quien
tiene 'dpo' o 'auditor' no tiene ningún otro rol activo en el mismo tenant. Se reescribe solo la función; el
trigger trg_utr_dpo_sod ya existe. Antes de reemplazarla cuenta los pares (user_id, tenant_id) que ya la
incumplen y, si hay alguno, aborta con el recuento, sin UPDATE ni DELETE.

El downgrade restaura el cuerpo de 20261019_dpo_sin_operativos.
"""
import sqlalchemy as sa
from alembic import op

revision = "org22b_auditor_sod_trigger"
down_revision = "20261112_ia10_trazas_ia"
branch_labels = None
depends_on = None

_CUENTA_PARES = """
SELECT count(*) FROM (
    SELECT a.user_id, a.tenant_id
    FROM user_tenant_roles a
    JOIN user_tenant_roles b
      ON b.user_id = a.user_id AND b.tenant_id = a.tenant_id AND b.id <> a.id
    WHERE a.role IN ('dpo', 'auditor')
      AND (a.valid_to IS NULL OR a.valid_to > now())
      AND (b.valid_to IS NULL OR b.valid_to > now())
    GROUP BY a.user_id, a.tenant_id
) pares
"""

_FUNCION_NUEVA = """
CREATE OR REPLACE FUNCTION fn_utr_dpo_sod() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF NEW.valid_to IS NOT NULL AND NEW.valid_to <= now() THEN
        RETURN NEW;
    END IF;
    -- Seguridad (#675): con READ COMMITTED dos INSERT simultáneos del mismo par no se verían entre sí; se
    -- serializan por (tenant, usuario) hasta el fin de la transacción y el segundo ve la fila del primero.
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.tenant_id::text || ':' || NEW.user_id::text, 0));
    IF NEW.role = 'dpo' THEN
        IF EXISTS (
            SELECT 1 FROM user_tenant_roles
            WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
              AND id <> NEW.id
              AND role IN ('implementador', 'coordinador', 'responsable_area', 'admin_organizacion', 'auditor')
              AND (valid_to IS NULL OR valid_to > now())
        ) THEN
            RAISE EXCEPTION 'SoD DPO: el usuario % ya tiene rol operativo en el tenant %', NEW.user_id, NEW.tenant_id
                USING ERRCODE = 'check_violation';
        END IF;
    ELSIF NEW.role = 'auditor' THEN
        IF EXISTS (
            SELECT 1 FROM user_tenant_roles
            WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
              AND id <> NEW.id
              AND (valid_to IS NULL OR valid_to > now())
        ) THEN
            RAISE EXCEPTION 'SoD auditor: el usuario % ya tiene otro rol en el tenant %', NEW.user_id, NEW.tenant_id
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
        IF EXISTS (
            SELECT 1 FROM user_tenant_roles
            WHERE user_id = NEW.user_id AND tenant_id = NEW.tenant_id
              AND id <> NEW.id
              AND role = 'auditor'
              AND (valid_to IS NULL OR valid_to > now())
        ) THEN
            RAISE EXCEPTION 'SoD auditor: el usuario % es auditor en el tenant %', NEW.user_id, NEW.tenant_id
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
"""

_FUNCION_ANTERIOR = """
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
"""


def upgrade() -> None:
    pares = op.get_bind().execute(sa.text(_CUENTA_PARES)).scalar_one()
    if pares:
        raise RuntimeError(
            f"ORG-22: {pares} par(es) (usuario, tenant) con dpo o auditor activo y otro rol activo; "
            "corríjalos a mano antes de migrar (esta migración no modifica ni borra filas)."
        )
    op.execute(_FUNCION_NUEVA)


def downgrade() -> None:
    op.execute(_FUNCION_ANTERIOR)
