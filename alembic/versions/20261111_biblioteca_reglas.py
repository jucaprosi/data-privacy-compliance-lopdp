# ¤adpa ¤rbac-tenant
# ¤¤security-engineer
"""BIB-204: modificaciones humanas y persistencia de aplicabilidad de plantillas.

Conserva el resultado original, motivo, evidencia, autor, fecha y revisión jurídica exigida
para excluir obligaciones confirmadas. Aislamiento por tenant_id con RLS forzado.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20261111_bib_reglas"
down_revision: Union[str, Sequence[str], None] = "20261110_merge_heads_tanda33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_aplicabilidad_modificaciones (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            plantilla_codigo varchar NOT NULL,
            resultado_original varchar NOT NULL CHECK (resultado_original IN ('Aplica', 'No aplica', 'Información insuficiente')),
            resultado_modificado varchar NOT NULL CHECK (resultado_modificado IN ('Aplica', 'No aplica')),
            motivo text NOT NULL CHECK (length(motivo) >= 3),
            evidencia text NOT NULL CHECK (length(evidencia) >= 1),
            autor_id varchar NOT NULL REFERENCES users(id),
            es_obligacion_confirmada boolean NOT NULL DEFAULT false,
            revisor_juridico_id varchar REFERENCES users(id),
            fecha timestamptz NOT NULL DEFAULT now(),
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ux_bib_aplic_mod_tenant_plantilla UNIQUE (tenant_id, plantilla_codigo),
            CONSTRAINT ck_bib_aplic_mod_exclusion_juridico CHECK (
                NOT es_obligacion_confirmada OR resultado_modificado <> 'No aplica' OR revisor_juridico_id IS NOT NULL
            )
        );
        CREATE INDEX ix_bib_aplic_mod_tenant ON biblioteca_aplicabilidad_modificaciones(tenant_id, plantilla_codigo);
        ALTER TABLE biblioteca_aplicabilidad_modificaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_aplicabilidad_modificaciones FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_aplicabilidad_mod ON biblioteca_aplicabilidad_modificaciones
            USING (tenant_id = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON biblioteca_aplicabilidad_modificaciones FROM lopdp_app;
        GRANT SELECT, INSERT ON biblioteca_aplicabilidad_modificaciones TO lopdp_app;
        GRANT UPDATE (resultado_modificado, motivo, evidencia, autor_id, es_obligacion_confirmada, revisor_juridico_id, fecha, actualizado_en)
            ON biblioteca_aplicabilidad_modificaciones TO lopdp_app;
    """)


# ¤adpa
def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS biblioteca_aplicabilidad_modificaciones;")
