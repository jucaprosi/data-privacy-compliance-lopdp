# ¤adpa ¤rbac-tenant
"""BIB-302: relación N:M entre revisiones documentales y acciones canónicas."""
from alembic import op

revision = "20261113_bib_enlaces"
down_revision = "20261113_bib_impactos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_revision_acciones (
            id varchar(240) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            documento_id varchar(36) NOT NULL REFERENCES biblioteca_documentos(id) ON DELETE CASCADE,
            documento_revision integer NOT NULL CHECK (documento_revision >= 1),
            accion_id varchar NOT NULL REFERENCES roadmap_tasks(id) ON DELETE CASCADE,
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_bib_revision_accion UNIQUE (tenant_id,documento_id,documento_revision,accion_id)
        );
        CREATE INDEX ix_bib_revision_acciones_documento
            ON biblioteca_revision_acciones(tenant_id,documento_id,documento_revision);
        CREATE INDEX ix_bib_revision_acciones_accion
            ON biblioteca_revision_acciones(tenant_id,accion_id);
        CREATE FUNCTION biblioteca_enlace_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_documentos_historial h
                           WHERE h.documento_id=NEW.documento_id AND h.revision=NEW.documento_revision
                             AND h.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_ENLACE_REVISION_INVALIDA' USING ERRCODE='23514';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM public.roadmap_tasks t
                           WHERE t.id=NEW.accion_id AND t.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_ENLACE_ACCION_AJENA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_enlace_validar BEFORE INSERT OR UPDATE ON biblioteca_revision_acciones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_enlace_validar();
        ALTER TABLE biblioteca_revision_acciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_revision_acciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_revision_acciones ON biblioteca_revision_acciones
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_revision_acciones FROM lopdp_app;
        GRANT SELECT,INSERT,DELETE ON biblioteca_revision_acciones TO lopdp_app;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_revision_acciones) THEN
                RAISE EXCEPTION 'BIB-302: hay enlaces documentales; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_revision_acciones;
        DROP FUNCTION biblioteca_enlace_validar();
    """)
