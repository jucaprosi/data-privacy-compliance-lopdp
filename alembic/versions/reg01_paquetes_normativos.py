# ¤regulation-code
# ¤paquete-normativo
"""REG-01: paquete normativo como dato, editable solo por el operador de la plataforma.

Tablas globales (sin tenant_id: no son datos de ningún cliente):
- paquetes_normativos: una fila por versión de un paquete (LOPDP, NIIF18); a lo sumo una publicada por código.
- parametros_normativos: plazos y demás valores, con unidad, término legal, artículo, fuente y verificación.
- requisitos_normativos, controles_comunes y requisito_control.

Permisos (Arquitecto ADPA y Seguridad, 2026-11-13):
- lopdp_app solo tiene SELECT. Nunca INSERT, UPDATE ni DELETE directos.
- Toda escritura pasa por funciones SECURITY DEFINER cuyo dueño es el rol que migra (dueño de las tablas),
  con search_path fijo y nombres calificados, sin SQL dinámico. Reciben el operador como argumento,
  comprueban que existe y está activo en operadores_plataforma y lo registran como autor.
- Las invariantes viven dentro de las funciones: un valor sin verificar no se publica (R1), una versión no
  borrador no se edita (R2), las versiones solo se agregan (no hay función de borrado), un plazo lleva unidad (R4).
- El control de quién es operador sigue en la aplicación (identidad del token verificado); la base garantiza
  qué se puede escribir y quién queda como autor.

Errores: RAISE con MESSAGE 'REG01:<CODIGO>'; la sala los traduce a ErrorNegocio.
Down-revision: la cabeza de main al implementar (FUSION_ALEMBIC).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "reg01_paquetes_normativos"
down_revision: Union[str, None] = "norm01_inteligencia_normativa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE public.paquetes_normativos (
            id VARCHAR(64) PRIMARY KEY,
            codigo VARCHAR(16) NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            version VARCHAR(16) NOT NULL,
            estado VARCHAR(10) NOT NULL DEFAULT 'borrador'
                CONSTRAINT ck_paquete_estado CHECK (estado IN ('borrador', 'publicado', 'retirado')),
            creado_por VARCHAR(64) NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            publicado_por VARCHAR(64),
            publicado_en TIMESTAMPTZ,
            retirado_en TIMESTAMPTZ,
            CONSTRAINT uq_paquete_codigo_version UNIQUE (codigo, version)
        );
        CREATE UNIQUE INDEX uq_paquete_un_publicado ON public.paquetes_normativos (codigo)
            WHERE estado = 'publicado';

        CREATE TABLE public.parametros_normativos (
            id VARCHAR(64) PRIMARY KEY,
            paquete_id VARCHAR(64) NOT NULL REFERENCES public.paquetes_normativos(id),
            clave VARCHAR(64) NOT NULL,
            valor TEXT NOT NULL,
            unidad VARCHAR(10)
                CONSTRAINT ck_parametro_unidad CHECK (unidad IS NULL OR unidad IN ('habiles', 'calendario')),
            termino_legal VARCHAR(10)
                CONSTRAINT ck_parametro_termino CHECK (termino_legal IS NULL OR termino_legal IN ('plazo', 'termino')),
            articulo TEXT NOT NULL DEFAULT '',
            fuente_url TEXT NOT NULL DEFAULT '',
            verificado BOOLEAN NOT NULL DEFAULT FALSE,
            verificado_por VARCHAR(64),
            verificado_en TIMESTAMPTZ,
            actualizado_por VARCHAR(64) NOT NULL,
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_parametro_paquete_clave UNIQUE (paquete_id, clave),
            CONSTRAINT ck_parametro_verificado_autor CHECK (
                NOT verificado OR (verificado_por IS NOT NULL AND verificado_en IS NOT NULL)
            )
        );

        CREATE TABLE public.requisitos_normativos (
            id VARCHAR(64) PRIMARY KEY,
            paquete_id VARCHAR(64) NOT NULL REFERENCES public.paquetes_normativos(id),
            codigo VARCHAR(16) NOT NULL,
            articulo TEXT NOT NULL DEFAULT '',
            texto TEXT NOT NULL,
            obligatoriedad VARCHAR(12) NOT NULL
                CONSTRAINT ck_requisito_obligatoriedad CHECK (obligatoriedad IN ('obligatorio', 'recomendado')),
            aplica_a TEXT[] NOT NULL DEFAULT '{}',
            CONSTRAINT uq_requisito_paquete_codigo UNIQUE (paquete_id, codigo)
        );

        CREATE TABLE public.controles_comunes (
            id VARCHAR(64) PRIMARY KEY,
            codigo VARCHAR(5) NOT NULL UNIQUE,
            dimension VARCHAR(3) NOT NULL,
            ponderacion NUMERIC(4, 2) NOT NULL
        );

        CREATE TABLE public.requisito_control (
            requisito_id VARCHAR(64) NOT NULL REFERENCES public.requisitos_normativos(id),
            control_id VARCHAR(64) NOT NULL REFERENCES public.controles_comunes(id),
            PRIMARY KEY (requisito_id, control_id)
        );
        """
    )

    # Operador activo: se comprueba en la tabla, nunca en un GUC que cualquier sesión puede fijar.
    op.execute(
        """
        CREATE FUNCTION public.reg01_operador_activo(p_operador VARCHAR)
        RETURNS VARCHAR
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        BEGIN
            IF p_operador IS NULL OR NOT EXISTS (
                SELECT 1 FROM public.operadores_plataforma o WHERE o.id = p_operador AND o.activo
            ) THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:NO_ES_OPERADOR';
            END IF;
            RETURN p_operador;
        END;
        $$;
        """
    )

    # Nueva versión en borrador, copia de la publicada (R2: cambiar es crear versión nueva).
    op.execute(
        """
        CREATE FUNCTION public.reg01_crear_version(p_operador VARCHAR, p_codigo VARCHAR, p_version VARCHAR)
        RETURNS VARCHAR
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE
            v_origen public.paquetes_normativos%ROWTYPE;
            v_id VARCHAR(64) := 'pqn-' || md5(random()::text || clock_timestamp()::text);
        BEGIN
            PERFORM public.reg01_operador_activo(p_operador);
            PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('reg01:' || p_codigo));
            IF p_version IS NULL OR length(trim(p_version)) = 0 THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:VERSION_REQUERIDA';
            END IF;
            IF EXISTS (SELECT 1 FROM public.paquetes_normativos p
                       WHERE p.codigo = p_codigo AND p.version = p_version) THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:VERSION_DUPLICADA';
            END IF;
            SELECT * INTO v_origen FROM public.paquetes_normativos p
             WHERE p.codigo = p_codigo AND p.estado = 'publicado';
            IF NOT FOUND THEN
                -- Sin publicada: se parte de la versión más reciente del código.
                SELECT * INTO v_origen FROM public.paquetes_normativos p
                 WHERE p.codigo = p_codigo ORDER BY p.creado_en DESC, p.id DESC LIMIT 1;
                IF NOT FOUND THEN
                    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PAQUETE_NO_ENCONTRADO';
                END IF;
            END IF;

            INSERT INTO public.paquetes_normativos (id, codigo, nombre, version, estado, creado_por)
            VALUES (v_id, v_origen.codigo, v_origen.nombre, p_version, 'borrador', p_operador);

            INSERT INTO public.parametros_normativos
                (id, paquete_id, clave, valor, unidad, termino_legal, articulo, fuente_url,
                 verificado, verificado_por, verificado_en, actualizado_por)
            SELECT 'pmn-' || md5(random()::text || x.id), v_id, x.clave, x.valor, x.unidad, x.termino_legal,
                   x.articulo, x.fuente_url, x.verificado, x.verificado_por, x.verificado_en, p_operador
              FROM public.parametros_normativos x WHERE x.paquete_id = v_origen.id;

            INSERT INTO public.requisitos_normativos
                (id, paquete_id, codigo, articulo, texto, obligatoriedad, aplica_a)
            SELECT 'rqn-' || md5(random()::text || r.id), v_id, r.codigo, r.articulo, r.texto,
                   r.obligatoriedad, r.aplica_a
              FROM public.requisitos_normativos r WHERE r.paquete_id = v_origen.id;

            INSERT INTO public.requisito_control (requisito_id, control_id)
            SELECT nuevo.id, rc.control_id
              FROM public.requisito_control rc
              JOIN public.requisitos_normativos viejo ON viejo.id = rc.requisito_id AND viejo.paquete_id = v_origen.id
              JOIN public.requisitos_normativos nuevo ON nuevo.paquete_id = v_id AND nuevo.codigo = viejo.codigo;

            RETURN v_id;
        END;
        $$;
        """
    )

    # Editar un parámetro: solo en borrador; un plazo lleva unidad; verificar deja autor y fecha.
    op.execute(
        """
        CREATE FUNCTION public.reg01_fijar_parametro(
            p_operador VARCHAR, p_paquete_id VARCHAR, p_clave VARCHAR, p_valor TEXT, p_unidad VARCHAR,
            p_termino_legal VARCHAR, p_articulo TEXT, p_fuente_url TEXT, p_verificado BOOLEAN
        )
        RETURNS VARCHAR
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE
            v_estado VARCHAR(10);
            v_id VARCHAR(64);
        BEGIN
            PERFORM public.reg01_operador_activo(p_operador);
            SELECT p.estado INTO v_estado FROM public.paquetes_normativos p WHERE p.id = p_paquete_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PAQUETE_NO_ENCONTRADO';
            END IF;
            IF v_estado <> 'borrador' THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PAQUETE_NO_BORRADOR';
            END IF;
            IF p_clave LIKE 'plazo\\_%' AND p_unidad IS NULL THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:UNIDAD_REQUERIDA';
            END IF;

            INSERT INTO public.parametros_normativos AS x
                (id, paquete_id, clave, valor, unidad, termino_legal, articulo, fuente_url,
                 verificado, verificado_por, verificado_en, actualizado_por, actualizado_en)
            VALUES ('pmn-' || md5(random()::text || clock_timestamp()::text), p_paquete_id, p_clave, p_valor,
                    p_unidad, p_termino_legal, coalesce(p_articulo, ''), coalesce(p_fuente_url, ''),
                    coalesce(p_verificado, FALSE),
                    CASE WHEN p_verificado THEN p_operador END,
                    CASE WHEN p_verificado THEN NOW() END,
                    p_operador, NOW())
            ON CONFLICT (paquete_id, clave) DO UPDATE SET
                valor = EXCLUDED.valor,
                unidad = EXCLUDED.unidad,
                termino_legal = EXCLUDED.termino_legal,
                articulo = EXCLUDED.articulo,
                fuente_url = EXCLUDED.fuente_url,
                verificado = EXCLUDED.verificado,
                verificado_por = EXCLUDED.verificado_por,
                verificado_en = EXCLUDED.verificado_en,
                actualizado_por = EXCLUDED.actualizado_por,
                actualizado_en = EXCLUDED.actualizado_en
            RETURNING x.id INTO v_id;
            RETURN v_id;
        END;
        $$;
        """
    )

    # Publicar: todo verificado (R1); la anterior pasa a retirado; autor y fecha; una sola transacción.
    op.execute(
        """
        CREATE FUNCTION public.reg01_publicar(p_operador VARCHAR, p_paquete_id VARCHAR)
        RETURNS VARCHAR
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE
            v_codigo VARCHAR(16);
            v_estado VARCHAR(10);
            v_anterior VARCHAR(16);
        BEGIN
            PERFORM public.reg01_operador_activo(p_operador);
            SELECT p.codigo INTO v_codigo FROM public.paquetes_normativos p WHERE p.id = p_paquete_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PAQUETE_NO_ENCONTRADO';
            END IF;
            -- Candado por código: dos publicaciones simultáneas se ordenan; la segunda ve el estado nuevo.
            PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('reg01:' || v_codigo));
            SELECT p.estado INTO v_estado FROM public.paquetes_normativos p WHERE p.id = p_paquete_id FOR UPDATE;
            IF v_estado <> 'borrador' THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PAQUETE_NO_BORRADOR';
            END IF;
            IF EXISTS (SELECT 1 FROM public.parametros_normativos x
                       WHERE x.paquete_id = p_paquete_id AND NOT x.verificado) THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:PARAMETRO_NO_VERIFICADO';
            END IF;
            IF EXISTS (SELECT 1 FROM public.parametros_normativos x
                       WHERE x.paquete_id = p_paquete_id AND x.clave LIKE 'plazo\\_%' AND x.unidad IS NULL) THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'REG01:UNIDAD_REQUERIDA';
            END IF;

            UPDATE public.paquetes_normativos p SET estado = 'retirado', retirado_en = NOW()
             WHERE p.codigo = v_codigo AND p.estado = 'publicado'
            RETURNING p.version INTO v_anterior;

            UPDATE public.paquetes_normativos p
               SET estado = 'publicado', publicado_por = p_operador, publicado_en = NOW()
             WHERE p.id = p_paquete_id;
            RETURN v_anterior;
        END;
        $$;
        """
    )

    # Siembra: LOPDP 1.0 y NIIF18 1.0 en borrador. Los valores llevan la palabra literal de la ley
    # (CITAS_LEGALES_VERIFICADAS.md); la unidad en días no está verificada (Código Orgánico Administrativo
    # no leído), así que nada queda verificado ni publicado: lo verifica y publica el operador (LEG-03).
    op.execute(
        """
        INSERT INTO public.paquetes_normativos (id, codigo, nombre, version, estado, creado_por)
        VALUES ('pqn-lopdp-1-0', 'LOPDP', 'Ley Orgánica de Protección de Datos Personales', '1.0',
                'borrador', 'migracion-reg01'),
               ('pqn-niif18-1-0', 'NIIF18', 'NIIF 18', '1.0', 'borrador', 'migracion-reg01');
        """
    )
    op.execute(
        """
        INSERT INTO public.parametros_normativos
            (id, paquete_id, clave, valor, unidad, termino_legal, articulo, fuente_url, verificado, actualizado_por)
        VALUES
            ('pmn-lopdp-1-0-derechos', 'pqn-lopdp-1-0', 'plazo_derechos_dias', '15', NULL, 'plazo',
             'LOPDP arts. 13 a 16 (15 días, «plazo»); art. 62 da 10 días, «término»: pendiente de verificar',
             'https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf', FALSE, 'migracion-reg01'),
            ('pmn-lopdp-1-0-encargado', 'pqn-lopdp-1-0', 'plazo_vulneracion_encargado_dias', '2', NULL, 'termino',
             'LOPDP art. 43', 'https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf', FALSE, 'migracion-reg01'),
            ('pmn-lopdp-1-0-autoridad', 'pqn-lopdp-1-0', 'plazo_vulneracion_autoridad_dias', '5', NULL, 'termino',
             'LOPDP art. 43', 'https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf', FALSE, 'migracion-reg01'),
            ('pmn-lopdp-1-0-titulares', 'pqn-lopdp-1-0', 'plazo_vulneracion_titulares_dias', '3', NULL, 'termino',
             'LOPDP art. 46', 'https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf', FALSE, 'migracion-reg01'),
            ('pmn-lopdp-1-0-autoridad-n', 'pqn-lopdp-1-0', 'autoridad', 'Pendiente de verificar', NULL, NULL,
             '', '', FALSE, 'migracion-reg01'),
            ('pmn-lopdp-1-0-canal', 'pqn-lopdp-1-0', 'canal_notificacion', 'Pendiente de verificar', NULL, NULL,
             '', '', FALSE, 'migracion-reg01');
        """
    )

    op.execute(
        """
        REVOKE ALL ON public.paquetes_normativos, public.parametros_normativos, public.requisitos_normativos, public.controles_comunes, public.requisito_control FROM lopdp_app;
        GRANT SELECT ON public.paquetes_normativos, public.parametros_normativos, public.requisitos_normativos, public.controles_comunes, public.requisito_control TO lopdp_app;
        REVOKE ALL ON FUNCTION public.reg01_operador_activo(varchar) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.reg01_operador_activo(varchar) TO lopdp_app;
        REVOKE ALL ON FUNCTION public.reg01_crear_version(varchar, varchar, varchar) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.reg01_crear_version(varchar, varchar, varchar) TO lopdp_app;
        REVOKE ALL ON FUNCTION public.reg01_fijar_parametro(varchar, varchar, varchar, text, varchar, varchar, text, text, boolean) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.reg01_fijar_parametro(varchar, varchar, varchar, text, varchar, varchar, text, text, boolean) TO lopdp_app;
        REVOKE ALL ON FUNCTION public.reg01_publicar(varchar, varchar) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION public.reg01_publicar(varchar, varchar) TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS public.reg01_publicar(varchar, varchar);
        DROP FUNCTION IF EXISTS public.reg01_fijar_parametro(varchar, varchar, varchar, text, varchar, varchar, text, text, boolean);
        DROP FUNCTION IF EXISTS public.reg01_crear_version(varchar, varchar, varchar);
        DROP FUNCTION IF EXISTS public.reg01_operador_activo(varchar);
        DROP TABLE IF EXISTS public.requisito_control;
        DROP TABLE IF EXISTS public.controles_comunes;
        DROP TABLE IF EXISTS public.requisitos_normativos;
        DROP TABLE IF EXISTS public.parametros_normativos;
        DROP TABLE IF EXISTS public.paquetes_normativos;
        """
    )
