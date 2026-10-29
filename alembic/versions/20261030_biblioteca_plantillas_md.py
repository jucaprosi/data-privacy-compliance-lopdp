# ¤adpa
# ¤¤developer-architect
"""BIB-109: versiones maestras en Markdown (formato MD) y lectura de publicadas por miembros.

No edita la migración de BIB-105: amplía sus restricciones y reemplaza el disparador de versiones con
la regla «archivo o cuerpo». No concede privilegios nuevos a lopdp_app ni carga ni publica plantillas.
"""
from alembic import op

revision = "20261030_bib_plantillas_md"
down_revision = "20261029_org_datos_documentales"
branch_labels = None
depends_on = None

# Cuerpo del disparador de BIB-105 tal como queda tras sus correcciones; el de BIB-109 solo cambia
# los dos puntos marcados (publicación completa e integridad del cuerpo).
_DISPARADOR = """
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
_INCOMPLETA_BIB105 = "NEW.archivo IS NULL OR NEW.sha256 IS NULL OR NEW.ficha IS NULL"
# BIB-109: un maestro DOCX/XLSX exige archivo; uno MD exige cuerpo. Ambos, huella y ficha.
_INCOMPLETA_BIB109 = ("NEW.sha256 IS NULL OR NEW.ficha IS NULL\n"
                      "                           OR (NEW.formato='MD' AND NEW.cuerpo_md IS NULL)\n"
                      "                           OR (NEW.formato<>'MD' AND NEW.archivo IS NULL)")
_INTEGRIDAD_CUERPO = """
            IF NEW.cuerpo_md IS NOT NULL
               AND NEW.sha256 IS DISTINCT FROM encode(sha256(convert_to(NEW.cuerpo_md,'UTF8')),'hex') THEN
                RAISE EXCEPTION 'BIB_INTEGRIDAD_INVALIDA' USING ERRCODE='23514';
            END IF;"""

# Borra las restricciones sin nombre explícito de BIB-105/BIB-108 (formato y coherencia del archivo),
# localizándolas por su definición. SQL literal: sin valores interpolados desde Python.
_BORRAR_CHECKS = """
        DO $$
        DECLARE tabla regclass; nombre text;
        BEGIN
            FOR tabla, nombre IN SELECT conrelid::regclass, conname FROM pg_constraint
                WHERE contype='c' AND (
                    (conrelid='public.biblioteca_versiones'::regclass
                     AND (pg_get_constraintdef(oid) LIKE '%XLSX%'
                          OR pg_get_constraintdef(oid) LIKE '%nombre_archivo IS NULL%'))
                    OR (conrelid='public.biblioteca_catalogo'::regclass
                        AND pg_get_constraintdef(oid) LIKE '%XLSX%'))
            LOOP
                EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', tabla, nombre);
            END LOOP;
        END $$;
"""


# ¤adpa
def upgrade() -> None:
    op.execute("""
        ALTER TABLE biblioteca_versiones
            ADD COLUMN cuerpo_md text CHECK (cuerpo_md IS NULL OR length(cuerpo_md) BETWEEN 1 AND 200000);
    """)
    op.execute(_BORRAR_CHECKS)
    op.execute("""
        ALTER TABLE biblioteca_versiones
            ADD CONSTRAINT bib_version_formato CHECK (formato IN ('DOCX','XLSX','MD')),
            ADD CONSTRAINT bib_version_contenido CHECK (
                (formato IN ('DOCX','XLSX') AND cuerpo_md IS NULL
                 AND ((archivo IS NULL AND sha256 IS NULL AND nombre_archivo IS NULL)
                   OR (archivo IS NOT NULL AND sha256 IS NOT NULL AND nombre_archivo IS NOT NULL)))
                OR (formato='MD' AND archivo IS NULL AND nombre_archivo IS NULL
                    AND (cuerpo_md IS NULL) = (sha256 IS NULL)));
        ALTER TABLE biblioteca_catalogo
            ADD CONSTRAINT bib_catalogo_formato CHECK (formato IS NULL OR formato IN ('DOCX','XLSX','MD'));
    """)
    op.execute(_DISPARADOR.replace("__PUBLICACION_INCOMPLETA__", _INCOMPLETA_BIB109)
               .replace("__INTEGRIDAD_CUERPO__", _INTEGRIDAD_CUERPO))
    # Lectura de publicadas: miembro activo de la organización fijada en la sesión, sin capacidad editorial.
    # Invoker: user_tenant_roles conserva su RLS por organización.
    op.execute("""
        CREATE FUNCTION biblioteca_miembro_activo() RETURNS boolean
        LANGUAGE sql STABLE SET search_path=pg_catalog,public AS $$
            SELECT EXISTS (
                SELECT 1 FROM public.user_tenant_roles r JOIN public.users u ON u.id=r.user_id
                WHERE r.user_id=current_setting('app.current_user_id',true)
                  AND r.tenant_id=current_setting('app.current_tenant_id',true)
                  AND (r.valid_to IS NULL OR r.valid_to > now())
                  AND u.activo AND u.deleted_at IS NULL
            )
        $$;
        REVOKE ALL ON FUNCTION biblioteca_miembro_activo() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION biblioteca_miembro_activo() TO lopdp_app;
        CREATE POLICY bib_version_publicada_miembro ON biblioteca_versiones FOR SELECT
            USING (estado='publicada' AND biblioteca_miembro_activo());
        CREATE POLICY bib_catalogo_publicado_miembro ON biblioteca_catalogo FOR SELECT
            USING (biblioteca_miembro_activo() AND EXISTS (
                SELECT 1 FROM biblioteca_versiones v
                WHERE v.codigo=biblioteca_catalogo.codigo AND v.estado='publicada'));
    """)


# ¤adpa
def downgrade() -> None:
    # Solo ramas de desarrollo: se niega si quedan versiones o catálogo en formato MD.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM public.biblioteca_versiones WHERE formato='MD')
               OR EXISTS (SELECT 1 FROM public.biblioteca_catalogo WHERE formato='MD') THEN
                RAISE EXCEPTION 'BIB_DOWNGRADE_CON_PLANTILLAS_MD';
            END IF;
        END $$;
    """)
    op.execute("DROP POLICY bib_catalogo_publicado_miembro ON biblioteca_catalogo")
    op.execute("DROP POLICY bib_version_publicada_miembro ON biblioteca_versiones")
    op.execute("DROP FUNCTION biblioteca_miembro_activo()")
    op.execute(_DISPARADOR.replace("__PUBLICACION_INCOMPLETA__", _INCOMPLETA_BIB105)
               .replace("__INTEGRIDAD_CUERPO__", ""))
    op.execute("""
        ALTER TABLE biblioteca_catalogo DROP CONSTRAINT bib_catalogo_formato;
        ALTER TABLE biblioteca_catalogo
            ADD CONSTRAINT biblioteca_catalogo_formato_check CHECK (formato IS NULL OR formato IN ('DOCX','XLSX'));
        ALTER TABLE biblioteca_versiones DROP CONSTRAINT bib_version_contenido, DROP CONSTRAINT bib_version_formato;
        ALTER TABLE biblioteca_versiones DROP COLUMN cuerpo_md;
        ALTER TABLE biblioteca_versiones
            ADD CONSTRAINT biblioteca_versiones_formato_check CHECK (formato IN ('DOCX','XLSX')),
            ADD CONSTRAINT biblioteca_versiones_check CHECK (
                (archivo IS NULL AND sha256 IS NULL AND nombre_archivo IS NULL)
                OR (archivo IS NOT NULL AND sha256 IS NOT NULL AND nombre_archivo IS NOT NULL));
    """)
