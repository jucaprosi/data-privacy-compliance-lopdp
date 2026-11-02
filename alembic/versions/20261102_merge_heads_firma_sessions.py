# ¤¤backend-developer
"""Fusión de las dos cabezas: la cadena principal (hasta merge_heads_rat_org16) y la de firma_sessions (FIRMA-03). ¤rbac-tenant ¤firma-electronica

No cambia el esquema: solo une las dos ramas de Alembic en una cabeza. Las bases que tengan ambas
cabezas aplican esta migración automáticamente al subir.
"""
from typing import Sequence, Union

revision: str = "20261102_merge_heads_firma_sessions"
down_revision: Union[str, Sequence[str], None] = (
    "20261108_merge_heads_rat_org16",
    "20261103_firma_sessions",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
