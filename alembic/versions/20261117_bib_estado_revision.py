# ¤¤backend-developer
"""Envío a revisión y devolución del documento por funciones acotadas (corrige BIB-301). ¤rbac-tenant

`lopdp_app` no tiene UPDATE sobre `biblioteca_documentos.estado` (invariante de BIB-107), así que
`enviar_a_revision` y `devolver_revision` fallaban con «permission denied». Igual que
`biblioteca_aprobar_documento`, las dos transiciones pasan por funciones que comprueban el tenant
de la sesión y solo cambian el estado permitido.
"""
from alembic import op

revision = "20261117_bib_estado_revision"
down_revision = "20261116_bib_generacion"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION biblioteca_enviar_documento_a_revision(p_doc varchar, p_tenant varchar) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE n integer;
    BEGIN
      IF p_tenant IS DISTINCT FROM current_setting('app.current_tenant_id', true) THEN
        RAISE EXCEPTION 'BIB_TENANT_NO_COINCIDE' USING ERRCODE='42501';
      END IF;
      UPDATE public.biblioteca_documentos SET estado='en_revision'
       WHERE id=p_doc AND tenant_id=p_tenant AND estado='borrador';
      GET DIAGNOSTICS n = ROW_COUNT;
      RETURN n;
    END $$;
    CREATE FUNCTION biblioteca_devolver_documento(p_doc varchar, p_tenant varchar, p_rev integer,
                                                  p_sha varchar) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE n integer;
    BEGIN
      IF p_tenant IS DISTINCT FROM current_setting('app.current_tenant_id', true) THEN
        RAISE EXCEPTION 'BIB_TENANT_NO_COINCIDE' USING ERRCODE='42501';
      END IF;
      UPDATE public.biblioteca_documentos SET estado='borrador'
       WHERE id=p_doc AND tenant_id=p_tenant AND revision=p_rev AND sha256=p_sha AND estado='en_revision';
      GET DIAGNOSTICS n = ROW_COUNT;
      RETURN n;
    END $$;
    REVOKE ALL ON FUNCTION biblioteca_enviar_documento_a_revision(varchar,varchar) FROM PUBLIC;
    REVOKE ALL ON FUNCTION biblioteca_devolver_documento(varchar,varchar,integer,varchar) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_enviar_documento_a_revision(varchar,varchar) TO lopdp_app;
    GRANT EXECUTE ON FUNCTION biblioteca_devolver_documento(varchar,varchar,integer,varchar) TO lopdp_app;
    """)


def downgrade():
    op.execute("DROP FUNCTION biblioteca_devolver_documento(varchar,varchar,integer,varchar)")
    op.execute("DROP FUNCTION biblioteca_enviar_documento_a_revision(varchar,varchar)")
