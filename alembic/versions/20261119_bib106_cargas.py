# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-106: cargas de documentos externos del cliente, con análisis y cuarentena.

- `biblioteca_cargas`: una reserva por usuario y organización; el archivo (bytea, máximo 10 MiB) se
  guarda una sola vez y no se reemplaza. El servidor calcula el SHA-256 y el tamaño real; un
  disparador los vuelve a comprobar. RLS ENABLE y FORCE con USING y WITH CHECK por tenant_id.
- `estado_analisis` separa el análisis de malware de la revisión humana. Solo una carga `limpio`
  puede finalizarse; al finalizar, el documento entra en `biblioteca_documentos` con origen
  `subido` y estado `borrador`. Una revisión nueva es una fila nueva (único por documento y número).
- `documento_id` debe ser un documento subido del mismo tenant; `version_maestra_id`, una versión
  publicada del catálogo, o nulo (origen no vinculado).
- lopdp_app lee, inserta y solo actualiza las columnas del ciclo de la carga; nunca borra.
"""
from alembic import op

revision = "20261119_bib106_cargas"
down_revision = "20261118_merge_heads_cierre_dev"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_cargas (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            usuario_id varchar NOT NULL REFERENCES users(id),
            titulo text NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
            codigo varchar(40) NOT NULL,
            version_propia varchar(40) NOT NULL,
            version_maestra_id varchar REFERENCES biblioteca_versiones(id),
            formato varchar(4) NOT NULL CHECK (formato IN ('DOCX','XLSX')),
            nombre_archivo varchar(160) NOT NULL,
            tamano_declarado integer NOT NULL CHECK (tamano_declarado BETWEEN 1 AND 10485760),
            archivo bytea CHECK (octet_length(archivo) BETWEEN 1 AND 10485760),
            sha256 varchar(64) CHECK (sha256 ~ '^[a-f0-9]{64}$'),
            tamano_bytes integer,
            estado_analisis varchar NOT NULL DEFAULT 'sin_archivo'
                CHECK (estado_analisis IN ('sin_archivo','pendiente','limpio','infectado','error','rechazado')),
            motivo text,
            documento_id varchar(36) REFERENCES biblioteca_documentos(id),
            revision_externa integer CHECK (revision_externa >= 1),
            finalizada_en timestamptz,
            expira_en timestamptz NOT NULL,
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ux_bib_cargas_revision UNIQUE (documento_id, revision_externa),
            CONSTRAINT bib_cargas_archivo CHECK (
                estado_analisis IN ('sin_archivo','rechazado')
                OR (archivo IS NOT NULL AND sha256 IS NOT NULL AND tamano_bytes IS NOT NULL)),
            CONSTRAINT bib_cargas_finalizada CHECK (
                finalizada_en IS NULL
                OR (estado_analisis = 'limpio' AND documento_id IS NOT NULL AND revision_externa IS NOT NULL))
        );
        CREATE INDEX ix_bib_cargas_tenant_documento ON biblioteca_cargas(tenant_id, documento_id);
    """)
    op.execute("""
        CREATE FUNCTION biblioteca_carga_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NEW.archivo IS NOT NULL AND (NEW.sha256 IS DISTINCT FROM encode(sha256(NEW.archivo),'hex')
                                            OR NEW.tamano_bytes IS DISTINCT FROM octet_length(NEW.archivo)) THEN
                RAISE EXCEPTION 'BIB_CARGA_INTEGRIDAD' USING ERRCODE='23514';
            END IF;
            IF TG_OP = 'UPDATE' THEN
                IF OLD.archivo IS NOT NULL AND NEW.archivo IS DISTINCT FROM OLD.archivo THEN
                    RAISE EXCEPTION 'BIB_CARGA_INMUTABLE' USING ERRCODE='23514';
                END IF;
                IF OLD.finalizada_en IS NOT NULL THEN
                    RAISE EXCEPTION 'BIB_CARGA_INMUTABLE' USING ERRCODE='23514';
                END IF;
            END IF;
            IF NEW.documento_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM public.biblioteca_documentos d
                WHERE d.id = NEW.documento_id AND d.tenant_id = NEW.tenant_id AND d.origen = 'subido') THEN
                RAISE EXCEPTION 'BIB_CARGA_DOCUMENTO_AJENO' USING ERRCODE='23514';
            END IF;
            IF NEW.version_maestra_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM public.biblioteca_versiones v
                WHERE v.id = NEW.version_maestra_id AND v.estado = 'publicada') THEN
                RAISE EXCEPTION 'BIB_CARGA_VERSION_MAESTRA_INVALIDA' USING ERRCODE='23514';
            END IF;
            NEW.actualizado_en := now();
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_carga_validar BEFORE INSERT OR UPDATE ON biblioteca_cargas
            FOR EACH ROW EXECUTE FUNCTION biblioteca_carga_validar();
    """)
    op.execute("ALTER TABLE biblioteca_cargas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_cargas FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_cargas ON biblioteca_cargas "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute("REVOKE ALL ON biblioteca_cargas FROM lopdp_app")
    op.execute("GRANT SELECT, INSERT ON biblioteca_cargas TO lopdp_app")
    op.execute("GRANT UPDATE (archivo, sha256, tamano_bytes, estado_analisis, motivo, documento_id, "
               "revision_externa, finalizada_en, actualizado_en) ON biblioteca_cargas TO lopdp_app")


def downgrade() -> None:
    # Solo ramas de desarrollo: se niega si ya hay cargas, para no perder archivos de las organizaciones.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_cargas) THEN
                RAISE EXCEPTION 'BIB-106: hay cargas de organizaciones; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_cargas;
        DROP FUNCTION biblioteca_carga_validar();
    """)
