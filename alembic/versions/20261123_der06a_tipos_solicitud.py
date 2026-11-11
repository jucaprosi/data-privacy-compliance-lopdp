# ¤¤backend-developer
"""DER-06a: tres valores nuevos en el tipo tiposolicitud (suspensión, decisiones automatizadas, queja), sin activarlos. ¤regulation-code

Expandir sin contraer: PostgreSQL no permite retirar valores de un tipo nativo, así que no hay downgrade
que los quite. ADD VALUE IF NOT EXISTS hace la migración idempotente.
"""
from alembic import op

revision = "20261123_der06a_tipos_solicitud"
down_revision = "20261109_inventario_activos"
branch_labels = None
depends_on = None

SENTENCIAS = (
    "ALTER TYPE tiposolicitud ADD VALUE IF NOT EXISTS 'SUSPENSION'",
    "ALTER TYPE tiposolicitud ADD VALUE IF NOT EXISTS 'DECISIONES_AUTOMATIZADAS'",
    "ALTER TYPE tiposolicitud ADD VALUE IF NOT EXISTS 'QUEJA'",
)


def upgrade() -> None:
    # ADD VALUE no se usa en la misma transacción: bloque autocommit.
    with op.get_context().autocommit_block():
        for sentencia in SENTENCIAS:
            op.execute(sentencia)


def downgrade() -> None:
    # PostgreSQL no retira valores de un tipo nativo: la contracción no existe y no se promete.
    pass
