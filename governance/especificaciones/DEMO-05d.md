# DEMO-05d · Purga de la demo frente a los triggers de inmutabilidad
`¤sdd` `¤demo` `¤seguridad` `¤arbitro`

## 1. Datos

Sin migraciones. Todo vive en `jobs/purga_demo/politicas_purga.sql`, que el propietario ejecuta solo en la base de la demo (criterio 2).

| Archivo | Estado final |
| :--- | :--- |
| `jobs/purga_demo/politicas_purga.sql` | además de lo de DEMO-05c, la función `public.purga_demo_borrar_inmutables(p_tenant character varying) RETURNS integer` y sus permisos |
| `jobs/purga_demo/purga.py` | `TABLAS_INMUTABLES` (las cinco tablas de §1) en `TABLAS_EXENTAS`; `purgar_tenant` llama a la función antes de `_borrar_filas` |
| `jobs/purga_demo/guardias.py` | `TRIGGERS_INMUTABLES` y `falta_funcion_inmutables(con) -> list[str]` |
| `jobs/purga_demo/__main__.py` | suma `falta_funcion_inmutables` a la guardia de `faltan_politicas`; si devuelve algo, sale con 1 sin borrar |
| `governance/operaciones/BRIEF_PROPIETARIO_DEMO05.md` | en el paso 5, el dueño de la función y la comprobación de solo lectura de §3 R7 |
| `tests/test_demo05d_purga_inmutables.py` (nuevo) | casos de §5 contra la PostgreSQL 16 efímera del CI |

**Lista literal y cerrada de triggers** (criterio 4), medida leyendo las migraciones de `origin/main` 045ddf7d. Son todos los triggers que lanzan una excepción en DELETE sobre una tabla con `tenant_id`:

| Tabla | Trigger | Código |
| :--- | :--- | :--- |
| `biblioteca_documentos_historial` | `biblioteca_documento_historial_inmutable` | 23514 `BIB_HISTORIAL_INMUTABLE` |
| `biblioteca_descargas` | `biblioteca_descargas_inmutable` | 23514 `BIB_HISTORIAL_INMUTABLE` |
| `biblioteca_eventos_documento` | `biblioteca_evento_inmutable` | 23514 `BIB_HISTORIAL_INMUTABLE` |
| `dpo_consultas_mensajes` | `trg_dpo_consultas_mensajes_solo_agrega` | 42501 |
| `dpo_consultas` | `trg_dpo_consultas_inmutable_tras_cierre` | 42501 |

`trg_normativa_versiones_inmutable` queda fuera porque `normativa_versiones` no tiene `tenant_id` y la purga no la toca; `bib_auditar_capacidad` no lanza en DELETE. Las cinco tablas tienen RLS ENABLE y FORCE.

