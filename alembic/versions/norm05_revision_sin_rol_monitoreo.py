# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤monitoreo-job
"""NORM-05 · la revisión escribe como `lopdp_app`: UPDATE solo sobre cuatro columnas de normativa_resoluciones. ¤inteligencia-normativa ¤seguridad

Revision ID: norm05_revision_sin_rol_mon
Revises: ia14_modelo_impacto_sin_literal (cabeza de la sala «inteligencia_normativa»)

Contrato: governance/especificaciones/NORM-05.md §1. Ningún `GRANT lopdp_normativa TO ...`: el backend no adopta el rol
del monitoreo. `SELECT` se concede solo si falta; como ya lo tenía, el `downgrade` revoca únicamente el `UPDATE` por columna.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm05_revision_sin_rol_mon"
down_revision: Union[str, Sequence[str], None] = "ia14_modelo_impacto_sin_literal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNAS = "estado, revisada_por, revisada_en, nota_revision"


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT has_table_privilege('lopdp_app', 'normativa_resoluciones', 'SELECT') THEN
                GRANT SELECT ON normativa_resoluciones TO lopdp_app;
            END IF;
        END $$;
        GRANT UPDATE ({COLUMNAS}) ON normativa_resoluciones TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE UPDATE ({COLUMNAS}) ON normativa_resoluciones FROM lopdp_app")
