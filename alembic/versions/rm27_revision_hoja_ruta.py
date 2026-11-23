# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap
"""RM-27: revisión humana antes de que la Hoja de Ruta valga, con cuatro ojos.

Añade `generado_por`, `revisado_por` y `revisado_en` a `roadmaps`, más dos restricciones CHECK:
- `ck_roadmaps_cuatro_ojos`: una hoja nueva activa tiene revisor distinto de quien la generó.
- `ck_roadmaps_con_autor`: creada `NOT VALID` para no tocar hojas anteriores; toda fila nueva o
  modificada en `generated` debe tener `generado_por`.

Sin backfill ni actualización de filas existentes. `lopdp_app` conserva sus permisos sobre `roadmaps`.
"""
from alembic import op

revision = "rm27_revision_hoja_ruta"
down_revision = "rm25b_evidencia_exigir"
branch_labels = None
depends_on = None

SQL_COLUMNAS = (
    "ALTER TABLE roadmaps ADD COLUMN generado_por VARCHAR NULL",
    "ALTER TABLE roadmaps ADD COLUMN revisado_por VARCHAR NULL",
    "ALTER TABLE roadmaps ADD COLUMN revisado_en TIMESTAMPTZ NULL",
)

SQL_RESTRICCIONES = (
    "ALTER TABLE roadmaps ADD CONSTRAINT ck_roadmaps_cuatro_ojos CHECK ("
    "status <> 'active' OR generado_por IS NULL "
    "OR (revisado_por IS NOT NULL AND revisado_por <> generado_por))",
    "ALTER TABLE roadmaps ADD CONSTRAINT ck_roadmaps_con_autor CHECK ("
    "status <> 'generated' OR generado_por IS NOT NULL) NOT VALID",
)

SQL_DESCENDENTE = (
    "ALTER TABLE roadmaps DROP CONSTRAINT IF EXISTS ck_roadmaps_con_autor",
    "ALTER TABLE roadmaps DROP CONSTRAINT IF EXISTS ck_roadmaps_cuatro_ojos",
    "ALTER TABLE roadmaps DROP COLUMN IF EXISTS revisado_en",
    "ALTER TABLE roadmaps DROP COLUMN IF EXISTS revisado_por",
    "ALTER TABLE roadmaps DROP COLUMN IF EXISTS generado_por",
)


def upgrade() -> None:
    for sentencia in SQL_COLUMNAS:
        op.execute(sentencia)
    for sentencia in SQL_RESTRICCIONES:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
