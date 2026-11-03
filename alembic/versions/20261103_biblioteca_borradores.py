# ¤adpa
# ¤¤security-engineer
"""BIB-201: borradores de la organización (respuestas `contexto.*` y copia de la plantilla usada).

Datos privados por organización, aparte de las versiones editoriales globales. RLS ENABLE y FORCE por
tenant_id. `lopdp_app` lee, inserta y solo actualiza las columnas editables: la copia de la plantilla y
su huella no cambian después de crear el borrador. Sin DELETE.
"""
from alembic import op

revision = "20261103_biblioteca_borradores"
down_revision = "20261102_merge_firma_main"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_borradores (
            id varchar(36) PRIMARY KEY,
            tenant_id varchar NOT NULL REFERENCES tenants(id),
            version_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            plantilla_md text NOT NULL CHECK (length(plantilla_md) BETWEEN 1 AND 200000),
            plantilla_sha256 varchar(64) NOT NULL CHECK (plantilla_sha256 ~ '^[a-f0-9]{64}$'),
            contexto jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(contexto)='object'),
            fecha_emision date NOT NULL,
            revision integer NOT NULL DEFAULT 1 CHECK (revision>=1),
            creado_por varchar NOT NULL REFERENCES users(id),
            actualizado_por varchar NOT NULL REFERENCES users(id),
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX biblioteca_borradores_tenant ON biblioteca_borradores(tenant_id, actualizado_en DESC);
        ALTER TABLE biblioteca_borradores ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_borradores FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_isolation_biblioteca_borradores ON biblioteca_borradores
            USING (tenant_id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        REVOKE ALL ON biblioteca_borradores FROM lopdp_app;
        GRANT SELECT, INSERT ON biblioteca_borradores TO lopdp_app;
        GRANT UPDATE (contexto, fecha_emision, revision, actualizado_por, actualizado_en)
            ON biblioteca_borradores TO lopdp_app;
    """)


# ¤adpa
def downgrade() -> None:
    # Solo ramas de desarrollo: borra los borradores (con FORCE RLS no se pueden contar sin contexto de organización).
    op.execute("DROP TABLE biblioteca_borradores")
