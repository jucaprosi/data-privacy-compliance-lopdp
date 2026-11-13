# ¤¤security-engineer
"""EVI-02: vigencia y visibilidad de los documentos de evidencia. ¤evidencias ¤evidencias-vigencia ¤rbac-tenant

`evidencias_documentos` no se edita (EVI-01); la vigencia y la visibilidad viven aparte, en
`evidencias_atributos`, una fila por documento:
- `vence_en`: fecha de vencimiento opcional. Un documento vencido no cuenta como vigente para ningún requisito;
  «vencido» es un atributo, no un estado que sustituya a «verificado eficaz».
- `visible_para`: roles de la organización que ven el documento (por omisión, los cuatro que consultan).
  Siempre incluye al `dpo`.
RLS forzada por `tenant_id`; `lopdp_app` lee, inserta y actualiza, y no borra.
"""
from alembic import op

revision = "20261031_evidencias_vigencia"
down_revision = "20261122_rol_auditor"
branch_labels = None
depends_on = None

SQL_ASCENDENTE = [
    """
    CREATE TABLE evidencias_atributos (
        documento_id VARCHAR PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        vence_en DATE NULL,
        visible_para VARCHAR[] NOT NULL DEFAULT ARRAY['dpo', 'coordinador', 'implementador', 'admin_organizacion']::VARCHAR[],
        actualizado_por VARCHAR NOT NULL REFERENCES users(id),
        actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT fk_evidencias_atributos_documento FOREIGN KEY (documento_id, tenant_id)
            REFERENCES evidencias_documentos (id, tenant_id),
        CONSTRAINT ck_evidencias_atributos_dpo CHECK ('dpo' = ANY (visible_para)),
        CONSTRAINT ck_evidencias_atributos_roles CHECK (
            visible_para <@ ARRAY['dpo', 'coordinador', 'implementador', 'admin_organizacion']::VARCHAR[]
        )
    )
    """,
    "CREATE INDEX ix_evidencias_atributos_tenant_vence ON evidencias_atributos (tenant_id, vence_en)",
    "ALTER TABLE evidencias_atributos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE evidencias_atributos FORCE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation_evidencias_atributos ON evidencias_atributos
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
    """,
    "REVOKE ALL ON evidencias_atributos FROM lopdp_app",
    "GRANT SELECT, INSERT, UPDATE ON evidencias_atributos TO lopdp_app",
]

SQL_DESCENDENTE = ["DROP TABLE IF EXISTS evidencias_atributos"]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
