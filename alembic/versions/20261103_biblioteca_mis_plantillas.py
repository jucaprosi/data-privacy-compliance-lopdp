# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""BIB-103: «Mi plantilla», la copia versionada que una organización hace de una plantilla SMARTCIDI.

Tabla privada por organización: RLS ENABLE y FORCE con USING y WITH CHECK por tenant_id. La aplicación
solo puede leer e insertar (sin UPDATE ni DELETE): cada edición futura será una fila de versión nueva y
la plantilla original (biblioteca_versiones) no se toca. No migra producción ni concede nada más.
"""
from alembic import op

revision = "20261103_bib_mis_plantillas"
down_revision = "20261102_merge_firma_main"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_mis_plantillas (
            id varchar(36) PRIMARY KEY,
            plantilla_id varchar(36) NOT NULL,
            version integer NOT NULL CHECK (version >= 1),
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            codigo varchar(40) NOT NULL,
            nombre varchar(200) NOT NULL CHECK (length(trim(nombre)) > 0),
            formato varchar NOT NULL DEFAULT 'MD' CHECK (formato = 'MD'),
            cuerpo_md text NOT NULL CHECK (length(cuerpo_md) BETWEEN 1 AND 200000),
            sha256 varchar(64) NOT NULL CHECK (sha256 = encode(sha256(convert_to(cuerpo_md, 'UTF8')), 'hex')),
            origen_plantilla_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            origen_version varchar(40) NOT NULL,
            creada_por varchar NOT NULL REFERENCES users(id),
            creada_en timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, plantilla_id, version),
            CHECK ((version = 1) = (plantilla_id = id))
        );
        CREATE INDEX biblioteca_mis_plantillas_tenant ON biblioteca_mis_plantillas (tenant_id, plantilla_id, version DESC);
        ALTER TABLE biblioteca_mis_plantillas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_mis_plantillas FORCE ROW LEVEL SECURITY;
        CREATE POLICY bib_mis_plantillas_tenant ON biblioteca_mis_plantillas
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)
                        AND creada_por = current_setting('app.current_user_id', true)
                        AND biblioteca_miembro_activo());
        GRANT SELECT, INSERT ON biblioteca_mis_plantillas TO lopdp_app;
    """)
    # El origen debe ser una versión publicada del mismo código y el cuerpo, el publicado: la copia no inventa ni altera.
    op.execute("""
        CREATE FUNCTION biblioteca_validar_mi_plantilla() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        DECLARE origen public.biblioteca_versiones;
        BEGIN
            SELECT * INTO origen FROM public.biblioteca_versiones WHERE id = NEW.origen_plantilla_id;
            IF origen.id IS NULL OR origen.estado <> 'publicada' OR origen.formato <> 'MD'
               OR origen.codigo <> NEW.codigo OR origen.version <> NEW.origen_version THEN
                RAISE EXCEPTION 'BIB_COPIA_ORIGEN_INVALIDO' USING ERRCODE = '23514';
            END IF;
            IF NEW.version = 1 AND NEW.cuerpo_md <> origen.cuerpo_md THEN
                RAISE EXCEPTION 'BIB_COPIA_ORIGEN_INVALIDO' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_mis_plantillas_validar BEFORE INSERT ON biblioteca_mis_plantillas
            FOR EACH ROW EXECUTE FUNCTION biblioteca_validar_mi_plantilla();
    """)


# ¤adpa
def downgrade() -> None:
    op.execute("""
        DROP TRIGGER biblioteca_mis_plantillas_validar ON biblioteca_mis_plantillas;
        DROP FUNCTION biblioteca_validar_mi_plantilla();
        DROP TABLE biblioteca_mis_plantillas;
    """)
