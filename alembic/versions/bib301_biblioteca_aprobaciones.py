"""Revisión y aprobación documental BIB-301. ¤rbac-tenant"""
from alembic import op

revision = "bib301_aprobaciones"
down_revision = "20261112_merge_heads_tanda35"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE biblioteca_documentos ADD CONSTRAINT uq_bib_documentos_id_tenant UNIQUE (id, tenant_id)")
    op.execute("""
    CREATE TABLE biblioteca_autoridades_aprobacion (
      id VARCHAR PRIMARY KEY, tenant_id VARCHAR NOT NULL REFERENCES tenants(id), usuario_id VARCHAR NOT NULL REFERENCES users(id),
      criterio VARCHAR(500) NOT NULL, vigente_desde TIMESTAMPTZ NOT NULL, vigente_hasta TIMESTAMPTZ,
      delegada_por VARCHAR NOT NULL REFERENCES users(id), revocada_en TIMESTAMPTZ,
      CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)
    );
    CREATE TABLE biblioteca_revisiones_documento (
      id VARCHAR PRIMARY KEY, tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
      documento_id VARCHAR NOT NULL, revision INTEGER NOT NULL, sha256 VARCHAR(64) NOT NULL,
      revisor_id VARCHAR NOT NULL REFERENCES users(id), tipo_participacion VARCHAR(16) NOT NULL,
      estado VARCHAR(12) NOT NULL DEFAULT 'asignada', observaciones TEXT, asignado_por VARCHAR NOT NULL REFERENCES users(id),
      asignado_en TIMESTAMPTZ NOT NULL DEFAULT now(), decidido_por VARCHAR REFERENCES users(id), decidido_en TIMESTAMPTZ,
      criterio_aprobacion TEXT, autoridad_id VARCHAR REFERENCES biblioteca_autoridades_aprobacion(id),
      FOREIGN KEY (documento_id, tenant_id) REFERENCES biblioteca_documentos(id, tenant_id),
      UNIQUE (documento_id, revision),
      CHECK (tipo_participacion IN ('revision','asesoria','supervision')),
      CHECK (estado IN ('asignada','devuelta','aprobada'))
    );
    CREATE INDEX ix_bib_autoridades_tenant_usuario ON biblioteca_autoridades_aprobacion(tenant_id, usuario_id);
    CREATE INDEX ix_bib_revisiones_doc_tenant ON biblioteca_revisiones_documento(tenant_id);
    ALTER TABLE biblioteca_autoridades_aprobacion ENABLE ROW LEVEL SECURITY;
    ALTER TABLE biblioteca_autoridades_aprobacion FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_biblioteca_autoridades_aprobacion ON biblioteca_autoridades_aprobacion
      USING (tenant_id = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
    ALTER TABLE biblioteca_revisiones_documento ENABLE ROW LEVEL SECURITY;
    ALTER TABLE biblioteca_revisiones_documento FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_biblioteca_revisiones_documento ON biblioteca_revisiones_documento
      USING (tenant_id = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
    GRANT SELECT, INSERT ON biblioteca_autoridades_aprobacion, biblioteca_revisiones_documento TO lopdp_app;
    GRANT UPDATE (revocada_en) ON biblioteca_autoridades_aprobacion TO lopdp_app;
    GRANT UPDATE (estado,observaciones,decidido_por,decidido_en,criterio_aprobacion,autoridad_id) ON biblioteca_revisiones_documento TO lopdp_app;
    """)
    # La aplicación no actualiza el estado del documento (invariante de BIB-107): las dos
    # transiciones pasan por funciones acotadas que comprueban el tenant de la sesión.
    op.execute("""
    CREATE FUNCTION biblioteca_aprobar_documento(p_doc varchar, p_tenant varchar, p_user varchar,
                                                 p_rev integer, p_sha varchar) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE n integer;
    BEGIN
      IF p_tenant IS DISTINCT FROM current_setting('app.current_tenant_id', true) THEN
        RAISE EXCEPTION 'BIB_TENANT_NO_COINCIDE' USING ERRCODE='42501';
      END IF;
      UPDATE public.biblioteca_documentos SET estado='aprobado',aprobado_por=p_user,aprobado_en=now()
       WHERE id=p_doc AND tenant_id=p_tenant AND revision=p_rev AND sha256=p_sha;
      GET DIAGNOSTICS n = ROW_COUNT;
      RETURN n;
    END $$;
    CREATE FUNCTION biblioteca_reabrir_documento(p_doc varchar, p_tenant varchar) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE nueva integer;
    BEGIN
      IF p_tenant IS DISTINCT FROM current_setting('app.current_tenant_id', true) THEN
        RAISE EXCEPTION 'BIB_TENANT_NO_COINCIDE' USING ERRCODE='42501';
      END IF;
      UPDATE public.biblioteca_documentos SET estado='borrador',revision=revision+1,aprobado_por=NULL,
             aprobado_en=NULL,actualizado_en=now()
       WHERE id=p_doc AND tenant_id=p_tenant AND estado='aprobado' RETURNING revision INTO nueva;
      RETURN nueva;
    END $$;
    REVOKE ALL ON FUNCTION biblioteca_aprobar_documento(varchar,varchar,varchar,integer,varchar) FROM PUBLIC;
    REVOKE ALL ON FUNCTION biblioteca_reabrir_documento(varchar,varchar) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_aprobar_documento(varchar,varchar,varchar,integer,varchar) TO lopdp_app;
    GRANT EXECUTE ON FUNCTION biblioteca_reabrir_documento(varchar,varchar) TO lopdp_app;
    """)


def downgrade():
    op.execute("DROP FUNCTION biblioteca_reabrir_documento(varchar,varchar); DROP FUNCTION biblioteca_aprobar_documento(varchar,varchar,varchar,integer,varchar)")
    op.execute("DROP TABLE biblioteca_revisiones_documento; DROP TABLE biblioteca_autoridades_aprobacion;")
    op.execute("ALTER TABLE biblioteca_documentos DROP CONSTRAINT uq_bib_documentos_id_tenant")
