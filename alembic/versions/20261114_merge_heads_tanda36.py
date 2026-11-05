# ¤¤backend-developer
"""Fusión de las dos cabezas de la tanda 36 de Biblioteca (BIB-301 y BIB-306). ¤rbac-tenant

No cambia el esquema: solo une las dos ramas de Alembic en una cabeza. Las dos migraciones se encadenaron
a la misma revisión (20261112_merge_heads_tanda35) y se fusionaron por separado; las bases que tengan una de
ellas aplican al subir la otra y después esta (precedente: 20261112_merge_heads_tanda35).
"""
from typing import Sequence, Union

revision: str = "20261114_merge_heads_tanda36"
down_revision: Union[str, Sequence[str], None] = (
    "bib301_aprobaciones",
    "20261113_bib_conservacion",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
