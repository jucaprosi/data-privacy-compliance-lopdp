"""RBAC: SoD del DPO, cuatro ojos en evidencia y auditoría de revocación.

Revision ID: 20261008_rbac_sod
Revises: 20261005_roadmaps
Create Date: 2026-10-08 10:00:00.000000

- Trigger en user_tenant_roles: un usuario con rol 'dpo' activo no puede
  tener 'implementador' ni 'encargado' activos en el mismo tenant (Art. 48 LOPDP).
- CHECK en task_evidence: quien sube una evidencia no puede validarla.
  Se crea NOT VALID para no fallar sobre filas históricas.
- user_tenant_roles.revoked_by: quién revocó la asignación (valid_to marca cuándo).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261008_rbac_sod"
down_revision: Union[str, None] = "20261005_roadmaps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_tenant_roles", sa.Column("revoked_by", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_utr_revoked_by", "user_tenant_roles", "users", ["revoked_by"], ["id"]
    )

    op.execute("""
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
    """)
    op.execute("""
        CREATE TRIGGER trg_utr_dpo_sod
        BEFORE INSERT OR UPDATE ON user_tenant_roles
        FOR EACH ROW EXECUTE FUNCTION fn_utr_dpo_sod();
    """)

    op.execute("""
        ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_four_eyes
        CHECK (validated_by IS NULL OR uploaded_by IS NULL OR validated_by <> uploaded_by)
        NOT VALID;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_four_eyes;")
    op.execute("DROP TRIGGER IF EXISTS trg_utr_dpo_sod ON user_tenant_roles;")
    op.execute("DROP FUNCTION IF EXISTS fn_utr_dpo_sod();")
    op.drop_constraint("fk_utr_revoked_by", "user_tenant_roles", type_="foreignkey")
    op.drop_column("user_tenant_roles", "revoked_by")
