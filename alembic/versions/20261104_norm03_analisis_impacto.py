# ¤¤backend-developer
"""NORM-03 · tabla normativa_analisis_impacto por organización, con RLS forzada. ¤inteligencia-normativa ¤dpo-independencia

Revision ID: norm03_analisis_impacto
Revises: ret02_clave_objeto (BASE_COMUN, primera migración de la sala; etiqueta «inteligencia_normativa»)

Contrato: governance/especificaciones/NORM-03.md §1. La tabla es nueva, sin filas previas. `lopdp_app` lee, inserta y
actualiza (la decisión del DPO cambia `estado`); no borra. Un CHECK exige que una propuesta decidida lleve quién,
cuándo y una nota de al menos 10 caracteres, y que `sin_base_normativa` y la propuesta vacía vayan juntas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm03_analisis_impacto"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"
branch_labels: Union[str, Sequence[str], None] = ("inteligencia_normativa",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE normativa_analisis_impacto (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
            resolucion_id UUID NOT NULL REFERENCES normativa_resoluciones(id),
            modelo VARCHAR(40) NOT NULL CHECK (modelo = 'gemini-2.5-pro'),
            corpus_sha256 VARCHAR(64) NOT NULL CHECK (corpus_sha256 ~ '^[0-9a-f]{64}$'),
            propuesta JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(propuesta) = 'array'),
            sin_base_normativa BOOLEAN NOT NULL DEFAULT FALSE,
            estado VARCHAR(12) NOT NULL DEFAULT 'propuesta' CHECK (estado IN ('propuesta', 'aceptada', 'rechazada')),
            solicitada_por VARCHAR NOT NULL,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            decidida_por VARCHAR,
            decidida_en TIMESTAMPTZ,
            nota TEXT,
            CONSTRAINT ck_normativa_impacto_decision CHECK (
                (estado = 'propuesta' AND decidida_por IS NULL AND decidida_en IS NULL)
                OR (estado <> 'propuesta' AND decidida_por IS NOT NULL AND decidida_en IS NOT NULL
                    AND nota IS NOT NULL AND length(btrim(nota)) >= 10)
            ),
            CONSTRAINT ck_normativa_impacto_sin_base CHECK (
                (sin_base_normativa AND jsonb_array_length(propuesta) = 0)
                OR (NOT sin_base_normativa AND jsonb_array_length(propuesta) > 0)
            )
        );
        CREATE INDEX ix_normativa_impacto_tenant_resolucion
            ON normativa_analisis_impacto (tenant_id, resolucion_id, creada_en DESC);
        ALTER TABLE normativa_analisis_impacto ENABLE ROW LEVEL SECURITY;
        ALTER TABLE normativa_analisis_impacto FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_normativa_impacto ON normativa_analisis_impacto
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON normativa_analisis_impacto FROM lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON normativa_analisis_impacto TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS normativa_analisis_impacto")
