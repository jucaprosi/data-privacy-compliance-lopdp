# DEMO-05c · Purga de la demo con políticas explícitas por rol, sin BYPASSRLS
`¤sdd` `¤demo` `¤seguridad` `¤arbitro`

## 1. Datos

Sin migraciones: nada de esto entra en la cadena de Alembic, que también corre en producción. Todo lo de la base vive en `politicas_purga.sql`, que el propietario ejecuta en la base de la demo.

| Archivo | Estado final |
| :--- | :--- |
| `jobs/purga_demo/politicas_purga.sql` (nuevo) | permisos, políticas `TO purga_demo` y la función `es_persona_ficticia`; idempotente |
| `jobs/purga_demo/guardias.py` | `faltan_politicas(con) -> list[str]` y `tablas_sin_rls(con) -> list[str]` |
| `jobs/purga_demo/__main__.py` | llama a `faltan_politicas` antes de `purgar`; si devuelve algo, sale con 1 sin borrar |
| `jobs/purga_demo/purga.py` | `purgar_tenant` sin el `UPDATE demo_sesiones`; acepta un `Engine` (como hoy: abre y confirma su transacción) o una `Connection` (usa un savepoint y no confirma) |
| `jobs/purga_demo/usuarios.py` | `email LIKE '%.invalid'` sustituido por `es_persona_ficticia(users.id)`; la comprobación de sesiones cuenta solo las que tienen organización |
| `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md` | paso 5: ejecutar `politicas_purga.sql` tras cada migración de la base de la demo y las comprobaciones de solo lectura de §3 R10 |
| `tests/test_demo05c_politicas_purga.py` (nuevo) | casos de §5 |
| `tests/test_demo_purga_usuarios.py` | solo se **añaden** casos; las pruebas de DEMO-05b no se reescriben |

Hechos medidos en `origin/main` 020bc051, en el PostgreSQL 16 local migrado:
- **Cinco tablas sin RLS:** `tenants`, `demo_sesiones`, `users`, `invitaciones_organizacion` y `auditoria_plataforma` tienen `relrowsecurity = false`; las demás tablas con `tenant_id` tienen la RLS forzada. En una tabla sin RLS una política no hace nada. `demo_sesiones` no la tiene a propósito (`20261121_demo_sesiones.py`: el resolutor la lee antes de conocer el tenant).
- `demo_sesiones`: `id`, `vendedor_sub`, `vendedor_email`, `tenant_id` y `persona_usuario_id` (las dos con `ON DELETE SET NULL`), `estado` (`'activa' | 'vencida'`), `iniciada_en`, `ultima_actividad`, `terminada_en` y `motivo_fin`. Al borrar el tenant solo se vacía `tenant_id`: `persona_usuario_id` apunta a `users` y se vacía cuando se borra el usuario (medido: tras borrar el tenant, `(NULL, 'zz-u')`).
- `jobs/purga_demo/usuarios.py` borra con `AND email LIKE '%.invalid'` (línea 32) y `AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id)` (línea 34). `jobs/purga_demo/purga.py:118` hace `UPDATE demo_sesiones SET persona_usuario_id = NULL, tenant_id = NULL`.
- El marcador se lee de `public.entorno_marcador.valor`. DEMO-05, DEMO-05b y SEC-20 están hechas.

## 2. API

Sin rutas. El Job `python -m jobs.purga_demo` sale con 0 si purga, con 1 si una guardia lo rechaza (mensaje «faltan políticas de purga en: <tablas>; ejecuta politicas_purga.sql»). Las tablas sin RLS se informan aparte, con su nombre.

## 3. Reglas

