# ¤¤backend-developer
"""Fusión de las cabezas de BIB-106 y SEC-13 (FUSION_ALEMBIC, opción B). ¤seguridad

No cambia el esquema: une 20261119_bib106_cargas y 20261121_sec13_ventana en una sola cabeza.
"""
from typing import Sequence, Union

revision: str = "20261122_merge_sec13_bib106"
down_revision: Union[str, Sequence[str], None] = (
    "20261119_bib106_cargas",
    "20261121_sec13_ventana",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
