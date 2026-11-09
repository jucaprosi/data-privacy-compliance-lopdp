"""DER-03 · derechos_arco_solicitudes: el tenant pasa a texto, como tenants.id (fase de expansión).

Revision ID: 20261108_derechos_tenant_texto
Revises: 20261108_bib_cap_propietario
Create Date: 2026-11-08

`¤seguridad-tenant` `¤rbac-tenant`

Expand/contract (GCP-07): esta migración solo añade; no cambia el tipo de `tenant_id` ni lo borra.
1. **Huérfanos primero.** Cuenta las filas cuyo `tenant_id` no existe en `tenants`. Si hay alguna, aborta
   con el número y no toca la tabla: son solicitudes de titulares con plazo legal, y qué hacer con ellas
   lo deciden el propietario y el DPO.
2. Columna nueva `tenant_id_texto VARCHAR`, copiada de `tenant_id::text`, con FK a `tenants(id)` creada
   `NOT VALID` y validada aparte, índice y NOT NULL.
3. `tenant_id` (uuid) deja de ser obligatorio: la revisión nueva ya no lo escribe. Un disparador sincroniza
   las dos columnas: copia `tenant_id::text` cuando la revisión anterior inserta solo la vieja, y copia
   `tenant_id_texto::uuid` cuando la nueva inserta un tenant con forma de uuid, para que la revisión
   anterior pueda volver a servir esas filas (ventana de reversión de código).
4. La política RLS se recrea sobre `tenant_id_texto`, sin cast, con USING y WITH CHECK; RLS sigue forzada.

La contracción (retirar `tenant_id` uuid y el disparador) va en una migración posterior con
`CONTRACCION = True`, cuando ninguna revisión en servicio use ya la columna vieja.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261108_derechos_tenant_texto"
down_revision: Union[str, None] = "20261108_bib_cap_propietario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = "derechos_arco_solicitudes"
POLITICA = "tenant_isolation_derechos_arco_solicitudes"

# ¤seguridad-tenant
SQL_HUERFANOS = f"""
DO $$
DECLARE
    huerfanas bigint;
BEGIN
    SELECT count(*) INTO huerfanas
    FROM {TABLA} s
    WHERE NOT EXISTS (SELECT 1 FROM tenants t WHERE t.id = s.tenant_id::text);
    IF huerfanas > 0 THEN
        RAISE EXCEPTION 'DER-03: % solicitud(es) ARCO con un tenant_id que no existe en tenants. '
            'La migración no borra ni reasigna ninguna: deciden el propietario y el DPO.', huerfanas;
    END IF;
END $$;
"""

FORMA_UUID = "'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"

# ¤seguridad-tenant
SQL_GUARDIA_DESCENDENTE = f"""
DO $$
DECLARE
    sin_uuid bigint;
BEGIN
    SELECT count(*) INTO sin_uuid
    FROM {TABLA}
    WHERE tenant_id IS NULL AND tenant_id_texto !~* {FORMA_UUID};
    IF sin_uuid > 0 THEN
        RAISE EXCEPTION 'DER-03: % solicitud(es) ARCO con un tenant de texto sin forma de uuid. '
            'El downgrade no puede devolverlas a la columna uuid y no cambia nada.', sin_uuid;
    END IF;
END $$;
"""

SQL_ASCENDENTE: tuple[str, ...] = (
    SQL_HUERFANOS,
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS tenant_id_texto VARCHAR NULL;",
    f"UPDATE {TABLA} SET tenant_id_texto = tenant_id::text WHERE tenant_id_texto IS NULL;",
    f"ALTER TABLE {TABLA} ALTER COLUMN tenant_id DROP NOT NULL;",
    f"""
    CREATE OR REPLACE FUNCTION derechos_arco_tenant_texto() RETURNS trigger AS $$
    BEGIN
        IF NEW.tenant_id_texto IS NULL AND NEW.tenant_id IS NOT NULL THEN
            NEW.tenant_id_texto := NEW.tenant_id::text;
        END IF;
        IF NEW.tenant_id IS NULL AND NEW.tenant_id_texto ~* {FORMA_UUID} THEN
            NEW.tenant_id := NEW.tenant_id_texto::uuid;
        END IF;
        RETURN NEW;
    END $$ LANGUAGE plpgsql;
    """,
    f"""
    CREATE TRIGGER trg_derechos_arco_tenant_texto
    BEFORE INSERT OR UPDATE ON {TABLA}
    FOR EACH ROW EXECUTE FUNCTION derechos_arco_tenant_texto();
    """,
    f"""
    ALTER TABLE {TABLA} ADD CONSTRAINT fk_derechos_arco_solicitudes_tenant
    FOREIGN KEY (tenant_id_texto) REFERENCES tenants(id) NOT VALID;
    """,
    f"ALTER TABLE {TABLA} VALIDATE CONSTRAINT fk_derechos_arco_solicitudes_tenant;",
    f"ALTER TABLE {TABLA} ALTER COLUMN tenant_id_texto SET NOT NULL;",
    f"CREATE INDEX IF NOT EXISTS ix_derechos_arco_solicitudes_tenant_id_texto ON {TABLA}(tenant_id_texto);",
    f"DROP POLICY IF EXISTS {POLITICA} ON {TABLA};",
    f"""
    CREATE POLICY {POLITICA} ON {TABLA}
    USING (tenant_id_texto = current_setting('app.current_tenant_id', true))
    WITH CHECK (tenant_id_texto = current_setting('app.current_tenant_id', true));
    """,
    f"ALTER TABLE {TABLA} ENABLE ROW LEVEL SECURITY;",
    f"ALTER TABLE {TABLA} FORCE ROW LEVEL SECURITY;",
)

SQL_DESCENDENTE: tuple[str, ...] = (
    SQL_GUARDIA_DESCENDENTE,
    f"DROP POLICY IF EXISTS {POLITICA} ON {TABLA};",
    f"""
    CREATE POLICY {POLITICA} ON {TABLA}
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));
    """,
    f"UPDATE {TABLA} SET tenant_id = tenant_id_texto::uuid WHERE tenant_id IS NULL;",
    f"ALTER TABLE {TABLA} ALTER COLUMN tenant_id SET NOT NULL;",
    f"DROP TRIGGER IF EXISTS trg_derechos_arco_tenant_texto ON {TABLA};",
    "DROP FUNCTION IF EXISTS derechos_arco_tenant_texto();",
    f"ALTER TABLE {TABLA} DROP COLUMN IF EXISTS tenant_id_texto;",
)


def upgrade() -> None:
    for sql in SQL_ASCENDENTE:
        op.execute(sql)


def downgrade() -> None:
    for sql in SQL_DESCENDENTE:
        op.execute(sql)
