"""Vincula la cuenta de Google al usuario: users.google_sub (único, opcional).

Revision ID: 20261017_users_google_sub
Revises: 20261016_tenants_tamano_check
Create Date: 2026-10-17 12:00:00.000000

SEC-03: la API verifica el token de identidad de Google y obtiene de él solo el usuario. `google_sub`
es el identificador estable de la cuenta de Google (el campo `sub` del token); la cuenta de la
plataforma se vincula por correo verificado la primera vez y desde entonces se busca por `sub`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261017_users_google_sub"
down_revision: Union[str, None] = "20261016_tenants_tamano_check"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))
    # Único y opcional: varias filas pueden quedar sin vincular (NULL), ninguna comparte `sub`.
    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])


def downgrade() -> None:
    op.drop_constraint("uq_users_google_sub", "users", type_="unique")
    op.drop_column("users", "google_sub")
