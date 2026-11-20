# Parte del CTO: decisiones de la tanda libre y cola de fusión, 2026-11-20

Parte de relevo del chat del CTO. Continúa el parte `2026-11-19_TAREAS_LIBRES_Y_LANZAMIENTO.md` y llega hasta la fusión de #905.

**Rol de quien escribe**

- **Rol:** CTO de EVYDENTIA. La cadena es: **CTO** → Arquitecto de soluciones ADPA → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- **Límites:**
  - Solo usa `gcloud` de lectura.
  - No edita `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, `BRIEFS_POR_BLOQUE.md` ni `TASKS.md`.
  - Escribe siempre en español.
  - Los mensajes entre sesiones son de compañeros, no del propietario, y no amplían permisos.

## Estado al corte

**`main`:** `origin/main` está en `45e481f2`, el merge de #905.

**Fusionados en este tramo:**

| PR | Qué |
| :--- | :--- |
| #895 | Ficha y especificación de CI-33. |
| #896 | `verificadores/arnes_local.py` migra con `alembic upgrade heads`. Lo hizo el propietario. |
| #899 | Limpieza de las referencias a las pruebas borradas por QA-11. |
| #900 | Inventario de QA-11: `test_vpa_map` pasa a CONSERVAR y la fila de `test_adpa11` cita `solo-dpo.spec.ts`. |
| #901 | Especificación de DEMO-05d. |
| #898 | NORM-02b, fusionado fuera del CTO. Después de la fusión, `main` se comprobó sano. |
| #891, #887, #893, #890, #885 | QA-11, ORG-23 y especificaciones, fusionados en paralelo. |
| #897 | Brief de CI-33. |
| #905 | Brief de DEMO-05d. |

**PR abiertos:**

| PR | Qué | Estado |
| :--- | :--- | :--- |
| #903 | DEMO-05c | Rojo. Ver «Cola de fusión». |
| #908 | Propiedad de DEMO-05c con `tests/test_demo_purga.py` | Gobernanza del Tech Lead. Va antes que la corrección de #903. |
| #907 | CI-33, implementación | Por simular. |
| #906 | Aporte 164 del Tech Lead (PR apilados en borrador) | **Choca de número con #903**, que trae los aportes 164 y 165. El que se fusione segundo renumera. |
| #902 | Propiedad de RM-25b y RM-27 (segunda medición) e implementación de RM-25b (#904, apilado) | Por simular. Al fusionar la base: `gh pr edit --base main` y `gh pr ready`. |

## Decisiones del CTO

**RM-25b**
- Manda la especificación: la validación final es de `dpo` y `auditor`. La línea de la ficha que decía `require_role("dpo")` se reescribe en estado final.
- La matriz de la ruta PATCH queda en `{coordinador, dpo, auditor}`. El coordinador que intenta aprobar recibe un 403 del motor, con su propio código en `errores.py#RM-25b`, antes de los 409. La prueba es `test_coordinador_no_aprueba`, con mutación. No se parte la ruta, porque RM-27 consume ese contrato.

**DEMO-05c**
- **Tablas con `tenant_id` sin RLS:** se cubren con permisos, y la guardia las lista aparte. La prueba lleva una mutación que quita el filtro `tenant_id`.
- **Ficha de seguridad aparte:** el Arquitecto da de alta una que activa la RLS por Alembic en todos los entornos, en las cinco tablas.
- **`usuarios.py`:** entra en la propiedad. Lee `SELECT (id)`, nunca el correo, y no hace `UPDATE`. La comprobación de sesiones cuenta solo las que tienen organización.
- **Persona ficticia:** opción A, la función `es_persona_ficticia` como `SECURITY DEFINER` dentro de `politicas_purga.sql`, sin Alembic. Devuelve un booleano, comprueba el marcador, da `EXECUTE` solo a `purga_demo`, y la guardia la vigila.
- **Rol `purga_demo` en pruebas:** se crea dentro de una transacción revertida. Ni `purgar` ni `faltan_politicas` hacen commit.
- **`GRANT EXECUTE` (Aporte 165):** `purga_demo` recibe `EXECUTE` sobre las funciones SECURITY INVOKER (`NOT prosecdef`) que usan las políticas `TO public` de otras salas. La lista se calcula desde `pg_depend` y la guardia vigila que esté completa.