- **R1 · Solo `purga_demo`, sin privilegios especiales.** Todas las políticas son `TO purga_demo`; las de los demás roles no cambian y la RLS de ninguna tabla se activa desde esta ficha. El rol tiene `rolsuper`, `rolbypassrls`, `rolcreaterole` y `rolcreatedb` en false. Ninguna política es `USING (true)`.
- **R2 · Marcador.** Cada política exige `EXISTS (SELECT 1 FROM public.entorno_marcador WHERE valor = 'demo')`, y `es_persona_ficticia` devuelve false si el marcador no es `demo`. Con otro marcador o sin marcador, `purga_demo` no ve ni borra nada en las tablas con RLS y no reconoce a ninguna persona ficticia.
- **R3 · Qué tenants se purgan.** Solo los vencidos: `es_demo`, distinto de `demo-plantilla-cooperativa`, con alguna sesión `vencida` y ninguna `activa`. Mientras `tenants` no tenga RLS, lo garantiza el código de la purga con `GRANT SELECT, DELETE`; si la tiene, también la política, que usa columnas de `tenants` y una subconsulta sobre `demo_sesiones`, nunca sobre `tenants`.
- **R4 · Tablas con `tenant_id`.** Para cada tabla con columna `tenant_id`, salvo `tenants` y `demo_sesiones`: `GRANT SELECT, DELETE`. **Con RLS**, además políticas `TO purga_demo` con `tenant_id::text IN (SELECT id::text FROM public.tenants)`, que heredan la exclusión de la plantilla y de los no vencidos. **Sin RLS**, solo el `GRANT` y el filtro por `tenant_id` del código de la purga.
- **R5 · `demo_sesiones`, por columnas.** `GRANT SELECT (id, tenant_id, estado, terminada_en, persona_usuario_id)` y `GRANT DELETE`. `vendedor_sub` y `vendedor_email` no se leen. El DELETE se limita a `estado = 'vencida' AND terminada_en < now() - interval '90 days'` (en el código; también en la política si la tabla tiene RLS). `purga_demo` nunca hace INSERT ni UPDATE.
- **R6 · `users`, sin correo.** `GRANT SELECT (id)`, `GRANT DELETE` y `EXECUTE` sobre `es_persona_ficticia`. `purga_demo` nunca tiene `SELECT` sobre `users.email` ni sobre la tabla entera.
- **R7 · `es_persona_ficticia(p_user_id)`.** En `politicas_purga.sql`, con `CREATE OR REPLACE`: `RETURNS boolean`, `LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public`. Dentro va **solo** el criterio del correo (`email LIKE '%.invalid'`) y el marcador de R2; devuelve un solo booleano y nunca el correo. Permisos: `REVOKE ALL … FROM PUBLIC` y `GRANT EXECUTE … TO purga_demo`, y nada más.
- **R8 · Reglas de `usuarios.py`.** Siguen en el código, como hoy: «sin roles restantes» y «ninguna sesión lo apunta», y esta última cuenta solo las sesiones con organización (`AND ds.tenant_id IS NOT NULL`): una sesión de una demo ya purgada no protege a nadie. Si para decidir a quién borrar hiciera falta leer el correo fuera de `es_persona_ficticia`, la sesión de ingeniería se detiene y lo informa; no se amplía el permiso.
- **R9 · Guardia que falla cerrada.** `faltan_politicas(con)` devuelve, y el Job no borra objetos ni filas, si:
  - una tabla de `tablas_con_tenant(con) ∪ {tenants, demo_sesiones, users}` **con RLS** no tiene políticas `select` y `delete` en `pg_policies WHERE 'purga_demo' = ANY(roles)`;
  - una de esas tablas **sin RLS** no tiene `GRANT SELECT, DELETE` (o, en `demo_sesiones` y `users`, sus permisos por columnas) para `purga_demo`;
  - `es_persona_ficticia` no existe o no es `SECURITY DEFINER`, o `PUBLIC` tiene `EXECUTE` sobre ella;
  - `purga_demo` tiene `SELECT` sobre `users.email`.
  `tablas_sin_rls(con)` devuelve aparte, con su nombre, las tablas sin RLS; no hacen fallar la guardia si tienen sus permisos. Una tabla nueva sin permisos sale en la lista de lo que falta.
