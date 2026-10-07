"""Add areas and user_tenant_roles.

Revision ID: 20261006_user_tenant_roles
Revises: 20261006_users
Create Date: 2026-10-06 12:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20261006_user_tenant_roles"
down_revision: Union[str, None] = "20261006_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "areas",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("parent_area_id", sa.String(), nullable=True),
        sa.Column("responsable_user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["parent_area_id"], ["areas.id"]),
        sa.ForeignKeyConstraint(["responsable_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_areas_tenant", "areas", ["tenant_id"])
    op.create_index("ix_areas_parent", "areas", ["parent_area_id"])

    op.create_table(
        "user_tenant_roles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("area_id", sa.String(), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("also_responsable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("granted_by", sa.String(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"]),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tenant_id", "area_id", "role", name="uq_utr_user_tenant_area_role"),
        sa.CheckConstraint(
            "role IN ('responsable_area','encargado','dpo','implementador','admin_organizacion')",
            name="ck_utr_role",
        ),
    )
    op.create_index("ix_utr_user_tenant", "user_tenant_roles", ["user_id", "tenant_id"])

    op.execute("ALTER TABLE areas ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_tenant_roles ENABLE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY tenant_isolation_areas ON areas USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("CREATE POLICY tenant_isolation_utr ON user_tenant_roles USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_utr ON user_tenant_roles;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_areas ON areas;")
    op.drop_index("ix_utr_user_tenant", table_name="user_tenant_roles")
    op.drop_table("user_tenant_roles")
    op.drop_index("ix_areas_parent", table_name="areas")
    op.drop_index("ix_areas_tenant", table_name="areas")
    op.drop_table("areas")
