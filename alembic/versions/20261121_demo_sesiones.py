# ¤¤backend-developer
"""Tabla demo_sesiones y tenants.es_demo (DEMO-00, PRD EVYDENTIA §5.6.4, invariantes 60 a 63). ¤demo

- Una sola demo activa por vendedor: índice único parcial `(vendedor_sub) WHERE estado = 'activa'`.
- `tenant_id` y `persona_usuario_id` nulables con `ON DELETE SET NULL`: la fila sobrevive a la purga
  del tenant y conserva `sub`, correo, inicio, fin y motivo durante 90 días.
- Sin RLS: el resolutor la lee antes de conocer el tenant (exención con su motivo). No se expone
  en ninguna ruta.
- `lopdp_app` con SELECT, INSERT y UPDATE; sin borrado (invariante 63).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261121_demo_sesiones"
down_revision: Union[str, Sequence[str], None] = "20261108_derechos_tenant_texto"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_ASCENDENTE = [
    "ALTER TABLE tenants ADD COLUMN es_demo BOOLEAN NOT NULL DEFAULT false",
    """
    CREATE TABLE demo_sesiones (
        id VARCHAR PRIMARY KEY,
        vendedor_sub VARCHAR NOT NULL,
        vendedor_email VARCHAR NOT NULL,
        tenant_id VARCHAR NULL REFERENCES tenants(id) ON DELETE SET NULL,
        persona_usuario_id VARCHAR NULL REFERENCES users(id) ON DELETE SET NULL,
        estado VARCHAR NOT NULL DEFAULT 'activa',
        iniciada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        ultima_actividad TIMESTAMPTZ NOT NULL DEFAULT now(),
        terminada_en TIMESTAMPTZ NULL,
        motivo_fin VARCHAR NULL,
        CONSTRAINT ck_demo_sesiones_estado CHECK (estado IN ('activa', 'vencida')),
        CONSTRAINT ck_demo_sesiones_motivo
            CHECK (motivo_fin IS NULL OR motivo_fin IN ('terminar', 'inactividad', 'reemplazada')),
        CONSTRAINT ck_demo_sesiones_fin CHECK ((estado = 'activa') = (terminada_en IS NULL))
    )
    """,
    "CREATE UNIQUE INDEX uq_demo_sesiones_una_activa ON demo_sesiones (vendedor_sub) WHERE estado = 'activa'",
    "CREATE INDEX ix_demo_sesiones_estado_actividad ON demo_sesiones (estado, ultima_actividad)",
    "GRANT SELECT, INSERT, UPDATE ON demo_sesiones TO lopdp_app",
]

SQL_DESCENDENTE = [
    "DROP TABLE IF EXISTS demo_sesiones",
    "ALTER TABLE tenants DROP COLUMN IF EXISTS es_demo",
]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
