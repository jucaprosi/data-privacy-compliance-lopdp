"""DER-01 · identidad verificada, resultado y respuesta como evidencia en derechos_arco_solicitudes; derechos_modelos.

`¤evidencias` `¤rbac-tenant` `¤arbitro`

Contrato: governance/especificaciones/DER-01.md §1. Primera migración de la sala derechos_arco: cuelga de
BASE_COMUN con la etiqueta de su sala (governance/operaciones/FUSION_ALEMBIC.md §2).

- Columnas nuevas, todas NULL: una solicitud sin contestar no tiene identidad verificada ni respuesta.
  `evidencia_respuesta_hash` ya existe y no se toca.
- `ck_arco_contestada_con_evidencia` (`INV_ARCO_EVIDENCIA_E1`). La condición del hash va con `coalesce`: un CHECK
  que da NULL se acepta, y un hash NULL daría NULL en vez de falso; sin `coalesce` una CONTESTADA sin hash pasaría.
- **Guardia antes del CHECK.** Cuenta exactamente las filas que el CHECK rechazaría (con la misma condición) y, si
  hay alguna, aborta dando el recuento. Sin `UPDATE` silencioso: la corrección de esas filas la decide el
  propietario.
- `derechos_modelos`: por organización, RLS ENABLE y FORCE por `tenant_id`, `lopdp_app` con SELECT, INSERT y UPDATE.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "der01_derechos_respuestas"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"  # BASE_COMUN (alembic/salas.py)
branch_labels: Union[str, Sequence[str], None] = ("derechos_arco",)
depends_on: Union[str, Sequence[str], None] = None

TABLA = "derechos_arco_solicitudes"
RESTRICCION = "ck_arco_contestada_con_evidencia"

# Una sola expresión para el CHECK y para el recuento previo: lo que uno rechaza, el otro lo cuenta.
CONDICION = (
    "estado::text <> 'CONTESTADA' "
    "OR (coalesce(evidencia_respuesta_hash ~ '^[0-9a-f]{64}$', false) AND respondida_en IS NOT NULL)"
)

# ¤arbitro — sentencia literal, sin valores dinámicos (test_sin_sql_interpolado).
SQL_GUARDIA = f"""
DO $$
DECLARE
    sin_evidencia bigint;
BEGIN
    SELECT count(*) INTO sin_evidencia FROM {TABLA} WHERE NOT ({CONDICION});
    IF sin_evidencia > 0 THEN
        RAISE EXCEPTION 'DER-01: % solicitud(es) ARCO en CONTESTADA sin hash de evidencia válido o sin '
            'respondida_en. La migración no cambia nada: decide el propietario.', sin_evidencia;
    END IF;
END $$;
"""

SQL_COLUMNAS = (
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_verificada_en TIMESTAMPTZ NULL",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_metodo VARCHAR(16) NULL "
    "CONSTRAINT ck_arco_identidad_metodo CHECK (identidad_metodo IN ('documento', 'correo', 'presencial'))",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_verificada_por VARCHAR NULL",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS resultado VARCHAR(10) NULL "
    "CONSTRAINT ck_arco_resultado CHECK (resultado IN ('concedido', 'denegado', 'parcial'))",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS respondida_en TIMESTAMPTZ NULL",
)

SQL_CHECK = f"ALTER TABLE {TABLA} ADD CONSTRAINT {RESTRICCION} CHECK ({CONDICION})"

SQL_MODELOS = (
    "CREATE TABLE derechos_modelos ("
    "id VARCHAR PRIMARY KEY, "
    "tenant_id VARCHAR NOT NULL REFERENCES tenants(id), "
    "derecho VARCHAR(32) NOT NULL, "
    "resultado VARCHAR(10) NOT NULL CONSTRAINT ck_derechos_modelos_resultado "
    "CHECK (resultado IN ('concedido', 'denegado', 'parcial')), "
    "texto TEXT NOT NULL, "
    "version INTEGER NOT NULL DEFAULT 1)",
    "CREATE INDEX ix_derechos_modelos_tenant_derecho ON derechos_modelos (tenant_id, derecho, resultado)",
    "ALTER TABLE derechos_modelos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE derechos_modelos FORCE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_isolation_derechos_modelos ON derechos_modelos "
    "USING (tenant_id = current_setting('app.current_tenant_id', true)) "
    "WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))",
    "REVOKE ALL ON derechos_modelos FROM lopdp_app",
    "GRANT SELECT, INSERT, UPDATE ON derechos_modelos TO lopdp_app",
)


def upgrade() -> None:
    for sentencia in SQL_COLUMNAS:
        op.execute(sentencia)
    op.execute(SQL_GUARDIA)
    op.execute(SQL_CHECK)
    for sentencia in SQL_MODELOS:
        op.execute(sentencia)


SQL_DESCENDENTE = (
    "DROP TABLE IF EXISTS derechos_modelos",
    f"ALTER TABLE {TABLA} DROP CONSTRAINT IF EXISTS {RESTRICCION}",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS respondida_en",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS resultado",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_verificada_por",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_metodo",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_verificada_en",
)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