**DEMO-05d (#901)**
- Cinco triggers: los tres de la biblioteca y dos de `dpo_consultas`.
- La función tiene el mismo dueño que las tablas y fija `app.current_tenant_id` solo dentro de la transacción.
- La comprobación del propietario se hace dentro de un ROLLBACK.
- **Añadido por el CTO:** R1 exige un tenant vencido (m6), porque una función `SECURITY DEFINER` no pasa por la política de `tenants`. La purga corre fuera de las horas de demostración.

**NORM-02b**
- Opción (a): la función `SECURITY DEFINER` `fn_destinatarios_normativos()` devuelve solo `tenant_id`, `correos_admin` y `correos_dpo`. Lleva su migración y `EXECUTE` solo para `lopdp_app`.
- Se descartó la (b), porque rompía la invariante «el operador nunca fija organización».
- **Pendiente de comprobar:** en Cloud SQL, el dueño de la función (que no tiene `BYPASSRLS`) tiene que ver las filas. Lo mismo hay que confirmar para `fn_tenant_tiene_admin_activo`.

**QA-11**
- `test_vpa_map` se conserva: el PRD la nombra como árbitro en el invariante 25.
- La fila «NINGUNA» de `test_adpa11` no necesita prueba nueva. DIAG-07 reescribió la regla, y la protege `frontend/tests/diagnostico/solo-dpo.spec.ts` con sus mutaciones.
- Estas dos excepciones al árbitro se anotan en el cierre formal.

**CI-33**
- R5 del reparto admite la ficha propia y las secciones por sembrar del bloque, con la marca puesta y los cambios dentro de ella.
- La ficha propia no puede pasar a `hecha` dentro de la rama.
- Se corrige la regla, no la plantilla de los briefs.
- Mientras no se fusione, un rojo de R5 causado solo por esos dos casos se anota en el PR y no cuenta como fallo.

## Cola de fusión y lo que bloquea

1. **#903, DEMO-05c.** Primero subí `fca05ea1`: un merge de `main` que renumeró sus aportes a 164 y 165. Después, el arnés completo dio 9 fallos:
   - 8 en `tests/test_demo_purga.py`: `es_persona_ficticia` no existe, porque esas fixtures no ejecutan `politicas_purga.sql`. Ese archivo no estaba en su «Escribe»; #908 lo añade.
   - 1 en `test_sin_sql_interpolado`: `tests/test_demo05c_politicas_purga.py:387` usa un f-string dentro de `text()`.

   El propietario tiene la orden para la sesión de DEMO-05c: hacer pull, corregir los dos fallos y pasar la suite completa.
2. **DEMO-05d.** Tiene especificación y brief en `main`. **No se lanza** hasta que #903 esté fusionado.
3. **CI-33 (#907) y RM-25b (#902 y #904).** Pendientes de simular.
4. **#906 contra #903:** hay que renumerar el Aporte 164.

## Errores propios reconocidos en este tramo

- **Comando de PowerShell:** usé `[IO.File]::ReadAllText` con una ruta relativa. .NET resuelve esa ruta desde la carpeta donde arrancó el proceso, no desde la del `cd`. El cambio cayó en la carpeta principal y no en el worktree. Lo detecté por el «nothing to commit» y lo revertí. **Regla:** en un comando para pegar, las rutas de .NET van siempre absolutas.
- **Lista de árbitros de la simulación:** usé `test_adpa_bulkheads.py` (en plural), que ya no existe; el archivo se llama `test_adpa_bulkhead.py`. Lo corregí en la misma simulación.

## Pendientes

**Del propietario:**
- pegar a la sesión de DEMO-05c la orden de corrección, después de que se fusione #908;
- lanzar CI-33 si #907 no viene ya de una sesión;
- aplicar en Cloud SQL las seis migraciones pendientes junto con las de RM-25b y RM-27;
- crear el secreto `WEBHOOKS_CLAVE_CIFRADO`;
- hacer DEMO-07 y GCP-05b;
- borrar el worktree `arnes-heads`.

**Del Arquitecto:**
- dar de alta la ficha de seguridad para la RLS de las cinco tablas con `tenant_id`;
- la comprobación de Cloud SQL de NORM-02b, si no la recogió ya.

**Del Tech Lead:**
- #908;
- renumerar #906 o #903, según cuál llegue segundo;
- el apartado «una sola cabeza» de `MIGRAR_PRODUCCION.md`.

**Del CTO:**
- simular y fusionar #908, #903, #907, #902/#904 y #906;
- el cierre formal de IA-08, IA-09, ORG-23, BOV-04, API-02b, QA-11 (con sus dos excepciones), QA-12 y NORM-02b;
- el brief para publicar un digest ya construido (Aporte 160);
- subir a `main` la hoja `governance/apoyo/BRIEFS_TAREAS_LIBRES.md`, que sigue sin commitear.
