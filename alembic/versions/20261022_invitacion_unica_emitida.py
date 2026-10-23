"""Una sola invitación emitida por organización y comprobación de administrador activo (ORG-11).

Revision ID: 20261022_invitacion_unica
Revises: 20261022_plataforma_operadores

1. Los duplicados históricos se corrigen antes de crear el índice: por cada organización se
   conserva como ``emitida`` la fila más reciente (created_at, id) y las demás se revocan con
   una identidad explícita de migración.
2. Índice único parcial: una sola invitación ``emitida`` por organización.
3. ``fn_tenant_tiene_admin_activo(tenant)``: el operador nunca fija tenant (ORG-09), y con
   ``lopdp_app`` el RLS de ``user_tenant_roles`` le oculta todas las filas, así que no puede
   saber por sí mismo si una organización ya tiene administrador. La función, ``SECURITY
   DEFINER`` como ``fn_utr_dpo_sod``, devuelve solo un booleano: no expone ningún dato.

El identificador de revisión cabe en ``alembic_version.version_num`` (32 caracteres).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261022_invitacion_unica"
down_revision: Union[str, None] = "20261022_plataforma_operadores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        WITH duplicadas AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY tenant_id
                       ORDER BY created_at DESC, id DESC
                   ) AS posicion
            FROM invitaciones_organizacion
            WHERE estado = 'emitida'
        )
        UPDATE invitaciones_organizacion invitacion
        SET estado = 'revocada',
            revoked_at = COALESCE(invitacion.revoked_at, NOW()),
            revoked_by = COALESCE(
                invitacion.revoked_by,
                'migracion:invitacion_unica_emitida'
            )
        FROM duplicadas
        WHERE invitacion.id = duplicadas.id
          AND duplicadas.posicion > 1
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_invitacion_emitida_por_tenant
        ON invitaciones_organizacion (tenant_id)
        WHERE estado = 'emitida'
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_tenant_tiene_admin_activo(p_tenant_id VARCHAR)
        RETURNS BOOLEAN
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
            SELECT EXISTS (
                SELECT 1
                FROM user_tenant_roles utr
                JOIN users u ON u.id = utr.user_id
                WHERE utr.tenant_id = p_tenant_id
                  AND utr.role = 'admin_organizacion'
                  AND (utr.valid_to IS NULL OR utr.valid_to > NOW())
                  AND u.activo
                  AND u.deleted_at IS NULL
            )
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION fn_tenant_tiene_admin_activo(VARCHAR) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION fn_tenant_tiene_admin_activo(VARCHAR) TO lopdp_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS fn_tenant_tiene_admin_activo(VARCHAR)")
    op.execute("DROP INDEX IF EXISTS uq_invitacion_emitida_por_tenant")
