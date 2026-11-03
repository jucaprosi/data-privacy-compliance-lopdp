# ¤¤backend-developer
"""Fusión de las tres cabezas de la tanda 33 de Biblioteca (BIB-107, BIB-201 y BIB-103). ¤rbac-tenant

No cambia el esquema: solo une las tres ramas de Alembic en una cabeza. Las tres migraciones se encadenaron
a la misma revisión y se fusionaron por separado; las bases que tengan una de ellas aplican al subir las
otras dos y después esta (precedente: 20261108_merge_heads_rat_org16).
"""
from typing import Sequence, Union

revision: str = "20261110_merge_heads_tanda33"
down_revision: Union[str, Sequence[str], None] = (
    "20261103_biblioteca_borradores",
    "20261103_bib_mis_plantillas",
    "20261109_bib_documentos",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
