# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""BIB-401: plantillas de la cuenta profesional (tercera capa entre la maestra y la organización).

Copia editable de una maestra publicada para la cuenta profesional del implementador.
RLS ENABLE y FORCE con USING y WITH CHECK por cuenta_id = current_setting('app.current_user_id', true).
Permisos mínimos para lopdp_app: SELECT, INSERT, UPDATE.
Disparador de desactualización automática en biblioteca_versiones cuando se publica una nueva versión.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20261103_bib_cuenta_profesional"
down_revision: Union[str, Sequence[str], None] = "20261113_merge_heads_jose_f02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_plantillas_cuenta (
            id varchar(36) PRIMARY KEY,
            cuenta_id varchar NOT NULL,
            maestra_codigo varchar(40) NOT NULL,
            maestra_version varchar(40) NOT NULL,
            contenido_key text,
            marca jsonb DEFAULT '{}'::jsonb CHECK (marca IS NULL OR jsonb_typeof(marca) = 'object'),
            estado varchar(12) NOT NULL DEFAULT 'vigente' CHECK (estado IN ('vigente', 'desactualizada', 'retirada')),
            creado_por varchar NOT NULL,
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_bib_plantillas_cuenta_cuenta ON biblioteca_plantillas_cuenta (cuenta_id);
        CREATE INDEX ix_bib_plantillas_cuenta_maestra ON biblioteca_plantillas_cuenta (maestra_codigo);
        ALTER TABLE biblioteca_plantillas_cuenta ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_plantillas_cuenta FORCE ROW LEVEL SECURITY;
        CREATE POLICY bib_plantillas_cuenta_isolation ON biblioteca_plantillas_cuenta
            USING (cuenta_id = current_setting('app.current_user_id', true))
            WITH CHECK (cuenta_id = current_setting('app.current_user_id', true));
        REVOKE ALL ON biblioteca_plantillas_cuenta FROM lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON biblioteca_plantillas_cuenta TO lopdp_app;

        CREATE OR REPLACE FUNCTION biblioteca_marcar_plantillas_cuenta_desactualizadas() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        BEGIN
            IF NEW.estado = 'publicada' THEN
                UPDATE public.biblioteca_plantillas_cuenta
                SET estado = 'desactualizada', actualizado_en = now()
                WHERE maestra_codigo = NEW.codigo
                  AND maestra_version <> NEW.version
                  AND estado = 'vigente';
            END IF;
            RETURN NEW;
        END $$;

        CREATE TRIGGER trg_biblioteca_marcar_desactualizadas
        AFTER INSERT OR UPDATE OF estado, version ON biblioteca_versiones
        FOR EACH ROW EXECUTE FUNCTION biblioteca_marcar_plantillas_cuenta_desactualizadas();
    """)


# ¤adpa
def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS trg_biblioteca_marcar_desactualizadas ON biblioteca_versiones;
        DROP FUNCTION IF EXISTS biblioteca_marcar_plantillas_cuenta_desactualizadas();
        DROP TABLE IF EXISTS biblioteca_plantillas_cuenta;
    """)
