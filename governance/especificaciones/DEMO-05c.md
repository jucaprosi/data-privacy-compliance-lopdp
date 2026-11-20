# DEMO-05c · Purga de la demo con políticas explícitas por rol, sin BYPASSRLS
`¤sdd` `¤demo` `¤seguridad` `¤arbitro`

## 1. Datos

Sin migraciones: nada de esto entra en la cadena de Alembic, que también corre en producción.

| Archivo | Estado final |
| :--- | :--- |
| `jobs/purga_demo/politicas_purga.sql` (nuevo) | permisos y políticas `TO purga_demo`, idempotente; lo ejecuta el propietario en la base de la demo |
| `jobs/purga_demo/guardias.py` | `faltan_politicas(con) -> list[str]` |
| `jobs/purga_demo/__main__.py` | llama a `faltan_politicas` antes de `purgar`; si devuelve algo, sale con 1 sin borrar |
| `jobs/purga_demo/purga.py` | `purgar_tenant` sin el `UPDATE demo_sesiones` (las claves foráneas `ON DELETE SET NULL` lo hacen) |
| `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md` | paso 5: ejecutar `politicas_purga.sql` tras cada migración de la base de la demo y la comprobación de solo lectura |
| `tests/test_demo05c_politicas_purga.py` (nuevo) | casos de §5 contra la PostgreSQL 16 efímera del CI |

Hecho medido en `origin/main` 04292440:
- `demo_sesiones` (`20261121_demo_sesiones.py`): `id`, `vendedor_sub`, `vendedor_email`, `tenant_id` y `persona_usuario_id` (las dos con `ON DELETE SET NULL`), `estado` (`'activa' | 'vencida'`), `iniciada_en`, `ultima_actividad`, `terminada_en` y `motivo_fin`.
- La purga lee de `demo_sesiones` `id`, `tenant_id`, `estado`, `terminada_en` y, en `jobs/purga_demo/usuarios.py`, `persona_usuario_id` (no borra a una persona que una sesión aún nombra). Borra de `users` las personas ficticias sin roles (DEMO-05b, hecha).
- `jobs/purga_demo/purga.py:118` hace `UPDATE demo_sesiones SET persona_usuario_id = NULL, tenant_id = NULL`.
- El marcador se lee de `public.entorno_marcador.valor`. DEMO-05, DEMO-05b y SEC-20 están hechas.

## 2. API

Sin rutas. El Job `python -m jobs.purga_demo` sale con 0 si purga, con 1 si una guardia lo rechaza (mensaje «faltan políticas de purga en: <tablas>; ejecuta politicas_purga.sql»).

## 3. Reglas

