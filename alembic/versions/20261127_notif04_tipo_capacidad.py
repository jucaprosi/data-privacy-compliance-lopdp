# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤backend-developer ¤notificaciones
"""NOTIF-04 · el aviso de concesiones y retiros de capacidades editoriales admite su tipo.

Revision ID: notif04_tipo_capacidad
Revises: notif02_avisos (cabeza de la rama «notificaciones»)

Contrato: governance/especificaciones/NOTIF-04.md §1. Solo rehace el CHECK de `avisos_plataforma.tipo`; sin tablas nuevas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "notif04_tipo_capacidad"
down_revision: Union[str, Sequence[str], None] = "notif02_avisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE avisos_plataforma DROP CONSTRAINT avisos_plataforma_tipo_check;
        ALTER TABLE avisos_plataforma ADD CONSTRAINT avisos_plataforma_tipo_check
            CHECK (tipo IN ('version_por_revisar', 'capacidad_editorial'));
    """)


def downgrade() -> None:
    # La tabla tiene RLS forzada: el dueño solo ve filas con la política, así que se suspende mientras se borra.
    op.execute("""
        ALTER TABLE avisos_plataforma NO FORCE ROW LEVEL SECURITY;
        DELETE FROM avisos_plataforma WHERE tipo = 'capacidad_editorial';
        ALTER TABLE avisos_plataforma FORCE ROW LEVEL SECURITY;
        ALTER TABLE avisos_plataforma DROP CONSTRAINT avisos_plataforma_tipo_check;
        ALTER TABLE avisos_plataforma ADD CONSTRAINT avisos_plataforma_tipo_check
            CHECK (tipo IN ('version_por_revisar'));
    """)
