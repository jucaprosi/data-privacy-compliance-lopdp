# ¤¤backend-developer
"""FIRMA-03: sesiones de firma electrónica persistidas con RLS por organización. ¤firma-electronica ¤rbac-tenant

`lopdp_app` inserta y lee; solo puede actualizar las columnas con las que se registra la firma
(estado, sha256_firmado, timestamp_tsa, certificado_json, metadatos, actualizado_en). El documento,
el firmante y la organización no se reescriben, y las sesiones no se borran.

La política usa `app.current_tenant_id`, el valor que fija `fijar_contexto_rls` en todo el repo.
"""
from alembic import op

revision = "20261103_firma_sessions"
down_revision = "20261030_hallazgos"
branch_labels = None
depends_on = None

APP_ROLE = "lopdp_app"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE firma_sessions (
            firma_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id        UUID NOT NULL,
            documento_id     TEXT NOT NULL,
            firmante_id      TEXT NOT NULL,
            estado           TEXT NOT NULL CHECK (estado IN (
                                 'borrador','pendiente_firma','firmado','rechazado','error_validacion')),
            formato          TEXT NOT NULL,
            proveedor        TEXT NOT NULL,
            sha256_original  TEXT NOT NULL,
            sha256_firmado   TEXT,
            timestamp_tsa    TIMESTAMPTZ,
            certificado_json JSONB,
            metadatos        JSONB NOT NULL DEFAULT '{}',
            creado_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE firma_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE firma_sessions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY firma_sessions_tenant ON firma_sessions "
        "USING (tenant_id::text = current_setting('app.current_tenant_id', true)) "
        "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))"
    )
    op.execute(f"REVOKE ALL ON firma_sessions FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON firma_sessions TO {APP_ROLE}")
    op.execute(
        "GRANT UPDATE (estado, sha256_firmado, timestamp_tsa, certificado_json, metadatos, actualizado_en) "
        f"ON firma_sessions TO {APP_ROLE}"
    )
    op.execute(
        "CREATE INDEX idx_firma_sessions_tenant_estado "
        "ON firma_sessions (tenant_id, estado, creado_en DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_firma_sessions_tenant_estado")
    op.execute("DROP TABLE IF EXISTS firma_sessions")
