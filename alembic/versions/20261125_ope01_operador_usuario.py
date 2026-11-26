# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤seguridad
"""OPE-01: cada operador de la plataforma tiene su usuario.

Revision ID: 20261125_ope01_operador_usuario
Revises: norm02b_destinatarios_normativos (cabeza de la sala `plataforma`)

Añade `operadores_plataforma.usuario_id` (nulo hasta `alta` o `vincular`), con clave foránea a `users`
y UNIQUE: un usuario es, como mucho, un operador. El `downgrade` quita la columna y sus restricciones.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261125_ope01_operador_usuario"
down_revision: Union[str, Sequence[str], None] = "norm02b_destinatarios_normativos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE operadores_plataforma
            ADD COLUMN usuario_id varchar NULL
                CONSTRAINT operadores_plataforma_usuario_id_fkey REFERENCES users(id),
            ADD CONSTRAINT operadores_plataforma_usuario_id_key UNIQUE (usuario_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE operadores_plataforma
            DROP CONSTRAINT operadores_plataforma_usuario_id_key,
            DROP CONSTRAINT operadores_plataforma_usuario_id_fkey,
            DROP COLUMN usuario_id;
        """
    )
