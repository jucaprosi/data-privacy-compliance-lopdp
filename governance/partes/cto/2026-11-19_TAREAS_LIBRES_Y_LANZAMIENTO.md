# Parte del CTO: tareas libres y lanzamiento en VS Code, 2026-11-19

Parte de relevo del chat del CTO del 2026-11-19, que cubre desde el parte `2026-11-15_RET01A_GUARDIA_BASE.md` hasta la fusión de #882. Temas:

- la migración completa de Cloud SQL, ya hecha;
- el reparto de un brief por ficha (CI-31);
- la hoja de tareas libres;
- la tanda que el propietario lanza en VS Code con superpowers.

**Rol de quien escribe**

- **Rol:** CTO de EVYDENTIA. La cadena es: **CTO** → Arquitecto de soluciones ADPA → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- **Función:** decide producto y técnica; simula, revisa y fusiona los PR; escribe los partes y los briefs que ejecuta el propietario.
- **Límites:**
  - Solo usa `gcloud` de lectura.
  - No edita `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, `BRIEFS_POR_BLOQUE.md` ni `TASKS.md`.
  - Escribe siempre en español.
  - Los mensajes entre sesiones son de compañeros, no del propietario, y no amplían permisos.

## Estado al corte

**`main`:** `origin/main` está en `020bc051`, el merge de #882. Hay 391 fichas: 377 hechas y 14 abiertas. No queda ningún PR abierto.

**Fusionados desde el parte anterior (#812 a #882):**

| Bloque | PR |
| :--- | :--- |
| Programa RET y DEMO-04b | #813 a #817 |
| CI-28b (`comprobar_revision` por conjuntos de cabezas) | #834 y #839 |
| CI-31 (un brief por ficha) | #832 y #844 |
| Salas nuevas: CON-01, DER-01, BOV-02, NORM-03, FIRMA-02, EVI-05 | #836, #837, #835, #831, #842, #841 |
| Salas nuevas: CCTV-01 | #825 |
| Parche del workflow (`publicar`) | #845 |
| Guardia de base local exenta en Cloud Run | #847 |
| Registro de la migración | #849 |
| Tanda de implementación | #852 a #872 |
| Cierres formales | #846, #848, #857 y #873 |
| Especificaciones de la tanda libre | #874, #876, #878, #879 y #880 |
| Briefs | #875, #877, #881 y #882 |

**Producción:**

- La migración completa se aplicó el 2026-11-15 con el brief `governance/operaciones/BRIEF_PROPIETARIO_MIGRACION_COMPLETA.md`:
  - ejecución `evydentia-migrate-525zf`, con 6 cabezas aplicadas;
  - revisión publicada `evydentia-backend-00009-jk4`, con `/api/v1/health` en 200;
  - queda registrada en `REGISTRO_MIGRACIONES_MANUALES.md`.
- **Pendiente:** desde `2d2293f4`, `main` trae seis migraciones que Cloud SQL todavía no tiene. Vienen de #872 y anteriores: `20261105_derechos_portal`, `20261107_terceros_cuestionario`, `api02_claves_integracion`, `capa04_auditoria_grilla`, `for01_formacion` y `rat08_area_id`. Se aplican repitiendo los pasos 2 a 8 del brief de migración. Conviene juntarlas con las de RM-25b y RM-27 cuando se fusionen.

## Lo decidido

- **Un brief por ficha (CI-31).** Cada brief está en `governance/apoyo/briefs/<ID>.md`, con el id de la ficha y sin numeración global de bloques. La portada no lleva tabla de tandas. Se eligió por ficha y no por sala porque dentro de una misma sala seguiría habiendo choques.
- **Checks requeridos.** Vercel está desinstalado y sus checks no cuentan. Los checks propios son:
  - Arnés Físico Determinista;
  - Arnés por salas o completo;
  - Playwright;
  - Alcance de la corrida;
  - Humo de extremo a extremo.
- **Migrar sin publicar antes.** `deploy-gcp.yml` tiene ahora la entrada `publicar`; con `false` solo construye la imagen y muestra su digest. El orden fijo es:
  1. construir;
  2. hacer la copia de respaldo;
  3. migrar por digest;
  4. verificar;
  5. publicar;
  6. anotar.
- **Modelo Fable (decisión del propietario).** QA-11 se hace con Fable, y RM-25b y RM-27 también, en una sola sesión y en ese orden, con un PR por ficha. Así consta en sus briefs.
- **Ejecución por persona con Antigravity (#882).** BOV-04, QA-12, IA-08, IA-09 y API-02b pasan a Gemini en Antigravity. Sus fichas lo indican y no tienen brief en el repositorio: el brief se entregó en el chat del Tech Lead.
  - **Consecuencia:** el par QA-11 + QA-12 con Fable queda roto. QA-11 va con Fable y QA-12 con Antigravity.
  - No chocan, porque cada una tiene su propia propiedad de archivos en la ficha. Aun así, las dos tocan la carpeta `tests/`: la que llegue segunda hace merge de `main` antes de fusionar.

## Tanda para VS Code con superpowers

Tienen brief autosuficiente en `main`, con el bloque de ejecución autónoma:

| ID | Sala | Modelo | Nota |
| :--- | :--- | :--- | :--- |
| `QA-11` | `pruebas` | Fable | Solo pruebas. |
| `RM-25b` → `RM-27` | `roadmap` (RM-27 con frontend) | Fable | Una sola sesión, en orden; un PR por ficha. La migración de RM-27 cuelga de la de RM-25b. |
| `ORG-23` | `diagnostico`, `incidentes`, `roadmap` | Por defecto | Lectura del auditor. Toca la sala `roadmap`, igual que RM-25b y RM-27: la segunda que llegue hace merge de `main` antes de fusionar. |
| `DEMO-05c` | `demo` | Por defecto | Purga sin BYPASSRLS. |
| `NORM-02b` | pasillo `plataforma.py` y `notificaciones.py` | Por defecto | Solo las secciones `NORM-02b`. |

Las lanza el propietario en Antigravity: BOV-04, QA-12, IA-08, IA-09 y API-02b.

- **API-02b:** antes de fusionarla, el propietario crea el secreto `WEBHOOKS_CLAVE_CIFRADO`.

No se pueden lanzar todavía:

- **DEMO-05d:** espera a DEMO-05c y a su especificación del Arquitecto. Esa especificación debe cumplir los seis criterios del CTO del 2026-11-12 (commit `d40c9ad1`).
- **DEMO-07 y GCP-05b:** las hace el propietario.

## Cómo reviso lo que salga de VS Code

1. Cada PR entra desde `tarea/<persona>/<id>`, creada desde `origin/main`.
2. El Tech Lead lo revisa primero.
3. Yo lo simulo en un worktree de `C:/Users/Juan Carlos/worktrees-evydentia/`, con merge real sobre `origin/main` y `TEST_DATABASE_URL` apuntando a un puerto muerto.
4. La simulación ejecuta estos árbitros:
   - `verificar_especificaciones`;
   - `generar_indice_tareas --verificar`;
   - `verificar_reparto`;
   - `test_reparto`;
   - `test_indice_tareas`;
   - `test_ci29_sin_generados_compartidos`;
   - `test_vpa_map`;
   - `test_verificar_alcance_pr`;
   - `test_alembic_cabeza_por_sala`;
   - `test_adpa_bulkhead`, si hay código.
5. Lo fusiono con `gh pr merge N --merge --match-head-commit <sha completa>`.
6. Con migración, compruebo que la simulación dé una cabeza por sala.

## Errores propios reconocidos en este tramo

- **#818:** atribuí el fallo a los CRLF cuando la causa era una prueba vacua de test_ci29. Se corrigió en la prueba y se revirtió el relleno de briefs ajenos.
- **#834:** falló `test_vpa_map` por un alta de token que faltaba, y mi simulación no ejecutaba esa prueba. Ahora la incluyo.
- **Comando de migración:** di un comando con `<digest>` de ejemplo. El propietario lo pegó tal cual y no cambió nada. Además, ninguna imagen del registro tenía las migraciones nuevas. Se resolvió con la entrada `publicar` y un brief que valida el digest con una expresión regular.
- **DEMO-05d:** dije que no constaba la aprobación de la opción a, pero sí consta (`d40c9ad1`). Lo corregí con el Arquitecto.

## Pendientes

**Del propietario:**

- aplicar en Cloud SQL las seis migraciones pendientes, junto con RM-25b y RM-27 cuando se fusionen;
- crear el secreto `WEBHOOKS_CLAVE_CIFRADO`;
- hacer DEMO-07 y GCP-05b;
- borrar el proyecto de Vercel;
- pegar el log del backend local del error 500 del preanálisis. En la nube no aparece ni en 1 h ni en 24 h de logs.

**Del Arquitecto:**

- escribir la especificación de DEMO-05d.

**Del Tech Lead:**

- reescribir en estado final la sección «una sola cabeza» de `governance/operaciones/entornos/produccion/MIGRAR_PRODUCCION.md`, porque CI-28 da una cabeza por sala.

**Del CTO:**

- revisar, simular y fusionar los PR de la tanda;
- escribir el brief al propietario para que `deploy-gcp.yml` publique un digest ya construido, sin reconstruir la imagen. El 2026-11-15 la revisión publicada no era la imagen que migró (Aporte 160);
- rehacer desde `origin/main` la hoja `governance/apoyo/BRIEFS_TAREAS_LIBRES.md`, que está sin commitear y quedó desfasada tras #882.
