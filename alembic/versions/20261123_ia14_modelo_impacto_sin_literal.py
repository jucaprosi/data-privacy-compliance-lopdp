# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""IA-14 · la base no repite la lista de modelos: `normativa_analisis_impacto.modelo` solo exige un valor no vacío. ¤gemini-vertex ¤inteligencia-normativa

Revision ID: ia14_modelo_impacto_sin_literal
Revises: norm03_analisis_impacto (sala «inteligencia_normativa»)

Contrato: governance/especificaciones/IA-14.md §1 y R4. La lista de modelos válidos vive solo en `MODELOS_PERMITIDOS`
(IA-13) y la compuerta la aplica antes de llamar. El `downgrade` devuelve el CHECK anterior con NOT VALID, para no
fallar sobre filas ya escritas con el modelo nuevo.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ia14_modelo_impacto_sin_literal"
down_revision: Union[str, Sequence[str], None] = "norm03_analisis_impacto"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE normativa_analisis_impacto DROP CONSTRAINT IF EXISTS normativa_analisis_impacto_modelo_check;
        ALTER TABLE normativa_analisis_impacto
            ADD CONSTRAINT ck_normativa_impacto_modelo CHECK (char_length(modelo) BETWEEN 1 AND 40);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE normativa_analisis_impacto DROP CONSTRAINT IF EXISTS ck_normativa_impacto_modelo;
        ALTER TABLE normativa_analisis_impacto
            ADD CONSTRAINT normativa_analisis_impacto_modelo_check CHECK (modelo = 'gemini-2.5-pro') NOT VALID;
        """
    )
