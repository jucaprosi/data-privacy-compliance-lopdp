"""Roadmap inteligente y evidencias de tareas.

Revision ID: 20261005_roadmaps
Revises: 20261006_user_tenant_roles
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261005_roadmaps"
down_revision: Union[str, None] = "20261006_user_tenant_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("variables_json", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("score_objetivo", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmaps_tenant", "roadmaps", ["tenant_id"])

    op.create_table(
        "roadmap_waves",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("roadmap_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_waves_roadmap", "roadmap_waves", ["roadmap_id"])
    op.create_index("ix_roadmap_waves_tenant", "roadmap_waves", ["tenant_id"])

    op.create_table(
        "roadmap_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("wave_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("area_id", sa.String(), nullable=True),
        sa.Column("control_ref", sa.String(length=5), nullable=False),
        sa.Column("dimension", sa.String(length=4), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("effort_hours", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pendiente", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kpi", sa.Text(), nullable=True),
        sa.Column("deliverable", sa.Text(), nullable=True),
        sa.Column("evidence_required", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["wave_id"], ["roadmap_waves.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("priority IN ('critica','alta','media')", name="ck_tasks_priority"),
        sa.CheckConstraint("status IN ('pendiente','en_progreso','completada','bloqueada')", name="ck_tasks_status"),
        sa.CheckConstraint("control_ref ~ '^P([1-9]|[1-6][0-9]|7[0-3])$'", name="ck_tasks_control_ref"),
        sa.CheckConstraint("dimension ~ '^D(0[1-9]|10)$'", name="ck_tasks_dimension"),
    )
    op.create_index("ix_roadmap_tasks_wave", "roadmap_tasks", ["wave_id"])
    op.create_index("ix_roadmap_tasks_tenant", "roadmap_tasks", ["tenant_id"])

    op.create_table(
        "task_dependencies",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("depends_on_task_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["roadmap_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_task_id"], ["roadmap_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "depends_on_task_id"),
    )

    op.create_table(
        "task_evidence",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("r2_key", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("uploaded_by", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("validation_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("validated_by", sa.String(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("signature_provider", sa.String(length=50), nullable=True),
        sa.Column("signature_type", sa.String(length=20), nullable=True),
        sa.Column("signature_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_hash", sa.String(length=64), nullable=True),
        sa.Column("certificate_subject", sa.Text(), nullable=True),
        sa.Column("tsa_token_url", sa.Text(), nullable=True),
        sa.Column("signature_status", sa.String(length=20), server_default="unsigned", nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["roadmap_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["validated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("validation_status IN ('pending','approved','rejected')", name="ck_evidence_status"),
    )
    op.create_index("ix_evidence_task", "task_evidence", ["task_id"])
    op.create_index("ix_evidence_tenant", "task_evidence", ["tenant_id"])

    op.create_table(
        "task_audit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["roadmap_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_task", "task_audit_log", ["task_id"])
    op.create_index("ix_audit_tenant", "task_audit_log", ["tenant_id"])

    for tabla in ["roadmaps", "roadmap_waves", "roadmap_tasks", "task_evidence", "task_audit_log"]:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"CREATE POLICY tenant_isolation_{tabla} ON {tabla} USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    for tabla in ["task_audit_log", "task_evidence", "task_dependencies", "roadmap_tasks", "roadmap_waves", "roadmaps"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{tabla} ON {tabla};")
    op.drop_index("ix_audit_tenant", table_name="task_audit_log")
    op.drop_index("ix_audit_task", table_name="task_audit_log")
    op.drop_table("task_audit_log")
    op.drop_index("ix_evidence_tenant", table_name="task_evidence")
    op.drop_index("ix_evidence_task", table_name="task_evidence")
    op.drop_table("task_evidence")
    op.drop_table("task_dependencies")
    op.drop_index("ix_roadmap_tasks_tenant", table_name="roadmap_tasks")
    op.drop_index("ix_roadmap_tasks_wave", table_name="roadmap_tasks")
    op.drop_table("roadmap_tasks")
    op.drop_index("ix_roadmap_waves_tenant", table_name="roadmap_waves")
    op.drop_index("ix_roadmap_waves_roadmap", table_name="roadmap_waves")
    op.drop_table("roadmap_waves")
    op.drop_index("ix_roadmaps_tenant", table_name="roadmaps")
    op.drop_table("roadmaps")
