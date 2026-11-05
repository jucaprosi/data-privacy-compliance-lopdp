# ¤¤backend-developer
"""Fusión de cabezas de Alembic tras sincronizar main en dev/jose (FIRMA-02 y tanda 35 de Biblioteca). ¤rbac-tenant

No cambia el esquema: solo une la rama de FIRMA-02 (20261103_aceptaciones) y la cabeza de main
(20261112_merge_heads_tanda35) en una sola cabeza para dev/jose.
"""
from typing import Sequence, Union

revision: str = "20261113_merge_heads_jose_f02"
down_revision: Union[str, Sequence[str], None] = (
    "20261103_aceptaciones",
    "20261112_merge_heads_tanda35",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
