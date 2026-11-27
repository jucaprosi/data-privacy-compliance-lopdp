# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""BIB-411: capacidades editoriales para operadores activos.

Revision ID: 20261125_bib411_operadores
Revises: 20261126_bib415_lectura_avisos (cabeza de la sala `biblioteca`)

- Tres capacidades (`editor`, `revisor_tecnico`, `publicador`) y revisiones de tipo `tecnica` (R6).
- `lopdp_app` sigue sin privilegios sobre `biblioteca_capacidades`: escribe y lee por cinco funciones plpgsql
  `SECURITY DEFINER` con `search_path` fijo y `EXECUTE` solo para `lopdp_app`. Las de escritura toman el actor
  de `app.current_user_id`, vuelven a validar la autoconcesión y el motivo (al menos 10 caracteres sin espacios
  al borde) y comprueban en la base, con `plataforma_operador_activo()` (OPE-02), que actor y destino son
  operadores activos. Las de lectura son `STABLE`.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261125_bib411_operadores"
down_revision: Union[str, Sequence[str], None] = "20261126_bib415_lectura_avisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRES_CAPACIDADES = """
    DELETE FROM biblioteca_revisiones WHERE tipo = 'juridica';
    DELETE FROM biblioteca_capacidades WHERE capacidad = 'revisor_juridico';
    ALTER TABLE biblioteca_capacidades DROP CONSTRAINT biblioteca_capacidades_capacidad_check;
    ALTER TABLE biblioteca_capacidades ADD CONSTRAINT biblioteca_capacidades_capacidad_check
        CHECK (capacidad IN ('editor','revisor_tecnico','publicador'));
    ALTER TABLE biblioteca_revisiones DROP CONSTRAINT biblioteca_revisiones_tipo_check;
    ALTER TABLE biblioteca_revisiones ADD CONSTRAINT biblioteca_revisiones_tipo_check CHECK (tipo IN ('tecnica'));
    DROP POLICY bib_revision_alta ON biblioteca_revisiones;
    CREATE POLICY bib_revision_alta ON biblioteca_revisiones FOR INSERT WITH CHECK (
        revisor_id=current_setting('app.current_user_id',true) AND tipo='tecnica'
        AND biblioteca_puede('revisor_tecnico'));
"""

CONCEDER = """
    CREATE OR REPLACE FUNCTION biblioteca_conceder_capacidad(p_destino varchar, p_capacidad varchar, p_motivo text)
    RETURNS varchar
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    DECLARE
        v_actor varchar := current_setting('app.current_user_id', true);
        v_motivo text := btrim(coalesce(p_motivo, ''));
        v_revocada timestamptz;
        v_existe boolean;
    BEGIN
        IF p_capacidad IS NULL OR p_capacidad NOT IN ('editor','revisor_tecnico','publicador') THEN
            RAISE EXCEPTION 'BIB_CAPACIDAD_INVALIDA' USING ERRCODE = '22023';
        END IF;
        IF coalesce(v_actor, '') = '' OR v_actor = p_destino THEN
            RAISE EXCEPTION 'BIB_AUTOCONCESION' USING ERRCODE = '42501';
        END IF;
        IF length(v_motivo) < 10 THEN
            RAISE EXCEPTION 'BIB_MOTIVO_OBLIGATORIO' USING ERRCODE = '22023';
        END IF;
        IF NOT coalesce(public.plataforma_operador_activo(v_actor), false) THEN
            RAISE EXCEPTION 'BIB_SOLO_OPERADORES' USING ERRCODE = '42501';
        END IF;
        IF NOT coalesce(public.plataforma_operador_activo(p_destino), false) THEN
            RAISE EXCEPTION 'BIB_DESTINO_NO_OPERADOR' USING ERRCODE = '22023';
        END IF;
        SELECT true, c.revocada_en INTO v_existe, v_revocada FROM public.biblioteca_capacidades c
            WHERE c.usuario_id = p_destino AND c.capacidad = p_capacidad FOR UPDATE;
        IF v_existe IS NULL THEN
            INSERT INTO public.biblioteca_capacidades (usuario_id, capacidad, concedida_por, motivo)
                VALUES (p_destino, p_capacidad, v_actor, v_motivo);
            RETURN 'alta';
        END IF;
        IF v_revocada IS NULL THEN
            RETURN 'vigente';
        END IF;
        UPDATE public.biblioteca_capacidades
            SET concedida_por = v_actor, motivo = v_motivo, concedida_en = now(),
                revocada_en = NULL, revocada_por = NULL, motivo_revocacion = NULL
            WHERE usuario_id = p_destino AND capacidad = p_capacidad;
        RETURN 'reactivacion';
    END $$;
"""

RETIRAR = """
    CREATE OR REPLACE FUNCTION biblioteca_retirar_capacidad(p_destino varchar, p_capacidad varchar, p_motivo text)
    RETURNS varchar
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    DECLARE
        v_actor varchar := current_setting('app.current_user_id', true);
        v_motivo text := btrim(coalesce(p_motivo, ''));
        v_filas integer;
    BEGIN
        IF p_capacidad IS NULL OR p_capacidad NOT IN ('editor','revisor_tecnico','publicador') THEN
            RAISE EXCEPTION 'BIB_CAPACIDAD_INVALIDA' USING ERRCODE = '22023';
        END IF;
        IF coalesce(v_actor, '') = '' OR v_actor = p_destino THEN
            RAISE EXCEPTION 'BIB_AUTOCONCESION' USING ERRCODE = '42501';
        END IF;
        IF length(v_motivo) < 10 THEN
            RAISE EXCEPTION 'BIB_MOTIVO_OBLIGATORIO' USING ERRCODE = '22023';
        END IF;
        IF NOT coalesce(public.plataforma_operador_activo(v_actor), false) THEN
            RAISE EXCEPTION 'BIB_SOLO_OPERADORES' USING ERRCODE = '42501';
        END IF;
        IF NOT coalesce(public.plataforma_operador_activo(p_destino), false) THEN
            RAISE EXCEPTION 'BIB_DESTINO_NO_OPERADOR' USING ERRCODE = '22023';
        END IF;
        UPDATE public.biblioteca_capacidades
            SET revocada_en = now(), revocada_por = v_actor, motivo_revocacion = v_motivo
            WHERE usuario_id = p_destino AND capacidad = p_capacidad AND revocada_en IS NULL;
        GET DIAGNOSTICS v_filas = ROW_COUNT;
        RETURN CASE WHEN v_filas > 0 THEN 'revocacion' ELSE 'sin_vigente' END;
    END $$;
