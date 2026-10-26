# ¤adpa
# ¤¤developer-architect
"""BIB-105: catálogo global, permisos explícitos, maestros y auditoría sin tenant.

No asigna capacidades ni importa/publica maestros. No crea datos privados de empresa.
Los archivos maestros se conservan en bytea (máximo 10 MiB); no requieren secretos R2.
"""
from alembic import op

revision = "20261025_biblioteca_base"
down_revision = "20261025_gran_escala_obligacion"
branch_labels = None
depends_on = None


# ¤adpa
def upgrade() -> None:
    op.execute("""
        CREATE TABLE biblioteca_capacidades (
            usuario_id varchar NOT NULL REFERENCES users(id),
            capacidad varchar NOT NULL CHECK (capacidad IN
                ('editor','revisor_tecnico','revisor_juridico','publicador')),
            concedida_por varchar NOT NULL REFERENCES users(id),
            motivo text NOT NULL CHECK (length(trim(motivo)) > 0),
            concedida_en timestamptz NOT NULL DEFAULT now(),
            revocada_en timestamptz,
            revocada_por varchar REFERENCES users(id),
            motivo_revocacion text,
            PRIMARY KEY(usuario_id,capacidad),
            CHECK ((revocada_en IS NULL AND revocada_por IS NULL AND motivo_revocacion IS NULL)
                OR (revocada_en IS NOT NULL AND revocada_por IS NOT NULL
                    AND length(trim(COALESCE(motivo_revocacion,'')))>0))
        );
        CREATE TABLE biblioteca_auditoria_capacidades (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            usuario_id varchar NOT NULL,
            capacidad varchar NOT NULL,
            accion varchar NOT NULL CHECK (accion IN ('alta','revocacion','reactivacion','modificacion','baja')),
            actor_id varchar,
            rol_bd text NOT NULL,
            motivo text,
            creada_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE biblioteca_catalogo (
            codigo varchar(40) PRIMARY KEY CHECK (codigo ~ '^[A-Z][A-Z0-9-]{1,39}$'),
            creada_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE biblioteca_versiones (
            id varchar(36) PRIMARY KEY,
            codigo varchar(40) NOT NULL REFERENCES biblioteca_catalogo(codigo),
            version varchar(40) NOT NULL CHECK (version ~ '^[0-9]+[.][0-9]+([.][0-9]+)?$'),
            formato varchar NOT NULL CHECK (formato IN ('DOCX','XLSX')),
            ficha jsonb CHECK (ficha IS NULL OR jsonb_typeof(ficha)='object'),
            responsable_id varchar NOT NULL REFERENCES users(id),
            autores jsonb NOT NULL CHECK (jsonb_typeof(autores)='array' AND jsonb_array_length(autores)>0),
            estado varchar NOT NULL DEFAULT 'en_revision'
                CHECK (estado IN ('en_revision','publicada','sustituida','retirada')),
            generacion integer NOT NULL DEFAULT 1 CHECK (generacion>=1),
            archivo bytea CHECK (octet_length(archivo) BETWEEN 1 AND 10485760),
            nombre_archivo varchar(160),
            sha256 varchar(64) CHECK (sha256 ~ '^[a-f0-9]{64}$'),
            sustituye_id varchar(36) REFERENCES biblioteca_versiones(id),
            motivo text,
            creada_en timestamptz NOT NULL DEFAULT now(),
            UNIQUE(codigo,version),
            CHECK ((archivo IS NULL AND sha256 IS NULL AND nombre_archivo IS NULL)
                OR (archivo IS NOT NULL AND sha256 IS NOT NULL AND nombre_archivo IS NOT NULL))
        );
        CREATE UNIQUE INDEX biblioteca_sucesora_publicada ON biblioteca_versiones(sustituye_id)
            WHERE estado='publicada';
        CREATE UNIQUE INDEX biblioteca_codigo_publicada ON biblioteca_versiones(codigo)
            WHERE estado='publicada';
        CREATE TABLE biblioteca_revisiones (
            id varchar(36) PRIMARY KEY,
            version_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            generacion integer NOT NULL CHECK (generacion>=1),
            tipo varchar NOT NULL CHECK (tipo IN ('tecnica','juridica')),
            aprobado boolean NOT NULL,
            revisor_id varchar NOT NULL REFERENCES users(id),
            comentario text NOT NULL CHECK (length(trim(comentario))>0),
            creada_en timestamptz NOT NULL DEFAULT now(),
            UNIQUE(version_id,generacion,tipo)
        );
        CREATE TABLE biblioteca_auditoria (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            version_id varchar(36) NOT NULL REFERENCES biblioteca_versiones(id),
            actor_id varchar NOT NULL REFERENCES users(id),
            alcance varchar NOT NULL DEFAULT 'editorial_global' CHECK (alcance='editorial_global'),
            accion varchar NOT NULL,
            generacion integer NOT NULL,
            motivo text,
            creada_en timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX biblioteca_revisiones_version ON biblioteca_revisiones(version_id);
        CREATE INDEX biblioteca_auditoria_version ON biblioteca_auditoria(version_id,id);
    """)
    op.execute("""
        CREATE FUNCTION biblioteca_puede(requerida text DEFAULT NULL) RETURNS boolean
        LANGUAGE sql STABLE SET search_path=pg_catalog,public AS $$
            SELECT EXISTS (
                SELECT 1 FROM public.biblioteca_capacidades c JOIN public.users u ON u.id=c.usuario_id
                WHERE c.usuario_id=current_setting('app.current_user_id',true)
                  AND c.revocada_en IS NULL AND u.activo AND u.deleted_at IS NULL
                  AND (requerida IS NULL OR c.capacidad=requerida)
            )
        $$;
        REVOKE ALL ON FUNCTION biblioteca_puede(text) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION biblioteca_puede(text) TO lopdp_app;
    """)
    op.execute("""
        ALTER TABLE biblioteca_capacidades ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_capacidades FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_capacidades FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_capacidades TO lopdp_app;
        ALTER TABLE biblioteca_catalogo ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_catalogo FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_catalogo FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_catalogo TO lopdp_app;
        ALTER TABLE biblioteca_versiones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_versiones FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_versiones FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_versiones TO lopdp_app;
        ALTER TABLE biblioteca_revisiones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_revisiones FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_revisiones FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_revisiones TO lopdp_app;
        ALTER TABLE biblioteca_auditoria ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_auditoria FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_auditoria FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_auditoria TO lopdp_app;
        ALTER TABLE biblioteca_auditoria_capacidades ENABLE ROW LEVEL SECURITY;
        ALTER TABLE biblioteca_auditoria_capacidades FORCE ROW LEVEL SECURITY;
        REVOKE ALL ON biblioteca_auditoria_capacidades FROM PUBLIC, lopdp_app;
        GRANT SELECT ON biblioteca_auditoria_capacidades TO lopdp_app;
    """)
    op.execute("""
        CREATE POLICY bib_cap_propia ON biblioteca_capacidades FOR SELECT
            USING (usuario_id=current_setting('app.current_user_id',true));
        CREATE POLICY bib_catalogo_lectura ON biblioteca_catalogo FOR SELECT USING (biblioteca_puede());
        CREATE POLICY bib_catalogo_alta ON biblioteca_catalogo FOR INSERT WITH CHECK (biblioteca_puede('editor'));
        CREATE POLICY bib_version_lectura ON biblioteca_versiones FOR SELECT USING (biblioteca_puede());
        CREATE POLICY bib_version_alta ON biblioteca_versiones FOR INSERT
            WITH CHECK (biblioteca_puede('editor') AND responsable_id=current_setting('app.current_user_id',true));
        CREATE POLICY bib_version_cambio ON biblioteca_versiones FOR UPDATE
            USING (biblioteca_puede())
            WITH CHECK (biblioteca_puede('editor') OR biblioteca_puede('publicador'));
        CREATE POLICY bib_revision_lectura ON biblioteca_revisiones FOR SELECT USING (biblioteca_puede());
        CREATE POLICY bib_revision_alta ON biblioteca_revisiones FOR INSERT WITH CHECK (
            revisor_id=current_setting('app.current_user_id',true) AND
            ((tipo='tecnica' AND biblioteca_puede('revisor_tecnico')) OR
             (tipo='juridica' AND biblioteca_puede('revisor_juridico'))));
        CREATE POLICY bib_auditoria_lectura ON biblioteca_auditoria FOR SELECT USING (biblioteca_puede());
        CREATE POLICY bib_auditoria_alta ON biblioteca_auditoria FOR INSERT WITH CHECK (
            actor_id=current_setting('app.current_user_id',true) AND biblioteca_puede());
        CREATE POLICY bib_auditoria_cap_lectura ON biblioteca_auditoria_capacidades FOR SELECT
            USING (biblioteca_puede());
        GRANT INSERT ON biblioteca_catalogo, biblioteca_versiones, biblioteca_revisiones TO lopdp_app;
        GRANT UPDATE ON biblioteca_versiones TO lopdp_app;
    """)
    # Defensa en profundidad: no basta con omitir una comprobación Python para publicar.
    op.execute("""
        CREATE FUNCTION biblioteca_validar_version() RETURNS trigger
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
                        IF NEW.archivo IS NULL OR NEW.sha256 IS NULL OR NEW.ficha IS NULL THEN
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
            END IF;
            IF NEW.sustituye_id IS NOT NULL THEN
                SELECT * INTO anterior FROM public.biblioteca_versiones WHERE id=NEW.sustituye_id;
                IF anterior.codigo<>NEW.codigo OR anterior.id=NEW.id THEN
                    RAISE EXCEPTION 'BIB_SUSTITUCION_INVALIDA' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER bib_validar_version BEFORE INSERT OR UPDATE ON biblioteca_versiones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_validar_version();
        CREATE FUNCTION biblioteca_validar_revision() RETURNS trigger
        LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
        DECLARE v public.biblioteca_versiones;
        BEGIN
            SELECT * INTO v FROM public.biblioteca_versiones WHERE id=NEW.version_id FOR UPDATE;
            IF v.id IS NULL OR v.estado<>'en_revision' OR v.generacion<>NEW.generacion
               OR v.autores ? NEW.revisor_id THEN
                RAISE EXCEPTION 'BIB_REVISION_INVALIDA' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER bib_validar_revision BEFORE INSERT ON biblioteca_revisiones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_validar_revision();
        CREATE FUNCTION biblioteca_registrar_evento() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        BEGIN
            IF TG_TABLE_NAME='biblioteca_versiones' THEN
                INSERT INTO public.biblioteca_auditoria(version_id,actor_id,accion,generacion,motivo)
                VALUES (NEW.id,current_setting('app.current_user_id',true),
                    CASE WHEN TG_OP='INSERT' THEN 'crear'
                         WHEN NEW.estado=OLD.estado THEN 'editar' ELSE NEW.estado END,
                    NEW.generacion,NEW.motivo);
            ELSE
                INSERT INTO public.biblioteca_auditoria(version_id,actor_id,accion,generacion,motivo)
                VALUES (NEW.version_id,current_setting('app.current_user_id',true),
                        'revision_'||NEW.tipo,NEW.generacion,NEW.comentario);
            END IF;
            RETURN NEW;
        END $$;
        REVOKE ALL ON FUNCTION biblioteca_registrar_evento() FROM PUBLIC;
        CREATE TRIGGER bib_auditar_version AFTER INSERT OR UPDATE ON biblioteca_versiones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_registrar_evento();
        CREATE TRIGGER bib_auditar_revision AFTER INSERT ON biblioteca_revisiones
            FOR EACH ROW EXECUTE FUNCTION biblioteca_registrar_evento();
    """)
    # Las capacidades solo las cambia el propietario: el disparador registra también sus cambios.
    op.execute("""
        CREATE FUNCTION biblioteca_auditar_capacidad() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        BEGIN
            IF TG_OP='INSERT' THEN
                INSERT INTO public.biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id,rol_bd,motivo)
                VALUES (NEW.usuario_id,NEW.capacidad,'alta',NEW.concedida_por,session_user,NEW.motivo);
            ELSIF TG_OP='DELETE' THEN
                INSERT INTO public.biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id,rol_bd,motivo)
                VALUES (OLD.usuario_id,OLD.capacidad,'baja',NULL,session_user,NULL);
            ELSIF OLD.revocada_en IS NULL AND NEW.revocada_en IS NOT NULL THEN
                INSERT INTO public.biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id,rol_bd,motivo)
                VALUES (NEW.usuario_id,NEW.capacidad,'revocacion',NEW.revocada_por,session_user,NEW.motivo_revocacion);
            ELSIF OLD.revocada_en IS NOT NULL AND NEW.revocada_en IS NULL THEN
                INSERT INTO public.biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id,rol_bd,motivo)
                VALUES (NEW.usuario_id,NEW.capacidad,'reactivacion',NEW.concedida_por,session_user,NEW.motivo);
            ELSE
                INSERT INTO public.biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id,rol_bd,motivo)
                VALUES (NEW.usuario_id,NEW.capacidad,'modificacion',
                        COALESCE(NEW.revocada_por,NEW.concedida_por),session_user,NEW.motivo);
            END IF;
            RETURN NULL;
        END $$;
        REVOKE ALL ON FUNCTION biblioteca_auditar_capacidad() FROM PUBLIC;
        CREATE TRIGGER bib_auditar_capacidad AFTER INSERT OR UPDATE OR DELETE ON biblioteca_capacidades
            FOR EACH ROW EXECUTE FUNCTION biblioteca_auditar_capacidad();
    """)


