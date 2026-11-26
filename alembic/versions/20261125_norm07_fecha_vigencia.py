# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤monitoreo-job ¤inteligencia-normativa
"""NORM-07 · fecha de entrada en vigencia de una resolución, que el operador da al revisarla.

Revision ID: norm07_fecha_vigencia
Revises: norm06_transcripciones (cabeza de la sala «inteligencia_normativa»)

Contrato: governance/especificaciones/NORM-07.md §1. La columna es nula (no toda norma indica fecha) y `lopdp_app`
solo puede actualizarla por columna, como las cuatro de la revisión (NORM-05).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm07_fecha_vigencia"
down_revision: Union[str, Sequence[str], None] = "norm06_transcripciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE normativa_resoluciones ADD COLUMN fecha_vigencia DATE;
        GRANT UPDATE (fecha_vigencia) ON normativa_resoluciones TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        REVOKE UPDATE (fecha_vigencia) ON normativa_resoluciones FROM lopdp_app;
        ALTER TABLE normativa_resoluciones DROP COLUMN fecha_vigencia;
        """
    )
