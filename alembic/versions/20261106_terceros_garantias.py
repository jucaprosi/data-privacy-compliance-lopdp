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
down_revision: Union[str, Sequence[str], None] = "norm01_inteligencia_normativa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = "transferencias_terceros"

# Mecanismos de la LOPDP, arts. 56 a 60 (CITAS_LEGALES_VERIFICADAS.md, «Transferencias internacionales»).
TIPOS_GARANTIA = ("nivel_adecuado", "clausulas_tipo", "normas_corporativas", "autorizacion_spdp", "caso_excepcional")
CRITICIDADES = ("baja", "media", "alta")

COLUMNAS = (
    ("pais", "VARCHAR(2) NULL CHECK (pais ~ '^[A-Z]{2}$')"),
    ("contrato_sha256", "VARCHAR(64) NULL CHECK (contrato_sha256 ~ '^[0-9a-f]{64}$')"),
    ("contrato_vigente_hasta", "DATE NULL"),
    ("garantia_tipo", "VARCHAR(24) NULL CHECK (garantia_tipo IN (%s))" % ", ".join(f"'{t}'" for t in TIPOS_GARANTIA)),
    ("garantia_sha256", "VARCHAR(64) NULL CHECK (garantia_sha256 ~ '^[0-9a-f]{64}$')"),
    ("criticidad", "VARCHAR(8) NULL CHECK (criticidad IN (%s))" % ", ".join(f"'{c}'" for c in CRITICIDADES)),
    ("proxima_revision", "DATE NULL"),
)


def upgrade() -> None:
    for nombre, definicion in COLUMNAS:
        op.execute(f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS {nombre} {definicion}")


def downgrade() -> None:
    for nombre, _ in reversed(COLUMNAS):
        op.execute(f"ALTER TABLE {TABLA} DROP COLUMN IF EXISTS {nombre}")
