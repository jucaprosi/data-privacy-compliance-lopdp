# ¤rbac-tenant
"""ORG-22a: ck_utr_role admite 'auditor' (expandir; sin contraer).

Es un CHECK sobre un String, no un ENUM nativo. Todavía nadie puede conceder el rol (ORG-22): esta
migración solo evita que la base lo rechace y que la revisión anterior se rompa al leerlo.
"""
from alembic import op

revision = "20261122_rol_auditor"
down_revision = "20261123_der06a_tipos_solicitud"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE user_tenant_roles DROP CONSTRAINT IF EXISTS ck_utr_role")
    op.execute(
        "ALTER TABLE user_tenant_roles ADD CONSTRAINT ck_utr_role CHECK (role IN "
        "('responsable_area', 'coordinador', 'dpo', 'implementador', 'admin_organizacion', 'auditor'))"
    )


def downgrade() -> None:
    # Contraer es de otra ficha: con filas 'auditor' la restricción anterior no se podría recrear.
    pass
