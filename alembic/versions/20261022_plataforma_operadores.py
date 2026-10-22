# ¤seguridad
# ¤rbac-tenant
"""ORG-09: Migración para operadores de plataforma, invitaciones y auditoría.

Crea:
- operadores_plataforma: identificación de operadores (por correo verificado y/o google_sub).
- invitaciones_organizacion: invitaciones para el administrador inicial de cada organización.
- auditoria_plataforma: registro de auditoría append-only para acciones de la plataforma.

Down-revision: 20261021_sec10_sin_delete
Permisos: GRANT SELECT, INSERT, UPDATE a lopdp_app (sin DELETE).
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20261022_plataforma_operadores"
down_revision: Union[str, None] = "20261021_sec10_sin_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. operadores_plataforma
    op.execute("""
        CREATE TABLE operadores_plataforma (
            id VARCHAR(64) PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            google_sub VARCHAR(255),
            nombre VARCHAR(255) NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uq_operadores_email ON operadores_plataforma(LOWER(email));
        CREATE UNIQUE INDEX uq_operadores_sub ON operadores_plataforma(google_sub) WHERE google_sub IS NOT NULL;
    """)

    # 2. invitaciones_organizacion
    op.execute("""
        CREATE TABLE invitaciones_organizacion (
            id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
            email VARCHAR(255) NOT NULL,
            codigo_hash VARCHAR(128) NOT NULL,
            expira_en TIMESTAMPTZ NOT NULL,
            estado VARCHAR(32) NOT NULL DEFAULT 'emitida'
                CONSTRAINT ck_invitacion_estado CHECK (estado IN ('emitida', 'aceptada', 'caducada', 'revocada')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by VARCHAR(64) NOT NULL,
            accepted_at TIMESTAMPTZ,
            accepted_by_user_id VARCHAR(64) REFERENCES users(id),
            revoked_at TIMESTAMPTZ,
            revoked_by VARCHAR(64)
        );
        CREATE UNIQUE INDEX uq_invitacion_codigo_hash ON invitaciones_organizacion(codigo_hash);
        CREATE INDEX idx_invitacion_tenant ON invitaciones_organizacion(tenant_id);
        CREATE INDEX idx_invitacion_email ON invitaciones_organizacion(LOWER(email));
    """)

    # 3. auditoria_plataforma (append-only)
    op.execute("""
        CREATE TABLE auditoria_plataforma (
            id VARCHAR(64) PRIMARY KEY,
            actor_tipo VARCHAR(32) NOT NULL,
            actor_id VARCHAR(255) NOT NULL,
            accion VARCHAR(64) NOT NULL,
            tenant_id VARCHAR(64),
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_auditoria_plataforma_tenant ON auditoria_plataforma(tenant_id);
        CREATE INDEX idx_auditoria_plataforma_actor ON auditoria_plataforma(actor_id);
        CREATE INDEX idx_auditoria_plataforma_created_at ON auditoria_plataforma(created_at);
    """)

    # Permisos para lopdp_app: SELECT, INSERT, UPDATE (sin DELETE)
    op.execute("""
        GRANT SELECT, UPDATE ON operadores_plataforma TO lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON invitaciones_organizacion TO lopdp_app;
        GRANT SELECT, INSERT ON auditoria_plataforma TO lopdp_app;
    """)


def downgrade() -> None:
    op.execute("REVOKE ALL ON auditoria_plataforma FROM lopdp_app;")
    op.execute("REVOKE ALL ON invitaciones_organizacion FROM lopdp_app;")
    op.execute("REVOKE ALL ON operadores_plataforma FROM lopdp_app;")

    op.execute("DROP TABLE IF EXISTS auditoria_plataforma CASCADE;")
    op.execute("DROP TABLE IF EXISTS invitaciones_organizacion CASCADE;")
    op.execute("DROP TABLE IF EXISTS operadores_plataforma CASCADE;")
