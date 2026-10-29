"""Escala SMARTCIDI en las respuestas del diagnóstico (DIAG-08).

`nivel_asignado` (1 a 5, nulo = sin responder con la escala nueva) y evidencia de 0 a 4. Las filas
existentes recorren la evidencia 1 → 2, 2 → 3, 3 → 4 (documentada → documental, implementada →
operativa, probada → revisada); 0 no cambia. El nivel asignado queda nulo: no se puede deducir si
un «Parcial» era 2 o 3. `diagnostico_resultados` no se toca: lo sellado es inmutable.

El `downgrade` pierde información: la evidencia vuelve a 0-3 (4 → 3, 3 → 2, 2 → 1, 1 → 0) y se
elimina `nivel_asignado`. Los permisos de `lopdp_app` y la RLS no cambian.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261031_diag_escala_smartcidi"
down_revision = "20261030_bib_plantillas_md"
branch_labels = None
depends_on = None

TABLA = "diagnostico_respuestas"


def upgrade() -> None:
    op.drop_constraint("ck_diag_evidencia", TABLA, type_="check")
    op.execute(f"UPDATE {TABLA} SET nivel_evidencia = nivel_evidencia + 1 WHERE nivel_evidencia > 0")
    op.create_check_constraint("ck_diag_evidencia", TABLA, "nivel_evidencia BETWEEN 0 AND 4")
    op.add_column(TABLA, sa.Column("nivel_asignado", sa.SmallInteger(), nullable=True))
    op.create_check_constraint("ck_diag_nivel_asignado", TABLA, "nivel_asignado BETWEEN 1 AND 5")


def downgrade() -> None:
    op.drop_constraint("ck_diag_nivel_asignado", TABLA, type_="check")
    op.drop_column(TABLA, "nivel_asignado")
    op.drop_constraint("ck_diag_evidencia", TABLA, type_="check")
    # Con pérdida: la evidencia informal (1) vuelve a 0 y se pierde el nivel asignado.
    op.execute(f"UPDATE {TABLA} SET nivel_evidencia = nivel_evidencia - 1 WHERE nivel_evidencia > 0")
    op.create_check_constraint("ck_diag_evidencia", TABLA, "nivel_evidencia BETWEEN 0 AND 3")
