# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤regulation-code ¤cita-verificada
# ¤¤developer-architect
"""BIB-403 R4: la publicación pide una revisión técnica aprobada, no dos.

Redefine `biblioteca_validar_version` y solo cambia la condición de revisiones: basta una revisión
`tecnica` aprobada de la generación, por alguien que no sea autor. Nadie escribe una revisión `juridica`:
la validación normativa se deriva de las citas verificadas (BIB-403). El resto del disparador no cambia.
El `downgrade` restaura literalmente la definición de `20261030_biblioteca_plantillas_md.py`.
"""
from alembic import op

revision = "20261124_bib403_publicacion"
down_revision = "ret02_clave_objeto"  # BASE_COMUN (alembic/salas.py): primera migración de la sala biblioteca
branch_labels = ("biblioteca",)
depends_on = None

_NUEVO = """
        CREATE OR REPLACE FUNCTION biblioteca_validar_version() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        DECLARE actor text := current_setting('app.current_user_id',true);
                requerida text; anterior public.biblioteca_versiones; vigente text;
        BEGIN
            SELECT o.id INTO vigente FROM public.biblioteca_versiones o
                WHERE o.codigo=NEW.codigo AND o.estado='publicada' AND o.id<>NEW.id;
            IF TG_OP='INSERT' THEN
                IF NEW.estado<>'en_revision' OR NEW.generacion<>1 OR NOT public.biblioteca_puede('editor')
                   OR NEW.responsable_id<>actor OR NEW.autores<>jsonb_build_array(actor) THEN
                    RAISE EXCEPTION 'BIB_ALTA_DENEGADA' USING ERRCODE='23514';
                END IF;
                IF vigente IS NOT NULL AND NEW.sustituye_id IS DISTINCT FROM vigente THEN
                    RAISE EXCEPTION 'BIB_SUSTITUCION_REQUERIDA' USING ERRCODE='23514';
                END IF;
            ELSE
                IF NEW.id<>OLD.id OR NEW.codigo<>OLD.codigo OR NEW.version<>OLD.version
                   OR NEW.formato<>OLD.formato OR NEW.responsable_id<>OLD.responsable_id
                   OR NEW.sustituye_id IS DISTINCT FROM OLD.sustituye_id OR NEW.creada_en<>OLD.creada_en THEN
                    RAISE EXCEPTION 'BIB_IDENTIDAD_INMUTABLE' USING ERRCODE='23514';
                END IF;
                IF NEW.estado=OLD.estado THEN
                    IF OLD.estado<>'en_revision' OR NOT public.biblioteca_puede('editor')
                       OR NEW.generacion<>OLD.generacion+1 OR NOT NEW.autores @> OLD.autores
                       OR NOT NEW.autores ? actor THEN
                        RAISE EXCEPTION 'BIB_VERSION_INMUTABLE' USING ERRCODE='23514';
                    END IF;
                ELSE
                    IF NOT public.biblioteca_puede('publicador') OR OLD.autores ? actor
                       OR length(trim(COALESCE(NEW.motivo,'')))=0
                       OR (to_jsonb(NEW)-'estado'-'motivo') IS DISTINCT FROM (to_jsonb(OLD)-'estado'-'motivo')
                       OR NOT ((OLD.estado='en_revision' AND NEW.estado='publicada')
                            OR (OLD.estado='publicada' AND NEW.estado IN ('retirada','sustituida'))) THEN
                        RAISE EXCEPTION 'BIB_TRANSICION_DENEGADA' USING ERRCODE='23514';
                    END IF;
                    IF NEW.estado='publicada' THEN
                        IF vigente IS NOT NULL THEN
                            RAISE EXCEPTION 'BIB_SUSTITUCION_REQUERIDA' USING ERRCODE='23514';
                        END IF;
                        IF __PUBLICACION_INCOMPLETA__ THEN
                            RAISE EXCEPTION 'BIB_PUBLICACION_INCOMPLETA' USING ERRCODE='23514';
                        END IF;
                        FOREACH requerida IN ARRAY ARRAY['nombre','objetivo','fuentes','fecha_revision',
                                                       'instrucciones','dependencias','restricciones'] LOOP
                            IF length(trim(COALESCE(NEW.ficha->>requerida,'')))=0 THEN
                                RAISE EXCEPTION 'BIB_FICHA_INCOMPLETA' USING ERRCODE='23514';
                            END IF;
                        END LOOP;
                        IF (SELECT count(*) FROM public.biblioteca_revisiones r
                            WHERE r.version_id=NEW.id AND r.generacion=NEW.generacion AND r.aprobado
                              AND r.tipo='tecnica' AND NOT NEW.autores ? r.revisor_id) < 1 THEN
                            RAISE EXCEPTION 'BIB_REVISION_PENDIENTE' USING ERRCODE='23514';
                        END IF;
                    END IF;
                END IF;
            END IF;
            IF NEW.archivo IS NOT NULL AND NEW.sha256 <> encode(sha256(NEW.archivo),'hex') THEN
                RAISE EXCEPTION 'BIB_INTEGRIDAD_INVALIDA' USING ERRCODE='23514';
            END IF;__INTEGRIDAD_CUERPO__
            IF NEW.sustituye_id IS NOT NULL THEN
                SELECT * INTO anterior FROM public.biblioteca_versiones WHERE id=NEW.sustituye_id;
                IF anterior.codigo<>NEW.codigo OR anterior.id=NEW.id THEN
                    RAISE EXCEPTION 'BIB_SUSTITUCION_INVALIDA' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END $$;
"""
_ANTERIOR = """
        CREATE OR REPLACE FUNCTION biblioteca_validar_version() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        DECLARE actor text := current_setting('app.current_user_id',true);
                requerida text; anterior public.biblioteca_versiones; vigente text;
        BEGIN
            SELECT o.id INTO vigente FROM public.biblioteca_versiones o
                WHERE o.codigo=NEW.codigo AND o.estado='publicada' AND o.id<>NEW.id;
            IF TG_OP='INSERT' THEN
                IF NEW.estado<>'en_revision' OR NEW.generacion<>1 OR NOT public.biblioteca_puede('editor')
                   OR NEW.responsable_id<>actor OR NEW.autores<>jsonb_build_array(actor) THEN
                    RAISE EXCEPTION 'BIB_ALTA_DENEGADA' USING ERRCODE='23514';
                END IF;
                IF vigente IS NOT NULL AND NEW.sustituye_id IS DISTINCT FROM vigente THEN
                    RAISE EXCEPTION 'BIB_SUSTITUCION_REQUERIDA' USING ERRCODE='23514';
                END IF;
            ELSE
                IF NEW.id<>OLD.id OR NEW.codigo<>OLD.codigo OR NEW.version<>OLD.version
                   OR NEW.formato<>OLD.formato OR NEW.responsable_id<>OLD.responsable_id
                   OR NEW.sustituye_id IS DISTINCT FROM OLD.sustituye_id OR NEW.creada_en<>OLD.creada_en THEN
                    RAISE EXCEPTION 'BIB_IDENTIDAD_INMUTABLE' USING ERRCODE='23514';
                END IF;
                IF NEW.estado=OLD.estado THEN
                    IF OLD.estado<>'en_revision' OR NOT public.biblioteca_puede('editor')
                       OR NEW.generacion<>OLD.generacion+1 OR NOT NEW.autores @> OLD.autores
                       OR NOT NEW.autores ? actor THEN
                        RAISE EXCEPTION 'BIB_VERSION_INMUTABLE' USING ERRCODE='23514';
                    END IF;
                ELSE
                    IF NOT public.biblioteca_puede('publicador') OR OLD.autores ? actor
                       OR length(trim(COALESCE(NEW.motivo,'')))=0
                       OR (to_jsonb(NEW)-'estado'-'motivo') IS DISTINCT FROM (to_jsonb(OLD)-'estado'-'motivo')
                       OR NOT ((OLD.estado='en_revision' AND NEW.estado='publicada')
                            OR (OLD.estado='publicada' AND NEW.estado IN ('retirada','sustituida'))) THEN
                        RAISE EXCEPTION 'BIB_TRANSICION_DENEGADA' USING ERRCODE='23514';
                    END IF;
                    IF NEW.estado='publicada' THEN
                        IF vigente IS NOT NULL THEN
                            RAISE EXCEPTION 'BIB_SUSTITUCION_REQUERIDA' USING ERRCODE='23514';
                        END IF;
                        IF __PUBLICACION_INCOMPLETA__ THEN
                            RAISE EXCEPTION 'BIB_PUBLICACION_INCOMPLETA' USING ERRCODE='23514';
                        END IF;
                        FOREACH requerida IN ARRAY ARRAY['nombre','objetivo','fuentes','fecha_revision',
                                                       'instrucciones','dependencias','restricciones'] LOOP
                            IF length(trim(COALESCE(NEW.ficha->>requerida,'')))=0 THEN
                                RAISE EXCEPTION 'BIB_FICHA_INCOMPLETA' USING ERRCODE='23514';
                            END IF;
                        END LOOP;
                        IF (SELECT count(*) FROM public.biblioteca_revisiones r
                            WHERE r.version_id=NEW.id AND r.generacion=NEW.generacion AND r.aprobado
                              AND NOT NEW.autores ? r.revisor_id) <> 2 THEN
                            RAISE EXCEPTION 'BIB_REVISION_PENDIENTE' USING ERRCODE='23514';
                        END IF;
                    END IF;
                END IF;
            END IF;
            IF NEW.archivo IS NOT NULL AND NEW.sha256 <> encode(sha256(NEW.archivo),'hex') THEN
                RAISE EXCEPTION 'BIB_INTEGRIDAD_INVALIDA' USING ERRCODE='23514';
            END IF;__INTEGRIDAD_CUERPO__
            IF NEW.sustituye_id IS NOT NULL THEN
                SELECT * INTO anterior FROM public.biblioteca_versiones WHERE id=NEW.sustituye_id;
                IF anterior.codigo<>NEW.codigo OR anterior.id=NEW.id THEN
                    RAISE EXCEPTION 'BIB_SUSTITUCION_INVALIDA' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END $$;
"""
_INCOMPLETA_BIB109 = ("NEW.sha256 IS NULL OR NEW.ficha IS NULL\n"
                      "                           OR (NEW.formato='MD' AND NEW.cuerpo_md IS NULL)\n"
                      "                           OR (NEW.formato<>'MD' AND NEW.archivo IS NULL)")
_INTEGRIDAD_CUERPO = """
            IF NEW.cuerpo_md IS NOT NULL
               AND NEW.sha256 IS DISTINCT FROM encode(sha256(convert_to(NEW.cuerpo_md,'UTF8')),'hex') THEN
                RAISE EXCEPTION 'BIB_INTEGRIDAD_INVALIDA' USING ERRCODE='23514';
            END IF;"""


def _definicion(cuerpo: str) -> str:
    return (cuerpo.replace("__PUBLICACION_INCOMPLETA__", _INCOMPLETA_BIB109)
            .replace("__INTEGRIDAD_CUERPO__", _INTEGRIDAD_CUERPO))


# ¤adpa
def upgrade() -> None:
    op.execute(_definicion(_NUEVO))


# ¤adpa
def downgrade() -> None:
    op.execute(_definicion(_ANTERIOR))
