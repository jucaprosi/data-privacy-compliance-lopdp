# ¤¤backend-developer
"""Fusión de las tres cabezas de las tandas 37-38 de Biblioteca (BIB-402, BIB-203 y BIB-303). ¤rbac-tenant

No cambia el esquema: solo une las ramas de Alembic en una cabeza. Las tres migraciones se encadenaron
a la misma revisión y se fusionaron por separado (precedente: 20261114_merge_heads_tanda36).
"""
from typing import Sequence, Union

revision: str = "20261115_merge_heads_tanda37"
down_revision: Union[str, Sequence[str], None] = (
    "20261103_bib_vinculos",
    "20261114_biblioteca_filas",
    "20261114_bib_verificaciones",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
