# ¤¤backend-developer
"""Fusión de las dos cabezas que dejó el cierre de las ramas dev/<persona> en main. ¤rbac-tenant

No cambia el esquema: solo une la cadena de dev/aleczandra (20261117_bib_estado_revision, tandas 36 a 39
de Biblioteca) y la de dev/jose (20261103_bib_cuenta_profesional, FIRMA-02 y BIB-401) en una sola cabeza.
Desde este cierre cada tarea entra a main por su propio PR y las ramas dev/<persona> se retiran.
"""
from typing import Sequence, Union

revision: str = "20261118_merge_heads_cierre_dev"
down_revision: Union[str, Sequence[str], None] = (
    "20261117_bib_estado_revision",
    "20261103_bib_cuenta_profesional",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
