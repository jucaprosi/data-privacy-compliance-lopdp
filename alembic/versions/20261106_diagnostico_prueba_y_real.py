# ¤diagnostico ¤dpo-independencia
"""Diagnóstico de prueba y diagnóstico real (DIAG-11, invariantes 58 y 59 de EVYDENTIA).

Cada organización sella el diagnóstico dos veces como máximo: la secuencia 1 es el de prueba y la 2,
el real, que es la línea base.

- Columna `tipo` (`prueba` o `real`) en `diagnostico_resultados`, una fila de cada tipo por organización
  (`uq_diagnostico_resultados_tipo`) y coherente con la secuencia (`ck_diagnostico_resultados_tipo`).
- Un disparador fija `tipo` a partir de `secuencia` cuando la inserción no lo trae (revisión anterior
  durante el despliegue progresivo) y rechaza una tercera secuencia: el límite vale también en la base.
- Filas existentes: secuencia 1 → `prueba`, 2 → `real`. Si una organización tiene más de dos, la
  migración se detiene y las enumera para que decida el propietario.
- La tabla conserva RLS (ENABLE y FORCE) y los permisos de `lopdp_app` (SELECT, INSERT): no se añade
  UPDATE ni DELETE. El relleno quita FORCE solo dentro de esta transacción y lo restituye.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261106_diag_prueba_y_real"
down_revision: Union[str, Sequence[str], None] = "20260420_01_terceros_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SQL_ASCENDENTE = [
    "ALTER TABLE diagnostico_resultados NO FORCE ROW LEVEL SECURITY",
    """
    DO $$
    DECLARE excedidas TEXT;
    BEGIN
        SELECT string_agg(tenant_id || ' (' || n || ')', ', ') INTO excedidas
        FROM (SELECT tenant_id, count(*) AS n FROM diagnostico_resultados GROUP BY tenant_id HAVING count(*) > 2) t;
        IF excedidas IS NOT NULL THEN
            RAISE EXCEPTION 'DIAG-11: organizaciones con más de dos diagnósticos sellados: %. Decide el propietario antes de migrar.', excedidas;
        END IF;
    END $$
    """,
    "ALTER TABLE diagnostico_resultados ADD COLUMN tipo VARCHAR(10)",
    "UPDATE diagnostico_resultados SET tipo = CASE secuencia WHEN 1 THEN 'prueba' ELSE 'real' END",
    "ALTER TABLE diagnostico_resultados ALTER COLUMN tipo SET NOT NULL",
    """
    ALTER TABLE diagnostico_resultados ADD CONSTRAINT ck_diagnostico_resultados_tipo
        CHECK ((tipo = 'prueba' AND secuencia = 1) OR (tipo = 'real' AND secuencia = 2))
    """,
    "ALTER TABLE diagnostico_resultados ADD CONSTRAINT uq_diagnostico_resultados_tipo UNIQUE (tenant_id, tipo)",
    """
    CREATE OR REPLACE FUNCTION diagnostico_resultados_tipo() RETURNS trigger AS $$
    BEGIN
        IF NEW.secuencia > 2 THEN
            RAISE EXCEPTION 'DIAG_SELLOS_AGOTADOS: la organización % ya selló el diagnóstico de prueba y el real', NEW.tenant_id;
        END IF;
        IF NEW.tipo IS NULL THEN
            NEW.tipo := CASE NEW.secuencia WHEN 1 THEN 'prueba' ELSE 'real' END;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """,
    """
    CREATE TRIGGER trg_diagnostico_resultados_tipo BEFORE INSERT ON diagnostico_resultados
        FOR EACH ROW EXECUTE FUNCTION diagnostico_resultados_tipo()
    """,
    "ALTER TABLE diagnostico_resultados FORCE ROW LEVEL SECURITY",
]

SQL_DESCENDENTE = [
    "DROP TRIGGER IF EXISTS trg_diagnostico_resultados_tipo ON diagnostico_resultados",
    "DROP FUNCTION IF EXISTS diagnostico_resultados_tipo()",
    "ALTER TABLE diagnostico_resultados DROP CONSTRAINT IF EXISTS uq_diagnostico_resultados_tipo",
    "ALTER TABLE diagnostico_resultados DROP CONSTRAINT IF EXISTS ck_diagnostico_resultados_tipo",
    "ALTER TABLE diagnostico_resultados DROP COLUMN IF EXISTS tipo",
]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
