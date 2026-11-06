# ¤adpa ¤rbac-tenant ¤rat
"""BIB-402: vínculos de un documento con tratamientos (RAT), controles (P1–P80) y tareas.

`ref` no lleva clave foránea: apunta a tres tablas de dos salas distintas según `tipo`; la validación
la hace el motor por las compuertas (R3). `lopdp_app` recibe DELETE porque el PUT reemplaza el
conjunto, y UPDATE solo sobre `estado` (R2).
"""
from alembic import op

revision = "20261103_bib_vinculos"
down_revision = "20261113_bib_enlaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_vinculos (
            id varchar(180) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            documento_id varchar(36) NOT NULL REFERENCES biblioteca_documentos(id) ON DELETE CASCADE,
            tipo varchar(12) NOT NULL CHECK (tipo IN ('tratamiento','control','tarea')),
            ref varchar(120) NOT NULL,
            estado varchar(10) NOT NULL DEFAULT 'vigente' CHECK (estado IN ('vigente','revisar')),
            creado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_bib_vinculo UNIQUE (tenant_id, documento_id, tipo, ref)
        );
        CREATE INDEX ix_bib_vinculos_ref ON biblioteca_vinculos(tenant_id, tipo, ref);
        ALTER TABLE biblioteca_vinculos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_vinculos FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_vinculos ON biblioteca_vinculos
            USING (tenant_id::text=current_setting('app.current_tenant_id',true))
            WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true));
        REVOKE ALL ON biblioteca_vinculos FROM lopdp_app;
        GRANT SELECT,INSERT,DELETE ON biblioteca_vinculos TO lopdp_app;
        GRANT UPDATE (estado) ON biblioteca_vinculos TO lopdp_app;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_vinculos) THEN
                RAISE EXCEPTION 'BIB-402: hay vínculos documentales; no se revierte';
            END IF;
        END $$;
        DROP TABLE biblioteca_vinculos;
    """)
