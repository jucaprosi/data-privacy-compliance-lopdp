# ¤¤backend-developer
"""NORM-02: nota de la revisión humana en `normativa_resoluciones`. ¤inteligencia-normativa ¤vigilancia-spdp

Revision ID: norm02_nota_revision
Revises: reg01_paquetes_normativos

`nota_revision` TEXT NULL; un CHECK la exige (al menos 10 caracteres sin espacios sobrantes) cuando hay
`revisada_en`. Las filas anteriores no tienen revisión, así que el CHECK se cumple sin recuento previo.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm02_nota_revision"
down_revision: Union[str, Sequence[str], None] = "reg01_paquetes_normativos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE normativa_resoluciones ADD COLUMN nota_revision TEXT")
    op.execute(
        "ALTER TABLE normativa_resoluciones ADD CONSTRAINT ck_normativa_nota_revision "
        "CHECK (revisada_en IS NULL OR (nota_revision IS NOT NULL AND length(btrim(nota_revision)) >= 10))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE normativa_resoluciones DROP CONSTRAINT ck_normativa_nota_revision")
    op.execute("ALTER TABLE normativa_resoluciones DROP COLUMN nota_revision")
