# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-207: trabajos de generación persistentes, idempotentes y recuperables.

Datos privados por organización: RLS ENABLE y FORCE por tenant_id. La petición es única por organización,
borrador, revisión del borrador y clave de idempotencia; cada generación pertenece a un solo trabajo. Un
disparador impide cambiar la identidad de la petición y exige que borrador y generación sean del mismo
tenant. `lopdp_app` lee, inserta y actualiza el estado; no borra.
"""
from alembic import op

revision = "20261117_bib_trabajos"
down_revision = "20261116_bib_generacion"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_trabajos (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            borrador_id varchar(36) NOT NULL REFERENCES biblioteca_borradores(id),
            revision_borrador integer NOT NULL CHECK (revision_borrador >= 1),
            clave varchar(80) NOT NULL CHECK (clave ~ '^[A-Za-z0-9_-]{8,80}$'),
            modo varchar(8) NOT NULL CHECK (modo IN ('borrador','revision')),
            formato varchar(4) NOT NULL CHECK (formato IN ('docx','xlsx')),
            estado varchar(9) NOT NULL DEFAULT 'pendiente'
                CHECK (estado IN ('pendiente','generando','listo','fallido')),
            intentos integer NOT NULL DEFAULT 0 CHECK (intentos >= 0),
            generacion_id varchar(36) UNIQUE REFERENCES biblioteca_generaciones(id),
            error_codigo varchar(64),
            error_detalle varchar(500),
            tomado_en timestamptz,
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_biblioteca_trabajos_peticion UNIQUE (tenant_id, borrador_id, revision_borrador, clave),
            CONSTRAINT ck_biblioteca_trabajos_listo CHECK ((estado='listo') = (generacion_id IS NOT NULL)),
            CONSTRAINT ck_biblioteca_trabajos_fallo CHECK ((estado='fallido') = (error_codigo IS NOT NULL)),
            CONSTRAINT ck_biblioteca_trabajos_tomado CHECK (estado <> 'generando' OR tomado_en IS NOT NULL)
        );
        CREATE INDEX ix_biblioteca_trabajos_borrador ON biblioteca_trabajos(tenant_id,borrador_id,creado_en);
        CREATE FUNCTION biblioteca_trabajos_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF TG_OP='UPDATE' AND (NEW.tenant_id, NEW.borrador_id, NEW.revision_borrador, NEW.clave, NEW.modo,
                                   NEW.formato, NEW.creado_por, NEW.creado_en)
                   IS DISTINCT FROM (OLD.tenant_id, OLD.borrador_id, OLD.revision_borrador, OLD.clave, OLD.modo,
                                     OLD.formato, OLD.creado_por, OLD.creado_en) THEN
                RAISE EXCEPTION 'BIB_TRABAJO_INMUTABLE' USING ERRCODE='23514';
            END IF;
            IF TG_OP='UPDATE' AND OLD.generacion_id IS NOT NULL THEN
                RAISE EXCEPTION 'BIB_TRABAJO_TERMINADO' USING ERRCODE='23514';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_borradores b
                           WHERE b.id=NEW.borrador_id AND b.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_TRABAJO_BORRADOR_AJENO' USING ERRCODE='23514';
            END IF;
            IF NEW.generacion_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM public.biblioteca_generaciones g WHERE g.id=NEW.generacion_id
                    AND g.tenant_id=NEW.tenant_id AND g.borrador_id=NEW.borrador_id) THEN
                RAISE EXCEPTION 'BIB_TRABAJO_GENERACION_AJENA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_trabajos_validar BEFORE INSERT OR UPDATE ON biblioteca_trabajos
            FOR EACH ROW EXECUTE FUNCTION biblioteca_trabajos_validar();
        ALTER TABLE biblioteca_trabajos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_trabajos FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_trabajos ON biblioteca_trabajos
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_trabajos FROM lopdp_app;
        GRANT SELECT,INSERT,UPDATE ON biblioteca_trabajos TO lopdp_app;
    """)


# ¤adpa
def downgrade() -> None:
    # Solo ramas de desarrollo: borra el historial de trabajos.
    op.execute("""
        DROP TABLE biblioteca_trabajos;
        DROP FUNCTION biblioteca_trabajos_validar();
    """)
