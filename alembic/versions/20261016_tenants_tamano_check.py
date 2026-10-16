"""check constraint sobre tenants.tamano y eliminacion de default.

Revision ID: 20261016_tenants_tamano_check
Revises: 20261012_audit_events
Create Date: 2026-10-16 17:18:00.000000

RM-15: Configuración de la organización y vocabulario de tamaños.
Restringe tenants.tamano al vocabulario cerrado ('micro', 'pequena', 'mediana', 'corporativo')
permitiendo NULL y sin valor por defecto.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261016_tenants_tamano_check"
down_revision: Union[str, None] = "20261012_audit_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = "tenants"
CONSTRAINT_NAME = "ck_tenants_tamano"
VALORES_VALIDOS = ("micro", "pequena", "mediana", "corporativo")


def upgrade() -> None:
    # 1. Normalizar valores existentes que no cumplan el vocabulario cerrado a NULL
    op.execute(
        sa.text(
            f"UPDATE {TABLA} SET tamano = NULL WHERE tamano IS NOT NULL AND tamano NOT IN {VALORES_VALIDOS}"
        )
    )

    # 2. Eliminar server default si existiera
    op.alter_column(TABLA, "tamano", server_default=None)

    # 3. Crear CHECK constraint permitiendo NULL o valores en VALORES_VALIDOS
    # En PostgreSQL, CHECK (tamano IN (...)) evalúa a NULL (TRUE) cuando tamano es NULL,
    # pero explicitamos tamano IS NULL OR tamano IN (...) para máxima claridad normativa.
    op.create_check_constraint(
        CONSTRAINT_NAME,
        TABLA,
        "tamano IS NULL OR tamano IN ('micro', 'pequena', 'mediana', 'corporativo')",
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, TABLA, type_="check")
