# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤inteligencia-normativa ¤transcripcion-normativa
"""NORM-06 · transcripciones de originales escaneados (una por sha256, inmutable) y origen del texto del análisis.

Revision ID: norm06_transcripciones
Revises: norm05_revision_sin_rol_mon (cabeza de la sala «inteligencia_normativa»)

Contrato: governance/especificaciones/NORM-06.md §1. `lopdp_app` lee e inserta; no actualiza ni borra.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm06_transcripciones"
down_revision: Union[str, Sequence[str], None] = "norm05_revision_sin_rol_mon"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE normativa_transcripciones (
            archivo_sha256 VARCHAR(64) PRIMARY KEY CHECK (archivo_sha256 ~ '^[0-9a-f]{64}$'),
            texto TEXT NOT NULL CHECK (length(texto) > 0),
            paginas INTEGER NOT NULL,
            caracteres INTEGER NOT NULL,
            modelo_solicitado VARCHAR(40) NOT NULL,
            modelo_version VARCHAR(80) NOT NULL,
            prompt_id VARCHAR(80) NOT NULL,
            prompt_version INTEGER NOT NULL,
            creada_en TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        REVOKE ALL ON normativa_transcripciones FROM lopdp_app;
        GRANT SELECT, INSERT ON normativa_transcripciones TO lopdp_app;
        ALTER TABLE normativa_analisis_impacto
            ADD COLUMN origen_texto VARCHAR(14) NOT NULL DEFAULT 'capa_texto'
            CONSTRAINT ck_normativa_impacto_origen_texto CHECK (origen_texto IN ('capa_texto', 'transcripcion'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE normativa_analisis_impacto DROP COLUMN origen_texto;
        DROP TABLE normativa_transcripciones;
        """
    )
