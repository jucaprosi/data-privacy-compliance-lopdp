"""DER-04 · derechos_arco_solicitudes: contracción de DER-03 (retira tenant_id uuid y el disparador).

Revision ID: 20261109_der04_contraccion
Revises: norm01_inteligencia_normativa
Create Date: 2026-11-13

`¤seguridad-tenant` `¤arbitro`

Fase de contracción del expand/contract de GCP-07; DER-03 (20261108_derechos_tenant_texto) fue la
expansión. Se aplica solo cuando se cumplen los tres criterios de governance/tareas/DER-04.md
(código sin la columna vieja, ninguna revisión anterior en servicio y ventana de vuelta atrás cerrada).

1. `lock_timeout`: ALTER y DROP toman ACCESS EXCLUSIVE; si la tabla está ocupada, aborta en vez de colgar
   la aplicación, y se reintenta.
2. **Guardia antes de cualquier DDL.** Cuenta las filas con `tenant_id_texto` NULL o sin fila en
   `tenants`, y las políticas de la tabla que nombran la columna vieja y no son la conocida de
   001_initial_schema. Si hay alguna, aborta solo con números: ninguna cédula ni ningún nombre.
3. NOT NULL de `tenant_id_texto`; retira la política vieja de 001 (por nombre), el disparador, su función y la
   columna `tenant_id` uuid, en ese orden. Nunca con CASCADE: una dependencia desconocida hace fallar el DROP.
4. Comprueba que la política vigente y RLS forzada siguen sobre `tenant_id_texto`.

`downgrade()` no existe: un uuid no se reconstruye a partir de un tenant de texto. Antes de aplicar en
producción, respaldo o punto de restauración (governance/apoyo/BRIEF_PROPIETARIO_DER04.md).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261109_der04_contraccion"  # alembic_version es VARCHAR(32)
down_revision: Union[str, None] = "norm01_inteligencia_normativa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ¤arbitro — scripts/verificar_migracion_compatible.py solo acepta los DROP con esta marca.
CONTRACCION = True

TABLA = "derechos_arco_solicitudes"
POLITICA = "tenant_isolation_derechos_arco_solicitudes"
POLITICA_VIEJA_001 = "tenant_isolation_policy"
LOCK_TIMEOUT = "5s"

# Palabra completa: `tenant_id_texto` no casa (el guion bajo es carácter de palabra).
_NOMBRA_VIEJA = r"'\mtenant_id\M'"

# ¤seguridad-tenant
SQL_GUARDIA = f"""
DO $$
DECLARE
    sin_tenant bigint;
    politicas_ajenas bigint;
BEGIN
    SELECT count(*) INTO sin_tenant
    FROM {TABLA} s
    WHERE s.tenant_id_texto IS NULL
       OR NOT EXISTS (SELECT 1 FROM tenants t WHERE t.id = s.tenant_id_texto);
    IF sin_tenant > 0 THEN
        RAISE EXCEPTION 'DER-04: % solicitud(es) ARCO sin tenant válido en tenant_id_texto. '
            'La contracción no cambia nada: deciden el propietario y el DPO.', sin_tenant;
    END IF;
    SELECT count(*) INTO politicas_ajenas
    FROM pg_policies
    WHERE schemaname = current_schema() AND tablename = '{TABLA}'
      AND policyname <> '{POLITICA_VIEJA_001}'
      AND (coalesce(qual, '') ~ {_NOMBRA_VIEJA} OR coalesce(with_check, '') ~ {_NOMBRA_VIEJA});
    IF politicas_ajenas > 0 THEN
        RAISE EXCEPTION 'DER-04: % política(s) desconocida(s) dependen de la columna tenant_id. '
            'La contracción no cambia nada.', politicas_ajenas;
    END IF;
END $$;
"""

# ¤seguridad-tenant
SQL_COMPROBACION_RLS = f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = current_schema() AND tablename = '{TABLA}' AND policyname = '{POLITICA}'
          AND qual ~ 'tenant_id_texto' AND with_check ~ 'tenant_id_texto'
    ) THEN
        RAISE EXCEPTION 'DER-04: la política % no está sobre tenant_id_texto.', '{POLITICA}';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_class
        WHERE oid = '{TABLA}'::regclass AND relrowsecurity AND relforcerowsecurity
    ) THEN
        RAISE EXCEPTION 'DER-04: RLS no está activa y forzada en %.', '{TABLA}';
    END IF;
END $$;
"""

# Literales en op.execute: así los lee scripts/verificar_migracion_compatible.py (AST), que solo los
# acepta por CONTRACCION = True. El orden es el de la ficha: guardia, NOT NULL, política vieja, disparador,
# función, columna; nunca CASCADE.
def upgrade() -> None:
    op.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}';")
    op.execute(SQL_GUARDIA)
    op.execute("ALTER TABLE derechos_arco_solicitudes ALTER COLUMN tenant_id_texto SET NOT NULL;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON derechos_arco_solicitudes;")
    op.execute("DROP TRIGGER IF EXISTS trg_derechos_arco_tenant_texto ON derechos_arco_solicitudes;")
    op.execute("DROP FUNCTION IF EXISTS derechos_arco_tenant_texto();")
    op.execute("ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS tenant_id;")
    op.execute(SQL_COMPROBACION_RLS)


def downgrade() -> None:
    raise RuntimeError(
        "DER-04: contracción irreversible. Un uuid no se reconstruye a partir de un tenant de texto; "
        "se vuelve atrás restaurando el respaldo tomado antes de aplicarla."
    )