# ¤adpa
def downgrade() -> None:
    op.execute("DROP TRIGGER bib_auditar_revision ON biblioteca_revisiones")
    op.execute("DROP TRIGGER bib_auditar_version ON biblioteca_versiones")
    op.execute("DROP TRIGGER bib_validar_revision ON biblioteca_revisiones")
    op.execute("DROP TRIGGER bib_validar_version ON biblioteca_versiones")
    op.execute("DROP FUNCTION biblioteca_registrar_evento()")
    op.execute("DROP FUNCTION biblioteca_validar_revision()")
    op.execute("DROP FUNCTION biblioteca_validar_version()")
    op.execute("DROP TABLE biblioteca_auditoria, biblioteca_revisiones, biblioteca_versiones, biblioteca_catalogo")
    # IF EXISTS: tolera esquemas aplicados antes de que se añadiera la auditoría de capacidades.
    # Antes que biblioteca_puede: su política de lectura depende de esa función.
    op.execute("DROP TRIGGER IF EXISTS bib_auditar_capacidad ON biblioteca_capacidades")
    op.execute("DROP FUNCTION IF EXISTS biblioteca_auditar_capacidad()")
    op.execute("DROP TABLE IF EXISTS biblioteca_auditoria_capacidades")
    op.execute("DROP FUNCTION biblioteca_puede(text)")
    op.execute("DROP TABLE biblioteca_capacidades")
