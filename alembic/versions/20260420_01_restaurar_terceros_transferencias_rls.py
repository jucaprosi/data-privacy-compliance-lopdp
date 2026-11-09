# ¤¤backend-developer
"""ADPA-08 · restaura terceros_encargados y transferencias_terceros con RLS forzada. ¤adpa ¤transferencias ¤seguridad-tenant

La revisión 9369ce2c67fd borró `transferencias_terceros` y ninguna migración creó `terceros_encargados`,
aunque los modelos de las salas `terceros` y `transferencias` las usan. Esta migración las crea:

- Es idempotente (`IF NOT EXISTS`) y solo añade, de modo que no rompe la revisión en servicio (GCP-07).
- `tenant_id VARCHAR` con FK a `tenants(id)`, igual que `tenants.id` (criterio de DER-03).
- Enumeraciones como `VARCHAR` con `CHECK`, sin tipos nativos de PostgreSQL.
- `ENABLE` y `FORCE ROW LEVEL SECURITY` con la política `tenant_isolation_<tabla>` en USING y WITH CHECK.
- `lopdp_app` con SELECT, INSERT y UPDATE; sin borrado.

El nombre del archivo conserva la fecha de la ficha; el orden lo fija `down_revision`.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260420_01_terceros_transferencias_rls"
down_revision: Union[str, Sequence[str], None] = "20261121_demo_sesiones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = ("terceros_encargados", "transferencias_terceros")

SQL_ASCENDENTE = [
    """
    CREATE TABLE IF NOT EXISTS terceros_encargados (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        nombre VARCHAR(200) NOT NULL,
        es_internacional BOOLEAN NOT NULL DEFAULT false
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_terceros_encargados_tenant_id ON terceros_encargados (tenant_id)",
    """
    CREATE TABLE IF NOT EXISTS transferencias_terceros (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        nombre VARCHAR(200) NOT NULL,
        rol VARCHAR(20) NOT NULL CHECK (rol IN ('ENCARGADO', 'SUBENCARGADO', 'DESTINATARIO')),
        pais_destino VARCHAR(100) NOT NULL,
        nivel_proteccion VARCHAR(20) NOT NULL CHECK (nivel_proteccion IN ('ADECUADO', 'ESTANDAR', 'NO_ADECUADO')),
        clausulas_firmadas BOOLEAN NOT NULL DEFAULT false
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_transferencias_terceros_tenant_id ON transferencias_terceros (tenant_id)",
]

for _tabla in TABLAS:
    SQL_ASCENDENTE += [
        f"ALTER TABLE {_tabla} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {_tabla} FORCE ROW LEVEL SECURITY",
        f"DROP POLICY IF EXISTS tenant_isolation_{_tabla} ON {_tabla}",
        f"""CREATE POLICY tenant_isolation_{_tabla} ON {_tabla}
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))""",
        f"""DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app') THEN
                GRANT SELECT, INSERT, UPDATE ON {_tabla} TO lopdp_app;
              END IF;
            END $$""",
    ]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for tabla in reversed(TABLAS):
        op.execute(f"DROP TABLE IF EXISTS {tabla}")
