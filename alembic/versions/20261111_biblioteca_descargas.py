# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-104: descarga controlada de plantillas Word/Excel y registro de auditoría.

- `biblioteca_descargas`: auditoría append-only con RLS ENABLE y FORCE (USING y WITH CHECK
  por tenant_id y pertenencia activa de la organización).
- Registra actor, empresa (tenant_id), plantilla, versión y fecha.
- Inmutable: solo INSERT y SELECT para lopdp_app; un disparador rechaza UPDATE y DELETE.
- La descarga no atribuye cumplimiento legal automático bajo LOPDP.
"""
from alembic import op

revision = "20261111_bib_descargas"
down_revision = "20261110_merge_heads_tanda33"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_descargas (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            usuario_id varchar NOT NULL REFERENCES users(id),
            plantilla_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            version varchar(40) NOT NULL,
            descargada_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_biblioteca_descargas_tenant ON biblioteca_descargas(tenant_id, descargada_en DESC);
        CREATE INDEX ix_biblioteca_descargas_plantilla ON biblioteca_descargas(plantilla_id, descargada_en DESC);
        CREATE FUNCTION biblioteca_descargas_inmutable() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        BEGIN
            RAISE EXCEPTION 'BIB_HISTORIAL_INMUTABLE' USING ERRCODE='23514';
        END $$;
        CREATE TRIGGER biblioteca_descargas_inmutable
            BEFORE UPDATE OR DELETE ON biblioteca_descargas
            FOR EACH ROW EXECUTE FUNCTION biblioteca_descargas_inmutable();
    """)
    op.execute("ALTER TABLE biblioteca_descargas ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE biblioteca_descargas FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_biblioteca_descargas ON biblioteca_descargas "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true) "
        "AND usuario_id::text = current_setting('app.current_user_id', true) "
        "AND biblioteca_miembro_activo())"
    )
    op.execute("REVOKE ALL ON biblioteca_descargas FROM PUBLIC, lopdp_app")
    op.execute("GRANT SELECT, INSERT ON biblioteca_descargas TO lopdp_app")


# ¤adpa
def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS biblioteca_descargas_inmutable ON biblioteca_descargas")
    op.execute("DROP FUNCTION IF EXISTS biblioteca_descargas_inmutable()")
    op.execute("DROP TABLE IF EXISTS biblioteca_descargas")
