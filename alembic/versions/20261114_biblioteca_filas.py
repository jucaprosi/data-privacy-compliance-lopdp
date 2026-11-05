# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-203: filas de las tablas de captura (inventarios, RAT y LEG) dentro de un borrador estructurado.

Datos privados por organización: RLS ENABLE y FORCE por tenant_id. El ID técnico lo pone el servidor; el
código visible es único por organización y tabla. El borrador y el tratamiento referidos deben ser de la
misma organización (lo comprueba el servicio y, de respaldo, el disparador). `lopdp_app` lee, inserta y
solo actualiza las columnas editables; sin DELETE. El plan (PLA) no se guarda aquí: se lee del canónico.
"""
from alembic import op

revision = "20261114_biblioteca_filas"
down_revision = "20261113_bib_enlaces"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_filas (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            borrador_id varchar(36) NOT NULL REFERENCES biblioteca_borradores(id),
            tabla varchar(3) NOT NULL CHECK (tabla IN ('INV','RAT','LEG')),
            codigo varchar(40) NOT NULL CHECK (codigo ~ '^[A-Za-z0-9._-]{1,40}$'),
            datos jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(datos)='object'),
            tratamiento_id varchar REFERENCES rat_actividades(id),
            revision integer NOT NULL DEFAULT 1 CHECK (revision>=1),
            creado_por varchar NOT NULL REFERENCES users(id),
            actualizado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_biblioteca_filas_codigo UNIQUE (tenant_id,tabla,codigo)
        );
        CREATE INDEX ix_biblioteca_filas_borrador ON biblioteca_filas(tenant_id,borrador_id,tabla);
        CREATE FUNCTION biblioteca_filas_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_borradores b
                           WHERE b.id=NEW.borrador_id AND b.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_FILA_BORRADOR_AJENO' USING ERRCODE='23514';
            END IF;
            IF NEW.tratamiento_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM public.rat_actividades r
                    WHERE r.id=NEW.tratamiento_id AND r.tenant_id=NEW.tenant_id AND r.deleted_at IS NULL) THEN
                RAISE EXCEPTION 'BIB_FILA_TRATAMIENTO_AJENO' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_filas_validar BEFORE INSERT OR UPDATE ON biblioteca_filas
            FOR EACH ROW EXECUTE FUNCTION biblioteca_filas_validar();
        ALTER TABLE biblioteca_filas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_filas FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_filas ON biblioteca_filas
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_filas FROM lopdp_app;
        GRANT SELECT,INSERT ON biblioteca_filas TO lopdp_app;
        GRANT UPDATE (datos,tratamiento_id,revision,actualizado_por,actualizado_en) ON biblioteca_filas TO lopdp_app;
    """)


# ¤adpa
def downgrade() -> None:
    # Solo ramas de desarrollo: borra las filas capturadas.
    op.execute("""
        DROP TABLE biblioteca_filas;
        DROP FUNCTION biblioteca_filas_validar();
    """)
