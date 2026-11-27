# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤notificaciones
"""NOTIF-02 · avisos de la plataforma (versiones por revisar). Primera migración de la sala «notificaciones».

Revision ID: notif02_avisos
Revises: ret02_clave_objeto (BASE_COMUN)

Contrato: governance/especificaciones/NOTIF-02.md §1. Cada persona lee y marca solo sus avisos (RLS por
`app.current_user_id`); un aviso por persona, tipo y referencia (UNIQUE).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "notif02_avisos"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"
branch_labels: Union[str, Sequence[str], None] = ("notificaciones",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE avisos_plataforma (
            id varchar(36) PRIMARY KEY,
            usuario_id varchar NOT NULL REFERENCES users(id),
            tipo varchar(40) NOT NULL CHECK (tipo IN ('version_por_revisar')),
            referencia varchar(64) NOT NULL,
            titulo varchar(300) NOT NULL,
            texto text NOT NULL,
            enlace varchar(300),
            leido_en timestamptz,
            pendiente boolean NOT NULL DEFAULT true,
            recordatorios_hechos integer NOT NULL DEFAULT 0 CHECK (recordatorios_hechos >= 0),
            proximo_recordatorio timestamptz,
            creado_en timestamptz NOT NULL DEFAULT now(),
            actualizado_en timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_avisos_usuario_tipo_referencia UNIQUE (usuario_id, tipo, referencia)
        );
        CREATE INDEX ix_avisos_usuario_creado ON avisos_plataforma (usuario_id, creado_en DESC);
        ALTER TABLE avisos_plataforma ENABLE ROW LEVEL SECURITY;
        ALTER TABLE avisos_plataforma FORCE ROW LEVEL SECURITY;
        CREATE POLICY avisos_propios_lectura ON avisos_plataforma FOR SELECT
            USING (usuario_id = current_setting('app.current_user_id', true));
        CREATE POLICY avisos_propios_alta ON avisos_plataforma FOR INSERT
            WITH CHECK (usuario_id = current_setting('app.current_user_id', true));
        CREATE POLICY avisos_propios_cambio ON avisos_plataforma FOR UPDATE
            USING (usuario_id = current_setting('app.current_user_id', true))
            WITH CHECK (usuario_id = current_setting('app.current_user_id', true));
        REVOKE ALL ON avisos_plataforma FROM PUBLIC, lopdp_app;
        GRANT SELECT, INSERT, UPDATE ON avisos_plataforma TO lopdp_app;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE avisos_plataforma;")