"""

EQUIPO = """
    CREATE OR REPLACE FUNCTION biblioteca_capacidades_equipo()
    RETURNS TABLE (usuario_id varchar, capacidad varchar)
    LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    BEGIN
        RETURN QUERY SELECT c.usuario_id, c.capacidad FROM public.biblioteca_capacidades c
            WHERE c.revocada_en IS NULL ORDER BY c.usuario_id, c.capacidad;
    END $$;
"""

HISTORIAL = """
    CREATE OR REPLACE FUNCTION biblioteca_historial_capacidades(p_usuario_id varchar)
    RETURNS TABLE (id bigint, usuario_id varchar, capacidad varchar, accion varchar, por varchar, motivo text,
                   en timestamptz)
    LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    BEGIN
        RETURN QUERY SELECT a.id, a.usuario_id, a.capacidad,
                CASE WHEN a.accion = 'revocacion' THEN 'retirada' ELSE 'concedida' END::varchar,
                a.actor_id, a.motivo, a.creada_en
            FROM public.biblioteca_auditoria_capacidades a
            WHERE a.usuario_id = p_usuario_id AND a.accion IN ('alta','reactivacion','revocacion')
            ORDER BY a.creada_en DESC, a.id DESC;
    END $$;
"""

CAMBIOS = """
    CREATE OR REPLACE FUNCTION biblioteca_cambios_capacidades(p_desde timestamptz)
    RETURNS TABLE (id bigint, usuario_id varchar, capacidad varchar, accion varchar, por varchar, motivo text,
                   en timestamptz)
    LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    BEGIN
        RETURN QUERY SELECT a.id, a.usuario_id, a.capacidad,
                CASE WHEN a.accion = 'revocacion' THEN 'retirada' ELSE 'concedida' END::varchar,
                a.actor_id, a.motivo, a.creada_en
            FROM public.biblioteca_auditoria_capacidades a
            WHERE a.creada_en > p_desde AND a.accion IN ('alta','reactivacion','revocacion')
            ORDER BY a.creada_en, a.id;
    END $$;
"""

PERMISOS = """
    REVOKE ALL ON FUNCTION biblioteca_conceder_capacidad(varchar, varchar, text) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_conceder_capacidad(varchar, varchar, text) TO lopdp_app;
    REVOKE ALL ON FUNCTION biblioteca_retirar_capacidad(varchar, varchar, text) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_retirar_capacidad(varchar, varchar, text) TO lopdp_app;
    REVOKE ALL ON FUNCTION biblioteca_capacidades_equipo() FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_capacidades_equipo() TO lopdp_app;
    REVOKE ALL ON FUNCTION biblioteca_historial_capacidades(varchar) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_historial_capacidades(varchar) TO lopdp_app;
    REVOKE ALL ON FUNCTION biblioteca_cambios_capacidades(timestamptz) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION biblioteca_cambios_capacidades(timestamptz) TO lopdp_app;
"""


def upgrade() -> None:
    op.execute(TRES_CAPACIDADES)
    for sql in (CONCEDER, RETIRAR, EQUIPO, HISTORIAL, CAMBIOS, PERMISOS):
        op.execute(sql)


def downgrade() -> None:
    op.execute("""
        DROP FUNCTION IF EXISTS biblioteca_cambios_capacidades(timestamptz);
        DROP FUNCTION IF EXISTS biblioteca_historial_capacidades(varchar);
        DROP FUNCTION IF EXISTS biblioteca_capacidades_equipo();
        DROP FUNCTION IF EXISTS biblioteca_retirar_capacidad(varchar, varchar, text);
        DROP FUNCTION IF EXISTS biblioteca_conceder_capacidad(varchar, varchar, text);
        DROP POLICY bib_revision_alta ON biblioteca_revisiones;
        CREATE POLICY bib_revision_alta ON biblioteca_revisiones FOR INSERT WITH CHECK (
            revisor_id=current_setting('app.current_user_id',true) AND
            ((tipo='tecnica' AND biblioteca_puede('revisor_tecnico')) OR
             (tipo='juridica' AND biblioteca_puede('revisor_juridico'))));
        ALTER TABLE biblioteca_revisiones DROP CONSTRAINT biblioteca_revisiones_tipo_check;
        ALTER TABLE biblioteca_revisiones ADD CONSTRAINT biblioteca_revisiones_tipo_check
            CHECK (tipo IN ('tecnica','juridica'));
        ALTER TABLE biblioteca_capacidades DROP CONSTRAINT biblioteca_capacidades_capacidad_check;
        ALTER TABLE biblioteca_capacidades ADD CONSTRAINT biblioteca_capacidades_capacidad_check
            CHECK (capacidad IN ('editor','revisor_tecnico','revisor_juridico','publicador'));
    """)
