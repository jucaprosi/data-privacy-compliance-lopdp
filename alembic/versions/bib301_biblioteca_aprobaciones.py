"""Revisión y aprobación documental BIB-301. ¤rbac-tenant"""
from alembic import op

revision = "bib301_aprobaciones"
down_revision = "20261112_merge_heads_tanda35"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE biblioteca_autoridades_aprobacion (
      id VARCHAR PRIMARY KEY, tenant_id VARCHAR NOT NULL REFERENCES tenants(id), usuario_id VARCHAR NOT NULL REFERENCES users(id),
      criterio VARCHAR(500) NOT NULL, vigente_desde TIMESTAMPTZ NOT NULL, vigente_hasta TIMESTAMPTZ,
      delegada_por VARCHAR NOT NULL REFERENCES users(id), revocada_en TIMESTAMPTZ,
      CHECK (vigente_hasta IS NULL OR vigente_hasta > vigente_desde)
    );
    CREATE TABLE biblioteca_revisiones (
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
    CREATE INDEX ix_bib_revisiones_tenant ON biblioteca_revisiones(tenant_id);
    ALTER TABLE biblioteca_autoridades_aprobacion ENABLE ROW LEVEL SECURITY;
    ALTER TABLE biblioteca_autoridades_aprobacion FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_biblioteca_autoridades_aprobacion ON biblioteca_autoridades_aprobacion
      USING (tenant_id = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
    ALTER TABLE biblioteca_revisiones ENABLE ROW LEVEL SECURITY;
    ALTER TABLE biblioteca_revisiones FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_biblioteca_revisiones ON biblioteca_revisiones
      USING (tenant_id = current_setting('app.current_tenant_id', true)) WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
    GRANT SELECT, INSERT ON biblioteca_autoridades_aprobacion, biblioteca_revisiones TO lopdp_app;
    GRANT UPDATE (revocada_en) ON biblioteca_autoridades_aprobacion TO lopdp_app;
    GRANT UPDATE (estado,observaciones,decidido_por,decidido_en,criterio_aprobacion,autoridad_id) ON biblioteca_revisiones TO lopdp_app;
    GRANT UPDATE (estado,aprobado_por,aprobado_en) ON biblioteca_documentos TO lopdp_app;
    """)


def downgrade():
    op.execute("DROP TABLE biblioteca_revisiones; DROP TABLE biblioteca_autoridades_aprobacion;")
