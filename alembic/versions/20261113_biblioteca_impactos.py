# ¤adpa ¤rbac-tenant
"""BIB-304: impactos editoriales, decisiones por organización y recepción de avisos."""
from alembic import op

revision = "20261113_bib_impactos"
down_revision = "20261112_merge_heads_tanda35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_impactos (
            id varchar(36) PRIMARY KEY,
            version_id varchar(36) NOT NULL UNIQUE REFERENCES biblioteca_versiones(id),
            version_anterior_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            codigo varchar(40) NOT NULL REFERENCES biblioteca_catalogo(codigo),
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE biblioteca_impactos_organizacion (
            id varchar(36) PRIMARY KEY,
            impacto_id varchar(36) NOT NULL REFERENCES biblioteca_impactos(id),
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            decision varchar NOT NULL DEFAULT 'pendiente'
                CHECK (decision IN ('actualizar','no_aplica','pendiente')),
            motivo text,
            decidente_id varchar REFERENCES users(id),
            decidido_en timestamptz,
            creado_en timestamptz NOT NULL DEFAULT now(),
            UNIQUE(impacto_id,tenant_id),
            CHECK ((decidente_id IS NULL AND decidido_en IS NULL AND motivo IS NULL)
                OR (decidente_id IS NOT NULL AND decidido_en IS NOT NULL AND length(trim(motivo))>0))
        );
        CREATE TABLE biblioteca_impactos_avisos (
            id varchar(36) PRIMARY KEY,
            expediente_id varchar(36) NOT NULL REFERENCES biblioteca_impactos_organizacion(id),
            estado varchar NOT NULL CHECK (estado IN ('pendiente','fallido','recibido')),
            intentos integer NOT NULL DEFAULT 0 CHECK (intentos>=0),
            ultimo_intento_en timestamptz,
            recibido_en timestamptz,
            ultimo_error varchar(500),
            creado_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_bib_impacto_org_tenant ON biblioteca_impactos_organizacion(tenant_id,creado_en);
        CREATE INDEX ix_bib_impacto_avisos_expediente ON biblioteca_impactos_avisos(expediente_id,creado_en);
    """)
    op.execute("""
        ALTER TABLE biblioteca_impactos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_impactos FORCE ROW LEVEL SECURITY;
        CREATE POLICY bib_impactos_editorial ON biblioteca_impactos USING (biblioteca_puede())
            WITH CHECK (biblioteca_puede('publicador'));
        ALTER TABLE biblioteca_impactos_organizacion ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_impactos_organizacion FORCE ROW LEVEL SECURITY;
        CREATE POLICY bib_impactos_org_tenant ON biblioteca_impactos_organizacion
            USING (tenant_id=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id=current_setting('app.current_tenant_id',true));
        CREATE POLICY bib_impactos_org_editorial ON biblioteca_impactos_organizacion
            USING (biblioteca_puede()) WITH CHECK (biblioteca_puede('publicador'));
        ALTER TABLE biblioteca_impactos_avisos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_impactos_avisos FORCE ROW LEVEL SECURITY;
        CREATE POLICY bib_impactos_avisos_tenant ON biblioteca_impactos_avisos USING (EXISTS (
            SELECT 1 FROM biblioteca_impactos_organizacion o WHERE o.id=expediente_id
              AND o.tenant_id=current_setting('app.current_tenant_id',true)));
        CREATE POLICY bib_impactos_avisos_editorial ON biblioteca_impactos_avisos
            USING (biblioteca_puede()) WITH CHECK (biblioteca_puede('publicador'));
        REVOKE ALL ON biblioteca_impactos,biblioteca_impactos_organizacion,biblioteca_impactos_avisos FROM lopdp_app;
        GRANT SELECT,INSERT ON biblioteca_impactos,biblioteca_impactos_organizacion,biblioteca_impactos_avisos TO lopdp_app;
        GRANT UPDATE(decision,motivo,decidente_id,decidido_en) ON biblioteca_impactos_organizacion TO lopdp_app;
        GRANT UPDATE(estado,intentos,ultimo_intento_en,recibido_en,ultimo_error) ON biblioteca_impactos_avisos TO lopdp_app;
    """)
    op.execute("""
        CREATE FUNCTION biblioteca_impacto_preservar_aprobado() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$ BEGIN
            IF OLD.estado='aprobado' AND NEW.contenido_markdown IS DISTINCT FROM OLD.contenido_markdown THEN
                RAISE EXCEPTION 'BIB_DOCUMENTO_APROBADO_INMUTABLE' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_impacto_preservar_aprobado BEFORE UPDATE ON biblioteca_documentos
            FOR EACH ROW EXECUTE FUNCTION biblioteca_impacto_preservar_aprobado();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER biblioteca_impacto_preservar_aprobado ON biblioteca_documentos")
    op.execute("DROP FUNCTION biblioteca_impacto_preservar_aprobado()")
    op.execute("DROP TABLE biblioteca_impactos_avisos")
    op.execute("DROP TABLE biblioteca_impactos_organizacion")
    op.execute("DROP TABLE biblioteca_impactos")
