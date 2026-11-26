# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""BIB-415: lectura de la biblioteca para la sincronización de avisos.

Revision ID: 20261126_bib415_lectura_avisos
Revises: 20261125_bib406_propuestas_ia (cabeza de la sala `biblioteca`)

Dos funciones `STABLE SECURITY DEFINER` de solo lectura (R2), del dueño de las tablas y con `EXECUTE` solo
para `lopdp_app`. Saltan las políticas `bib_version_lectura` y `bib_cap_propia` para que NOTIF-02 vea, sin
capacidades, las versiones `en_revision` y a los revisores técnicos vigentes; devuelven solo los campos de
R1: ni cuerpo ni texto ni motivos ni datos de quién concedió.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261126_bib415_lectura_avisos"
down_revision: Union[str, Sequence[str], None] = "20261125_bib406_propuestas_ia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERSIONES_EN_REVISION = """
    CREATE OR REPLACE FUNCTION biblioteca_versiones_en_revision()
    RETURNS TABLE (id varchar, codigo varchar, titulo varchar, redactada_por varchar, origen_ia varchar,
                   id_resolucion varchar, creada_en timestamptz)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        SELECT v.id, v.codigo, c.nombre, v.redactada_por, v.origen_ia, v.id_resolucion, v.creada_en
        FROM public.biblioteca_versiones v
        JOIN public.biblioteca_catalogo c ON c.codigo = v.codigo
        WHERE v.estado = 'en_revision'
        ORDER BY v.creada_en, v.id
    $$;
"""

REVISORES_TECNICOS = """
    CREATE OR REPLACE FUNCTION biblioteca_revisores_tecnicos()
    RETURNS TABLE (usuario_id varchar)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        SELECT k.usuario_id
        FROM public.biblioteca_capacidades k
        WHERE k.capacidad = 'revisor_tecnico' AND k.revocada_en IS NULL
        ORDER BY k.usuario_id
    $$;
"""

PERMISOS = """
    REVOKE ALL ON FUNCTION biblioteca_versiones_en_revision() FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_versiones_en_revision() TO lopdp_app;
    REVOKE ALL ON FUNCTION biblioteca_revisores_tecnicos() FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_revisores_tecnicos() TO lopdp_app;
"""


def upgrade() -> None:
    op.execute(VERSIONES_EN_REVISION)
    op.execute(REVISORES_TECNICOS)
    op.execute(PERMISOS)


def downgrade() -> None:
    op.execute("""
        DROP FUNCTION IF EXISTS biblioteca_revisores_tecnicos();
        DROP FUNCTION IF EXISTS biblioteca_versiones_en_revision();
    """)
