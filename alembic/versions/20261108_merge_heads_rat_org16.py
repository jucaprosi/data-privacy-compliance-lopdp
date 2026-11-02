# ¤¤backend-developer
"""Fusión de las dos cabezas: la cadena de main (RAT-05, RM-23) y la de dev/aleczandra (DIAG-08, DPO-02, ORG-16). ¤rbac-tenant

No cambia el esquema: solo une las dos ramas de Alembic en una cabeza. Las bases que tengan una de las dos
cabezas aplican al subir las revisiones de la otra y después esta (precedente: ef238d956830).
"""
from typing import Sequence, Union

revision: str = "20261108_merge_heads_rat_org16"
down_revision: Union[str, Sequence[str], None] = ("20261101_org16_perfil_alta", "20261107_recordatorios")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
