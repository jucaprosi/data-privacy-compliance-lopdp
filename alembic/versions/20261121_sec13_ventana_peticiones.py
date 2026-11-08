# ¤¤backend-developer
"""Tabla ventana_peticiones del limitador de SEC-13. ¤seguridad

Revision ID: 20261121_sec13_ventana
Revises: 20261118_merge_heads_cierre_dev

Una fila por clave `lim:<politica>:<ambito>:<resumen>` (sin datos personales: el id va resumido en
SHA-256). Sin tenant_id ni RLS: no guarda datos de ninguna organización. `lopdp_app` recibe SELECT,
INSERT y UPDATE, sin DELETE: la ventana vencida se reinicia con UPSERT sobre la misma fila.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261121_sec13_ventana"
down_revision: Union[str, Sequence[str], None] = "20261118_merge_heads_cierre_dev"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"
TABLA = "ventana_peticiones"


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column("clave", sa.String(length=96), primary_key=True),
        sa.Column("inicio", sa.BigInteger(), nullable=False),
        sa.Column("contador", sa.Integer(), nullable=False),
        sa.Column("previo", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {TABLA} TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table(TABLA)
