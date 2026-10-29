# ¤¤security-engineer
"""RM-21: hallazgos con origen y tareas que guardan el hallazgo que las originó. ¤hallazgos ¤roadmap ¤rbac-tenant

- Tabla `hallazgos` por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por tenant_id).
  La aplicación (lopdp_app) lee, inserta y solo actualiza `estado` y `actualizado_en`; no borra.
- `roadmap_tasks.hallazgo_id` con índice único parcial: un hallazgo genera a lo sumo una tarea.
- Corrige `ck_tasks_control_ref`: admitía P1-P73 (20261005_roadmaps) mientras el dominio y el banco
  de RM-19 usan P1-P80; convertir un hallazgo de P74-P80 terminaba en error 500.

Contrato: governance/especificaciones/RM-21.md §1.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_hallazgos"
down_revision = "20261030_bib_plantillas_md"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hallazgos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("origen_ref", sa.String(length=120), nullable=False),
        sa.Column("control_ref", sa.String(length=5), nullable=True),
        sa.Column("dimension", sa.String(length=4), nullable=True),
        sa.Column("severidad", sa.String(length=10), nullable=False),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=20), server_default="abierto", nullable=False),
        sa.Column("creado_por", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "origen IN ('diagnostico','auditoria','eipd','incidente','tercero','control_periodico')",
            name="ck_hallazgos_origen",
        ),
        sa.CheckConstraint("control_ref ~ '^P([1-9]|[1-7][0-9]|80)$'", name="ck_hallazgos_control_ref"),
        sa.CheckConstraint("dimension ~ '^D(0[1-9]|10)$'", name="ck_hallazgos_dimension"),
        sa.CheckConstraint("severidad IN ('critica','alta','media')", name="ck_hallazgos_severidad"),
        sa.CheckConstraint("char_length(titulo) BETWEEN 1 AND 200", name="ck_hallazgos_titulo"),
        sa.CheckConstraint("estado IN ('abierto','en_tratamiento','cerrado')", name="ck_hallazgos_estado"),
    )
    op.create_index("ux_hallazgos_origen", "hallazgos", ["tenant_id", "origen", "origen_ref"], unique=True)
    op.create_index("ix_hallazgos_tenant_estado", "hallazgos", ["tenant_id", "estado"])

    op.execute("ALTER TABLE hallazgos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hallazgos FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_hallazgos ON hallazgos "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON hallazgos FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON hallazgos TO lopdp_app")
    op.execute("GRANT UPDATE (estado, actualizado_en) ON hallazgos TO lopdp_app")

    op.add_column("roadmap_tasks", sa.Column("hallazgo_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_roadmap_tasks_hallazgo", "roadmap_tasks", "hallazgos", ["hallazgo_id"], ["id"]
    )
    op.create_index("ix_roadmap_tasks_hallazgo", "roadmap_tasks", ["hallazgo_id"])
    op.create_index(
        "ux_roadmap_tasks_hallazgo",
        "roadmap_tasks",
        ["hallazgo_id"],
        unique=True,
        postgresql_where=sa.text("hallazgo_id IS NOT NULL"),
    )

    op.drop_constraint("ck_tasks_control_ref", "roadmap_tasks", type_="check")
    op.create_check_constraint(
        "ck_tasks_control_ref", "roadmap_tasks", "control_ref ~ '^P([1-9]|[1-7][0-9]|80)$'"
    )


def downgrade() -> None:
    # Volver a P1-P73 fallaría si ya hay tareas de P74-P80: se deja que la base lo rechace.
    op.drop_constraint("ck_tasks_control_ref", "roadmap_tasks", type_="check")
    op.create_check_constraint(
        "ck_tasks_control_ref", "roadmap_tasks", "control_ref ~ '^P([1-9]|[1-6][0-9]|7[0-3])$'"
    )
    op.drop_index("ux_roadmap_tasks_hallazgo", table_name="roadmap_tasks")
    op.drop_index("ix_roadmap_tasks_hallazgo", table_name="roadmap_tasks")
    op.drop_constraint("fk_roadmap_tasks_hallazgo", "roadmap_tasks", type_="foreignkey")
    op.drop_column("roadmap_tasks", "hallazgo_id")
    op.drop_table("hallazgos")
