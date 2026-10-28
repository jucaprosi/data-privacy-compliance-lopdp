# ¤adpa
# ¤¤developer-architect
"""BIB-108: metadatos del catálogo global y registro append-only de importaciones.

No importa datos ni asigna capacidades. Sin tenant: catálogo editorial global.
"""
from alembic import op

revision = "20261026_biblioteca_catalogo"
down_revision = "20261028_diagnostico_resultados"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        ALTER TABLE biblioteca_catalogo
            ADD COLUMN nombre varchar(200) CHECK (nombre IS NULL OR length(trim(nombre)) > 0),
            ADD COLUMN familia varchar(60),
            ADD COLUMN tipo varchar(60),
            ADD COLUMN naturaleza varchar(80),
            ADD COLUMN etapa varchar(60),
            ADD COLUMN formato varchar CHECK (formato IS NULL OR formato IN ('DOCX','XLSX')),
            ADD COLUMN fuentes text,
            ADD COLUMN disponibilidad varchar NOT NULL DEFAULT 'planificada'
                CHECK (disponibilidad IN ('con_archivo','salida_por_mapear','planificada')),
            ADD COLUMN metadatos jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadatos)='object');
        CREATE TABLE biblioteca_importaciones (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            clave varchar(80) NOT NULL CHECK (clave ~ '^[A-Za-z0-9][A-Za-z0-9._@-]{0,79}$'),
            codigo varchar(40) NOT NULL REFERENCES biblioteca_catalogo(codigo),
            version_id varchar(36) REFERENCES biblioteca_versiones(id),
            origen varchar(200),
            tipo varchar CHECK (tipo IS NULL OR tipo IN ('DOCX','XLSX')),
            tamano integer CHECK (tamano IS NULL OR tamano > 0),
            sha256 varchar(64) CHECK (sha256 IS NULL OR sha256 ~ '^[a-f0-9]{64}$'),
            apertura varchar NOT NULL CHECK (apertura IN ('ok','sin_archivo')),
            ejecutada_por varchar NOT NULL REFERENCES users(id),
            creada_en timestamptz NOT NULL DEFAULT now(),
            UNIQUE (clave, codigo),
            CHECK ((apertura='ok' AND version_id IS NOT NULL AND sha256 IS NOT NULL AND tamano IS NOT NULL
                    AND tipo IS NOT NULL AND origen IS NOT NULL)
                OR (apertura='sin_archivo' AND version_id IS NULL AND sha256 IS NULL AND tamano IS NULL))
        );
        CREATE INDEX biblioteca_importaciones_codigo ON biblioteca_importaciones(codigo);
        ALTER TABLE biblioteca_importaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_importaciones FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_importaciones FROM PUBLIC, lopdp_app;
        GRANT SELECT, INSERT ON biblioteca_importaciones TO lopdp_app;
        CREATE POLICY bib_importacion_lectura ON biblioteca_importaciones FOR SELECT USING (biblioteca_puede());
        CREATE POLICY bib_importacion_alta ON biblioteca_importaciones FOR INSERT WITH CHECK (
            biblioteca_puede('editor') AND ejecutada_por=current_setting('app.current_user_id',true));
    """)


# ¤adpa
def downgrade() -> None:
    # Destructivo: elimina el registro de importaciones y los metadatos. Solo ramas de desarrollo.
    op.execute("DROP TABLE biblioteca_importaciones")
    op.execute("""
        ALTER TABLE biblioteca_catalogo
            DROP COLUMN metadatos, DROP COLUMN disponibilidad, DROP COLUMN fuentes, DROP COLUMN formato,
            DROP COLUMN etapa, DROP COLUMN naturaleza, DROP COLUMN tipo, DROP COLUMN familia, DROP COLUMN nombre
    """)
