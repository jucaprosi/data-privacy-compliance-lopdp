"""Trigger encargado/responsable_area según el tamaño de la organización.

Revision ID: 20261017_encargado_resp_trigger
Revises: 20261016_tenants_tamano_check
Create Date: 2026-10-17 10:00:00.000000

RM-16: INV_LOPDP_ENCARGADO_RESPONSABLE_SIZE. Valida ambas direcciones (insertar
responsable_area a quien tiene encargado activo y viceversa), no depende de
also_responsable y falla cerrado si el tamaño es nulo o inválido.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261017_encargado_resp_trigger"
down_revision: Union[str, None] = "20261016_tenants_tamano_check"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
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
    """)
    op.execute("""
        CREATE TRIGGER trg_utr_encargado_responsable
        BEFORE INSERT OR UPDATE ON user_tenant_roles
        FOR EACH ROW EXECUTE FUNCTION fn_utr_encargado_responsable();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_utr_encargado_responsable ON user_tenant_roles;")
    op.execute("DROP FUNCTION IF EXISTS fn_utr_encargado_responsable();")
