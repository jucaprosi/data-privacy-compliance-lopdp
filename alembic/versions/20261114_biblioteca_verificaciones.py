# ¤adpa ¤rbac-tenant
"""BIB-303: evidencias y verificaciones de cierre, solo-anexar y aisladas por organización."""
from alembic import op

revision = "20261114_bib_verificaciones"
down_revision = "20261113_bib_enlaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_evidencias (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            accion_id varchar NOT NULL REFERENCES roadmap_tasks(id) ON DELETE RESTRICT,
            titulo varchar(200) NOT NULL,
            version varchar(40) NOT NULL,
            sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            clasificacion varchar(20) NOT NULL
                CHECK (clasificacion IN ('publica','interna','confidencial','restringida')),
            permisos text[] NOT NULL CHECK (cardinality(permisos) >= 1),
            fecha date NOT NULL,
            control_ref varchar(64),
            documento_id varchar(36) REFERENCES biblioteca_documentos(id) ON DELETE RESTRICT,
            documento_revision integer CHECK (documento_revision >= 1),
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_bib_evidencia_revision CHECK ((documento_id IS NULL) = (documento_revision IS NULL))
        );
        CREATE INDEX ix_bib_evidencias_accion ON biblioteca_evidencias(tenant_id,accion_id);
        CREATE TABLE biblioteca_verificaciones (
            id varchar(36) PRIMARY KEY,
            secuencia bigint GENERATED ALWAYS AS IDENTITY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            accion_id varchar NOT NULL REFERENCES roadmap_tasks(id) ON DELETE RESTRICT,
            evidencia_id varchar(36) NOT NULL REFERENCES biblioteca_evidencias(id) ON DELETE RESTRICT,
            criterio text NOT NULL CHECK (length(criterio) >= 5),
            evidencia_legible boolean NOT NULL,
            resultado varchar(12) NOT NULL CHECK (resultado IN ('conforme','no_conforme')),
            eficacia_requerida boolean NOT NULL DEFAULT false,
            eficacia_conforme boolean,
            revisor varchar NOT NULL REFERENCES users(id),
            fecha date NOT NULL,
            observaciones text,
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_bib_verif_conforme_legible CHECK (resultado <> 'conforme' OR evidencia_legible),
            CONSTRAINT ck_bib_verif_conforme_eficaz
                CHECK (resultado <> 'conforme' OR NOT eficacia_requerida OR eficacia_conforme IS TRUE)
        );
        CREATE INDEX ix_bib_verificaciones_accion ON biblioteca_verificaciones(tenant_id,accion_id,creado_en);
        CREATE FUNCTION biblioteca_evidencia_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.roadmap_tasks t
                           WHERE t.id=NEW.accion_id AND t.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_VERIF_ACCION_AJENA' USING ERRCODE='23514';
            END IF;
            IF NEW.documento_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM public.biblioteca_documentos_historial h
                WHERE h.documento_id=NEW.documento_id AND h.revision=NEW.documento_revision
                  AND h.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_EVIDENCIA_REVISION_INCOMPLETA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_evidencia_validar BEFORE INSERT ON biblioteca_evidencias
            FOR EACH ROW EXECUTE FUNCTION biblioteca_evidencia_validar();
        CREATE FUNCTION biblioteca_verificacion_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_evidencias e
                           WHERE e.id=NEW.evidencia_id AND e.accion_id=NEW.accion_id
                             AND e.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_EVIDENCIA_NO_ENCONTRADA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_verificacion_validar BEFORE INSERT ON biblioteca_verificaciones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_verificacion_validar();
        ALTER TABLE biblioteca_evidencias ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_evidencias FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_evidencias ON biblioteca_evidencias
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        ALTER TABLE biblioteca_verificaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_verificaciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_verificaciones ON biblioteca_verificaciones
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_evidencias, biblioteca_verificaciones FROM lopdp_app;
        GRANT SELECT,INSERT ON biblioteca_evidencias, biblioteca_verificaciones TO lopdp_app;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_evidencias) THEN
                RAISE EXCEPTION 'BIB-303: hay evidencias o verificaciones; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_verificaciones;
        DROP TABLE biblioteca_evidencias;
        DROP FUNCTION biblioteca_verificacion_validar();
        DROP FUNCTION biblioteca_evidencia_validar();
    """)
