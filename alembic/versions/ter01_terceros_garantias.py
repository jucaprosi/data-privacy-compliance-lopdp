# ¤¤backend-developer
"""TER-01 · contrato, garantía y revisión de cada tercero en transferencias_terceros. ¤hallazgos ¤evidencias ¤transferencias

Contrato: governance/especificaciones/TER-01.md §1, con las decisiones del Arquitecto ADPA (2026-11-13):

- Sin tabla nueva y sin tocar la columna `rol` existente (ENCARGADO, SUBENCARGADO, DESTINATARIO).
- `pais` (ISO 3166-1 alfa-2) se añade aparte de `pais_destino`, que es texto libre y no sirve para la regla R2.
- Todas las columnas admiten NULL y no hay relleno: las filas existentes quedan «sin declarar».
- CHECK en `pais`, en las huellas, en `garantia_tipo` y en `criticidad`.
- La tabla ya tiene RLS forzada (20260420_01_terceros_rls) y `lopdp_app` ya tiene SELECT, INSERT y UPDATE.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ter01_terceros_garantias"
down_revision: Union[str, Sequence[str], None] = "reg01_paquetes_normativos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mecanismos de la LOPDP, arts. 56 a 60 (CITAS_LEGALES_VERIFICADAS.md, «Transferencias internacionales»).
# Sentencias literales: el árbitro test_sin_sql_interpolado prohíbe construir SQL con valores dinámicos.
SQL_ASCENDENTE = (
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS pais VARCHAR(2) NULL CHECK (pais ~ '^[A-Z]{2}$')",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS contrato_sha256 VARCHAR(64) NULL "
    "CHECK (contrato_sha256 ~ '^[0-9a-f]{64}$')",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS contrato_vigente_hasta DATE NULL",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS garantia_tipo VARCHAR(24) NULL CHECK (garantia_tipo IN "
    "('nivel_adecuado', 'clausulas_tipo', 'normas_corporativas', 'autorizacion_spdp', 'caso_excepcional'))",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS garantia_sha256 VARCHAR(64) NULL "
    "CHECK (garantia_sha256 ~ '^[0-9a-f]{64}$')",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS criticidad VARCHAR(8) NULL "
    "CHECK (criticidad IN ('baja', 'media', 'alta'))",
    "ALTER TABLE transferencias_terceros ADD COLUMN IF NOT EXISTS proxima_revision DATE NULL",
)
SQL_DESCENDENTE = (
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS proxima_revision",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS criticidad",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS garantia_sha256",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS garantia_tipo",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS contrato_vigente_hasta",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS contrato_sha256",
    "ALTER TABLE transferencias_terceros DROP COLUMN IF EXISTS pais",
)


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)