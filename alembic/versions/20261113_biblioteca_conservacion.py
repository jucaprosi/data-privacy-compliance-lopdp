# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-306: cronología append-only y conservación por documento, aisladas por tenant."""
from alembic import op

revision = "20261113_bib_conservacion"
down_revision = "20261112_merge_heads_tanda35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_conservacion (
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            documento_id varchar(36) PRIMARY KEY REFERENCES biblioteca_documentos(id),
            retenido_hasta timestamptz,
            bloqueo_legal boolean NOT NULL DEFAULT false,
            motivo text CHECK (motivo IS NULL OR length(trim(motivo)) > 0),
            politica_id varchar(120),
            politica_aprobada boolean NOT NULL DEFAULT false,
            actualizado_por varchar REFERENCES users(id),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CHECK (NOT politica_aprobada OR politica_id IS NOT NULL)
        );
        CREATE TABLE biblioteca_eventos_documento (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            documento_id varchar(36) NOT NULL REFERENCES biblioteca_documentos(id),
            tipo varchar NOT NULL CHECK (tipo IN
                ('descarga','generacion','aprobacion','notificacion','reapertura','restauracion')),
            revision integer CHECK (revision IS NULL OR revision >= 1),
            actor_id varchar NOT NULL REFERENCES users(id),
            detalle jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(detalle)='object'),
            creado_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_bib_eventos_documento ON biblioteca_eventos_documento(tenant_id,documento_id,creado_en);
    """)
    op.execute("ALTER TABLE biblioteca_conservacion ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_conservacion FORCE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON biblioteca_conservacion FROM lopdp_app")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_conservacion ON biblioteca_conservacion "
        "USING (tenant_id::text=current_setting('app.current_tenant_id',true)) "
        "WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))"
    )
    op.execute("ALTER TABLE biblioteca_eventos_documento ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_eventos_documento FORCE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON biblioteca_eventos_documento FROM lopdp_app")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_eventos_documento ON biblioteca_eventos_documento "
        "USING (tenant_id::text=current_setting('app.current_tenant_id',true)) "
        "WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON biblioteca_conservacion TO lopdp_app")
    op.execute("GRANT SELECT, INSERT ON biblioteca_eventos_documento TO lopdp_app")
    op.execute("""
        CREATE FUNCTION biblioteca_evento_inmutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN RAISE EXCEPTION 'BIB_HISTORIAL_INMUTABLE' USING ERRCODE='23514'; END $$;
        CREATE TRIGGER biblioteca_evento_inmutable BEFORE UPDATE OR DELETE ON biblioteca_eventos_documento
            FOR EACH ROW EXECUTE FUNCTION biblioteca_evento_inmutable();
        CREATE FUNCTION biblioteca_conservacion_mismo_tenant() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_documentos d
                           WHERE d.id=NEW.documento_id AND d.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_DOCUMENTO_AJENO' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_conservacion_mismo_tenant BEFORE INSERT OR UPDATE ON biblioteca_conservacion
            FOR EACH ROW EXECUTE FUNCTION biblioteca_conservacion_mismo_tenant();
        CREATE TRIGGER biblioteca_evento_mismo_tenant BEFORE INSERT ON biblioteca_eventos_documento
            FOR EACH ROW EXECUTE FUNCTION biblioteca_conservacion_mismo_tenant();
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM biblioteca_eventos_documento)
               OR EXISTS (SELECT 1 FROM biblioteca_conservacion) THEN
                RAISE EXCEPTION 'BIB-306: existe historial o conservacion; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_eventos_documento;
        DROP TABLE biblioteca_conservacion;
        DROP FUNCTION biblioteca_evento_inmutable();
        DROP FUNCTION biblioteca_conservacion_mismo_tenant();
    """)