- **R1 · Solo `purga_demo`, sin privilegios especiales.** Todas las políticas son `TO purga_demo`; las de los demás roles no cambian. El rol tiene `rolsuper`, `rolbypassrls`, `rolcreaterole` y `rolcreatedb` en false. Ninguna política es `USING (true)`.
- **R2 · Marcador en cada política.** Cada política exige `EXISTS (SELECT 1 FROM public.entorno_marcador WHERE valor = 'demo')`. Con otro marcador o sin marcador, `purga_demo` no ve ni borra nada.
- **R3 · `tenants`.** SELECT y DELETE solo de los tenants vencidos: `es_demo`, distinto de `demo-plantilla-cooperativa`, con alguna sesión `vencida` y ninguna `activa`. La política usa columnas de `tenants` y una subconsulta sobre `demo_sesiones`, nunca sobre `tenants`.
- **R4 · Tablas con `tenant_id`.** Para cada tabla con columna `tenant_id`, salvo `tenants` y `demo_sesiones`: `GRANT SELECT, DELETE` y políticas `tenant_id::text IN (SELECT id::text FROM public.tenants)`, que heredan la exclusión de la plantilla y de los no vencidos.
- **R5 · `demo_sesiones`, por columnas.** `GRANT SELECT (id, tenant_id, estado, terminada_en, persona_usuario_id)` y `GRANT DELETE`. `vendedor_sub` y `vendedor_email` no se leen. El DELETE se limita a `estado = 'vencida' AND terminada_en < now() - interval '90 days'`. `purga_demo` nunca hace INSERT ni UPDATE.
- **R6 · `users`.** `GRANT SELECT (id)` y `GRANT DELETE`. Si `users` tiene RLS, la política deja ver y borrar solo a quien no tiene filas en `user_tenant_roles` ni sesiones que lo nombren, con el marcador.
- **R7 · Guardia que falla cerrada.** `faltan_politicas(con)` compara `tablas_con_tenant(con) ∪ {tenants, demo_sesiones, users}` con `pg_policies WHERE 'purga_demo' = ANY(roles)` y exige `select` y `delete` en cada una. Lo que falte, lo devuelve; el Job no borra objetos ni filas.
- **R8 · Triggers de inmutabilidad, fuera de esta ficha.** Las políticas no desactivan los triggers `BIB_HISTORIAL_INMUTABLE` de la biblioteca. Una demo con filas de biblioteca la purga DEMO-05d, con la función `purga_demo_borrar_inmutables` en este mismo `politicas_purga.sql` (opción a, confirmada por el CTO el 2026-11-12). Esta ficha prueba la purga con demos sin filas de biblioteca y no promete vaciarla.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-05c`).** Solo `jobs/purga_demo/`, su prueba y el brief del propietario.

## 4. Interfaz

No aplica.

## 5. Aceptación

Todas contra la PostgreSQL 16 efímera del CI, con todas las migraciones y `politicas_purga.sql`, el marcador `demo`, un tenant demo vencido, la plantilla, un tenant demo con sesión activa y un tenant no demo.

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol migrado y el SQL, **entonces** `faltan_politicas` devuelve vacío. Mutación m1: crear una tabla con `tenant_id` sin volver a ejecutar el SQL hace que la guardia la nombre y que el Job salga con 1 antes de borrar. | `test_guardia_nombra_la_tabla_sin_politicas` |
| **Dado** `SET ROLE purga_demo`, **entonces** la purga borra el tenant demo vencido y no ve la plantilla, el tenant con sesión activa ni el no demo. Mutaciones: m2, quitar la exclusión de la plantilla, la deja visible; m3, quitar `NOT EXISTS` de la sesión activa purga esa demo. | `test_purga_solo_los_vencidos` |
| **Dado** el marcador `pruebas`, o sin marcador, **entonces** `purga_demo` ve 0 filas en todas las tablas. | `test_sin_marcador_demo_no_ve_nada` |
| **Dado** sesiones vencidas hace 91 y 89 días, **entonces** solo se borra la de 91. Mutación m4: cambiar `90 days` por `0` borra la reciente. | `test_caducidad_a_90_dias` |
| **Dado** `purga_demo`, **cuando** lee `vendedor_email` o `vendedor_sub`, o hace UPDATE o INSERT, **entonces** «permission denied». Mutación m5: volver al `GRANT SELECT` de la tabla entera deja leer el correo. | `test_demo_sesiones_por_columnas` |
| **Dado** `pg_roles`, **entonces** `purga_demo` no tiene privilegios especiales; y `pg_policies` con `policyname LIKE 'purga_demo_%'` y `roles <> '{purga_demo}'` da 0. | `test_rol_sin_privilegios_especiales` |
| **Dado** el SQL ejecutado dos veces, **entonces** no falla y el estado es el mismo. | `test_sql_idempotente` |

Las pruebas van sin `import yaml` y saltan sin `TEST_DATABASE_URL`.

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-05c.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD EVYDENTIA §5.6.4, invariantes 60 a 63. Decisiones del CTO de 2026-11-12: política explícita sin `BYPASSRLS`, políticas estrechas y SELECT de `demo_sesiones` por columnas. `persona_usuario_id` entra en esas columnas porque `usuarios.py` lo necesita para no borrar a una persona que una sesión nombra; es un identificador, no un dato personal.
- Depende de DEMO-05, DEMO-05b y SEC-20, hechas. DEMO-05d depende de esta ficha y comparte `politicas_purga.sql`, `purga.py` y `guardias.py`: va después.
