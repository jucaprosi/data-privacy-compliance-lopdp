# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-205: archivos Word y Excel generados desde un borrador, con su instantánea y checksum.

Datos privados por organización: RLS ENABLE y FORCE por tenant_id. Cada generación es inmutable: guarda la
instantánea de la que salió (plantilla, esquema y valores), su huella, el archivo y la huella del archivo.
`lopdp_app` solo lee e inserta: sin UPDATE ni DELETE. El borrador referido debe ser de la misma
organización (lo comprueba el servicio con la RLS y, de respaldo, el disparador).
"""
from alembic import op

revision = "20261116_bib_generacion"
down_revision = "20261115_merge_heads_tanda37"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_generaciones (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            borrador_id varchar(36) NOT NULL REFERENCES biblioteca_borradores(id),
            modo varchar(8) NOT NULL CHECK (modo IN ('borrador','revision')),
            formato varchar(4) NOT NULL CHECK (formato IN ('docx','xlsx')),
            estado varchar(13) NOT NULL CHECK (estado IN ('borrador','para_revision')),
            plantilla_sha256 char(64) NOT NULL CHECK (plantilla_sha256 ~ '^[a-f0-9]{64}$'),
            instantanea jsonb NOT NULL CHECK (jsonb_typeof(instantanea)='object'),
            instantanea_sha256 char(64) NOT NULL CHECK (instantanea_sha256 ~ '^[a-f0-9]{64}$'),
            archivo bytea NOT NULL,
            archivo_sha256 char(64) NOT NULL CHECK (archivo_sha256 ~ '^[a-f0-9]{64}$'),
            bytes integer NOT NULL CHECK (bytes > 0 AND bytes = octet_length(archivo)),
            faltantes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(faltantes)='array'),
            nombre_archivo varchar(120) NOT NULL CHECK (nombre_archivo ~ '^[A-Za-z0-9._-]{1,120}$'),
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_biblioteca_generaciones_revision CHECK (
                modo='borrador' OR (estado='para_revision' AND faltantes='[]'::jsonb)),
            CONSTRAINT ck_biblioteca_generaciones_estado CHECK (
                (modo='borrador' AND estado='borrador') OR (modo='revision' AND estado='para_revision'))
        );
        CREATE INDEX ix_biblioteca_generaciones_borrador ON biblioteca_generaciones(tenant_id,borrador_id,creado_en);
        CREATE FUNCTION biblioteca_generaciones_validar() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.biblioteca_borradores b
                           WHERE b.id=NEW.borrador_id AND b.tenant_id=NEW.tenant_id) THEN
                RAISE EXCEPTION 'BIB_GEN_BORRADOR_AJENO' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER biblioteca_generaciones_validar BEFORE INSERT ON biblioteca_generaciones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_generaciones_validar();
        ALTER TABLE biblioteca_generaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_generaciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_generaciones ON biblioteca_generaciones
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_generaciones FROM lopdp_app;
        GRANT SELECT,INSERT ON biblioteca_generaciones TO lopdp_app;
    """)


# ¤adpa
def downgrade() -> None:
    # Solo ramas de desarrollo: borra los archivos generados.
    op.execute("""
        DROP TABLE biblioteca_generaciones;
        DROP FUNCTION biblioteca_generaciones_validar();
    """)