- **R10 · Comprobación en la nube.** Si una tabla que lee `es_persona_ficticia` tuviera la RLS forzada, el dueño de la función también la sufriría salvo que tenga `BYPASSRLS`, y en Cloud SQL el usuario que migra no es superusuario. El paso 5 del brief del propietario añade comprobaciones de solo lectura que devuelven solo números o booleanos: `es_persona_ficticia` da true para al menos una persona ficticia conocida de la demo, y `faltan_politicas` da vacío. Si no, se detiene y se informa al CTO: no habrá una purga que en la nube no borre a nadie sin que se sepa.
- **R11 · Pruebas en una transacción revertida.** `CREATE ROLE purga_demo` es global en el servidor: las pruebas lo crean dentro de una transacción que se revierte (en PostgreSQL `CREATE ROLE` es transaccional y la segunda sesión espera a la primera). `purgar_tenant` con una `Connection` y `faltan_politicas` no confirman nada; las pruebas de varios pasos usan savepoints. `test_sql_idempotente` ejecuta el SQL dos veces dentro de la misma transacción. La prueba de que el Job sale con 1 (m1) llama a la función de entrada con esa conexión, no lanza un proceso aparte.
- **R12 · Triggers de inmutabilidad, fuera de esta ficha.** Las políticas no desactivan los triggers `BIB_HISTORIAL_INMUTABLE` de la biblioteca. Una demo con filas de biblioteca la purga DEMO-05d; su especificación fija el mecanismo y el CTO lo revisa allí. Esta ficha prueba la purga con demos sin filas de biblioteca y no promete vaciarla.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-05c`).** Solo `jobs/purga_demo/`, sus pruebas y el brief del propietario.

## 4. Interfaz

No aplica.

## 5. Aceptación

Todas contra la PostgreSQL 16 local con todas las migraciones (`alembic upgrade heads`) y `politicas_purga.sql`, dentro de una transacción revertida (R11), con el marcador `demo`, un tenant demo vencido, la plantilla, un tenant demo con sesión activa y un tenant no demo. Los casos nuevos van en `tests/test_demo05c_politicas_purga.py`; los de personas ficticias se **añaden** a `tests/test_demo_purga_usuarios.py`. Las pruebas de DEMO-05b pasan sin cambiarlas.

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol migrado y el SQL, **entonces** `faltan_politicas` devuelve vacío. Mutación m1: crear una tabla con `tenant_id` sin volver a ejecutar el SQL hace que la guardia la nombre y que el Job salga con 1 antes de borrar. | `test_guardia_nombra_la_tabla_sin_politicas` |
| **Dado** el árbol migrado, **entonces** `tablas_sin_rls` nombra las cinco tablas sin RLS y la guardia no falla por ellas si tienen sus permisos; sin el `GRANT` de una de ellas, falla. | `test_guardia_lista_aparte_las_tablas_sin_rls` |
| **Dado** `SET ROLE purga_demo`, **entonces** la purga borra el tenant demo vencido y no toca la plantilla, el tenant con sesión activa ni el no demo. Mutaciones: m2, quitar la exclusión de la plantilla la purga; m3, quitar la condición de sesión activa purga esa demo. | `test_purga_solo_los_vencidos` |
| **Dado** una tabla sin RLS con filas de la plantilla y de un tenant con sesión activa, **cuando** se purga el vencido, **entonces** esas filas quedan. Mutación: quitar el filtro por `tenant_id` del código hace fallar la prueba. | `test_tabla_sin_rls_respeta_plantilla_y_activas` |
| **Dado** el marcador `pruebas`, o sin marcador, **entonces** `purga_demo` ve 0 filas en las tablas con RLS y `es_persona_ficticia` devuelve false. | `test_sin_marcador_demo_no_ve_nada` |
| **Dado** sesiones vencidas hace 91 y 89 días, **entonces** solo se borra la de 91. Mutación m4: cambiar `90 days` por `0` borra la reciente. | `test_caducidad_a_90_dias` |
| **Dado** `purga_demo`, **cuando** lee `vendedor_email`, `vendedor_sub` o `users.email`, o hace UPDATE o INSERT, **entonces** «permission denied». Mutaciones: m5, volver al `GRANT SELECT` de `demo_sesiones` entera deja leer el correo; m6, volver a `GRANT SELECT (id, email)` sobre `users` hace fallar la prueba. | `test_permisos_por_columnas` |
| **Dado** `es_persona_ficticia`, **entonces** es `SECURITY DEFINER`, su `search_path` está fijado, devuelve un booleano y no el correo, y `PUBLIC` no tiene `EXECUTE`. Mutación m7: si devuelve siempre true, falla `test_se_conserva_un_usuario_real_correo_sin_invalid_con_rol_en_demo_vencida` (DEMO-05b). | `test_funcion_persona_ficticia` |
| **Dado** la función sin `SECURITY DEFINER`, borrada, con `EXECUTE` para `PUBLIC`, o `purga_demo` con `SELECT` sobre `users.email`, **entonces** `faltan_politicas` falla. Mutación m8: dar `EXECUTE` a `PUBLIC` hace fallar la guardia. | `test_guardia_vigila_la_funcion_y_el_correo` |
| **Dado** la persona ficticia de una demo vencida y la purga como `purga_demo`, sin `UPDATE`, **entonces** la persona se borra aunque su sesión siga nombrándola con `tenant_id` nulo. Mutación m9: quitar `ds.tenant_id IS NOT NULL` hace fallar `test_se_borra_el_usuario_invalid_cuyos_roles_eran_solo_de_demos_vencidas` (DEMO-05b). | `test_persona_ficticia_se_borra_sin_update` (en `tests/test_demo_purga_usuarios.py`) |
| **Dado** `pg_roles`, **entonces** `purga_demo` no tiene privilegios especiales; y `pg_policies` con `policyname LIKE 'purga_demo_%'` y `roles <> '{purga_demo}'` da 0. | `test_rol_sin_privilegios_especiales` |
| **Dado** el SQL ejecutado dos veces en la misma transacción, **entonces** no falla y el estado es el mismo. | `test_sql_idempotente` |

Las pruebas van sin `import yaml` y saltan sin `TEST_DATABASE_URL`.

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-05c.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD EVYDENTIA §5.6.4, invariantes 60 a 63. Decisiones del CTO de 2026-11-12 (política explícita sin `BYPASSRLS`, políticas estrechas, `demo_sesiones` por columnas) y de 2026-11-19: tablas sin RLS por permisos y filtros del código, sin activar la RLS aquí; `usuarios.py` en la propiedad; `users` solo `SELECT (id)`; sin `UPDATE`, con la comprobación de sesiones limitada a las que tienen organización; `es_persona_ficticia` (opción A); rol de pruebas en transacción revertida. `persona_usuario_id` entra en las columnas de `demo_sesiones` porque `usuarios.py` lo necesita; es un identificador, no un dato personal.
- **Ficha de seguridad aparte**, la da de alta el Arquitecto: una tabla con `tenant_id` sin RLS es un hueco multi-tenant en todos los entornos. Nombra las cinco tablas y activa la RLS y sus políticas por Alembic en todos los entornos. Cuando se fusione, `tablas_sin_rls` quedará vacía.
- Depende de DEMO-05, DEMO-05b y SEC-20, hechas. DEMO-05d depende de esta ficha y comparte `politicas_purga.sql`, `purga.py`, `guardias.py` y `usuarios.py`: su especificación la escribe el Arquitecto sobre DEMO-05c ya fusionada y contempla la lista de tablas sin RLS.
