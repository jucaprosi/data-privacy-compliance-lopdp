# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-107: documentos de cada organización e historial básico inmutable.

- `biblioteca_documentos`: una fila por documento y organización, con RLS ENABLE y FORCE (USING y
  WITH CHECK por tenant_id). lopdp_app lee, inserta y solo actualiza las columnas del contenido: el
  estado, la aprobación y la identidad del documento los cambia BIB-301 con su propia migración.
- `biblioteca_documentos_historial`: una fila por revisión del documento; append-only (lopdp_app solo
  lee e inserta y un disparador rechaza UPDATE y DELETE incluso del propietario).
- `tarea_hoja_ruta_id` es opcional y un disparador exige que la tarea sea del mismo tenant.
"""
from alembic import op

revision = "20261109_bib_documentos"
down_revision = "20261102_merge_firma_main"
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_documentos (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            codigo varchar NOT NULL,
            nombre text NOT NULL,
            origen varchar NOT NULL CHECK (origen IN ('plantilla','propio','subido')),
            plantilla_id varchar REFERENCES biblioteca_versiones(id),
            plantilla_version varchar,
            contenido_markdown text NOT NULL CHECK (length(contenido_markdown) <= 200000),
            editado boolean NOT NULL DEFAULT false,
            estado varchar NOT NULL DEFAULT 'borrador'
                CHECK (estado IN ('borrador','en_revision','aprobado','vencido')),
            aprobado_por varchar REFERENCES users(id),
            aprobado_en timestamptz,
            sha256 varchar(64) NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
            fecha_emision date NOT NULL,
            proxima_revision date NOT NULL,
            tarea_hoja_ruta_id varchar REFERENCES roadmap_tasks(id),
            revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT bib_doc_origen_plantilla CHECK (
                origen <> 'plantilla' OR (plantilla_id IS NOT NULL AND plantilla_version IS NOT NULL)),
            CONSTRAINT bib_doc_aprobacion CHECK (
                estado <> 'aprobado' OR (aprobado_por IS NOT NULL AND aprobado_en IS NOT NULL))
        );
        CREATE INDEX ix_bib_documentos_tenant_estado ON biblioteca_documentos(tenant_id, estado);
        CREATE INDEX ix_bib_documentos_tenant_codigo ON biblioteca_documentos(tenant_id, codigo);
        CREATE TABLE biblioteca_documentos_historial (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            documento_id varchar(36) NOT NULL REFERENCES biblioteca_documentos(id),
            revision integer NOT NULL CHECK (revision >= 1),
            accion varchar NOT NULL CHECK (accion IN ('creado','editado')),
            contenido_markdown text NOT NULL,
            sha256 varchar(64) NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
            actor_id varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ux_bib_doc_historial_revision UNIQUE (documento_id, revision)
        );
        CREATE INDEX ix_bib_doc_historial_tenant ON biblioteca_documentos_historial(tenant_id, documento_id);
    """)
    op.execute("""
        CREATE FUNCTION biblioteca_documento_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NEW.tarea_hoja_ruta_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM public.roadmap_tasks t
                WHERE t.id = NEW.tarea_hoja_ruta_id AND t.tenant_id = NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_TAREA_AJENA' USING ERRCODE='23514';
            END IF;
            IF NEW.sha256 <> encode(sha256(convert_to(NEW.contenido_markdown,'UTF8')),'hex') THEN
                RAISE EXCEPTION 'BIB_INTEGRIDAD_INVALIDA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_documento_validar BEFORE INSERT OR UPDATE ON biblioteca_documentos
            FOR EACH ROW EXECUTE FUNCTION biblioteca_documento_validar();
        CREATE FUNCTION biblioteca_documento_historial_inmutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            RAISE EXCEPTION 'BIB_HISTORIAL_INMUTABLE' USING ERRCODE='23514';
        END $$;
        CREATE TRIGGER biblioteca_documento_historial_inmutable
            BEFORE UPDATE OR DELETE ON biblioteca_documentos_historial
            FOR EACH ROW EXECUTE FUNCTION biblioteca_documento_historial_inmutable();
    """)
    op.execute("ALTER TABLE biblioteca_documentos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_documentos FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_documentos ON biblioteca_documentos "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON biblioteca_documentos FROM lopdp_app")
    op.execute("ALTER TABLE biblioteca_documentos_historial ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_documentos_historial FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_documentos_historial ON biblioteca_documentos_historial "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON biblioteca_documentos_historial FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON biblioteca_documentos, biblioteca_documentos_historial TO lopdp_app")
    op.execute("GRANT UPDATE (contenido_markdown, editado, sha256, revision, actualizado_en) "
               "ON biblioteca_documentos TO lopdp_app")


def downgrade() -> None:
    # Solo ramas de desarrollo: se niega si ya hay documentos, para no perder el trabajo de las organizaciones.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_documentos) THEN
                RAISE EXCEPTION 'BIB-107: hay documentos de organizaciones; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_documentos_historial;
        DROP TABLE biblioteca_documentos;
        DROP FUNCTION biblioteca_documento_historial_inmutable();
        DROP FUNCTION biblioteca_documento_validar();
    """)
