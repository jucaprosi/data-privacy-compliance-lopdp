# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤seguridad
"""OPE-02: la plataforma expone en la base si alguien es operador activo.

Revision ID: 20261126_ope02_operador_activo (el archivo conserva el sufijo _bd: el id cabe en los 32 caracteres de alembic_version)
Revises: 20261125_ope01_operador_usuario (cabeza de la sala `plataforma`)

`plataforma_operador_activo(usuario_id varchar)` es el pasillo de la sala `plataforma` dentro de la base: las
funciones de otras salas (BIB-411) la llaman en vez de leer `operadores_plataforma`. Devuelve solo un
booleano: verdadero si existe un operador con ese `usuario_id` y `activo`; con `NULL`, falso. Se lee en cada
llamada, como `operador_activo()` de OPE-01. `SECURITY DEFINER` (la ejecuta el dueño de las tablas), sin SQL
dinámico; `EXECUTE` solo para `lopdp_app`.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261126_ope02_operador_activo"
down_revision: Union[str, Sequence[str], None] = "20261125_ope01_operador_usuario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FUNCION = """
CREATE OR REPLACE FUNCTION plataforma_operador_activo(usuario_id varchar)
RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
    IF usuario_id IS NULL THEN
        RETURN false;
    END IF;
    RETURN EXISTS (
        SELECT 1 FROM operadores_plataforma o
        WHERE o.usuario_id = plataforma_operador_activo.usuario_id AND o.activo
    );
END
$$
"""

PERMISOS = """
REVOKE ALL ON FUNCTION plataforma_operador_activo(varchar) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_operador_activo(varchar) TO lopdp_app;
"""


def upgrade() -> None:
    op.execute(FUNCION)
    op.execute(PERMISOS)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS plataforma_operador_activo(varchar)")
