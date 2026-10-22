"""SEC-10: lopdp_app sin DELETE sobre las tablas globales users y tenants.

La aplicación nunca borra usuarios ni organizaciones (la baja de un usuario es lógica, con
deleted_at). El permiso DELETE que lopdp_app tenía heredado sobre esas tablas era una
superficie sin uso: con la credencial de la aplicación se podía borrar cualquier
organización o usuario, porque users y tenants no tienen RLS.

Las limpiezas de las pruebas usan la credencial del dueño, no la de la aplicación.

Revision ID: 20261021_sec10_sin_delete
Revises: 20261020_arco_solicitudes
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261021_sec10_sin_delete"
down_revision: Union[str, None] = "20261020_arco_solicitudes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("REVOKE DELETE ON users FROM lopdp_app")
    op.execute("REVOKE DELETE ON tenants FROM lopdp_app")


def downgrade() -> None:
    op.execute("GRANT DELETE ON users TO lopdp_app")
    op.execute("GRANT DELETE ON tenants TO lopdp_app")
