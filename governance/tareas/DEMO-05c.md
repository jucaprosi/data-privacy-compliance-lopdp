+++
id = "DEMO-05c"
titulo = "Purga de la demo con políticas explícitas por rol, sin BYPASSRLS, y guardia que falla cerrada si falta alguna"
ola = "backlog"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-05", "SEC-20"]
propiedad = ["jobs/purga_demo/politicas_purga.sql", "jobs/purga_demo/guardias.py", "jobs/purga_demo/__main__.py", "governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md", "tests/test_demo05c_politicas_purga.py"]
crea = ["jobs/purga_demo/politicas_purga.sql", "tests/test_demo05c_politicas_purga.py"]
arbitro = "pytest tests/test_demo05c_politicas_purga.py contra la PostgreSQL efímera del CI (sin producción ni Cloud SQL): aplica todas las migraciones y politicas_purga.sql, siembra el marcador demo, un tenant demo, la plantilla y un tenant no demo; la guardia devuelve vacío; como purga_demo borra el tenant demo y no ve ni borra la plantilla ni el tenant no demo; con el marcador en pruebas o sin marcador no ve nada; demo_sesiones solo acepta UPDATE que pongan a NULL; rolbypassrls es false; mutaciones documentadas: crear una tabla con tenant_id sin ejecutar el SQL hace que la guardia la nombre y la purga falle antes de borrar; quitar la exclusión de la plantilla hace caer su prueba"
rastros = ["¤demo"]
+++

# DEMO-05c · Purga de la demo con políticas explícitas por rol

Diseño del Arquitecto ADPA (2026-11-12) por decisión del CTO: **política explícita, sin `BYPASSRLS`**. Es el paso 5 del brief del propietario de DEMO-05. Medido sobre `origin/main` leyendo `jobs/purga_demo/purga.py`, `features/demo/domain/plantilla.py` y `BRIEF_PROPIETARIO_DEMO05.md`. **El SQL no se ha ejecutado**: lo valida la prueba de esta ficha en la PostgreSQL efímera del CI antes de llegar al brief.

## Principios
1. Las políticas son `TO purga_demo` y nada más; las de los demás roles no cambian.
2. **Cada política exige el marcador `demo`** (`entorno_marcador.valor = 'demo'`): si el rol existiera en otra base o el marcador cambiara, no ve ni borra nada (falla cerrado, independiente de la guardia del Job).
3. La plantilla `demo-plantilla-cooperativa` queda fuera **en la base**, no solo en el código.
4. `tenants` usa sus propias columnas (sin subconsulta sobre sí misma, para evitar la recursión de políticas); el resto de tablas con `tenant_id` pregunta a `tenants`, que el rol ve solo por su política.
5. Hacen falta las dos políticas, SELECT y DELETE (el `WHERE` y el conteo de comprobación leen filas).

## Entrega
1. **`jobs/purga_demo/politicas_purga.sql`** (nuevo, versionado e idempotente; el brief lo pega tal cual): marcador solo lectura; `tenants` con `es_demo AND id::text <> 'demo-plantilla-cooperativa'` y el marcador, SELECT y DELETE; `demo_sesiones` con `GRANT SELECT, UPDATE (persona_usuario_id, tenant_id), DELETE`, UPDATE con `WITH CHECK (persona_usuario_id IS NULL AND tenant_id IS NULL)` y DELETE solo de las `estado = 'vencida'`; y, para cada otra tabla con `tenant_id`, `GRANT SELECT, DELETE` y políticas `tenant_id::text IN (SELECT id::text FROM public.tenants)` (hereda la exclusión de la plantilla). `users` espera a DEMO-05b: hasta entonces no hay GRANT sobre `users`. Las acciones `ON DELETE SET NULL` y `CASCADE` las ejecuta PostgreSQL como dueño de la tabla y no necesitan políticas del rol.
2. **Guardia `faltan_politicas(con)`** en `jobs/purga_demo/guardias.py`, llamada desde `__main__.py` antes de `purgar`: compara `tablas_con_tenant(con) ∪ {tenants, demo_sesiones}` con `pg_policies WHERE 'purga_demo' = ANY(roles)`, exigiendo `select` y `delete` por tabla. Si falta alguna, el Job sale con 1 («faltan políticas de purga en: X; ejecuta politicas_purga.sql») y no borra ni objetos ni filas (esa salida ya la vigila la alerta del Job).
3. **Prueba en el CI**, `tests/test_demo05c_politicas_purga.py`, con la PostgreSQL efímera (sin producción ni Cloud SQL), con los casos y mutaciones del árbitro. También atrapa en el CI una migración nueva que rompa el SQL (por ejemplo, un `tenant_id` sin cast a texto).
4. **Paso 5 del brief** `BRIEF_PROPIETARIO_DEMO05.md`: ejecutar `politicas_purga.sql` después de cada migración aplicada a la base de la demo (la guardia lo recuerda) y la comprobación de solo lectura de abajo.
- Se descarta la «migración condicionada al rol»: obliga a cada autora de migración a acordarse y ejecutaría DDL de la demo desde la cadena de Alembic que también corre en producción.

