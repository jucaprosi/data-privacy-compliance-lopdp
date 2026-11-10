# ¤¤security-engineer
"""EVI-01: documentos de evidencia guardados y comprobados por el servidor. ¤evidencias ¤rbac-tenant

- `evidencias_documentos`: un registro por documento y organización, con la huella que calculó el
  servidor, la clave en el almacén, quién lo subió y cuándo, y la retención que se fijó. La
  aplicación (lopdp_app) solo lee e inserta: un documento registrado no se edita ni se borra.
- `evidencias_vinculos`: documento y control (pregunta 1 a 80), con quién vinculó y cuándo. Pueden
  quitarse; cada alta y cada baja deja un evento en `audit_events` (lo escribe el servicio).
- RLS forzada en las dos tablas, por `tenant_id`.
"""
from alembic import op

revision = "20261029_evidencias_documentales"
down_revision = "20261106_diag_prueba_y_real"
branch_labels = None
depends_on = None

SQL_ASCENDENTE = [
    """
    CREATE TABLE evidencias_documentos (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        codigo VARCHAR(32) NOT NULL,
        nombre_archivo VARCHAR(255) NOT NULL,
        tipo_mime VARCHAR(128) NOT NULL,
        tamano_bytes BIGINT NOT NULL,
        sha256 CHAR(64) NOT NULL,
        normativa VARCHAR(32) NOT NULL,
        clave_almacen VARCHAR(512) NOT NULL,
        subido_por VARCHAR NOT NULL REFERENCES users(id),
        subido_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        retencion_dias INTEGER NOT NULL,
        CONSTRAINT ck_evidencias_documentos_tamano CHECK (tamano_bytes >= 0),
        CONSTRAINT ck_evidencias_documentos_retencion CHECK (retencion_dias > 0),
        CONSTRAINT ck_evidencias_documentos_sha256 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
        CONSTRAINT uq_evidencias_documentos_huella UNIQUE (tenant_id, sha256, normativa),
        CONSTRAINT uq_evidencias_documentos_codigo UNIQUE (tenant_id, codigo),
        CONSTRAINT uq_evidencias_documentos_clave UNIQUE (clave_almacen),
        CONSTRAINT uq_evidencias_documentos_id_tenant UNIQUE (id, tenant_id)
    )
    """,
    """
    CREATE TABLE evidencias_vinculos (
        id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        documento_id VARCHAR NOT NULL,
        control_id SMALLINT NOT NULL,
        vinculado_por VARCHAR NOT NULL REFERENCES users(id),
        vinculado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT ck_evidencias_vinculos_control CHECK (control_id BETWEEN 1 AND 80),
        CONSTRAINT uq_evidencias_vinculos_par UNIQUE (documento_id, control_id),
        CONSTRAINT fk_evidencias_vinculos_documento FOREIGN KEY (documento_id, tenant_id)
            REFERENCES evidencias_documentos (id, tenant_id)
    )
    """,
    "CREATE INDEX ix_evidencias_vinculos_tenant_control ON evidencias_vinculos (tenant_id, control_id)",
    "ALTER TABLE evidencias_documentos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE evidencias_documentos FORCE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation_evidencias_documentos ON evidencias_documentos
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
    """,
    "ALTER TABLE evidencias_vinculos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE evidencias_vinculos FORCE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation_evidencias_vinculos ON evidencias_vinculos
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
    """,
    "REVOKE ALL ON evidencias_documentos FROM lopdp_app",
    "GRANT SELECT, INSERT ON evidencias_documentos TO lopdp_app",
    "REVOKE ALL ON evidencias_vinculos FROM lopdp_app",
    "GRANT SELECT, INSERT, DELETE ON evidencias_vinculos TO lopdp_app",
]

SQL_DESCENDENTE = [
    "DROP TABLE IF EXISTS evidencias_vinculos",
    "DROP TABLE IF EXISTS evidencias_documentos",
]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
