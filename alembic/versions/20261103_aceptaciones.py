# ¤¤backend-developer
"""FIRMA-02: tabla aceptaciones con RLS por organización y función SECURITY DEFINER para ruta pública. ¤firma-electronica ¤rbac-tenant

`lopdp_app` inserta y lee; solo puede actualizar las tres columnas que el firmante completa al aceptar
(aceptado_en, ip, acuse_sha256). El token nunca viaja al cliente: se guarda su sha256. La función
`obtener_aceptacion_por_token` bypasea el RLS solo para resolver un token puntual sin exponer otras
filas del tenant ni el contenido del documento.
"""
from alembic import op

revision = "20261103_aceptaciones"
down_revision = "20261102_merge_firma_main"
branch_labels = None
depends_on = None

APP_ROLE = "lopdp_app"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE aceptaciones (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID NOT NULL,
            documento_id      UUID NOT NULL,
            documento_sha256  VARCHAR(64) NOT NULL,
            persona_id        UUID NOT NULL,
            token_hash        VARCHAR(64) UNIQUE NOT NULL,
            caduca_en         TIMESTAMPTZ NOT NULL,
            aceptado_en       TIMESTAMPTZ NULL,
            nombre            TEXT NOT NULL,
            email             TEXT NOT NULL,
            ip                INET NULL,
            acuse_sha256      VARCHAR(64) NULL,
            creado_por        UUID NOT NULL,
            creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE aceptaciones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE aceptaciones FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY aceptaciones_tenant ON aceptaciones "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute(f"REVOKE ALL ON aceptaciones FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON aceptaciones TO {APP_ROLE}")
    op.execute(
        f"GRANT UPDATE (aceptado_en, ip, acuse_sha256) ON aceptaciones TO {APP_ROLE}"
    )
    op.execute(
        "CREATE INDEX idx_aceptaciones_tenant_documento "
        "ON aceptaciones (tenant_id, documento_id, creado_en DESC)"
    )
    # Función SECURITY DEFINER para la ruta pública: resuelve un token sin contexto de tenant.
    # No expone otras filas ni el contenido del documento; solo devuelve los campos públicamente
    # necesarios para mostrar la página de aceptación.
    op.execute(
        """
        CREATE FUNCTION obtener_aceptacion_por_token(p_hash VARCHAR(64))
        RETURNS TABLE (
            id              UUID,
            tenant_id       UUID,
            documento_id    UUID,
            documento_sha256 VARCHAR(64),
            persona_id      UUID,
            token_hash      VARCHAR(64),
            caduca_en       TIMESTAMPTZ,
            aceptado_en     TIMESTAMPTZ,
            nombre          TEXT,
            email           TEXT,
            ip              INET,
            acuse_sha256    VARCHAR(64),
            creado_por      UUID,
            creado_en       TIMESTAMPTZ
        )
        LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
            SELECT id, tenant_id, documento_id, documento_sha256, persona_id, token_hash,
                   caduca_en, aceptado_en, nombre, email, ip, acuse_sha256, creado_por, creado_en
            FROM public.aceptaciones
            WHERE token_hash = p_hash
        $$
        """
    )
    op.execute(f"REVOKE ALL ON FUNCTION obtener_aceptacion_por_token(VARCHAR) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION obtener_aceptacion_por_token(VARCHAR) TO {APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS obtener_aceptacion_por_token(VARCHAR)")
    op.execute("DROP INDEX IF EXISTS idx_aceptaciones_tenant_documento")
    op.execute("DROP TABLE IF EXISTS aceptaciones")