## Lo que debe confirmar la ficha antes de escribir el SQL
- Qué tablas tienen RLS activada y forzada (donde no la tienen, las políticas no hacen nada y basta el GRANT); que `entorno_marcador.valor` se llama así; que `demo_sesiones.estado` admite `'vencida'`.
- **Hallazgo de la sesión de DEMO-02 que este diseño no cubre y hay que resolver aquí o en otra ficha:** con datos reales de biblioteca la purga falla con `no se pudo vaciar por claves foráneas: biblioteca_documentos, biblioteca_documentos_historial`, porque `biblioteca_documentos_historial`, `biblioteca_eventos_documento` y `biblioteca_descargas` tienen triggers `BEFORE DELETE OR UPDATE` que lanzan siempre `BIB_HISTORIAL_INMUTABLE`, y `biblioteca_documentos` no se borra mientras existan sus filas de historial. Las políticas de RLS no desactivan esos triggers. Propuesta de la sesión (a decidir por el Arquitecto): `SET LOCAL session_replication_role = replica` por transacción de tenant (en PostgreSQL 15 o más, `GRANT SET ON PARAMETER session_replication_role TO purga_demo`; a confirmar que Cloud SQL lo permite) o un rol dueño de las tablas con `ALTER TABLE ... DISABLE TRIGGER`. Mientras no haya decisión, esta ficha no debe prometer que la purga vacía la biblioteca.

## Comprobación de solo lectura para el propietario (base de la demo, con el usuario administrador)
Marcador `demo` (una fila); `pg_roles` de `purga_demo` sin privilegios especiales (`rolsuper`, `rolbypassrls`, `rolcreaterole`, `rolcreatedb` en false); ninguna tabla con `tenant_id` sin sus dos políticas (0 filas); privilegios de tabla solo `SELECT` y `DELETE` más el `UPDATE` de dos columnas de `demo_sesiones` (`information_schema.column_privileges` solo debe listar `persona_usuario_id` y `tenant_id`); con `SET ROLE purga_demo` la plantilla no aparece (si `SET ROLE` no está permitido, se salta y se dice); en producción y en pruebas, `SELECT count(*) FROM pg_roles WHERE rolname = 'purga_demo'` da 0. El propietario pega las salidas, sin la contraseña, al Tech Lead.

## Nota de orden (Tech Lead)
DEMO-05 sigue `en_curso` hasta que el propietario ejecute sus briefs, y es dueña entera de `jobs/purga_demo/**`; este paso 5 sale de esta ficha, así que antes de lanzarla hay que decidir con el CTO si DEMO-05 (cuyo código ya está en main) pasa a `hecha` con el brief como pendiente del propietario, o si DEMO-05c toma las secciones que corresponda.

**Contenido de partida verificado (2026-11-12, Arquitecto):** el SQL del paso 5 de este diseño se probó en una PostgreSQL 16 desechable: idempotente, la plantilla y los tenants no demo son invisibles para `purga_demo`, sin marcador ve 0 filas, no puede insertar, y `lopdp_app` queda sin cambios. Incluye una precondición (el marcador debe devolver exactamente una fila `demo`; si no, parar) y una comprobación final adicional (las políticas `purga_demo_%` son solo de `purga_demo`: `SELECT count(*) FROM pg_policies WHERE policyname LIKE 'purga_demo_%' AND roles <> '{purga_demo}'` da 0). El ingeniero que lo escriba parte del bloque de esta ficha y lo vuelve a validar en la prueba del CI; el archivo de trabajo del Arquitecto queda fuera del repositorio.
