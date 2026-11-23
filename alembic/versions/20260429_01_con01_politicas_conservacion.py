# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer
"""CON-01: políticas de conservación y bloqueo vinculadas a las actividades del RAT. ¤conservacion ¤rat

Revision ID: con01_politicas_conservacion
Revises: ret02_clave_objeto (BASE_COMUN; primera migración de la sala `conservacion`, CI-28)

`politicas_conservacion`: una política por actividad del RAT y plazo, con RLS ENABLE y FORCE por
`app.current_tenant_id`. `lopdp_app` lee, crea y actualiza; no borra. El acta de ejecución es un SHA-256
que solo existe cuando la política dejó de estar ACTIVA (CHECK `politicas_conservacion_acta_coherente`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "con01_politicas_conservacion"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"
branch_labels: Union[str, Sequence[str], None] = ("conservacion",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE politicas_conservacion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            actividad_rat_id VARCHAR(64) NOT NULL,
            plazo_meses INTEGER NOT NULL CHECK (plazo_meses > 0),
            accion_vencimiento VARCHAR(16) NOT NULL
                CHECK (accion_vencimiento IN ('BLOQUEO', 'ANONIMIZACION', 'SUPRESION')),
            fecha_proxima_revision DATE NOT NULL,
            estado VARCHAR(16) NOT NULL DEFAULT 'ACTIVA'
                CHECK (estado IN ('ACTIVA', 'BLOQUEADA', 'EJECUTADA')),
            acta_ejecucion_hash VARCHAR(64) NULL CHECK (acta_ejecucion_hash ~ '^[0-9a-f]{64}$'),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT politicas_conservacion_acta_coherente
                CHECK ((estado = 'ACTIVA') = (acta_ejecucion_hash IS NULL))
        );
        CREATE INDEX ix_politicas_conservacion_tenant_revision
            ON politicas_conservacion (tenant_id, fecha_proxima_revision);
        ALTER TABLE politicas_conservacion ENABLE ROW LEVEL SECURITY;
        ALTER TABLE politicas_conservacion FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_politicas_conservacion ON politicas_conservacion
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON politicas_conservacion FROM lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON politicas_conservacion TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS politicas_conservacion")
