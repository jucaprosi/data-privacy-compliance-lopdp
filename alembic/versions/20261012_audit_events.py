"""Tabla audit_events, RLS e indice.

Revision ID: 20261012_audit_events
Revises: 20261008_app_role_rls
Create Date: 2026-10-12 22:00:00.000000

Registro inmutable de eventos que no son de una tarea (solicitudes de
responsables, asignacion y revocacion de roles, configuracion).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261012_audit_events"
down_revision: Union[str, None] = "20261008_app_role_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"
TABLA = "audit_events"


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_tenant_entity_timestamp",
        TABLA,
        ["tenant_id", "entity_type", "entity_id", "timestamp"],
    )
    op.execute(
        "ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        "ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_audit_events ON audit_events "
        "USING (tenant_id = current_setting('app.current_tenant_id', true));"
    )
    op.execute(
        f"GRANT SELECT, INSERT ON {TABLA} TO {APP_ROLE};"
    )


def downgrade() -> None:
    op.execute(
        f"REVOKE SELECT, INSERT ON {TABLA} FROM {APP_ROLE};"
    )
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_audit_events ON audit_events;"
    )
    op.execute(
        "ALTER TABLE audit_events NO FORCE ROW LEVEL SECURITY;"
    )
    op.drop_index("ix_audit_events_tenant_entity_timestamp", table_name=TABLA)
    op.drop_table(TABLA)