Base de partida: la especificación de DEMO-05c en `main` (#893) y su implementación en `tarea/juan-carlos/demo-05c` 1ecd7a49: `politicas_purga.sql` exige el rol y el marcador, define `es_persona_ficticia` como `SECURITY DEFINER` con `search_path` fijo y `REVOKE … FROM PUBLIC`; `guardias.py` tiene `faltan_politicas` y `tablas_sin_rls`; `purga.py` tiene `TABLAS_EXENTAS = {"demo_sesiones", "tenants"}`.

## 2. API

Sin rutas. `purga_demo_borrar_inmutables(p_tenant)` devuelve el número de filas borradas en las cinco tablas. Lanza una excepción (y la transacción del Job revierte) si no se cumple R1.

## 3. Reglas

- **R1 · Falla cerrada** (criterio 1). Antes de tocar nada, la función exige:
  - una sola fila en `public.entorno_marcador` con `valor = 'demo'`;
  - `p_tenant` distinto de `'demo-plantilla-cooperativa'`;
  - `tenants.es_demo` verdadero para `p_tenant`.
  Si falla una, lanza `purga_demo_borrar_inmutables: <motivo>` con código `42501`, sin desactivar ningún trigger.
- **R2 · Solo en la base de la demo** (criterio 2). La crea `politicas_purga.sql`. Ninguna migración de `alembic/versions/` define ni llama a `purga_demo_borrar_inmutables`.
- **R3 · Permisos mínimos** (criterio 3). `SECURITY DEFINER`, `SET search_path = pg_catalog, public`, `REVOKE ALL ON FUNCTION … FROM PUBLIC` y `GRANT EXECUTE … TO purga_demo`, a nadie más. El dueño de la función es el dueño de las cinco tablas: es el único rol que puede desactivar sus triggers, y no tiene `rolsuper` ni `rolbypassrls`. `purga_demo` sigue sin ser dueño de nada.
- **R4 · Triggers en la misma transacción** (criterio 4). La función recorre la lista de §1, escrita literal en el SQL, y por cada tabla:
  - `ALTER TABLE … DISABLE TRIGGER <nombre>`;
  - `DELETE FROM … WHERE tenant_id::text = p_tenant`;
  - `ALTER TABLE … ENABLE TRIGGER <nombre>`.

  Todo ocurre dentro de la transacción del Job, y el bloqueo del `ALTER TABLE` impide que otra sesión escriba mientras tanto. Si algo falla a mitad, el rollback deja cada trigger como estaba (`tgenabled = 'O'`). La función nunca usa `session_replication_role` ni `DISABLE TRIGGER ALL`.
- **R5 · RLS forzada.** Las cinco tablas tienen FORCE RLS, así que el dueño también queda sujeto a sus políticas. La función fija `set_config('app.current_tenant_id', p_tenant, true)` (local a la transacción) antes de los DELETE, para que las políticas de la sala vean las filas del tenant. No cambia ninguna política.
- **R6 · Guardia del Job.** `falta_funcion_inmutables(con)` devuelve lo que falta, y el Job sale con 1 sin borrar nada si:
  - la función no existe, no es `SECURITY DEFINER`, no fija `search_path`, es ejecutable por `PUBLIC` o `purga_demo` no puede ejecutarla;
  - existe en la base un trigger que lanza en DELETE sobre una tabla con `tenant_id` fuera de `TRIGGERS_INMUTABLES`. Se mide con `pg_trigger` (`tgtype` con DELETE) sobre las tablas con `tenant_id`, menos la lista de triggers conocidos que no lanzan.
- **R7 · Comprobación del propietario.** El paso 5 del brief añade, tras ejecutar el SQL en la base de la demo:
  - el dueño de la función y de las cinco tablas es el mismo rol, sin `rolsuper` ni `rolbypassrls` (en Cloud SQL, `postgres` no tiene `BYPASSRLS`);
  - una prueba dentro de `BEGIN … ROLLBACK`, como `purga_demo`, sobre una demo con filas de biblioteca: el recuento de las cinco tablas para ese tenant antes de la llamada, el número que devuelve la función, el recuento después (0) y `tgenabled = 'O'` en los cinco triggers;
  - nada se confirma.

  El propietario pega las salidas al Tech Lead.
- **R8 · Producción no cambia** (criterio 6). La inmutabilidad de producción sigue igual: los triggers, las políticas y las migraciones no cambian. La función solo existe donde se ejecuta `politicas_purga.sql`, y R1 la detiene fuera de la base con marcador `demo`. Cumple el invariante 63 (`INV_DEMO_APP_NEVER_DELETES`): el único que borra es el Job `purga-demo`, nunca la plantilla, y `lopdp_app` no gana `DELETE` ni `EXECUTE`.
- **R9 · Tablas sin RLS.** Las cinco tablas de §1 tienen RLS. Si una tabla de biblioteca con `tenant_id` no la tiene, sigue la regla de DEMO-05c: permisos de `purga_demo` y la lista aparte de `tablas_sin_rls` en la guardia. Esta ficha no la añade a la función.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-05d`).** Solo `jobs/purga_demo/`, su prueba y el brief del propietario.

## 4. Interfaz

No aplica.

## 5. Aceptación

Todas contra la PostgreSQL 16 efímera del CI, con todas las migraciones y `politicas_purga.sql`. El rol `purga_demo` se crea dentro de una transacción que la prueba revierte, como en DEMO-05c. Se siembra un tenant demo vencido con filas en las cinco tablas, la plantilla y un tenant no demo. Las pruebas van sin `import yaml` y saltan sin `TEST_DATABASE_URL`.

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el marcador `demo` y el tenant demo vencido, **cuando** el Job purga, **entonces** las cinco tablas y el resto quedan con 0 filas del tenant, y la plantilla y el no demo quedan intactos. | `test_demo_con_biblioteca_queda_vacia` |
| **Dado** el marcador `pruebas`, el marcador `produccion` o ningún marcador, **cuando** se llama a la función, **entonces** falla con 42501 y ningún trigger cambia. Mutación m1: quitar la comprobación del marcador hace que la llamada borre y la prueba falle. | `test_sin_marcador_demo_falla_cerrada` |
| **Dado** la plantilla o un tenant no demo, **entonces** la función falla. Mutación m2: quitar la exclusión de la plantilla hace fallar la prueba. | `test_plantilla_y_no_demo_fallan` |
| **Dado** un fallo inyectado tras el segundo DELETE, **entonces** la transacción revierte y los cinco triggers quedan con `tgenabled = 'O'`. Mutación m3: rehabilitar fuera de la transacción deja un trigger apagado. | `test_fallo_a_mitad_deja_los_triggers_encendidos` |
| **Dado** `lopdp_app` o `PUBLIC`, **entonces** no pueden ejecutar la función; la función es `SECURITY DEFINER` con `search_path` fijo. Mutación m4: quitar el `REVOKE … FROM PUBLIC` deja a `lopdp_app` ejecutarla. | `test_permisos_de_la_funcion` |
| **Dado** un trigger nuevo que lanza en DELETE sobre una tabla con `tenant_id`, creado en la prueba, **entonces** `falta_funcion_inmutables` lo nombra y el Job sale con 1 sin borrar. Mutación m5: no comparar con `TRIGGERS_INMUTABLES` deja el Job en verde. | `test_guardia_nombra_el_trigger_nuevo` |
| **Dado** el árbol, **entonces** ninguna migración de `alembic/versions/` contiene `purga_demo_borrar_inmutables`. | `test_ninguna_migracion_define_la_funcion` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-05d.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Decisión del CTO del 2026-11-12 (opción a y sus seis criterios, commit d40c9ad1); pedido del CTO del 2026-11-19. PRD EVYDENTIA §5.6.4; invariante 63 (`INV_DEMO_APP_NEVER_DELETES`).
- Depende de DEMO-05c, que crea `politicas_purga.sql`, `guardias.py` y el resto de la purga: DEMO-05d se lanza cuando DEMO-05c esté fusionada y comparte sus archivos por dependencia.
