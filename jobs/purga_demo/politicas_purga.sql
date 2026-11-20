-- ¤demo ¤seguridad
-- DEMO-05c · Permisos y políticas del rol `purga_demo`, sin BYPASSRLS (PRD EVYDENTIA §5.6.4, invariantes 60 a 63).
--
-- Lo ejecuta el propietario en la base de la DEMO tras cada migración (paso 5 de
-- governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md):
--   psql --single-transaction -v ON_ERROR_STOP=1 -f jobs/purga_demo/politicas_purga.sql
-- No entra en Alembic, no crea el rol, no activa la RLS de ninguna tabla y no toca las políticas de otros
-- roles. Es idempotente: cada ejecución deja los mismos permisos y las mismas políticas.
--
-- Reglas (governance/especificaciones/DEMO-05c.md §3):
--   R1  todas las políticas son `TO purga_demo`; ninguna es `USING (true)`.
--   R2  cada política exige el marcador `demo` en public.entorno_marcador.
--   R4  tablas con `tenant_id`: GRANT SELECT, DELETE; con RLS, políticas acotadas a los tenants visibles.
--   R5  demo_sesiones por columnas, sin vendedor_sub ni vendedor_email; nunca INSERT ni UPDATE.
--   R6  users solo SELECT (id) y DELETE; el correo lo consulta únicamente es_persona_ficticia.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'purga_demo') THEN
    RAISE EXCEPTION 'falta el rol purga_demo: créalo antes (paso 5 del brief del propietario de DEMO-05)';
  END IF;
  IF to_regclass('public.entorno_marcador') IS NULL THEN
    RAISE EXCEPTION 'falta public.entorno_marcador: esta base no tiene marcador de entorno';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO purga_demo;
REVOKE ALL ON public.entorno_marcador FROM purga_demo;
GRANT SELECT ON public.entorno_marcador TO purga_demo;

-- R7 · Única puerta al correo: devuelve un booleano, nunca el correo.
-- [es_persona_ficticia]
CREATE OR REPLACE FUNCTION public.es_persona_ficticia(p_user_id character varying)
  RETURNS boolean
  LANGUAGE sql STABLE SECURITY DEFINER
  SET search_path = pg_catalog, public
AS $fn$
  SELECT EXISTS (SELECT 1 FROM public.entorno_marcador WHERE valor = 'demo')
     AND EXISTS (SELECT 1 FROM public.users u WHERE u.id = p_user_id AND u.email LIKE '%.invalid');
$fn$;
-- [/es_persona_ficticia]
REVOKE ALL ON FUNCTION public.es_persona_ficticia(character varying) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.es_persona_ficticia(character varying) TO purga_demo;

DO $$
DECLARE
  marcador CONSTANT text := 'EXISTS (SELECT 1 FROM public.entorno_marcador WHERE valor = ''demo'')';
  t record;
