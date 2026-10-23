"""RLS forzado en las dos tablas con tenant_id que no lo tenían (QA-04).

Revision ID: 20261023_rls_pendientes
Revises: 20261022_invitacion_unica

La consulta del catálogo del 2026-10-22 encontró cuatro tablas con ``tenant_id`` y sin RLS
forzado. Dos son de la plataforma y quedan exentas (``invitaciones_organizacion`` y
``auditoria_plataforma``: el operador las consulta para todas las organizaciones y nunca fija
tenant, ORG-09). Las otras dos guardan datos de una organización:

- ``tareas_mitigacion``: tareas de mitigación que crea y lista el copiloto. Su router usa
  ``get_tenant_session``, que fija ``app.current_tenant_id``: el RLS no lo rompe. Además
  ``lopdp_app`` pierde ``DELETE``, que ningún código usa.
- ``registro_auditoria``: certificaciones de diagnóstico por organización (bitácora). Ningún
  código la consulta hoy; queda protegida antes de que alguien la use.

Mismo patrón de política que las tablas existentes (``tenant_isolation_<tabla>``).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261023_rls_pendientes"
down_revision: Union[str, None] = "20261022_invitacion_unica"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_POLITICA = "USING (tenant_id::text = current_setting('app.current_tenant_id', true))"

SUBIDA = [
    "ALTER TABLE tareas_mitigacion ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE tareas_mitigacion FORCE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_isolation_tareas_mitigacion ON tareas_mitigacion " + _POLITICA,
    "ALTER TABLE registro_auditoria ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE registro_auditoria FORCE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_isolation_registro_auditoria ON registro_auditoria " + _POLITICA,
    "REVOKE DELETE ON tareas_mitigacion FROM lopdp_app",
]

BAJADA = [
    "GRANT DELETE ON tareas_mitigacion TO lopdp_app",
    "DROP POLICY IF EXISTS tenant_isolation_registro_auditoria ON registro_auditoria",
    "ALTER TABLE registro_auditoria NO FORCE ROW LEVEL SECURITY",
    "ALTER TABLE registro_auditoria DISABLE ROW LEVEL SECURITY",
    "DROP POLICY IF EXISTS tenant_isolation_tareas_mitigacion ON tareas_mitigacion",
    "ALTER TABLE tareas_mitigacion NO FORCE ROW LEVEL SECURITY",
    "ALTER TABLE tareas_mitigacion DISABLE ROW LEVEL SECURITY",
]


def upgrade() -> None:
    for sentencia in SUBIDA:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in BAJADA:
        op.execute(sentencia)
