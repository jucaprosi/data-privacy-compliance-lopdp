"""«No aplica» con justificación obligatoria en las respuestas del diagnóstico (DIAG-05). ¤diagnostico-no-aplica

Columnas nuevas en `diagnostico_respuestas`: `no_aplica`, `justificacion_no_aplica`, `justificado_por` y
`justificado_en`. Una restricción en la base repite la regla del servidor: un «no aplica» sin
justificación de al menos 10 caracteres no se guarda. La tabla ya tiene RLS (ENABLE y FORCE, USING y
WITH CHECK por `tenant_id`) y `lopdp_app` ya tiene SELECT, INSERT y UPDATE: no cambian.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_diagnostico_no_aplica"
down_revision = "20261122_merge_sec13_bib106"
branch_labels = None
depends_on = None

TABLA = "diagnostico_respuestas"


def upgrade() -> None:
    op.add_column(TABLA, sa.Column("no_aplica", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(TABLA, sa.Column("justificacion_no_aplica", sa.Text(), nullable=True))
    op.add_column(TABLA, sa.Column("justificado_por", sa.String(255), nullable=True))
    op.add_column(TABLA, sa.Column("justificado_en", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_diag_no_aplica_justificado",
        TABLA,
        "NOT no_aplica OR (length(trim(justificacion_no_aplica)) >= 10 AND justificado_por IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_diag_no_aplica_justificado", TABLA, type_="check")
    for columna in ("justificado_en", "justificado_por", "justificacion_no_aplica", "no_aplica"):
        op.drop_column(TABLA, columna)
