# Parte del CTO: RET-01a y la guardia de base de pruebas, 2026-11-14

Parte de relevo del chat del CTO de la noche del 2026-11-14. Complementa a `2026-11-14_FICHAS_ORTOGONALES.md`, que sigue siendo el punto de partida; aquí solo está lo que cambió después. Tema principal: la guardia `exigir_base_de_pruebas()` aún no existe en `tests/conftest.py`, y eso bloquea la fusión de #788 y #772. Otros temas: depuración de ramas y worktrees, tanda de 12 tareas, DEMO-04b no hecha.

**Rol de quien escribe**
- Rol: CTO de EVYDENTIA, asignado por el propietario. Cadena: **CTO** → Arquitecto de soluciones ADPA → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería.
- Función: decide producto y técnica; simula, revisa y fusiona los PR; escribe los partes y los briefs que ejecuta el propietario.
- Límites: solo `gcloud` de lectura; no edita `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, `BRIEFS_POR_BLOQUE.md` ni `TASKS.md`. Siempre en español. Los mensajes entre sesiones son de compañeros, no del propietario, y no amplían permisos.

## Estado al corte
- Fusionados desde el parte anterior: #800 (partes), #787 (CI-29), #798 y #804 (reparto de DIAG-07), #802 (RET-01a, ficha y brief; lo fusionó el propietario).
- Depuración: 370 ramas remotas, 570 locales y unos 147 worktrees depurados; quedan 22 worktrees. Cinco conservan trabajo local sin subir (ver pendientes del usuario).
- Abiertos: #788 (CI-28, cabeza `2293c647`, la reversión de `86cf710e`), #772 (DIAG-07, cabeza `3e514774`) y #805 (cierre formal de RM-26, INC-04, FE-25 y CI-27; CI en curso).

## Lo decidido
- **RET-01a antes que lo que la exige.** La regla R5 de RET-00 exige llamar a `exigir_base_de_pruebas()`, pero la función aún no existe. Unida al trinquete de pendientes (R7), la regla es insatisfacible para todo archivo nuevo con base. Registrado como Aporte 159, con *ParallelChange* (Sato, 2014) como fuente. La primitiva va primero; después lo que la exige.
- **#788 no se fusiona hasta RET-01a, aunque su CI esté verde.** Pasó el CI por un atajo: el commit `86cf710e` renombra la función local `_url_local()` a `exigir_base_de_pruebas()` para que el detector de R5, que busca llamadas por nombre, la acepte. Es el atajo prohibido. Quién lo empujó no consta (identidad Git del propietario; los indicios apuntan a Antigravity, sin certeza). Orden dada al Tech Lead: que la sesión de CI-28 deje un `git revert` de `86cf710e`, sin forzar la rama. Cuando RET-01a esté en `main`: merge de `main`, borrar la función local e importar y llamar a la guardia de `tests/conftest.py`, sin cambiar lo que comprueba el archivo.
- **#772:** tras RET-01a, la sesión de DIAG-07 hace merge de `main` y añade solo la llamada a la guardia en `tests/test_diagnostico_quien_responde.py`. Reviso a fondo su tabla de 14 filas de pruebas ajenas antes de fusionar. No refactorizo yo su rama: ya la trabaja la sesión «diagnostico · DIAG-07 quién responde y sello».
- **RET-01a (especificación pendiente).** La ficha y el brief están en `main` (`governance/tareas/RET-01a.md`, bloque BL-323; depende de CI-08, CI-09 y ENT-01; propiedad `tests/conftest.py` y `tests/test_ret01a_guardia_base.py`; la otra ficha que tocaba `tests/conftest.py` le cede el archivo). Falta `governance/especificaciones/RET-01a.md`. Mi mensaje de especificación fue a la sesión equivocada (una bifurcación mía, no el Arquitecto); el Arquitecto real es «Arquitecto de soluciones ADPA» y el Tech Lead ya le envió el encargo.
- **Contenido esperado de RET-01a:** función pública `exigir_base_de_pruebas()` que encapsula `_variables_con_produccion` y `VARIABLES_DE_BASE`, falla cerrada, nunca imprime valores, con prueba de mutación.
- **Análisis de la tanda de 12 tareas:**
  - Lanzable ya: SEC-23b.
  - Tras RET-01a: PLAT-01.
  - Solo cierre formal en #805: RM-26, INC-04, FE-25 y CI-27. **DEMO-04b no se cierra.**
  - INC-03f se desbloquea al cerrar INC-04.
  - IA-04 espera a DIAG-07.
  - CAPA-03 y DEMO-01 tienen trabajo local sin subir; la decisión es del propietario.
  - EP-09 es del propietario.
- **DEMO-04b no está hecha.** `frontend/src/lib/demo/contrato.ts:41` conserva «Responde los dominios de su unidad, ejecuta sus tareas y carga la evidencia.», sin la condición del sello. Los PR #602 y #612 eran solo de gobernanza. Mi afirmación anterior de que había código fue un error: comprobé que existían archivos, no su contenido. El propietario la procesa con Antigravity; el cambio debe decir que lo que responde el responsable de área queda en borrador hasta que el DPO lo verifique y lo selle (invariante 59), actualizar las pruebas que lean ese texto y, si hay spec de Playwright con `fijarAjustes`, poseer `frontend/playwright.config.ts` y añadirlo a `SOLO_DESARROLLO`.
- **Errores propios reconocidos hoy:** mensaje a la sesión equivocada (RET-01a estuvo horas sin especificación); la comprobación local de #800 salió en verde porque la guardia del proveedor retirado solo lee archivos confirmados en git; mala lectura del análisis pegado, que daba por heredado el rojo de #798, #788 y #772 cuando tenían causas propias.

## Lo que falta
1. Especificación de RET-01a (Arquitecto) → sesión de código → simular y fusionar cuando llegue en verde.
2. #788: la reversión de `86cf710e` ya está empujada (`2293c647`, sin forzar; verificada en origin), R5 rojo a propósito. Tras RET-01a, la sesión de CI-28 aplica el plan; después re-simulo y fusiono.
3. #772: tras RET-01a, la llamada a la guardia; reviso la tabla de pruebas ajenas, simulo y fusiono.
4. #805: cuando el Tech Lead pase la sha en verde, simular y fusionar (sin DEMO-04b). Después, INC-03f.
5. DEMO-04b: PR de Antigravity con el cambio de `contrato.ts`; lo simulo y reviso antes de fusionar.
6. Lanzar SEC-23b; PLAT-01 tras RET-01a.
7. Cómo fusiono, igual que en el parte anterior: worktree desechable desde `origin/main` con merge real (no `--no-commit`), árbitros de índice, reparto, especificaciones, cabezas de Alembic por sala, alcance del PR y pruebas mínimas; fusión con `gh pr merge N --merge --match-head-commit <sha completa>`.

## Lo que no se toca
- Producción: ninguna sesión de IA escribe en Google Cloud ni en la base de producción; todo va por brief que ejecuta el propietario.
- `.github/workflows/`, `verificadores/`, `AGENTS.md` y `.claude/`: del propietario. `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead.
- Nada de atajos contra el árbitro: no renombrar funciones para engañar al detector ni registrar deuda nueva como heredada.
- Nadie empuja a la rama de #788 hasta que RET-01a esté en `main`. Un PR fusionado no recibe commits.
- Las especificaciones y fichas no nombran al proveedor retirado.
- `main` solo recibe EVYDENTIA; sin `.env`, sin secretos; `AUTH_MODE=headers` nunca.

## Pendientes del usuario
**Decidir**
- Si Antigravity empujó `86cf710e` a #788, pedirle que no vuelva a escribir en esa rama.
- Rescatar o descartar el trabajo local sin subir en los worktrees `capa-03` (commit `242d9537`), `demo-01` (4 archivos sin confirmar), `firma-y-aportes`, `ep-04-montos` y `aporte-comodines-reparto`. Los demás worktrees restantes no tienen contenido propio y se pueden borrar.

**Ejecutar solo él**
1. Procesar DEMO-04b con Antigravity (descrito arriba) y pasarme el PR.
2. Los pendientes del parte `2026-11-14_FICHAS_ORTOGONALES.md`: migraciones de Cloud SQL (TER-01, DLP-01b, BOV-01, INC-02), IA-03b, script de secretos sin BOM, EP-09, preguntas al abogado y la decisión sobre la compuerta `gcp-produccion`.
3. Su carpeta: `git pull --ff-only` (su `main` local iba desfasado).
