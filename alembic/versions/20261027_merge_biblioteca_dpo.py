"""merge heads de biblioteca_base y dpo_bitacora

Revision ID: 20261027_merge_biblioteca_dpo
Revises: 20261025_biblioteca_base, 20261027_dpo_bitacora
Create Date: 2026-10-27

Une las dos cabezas que quedaron en main (#158 y #182 colgaban de
20261025_gran_escala_obligacion). No altera el esquema.
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "20261027_merge_biblioteca_dpo"
down_revision: Union[str, None] = ("20261025_biblioteca_base", "20261027_dpo_bitacora")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
