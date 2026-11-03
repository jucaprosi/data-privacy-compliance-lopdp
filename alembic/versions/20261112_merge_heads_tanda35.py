# ¤¤backend-developer
"""Fusión de las dos cabezas de la tanda 35 de Biblioteca (BIB-104 y BIB-204). ¤rbac-tenant

No cambia el esquema: solo une las dos ramas de Alembic en una cabeza. Las dos migraciones se encadenaron
a la misma revisión (20261110_merge_heads_tanda33) y se fusionaron por separado; las bases que tengan una de
ellas aplican al subir la otra y después esta (precedente: 20261110_merge_heads_tanda33).
"""
from typing import Sequence, Union

revision: str = "20261112_merge_heads_tanda35"
down_revision: Union[str, Sequence[str], None] = (
    "20261111_bib_descargas",
    "20261111_bib_reglas",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass