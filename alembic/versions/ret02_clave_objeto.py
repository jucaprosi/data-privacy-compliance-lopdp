# ¤roadmap ¤organizacion ¤almacenamiento
"""RET-02: renombra las columnas `r2_key` a `clave_objeto` en `task_evidence` y `exportaciones`."""
from typing import Sequence, Union

from alembic import op

revision: str = "ret02_clave_objeto"
down_revision: Union[str, Sequence[str], None] = "inc02_incidentes_asistente"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("task_evidence", "r2_key", new_column_name="clave_objeto")
    op.alter_column("exportaciones", "r2_key", new_column_name="clave_objeto")


def downgrade() -> None:
    op.alter_column("exportaciones", "clave_objeto", new_column_name="r2_key")
    op.alter_column("task_evidence", "clave_objeto", new_column_name="r2_key")