BEGIN
  -- R4 · Todas las tablas con `tenant_id`, salvo tenants y demo_sesiones (catálogo, no information_schema).
  -- Orden de bloqueos: políticas (AccessExclusiveLock) antes que REVOKE/GRANT (tupla en pg_class) para no
  -- cruzarse en interbloqueo con autovacuum (VACUUM ANALYZE actualiza pg_class al cerrar su bloqueo).
  FOR t IN
    SELECT c.relname, c.relrowsecurity
      FROM pg_class c
      JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND a.attnum > 0 AND NOT a.attisdropped
     WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p')
       AND c.relname NOT IN ('tenants', 'demo_sesiones')
     ORDER BY c.relname
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS purga_demo_select ON public.%I', t.relname);
    EXECUTE format('DROP POLICY IF EXISTS purga_demo_delete ON public.%I', t.relname);
    IF t.relrowsecurity THEN
      EXECUTE format('CREATE POLICY purga_demo_select ON public.%I AS PERMISSIVE FOR SELECT TO purga_demo '
                     'USING (%s AND tenant_id::text IN (SELECT id::text FROM public.tenants))', t.relname, marcador);
      EXECUTE format('CREATE POLICY purga_demo_delete ON public.%I AS PERMISSIVE FOR DELETE TO purga_demo '
                     'USING (%s AND tenant_id::text IN (SELECT id::text FROM public.tenants))', t.relname, marcador);
    END IF;
    EXECUTE format('REVOKE ALL ON public.%I FROM purga_demo', t.relname);
    EXECUTE format('GRANT SELECT, DELETE ON public.%I TO purga_demo', t.relname);
  END LOOP;

  -- Las políticas permisivas se combinan con OR y PostgreSQL comprueba al iniciar cada sentencia el EXECUTE
  -- de toda función que aparezca en ellas, aunque no haya filas. Las políticas `TO public` de otras salas
  -- (p. ej. la biblioteca) llaman a funciones con EXECUTE solo para la aplicación: sin este GRANT, cualquier
  -- DELETE de la purga sobre esas tablas falla con «permission denied for function». Solo funciones
  -- SECURITY INVOKER (corren con los permisos de purga_demo y no le abren nada); las SECURITY DEFINER no se
  -- conceden y la guardia las nombra. Las políticas no cambian.
  FOR t IN
    SELECT DISTINCT p.oid::regprocedure::text AS firma
      FROM pg_policy pol
      JOIN pg_depend d ON d.classid = 'pg_policy'::regclass AND d.objid = pol.oid AND d.refclassid = 'pg_proc'::regclass
      JOIN pg_proc p ON p.oid = d.refobjid AND p.pronamespace = 'public'::regnamespace AND NOT p.prosecdef
      JOIN pg_class c ON c.oid = pol.polrelid AND c.relnamespace = 'public'::regnamespace
     WHERE pol.polcmd IN ('r', 'd', '*') AND 0 = ANY (pol.polroles)
       AND (c.relname IN ('tenants', 'demo_sesiones', 'users')
            OR EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'tenant_id'
                       AND a.attnum > 0 AND NOT a.attisdropped))
     ORDER BY 1
  LOOP
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO purga_demo', t.firma);
  END LOOP;

  -- Las tres tablas fijas: políticas solo si ya tienen RLS (la activa la ficha de seguridad, no esta).
  DROP POLICY IF EXISTS purga_demo_select ON public.tenants;
  DROP POLICY IF EXISTS purga_demo_delete ON public.tenants;
  IF (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.tenants'::regclass) THEN
    EXECUTE format('CREATE POLICY purga_demo_select ON public.tenants AS PERMISSIVE FOR SELECT TO purga_demo USING (%s '
                   'AND tenants.es_demo AND tenants.id <> ''demo-plantilla-cooperativa'' '
                   'AND EXISTS (SELECT 1 FROM public.demo_sesiones s WHERE s.tenant_id = tenants.id AND s.estado = ''vencida'') '
                   'AND NOT EXISTS (SELECT 1 FROM public.demo_sesiones s WHERE s.tenant_id = tenants.id AND s.estado = ''activa''))',
                   marcador);
    EXECUTE format('CREATE POLICY purga_demo_delete ON public.tenants AS PERMISSIVE FOR DELETE TO purga_demo USING (%s '
                   'AND tenants.es_demo AND tenants.id <> ''demo-plantilla-cooperativa'' '
                   'AND EXISTS (SELECT 1 FROM public.demo_sesiones s WHERE s.tenant_id = tenants.id AND s.estado = ''vencida'') '
                   'AND NOT EXISTS (SELECT 1 FROM public.demo_sesiones s WHERE s.tenant_id = tenants.id AND s.estado = ''activa''))',
                   marcador);
  END IF;

  DROP POLICY IF EXISTS purga_demo_select ON public.demo_sesiones;
  DROP POLICY IF EXISTS purga_demo_delete ON public.demo_sesiones;
  IF (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.demo_sesiones'::regclass) THEN
    EXECUTE format('CREATE POLICY purga_demo_select ON public.demo_sesiones AS PERMISSIVE FOR SELECT TO purga_demo '
                   'USING (%s)', marcador);
    EXECUTE format('CREATE POLICY purga_demo_delete ON public.demo_sesiones AS PERMISSIVE FOR DELETE TO purga_demo '
                   'USING (%s AND estado = ''vencida'' AND terminada_en < now() - interval ''90 days'')', marcador);
  END IF;

  DROP POLICY IF EXISTS purga_demo_select ON public.users;
  DROP POLICY IF EXISTS purga_demo_delete ON public.users;
  IF (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.users'::regclass) THEN
    EXECUTE format('CREATE POLICY purga_demo_select ON public.users AS PERMISSIVE FOR SELECT TO purga_demo '
                   'USING (%s)', marcador);
    EXECUTE format('CREATE POLICY purga_demo_delete ON public.users AS PERMISSIVE FOR DELETE TO purga_demo '
                   'USING (%s)', marcador);
  END IF;
END $$;

-- R6 · users: solo el identificador; jamás el correo (después de sus políticas por orden de bloqueos).
REVOKE ALL ON public.users FROM purga_demo;
GRANT SELECT (id), DELETE ON public.users TO purga_demo;

-- R5 · demo_sesiones: solo las columnas que la purga necesita.
REVOKE ALL ON public.demo_sesiones FROM purga_demo;
GRANT SELECT (id, tenant_id, estado, terminada_en, persona_usuario_id), DELETE ON public.demo_sesiones TO purga_demo;

-- R3 · tenants: el filtro de vencidos lo aplica el código mientras la tabla no tenga RLS.
REVOKE ALL ON public.tenants FROM purga_demo;
GRANT SELECT, DELETE ON public.tenants TO purga_demo;
