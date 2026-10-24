"""Respuestas del diagnóstico guardadas por organización, con RLS (DIAG-01).

Una fila por organización y pregunta del banco del diagnóstico (pregunta_id). Se guarda el nombre
del control tal como lo trae el banco: el banco (80 preguntas) no tiene código P y no hay una
correspondencia definida con el catálogo P1-P73 de la hoja de ruta (hallazgo anotado para RM-19).
Las restricciones CHECK repiten en la base las escalas que valida el servidor.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261024_diag_respuestas"
down_revision = "20261023_rls_pendientes"
branch_labels = None
depends_on = None

TABLA = "diagnostico_respuestas"


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("pregunta_id", sa.Integer(), nullable=False),
        sa.Column("control", sa.String(300), nullable=False),
        sa.Column("dimension", sa.String(3), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("nivel_evidencia", sa.Integer(), nullable=False),
        sa.Column("criticidad", sa.Integer(), nullable=False),
        sa.Column("es_critica", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("riesgo_base", sa.Integer(), nullable=False),
        sa.Column("respondido_por", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "pregunta_id"),
        sa.CheckConstraint("pregunta_id >= 1", name="ck_diag_pregunta"),
        sa.CheckConstraint("length(trim(control)) > 0", name="ck_diag_control"),
        sa.CheckConstraint("dimension ~ '^D(0[1-9]|10)$'", name="ck_diag_dimension"),
        sa.CheckConstraint("estado IN ('Conforme', 'Parcial', 'No Conforme', 'Pendiente')", name="ck_diag_estado"),
        sa.CheckConstraint("nivel_evidencia BETWEEN 0 AND 3", name="ck_diag_evidencia"),
        sa.CheckConstraint("criticidad BETWEEN 1 AND 5", name="ck_diag_criticidad"),
        sa.CheckConstraint("riesgo_base BETWEEN 1 AND 10", name="ck_diag_riesgo"),
    )
    op.execute(f"ALTER TABLE {TABLA} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLA} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation_{TABLA} ON {TABLA} "
        "USING (tenant_id = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {TABLA} TO lopdp_app")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{TABLA} ON {TABLA}")
    op.drop_table(TABLA)
