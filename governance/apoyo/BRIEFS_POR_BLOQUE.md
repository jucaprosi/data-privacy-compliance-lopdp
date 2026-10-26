# Briefs por bloque de trabajo — Hoja de Ruta Inteligente
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento:** 3 tasks abiertas (de 73; las otras 70 ya están hechas) = 3 en 3 bloques · 1 tanda · 12 cruces de archivos entre tasks (más las secciones reservadas).

## Preámbulo común (aplica a todos los bloques)

- Lee primero `governance/tareas/<ID>.md` de cada task de tu bloque (es la fuente de verdad), el PRD Módulo 5 (`governance/artefactos/PRD.md`, §7.1 catálogo de salas) y `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`.
- **Escribe solo en tu sala** y solo los archivos de la lista «Escribe» de tu bloque. Fuera de esa lista, no edites nada.
- **Cruza salas solo por compuertas** (`<sala>_service.py`): sin imports directos entre salas. Si tu sala no tiene compuerta, créala.
- **No edites** el índice generado de `governance/artefactos/TASKS.md` (lo produce `scripts/generar_indice_tareas.py --escribir`), `FUENTES_Y_BIBLIOGRAFIA.md` ni `APORTES_INEDITOS.md`. Los aportes los registra el coordinador.
- **Archivos de gobernanza reservada** (`.github/workflows/`, `verificadores/`, `ejecutar_arnes_*.bat`, `AGENTS.md`, `.claude/`, hooks, `scripts/entorno.bat`, `governance/artefactos/data/`): no los edites. Si tu task lo exigiera, prepara el parche y su prueba y entrégalos en el informe; el propietario los aplica. Con este reparto ninguna task de agente los toca (comprobado contra la `propiedad` de cada task); solo GOB-01, que va en «Sin agente».
- **Propiedad, no git:** el aislamiento es que cada archivo tenga un solo dueño (la `propiedad` de su task). Un archivo que no es tuyo no lo modificas, ni lo reviertes ni lo «limpias»: si el árbol aparece sucio con archivos ajenos es lo esperado, ignóralos; si algo ajeno te impide avanzar, PARA y repórtalo. No hace falta prohibir comandos de git: basta con no tener nada que revertir fuera de lo propio. Un árbol de trabajo propio (`git worktree`) es una comodidad, no la frontera.
- **Pruebas mínimas pero decisivas:** una prueba que falle si el comportamiento falta; no añadas pruebas ni tasks para alcanzar un número. Cada prueba nueva debe matar una mutación que ninguna otra mata: la que pasa aunque la función devuelva siempre verdadero no cuenta. Lo que entregues debe estar **conectado** a un árbitro que se ejecute (un verificador que nadie invoca no cuenta como entregado). Las exenciones de un verificador son datos declarados con su motivo, nunca exclusiones por directorio dentro del código.
- **El estado documentado no supera al verificado:** lo que no comprobaste con la salida de un árbitro lo marcas «no verificado»; no escribas «verificado» ni «integrado» sin ella. No copies a un documento lo que ya dice la task: referencia su ID.
- **El avance se mide por el diff, no por el mensaje del commit.** El mensaje declara solo lo que el diff contiene. Antes de integrar una rama, el coordinador ejecuta `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5: todo archivo del diff cabe en «Escribe»); si sobra uno, la rama no se integra.
- **El éxito lo decide un árbitro exógeno**, no tu opinión: el comando de «Hecho si» con código de salida 0. En Windows con Git Bash lanza el arnés con `cmd //c ".\ejecutar_arnes_tres_pilares.bat"` (o ruta absoluta) y acéptalo **solo** si la salida contiene `[ARNES] Los tres pilares pasaron exitosamente.` (`cmd /c` con una sola barra devuelve 0 sin ejecutar nada; ver Aporte 106). El intérprete lo resuelve `scripts\entorno.bat`; ver `governance/operaciones/ENTORNO_LOCAL.md`.
- **Rama y commit:** una rama por task (`feat/<id-de-la-task>`), desde `main` actualizado y en el orden del bloque; un PR por task (regla 8 de `governance/tareas/README.md`, que manda sobre este documento). Añade siempre los archivos por su ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`. Antes de cada commit comprueba la rama con `git branch --show-current`. No empujes ni abras PR sin que el coordinador lo pida.
- **Rastros `¤`:** búscalos con `git grep --untracked -F "<rastro>"` antes de buscar en lenguaje natural. No inventes rastros; si el de tu bloque no existe, tu primera task crea `¦tag` y lo indexa.
- **Los tokens `¤` no van en la interfaz de usuario** (solo en metadatos y código de gobernanza).

### Informe final (formato fijo)

```
BLOQUE: BL-xx <nombre>
RAMA / COMMITS: <rama> · <sha> por task
TASKS: <ID>: hecha | parcial | bloqueada — una línea
ÁRBITRO: <comando> → <código de salida>; arnés: <línea final vista sí/no>
ARCHIVOS ESCRITOS: <lista; debe estar incluida en «Escribe»>
PARCHES PARA EL PROPIETARIO: <ninguno | archivo y motivo>
NO VERIFICADO: <lo que no pudiste comprobar>
```

## Cruces y cómo se resuelve cada uno

Una task nunca escribe un archivo que otra task de la misma tanda también escribe; cuando dos tasks comparten archivo, una depende de la otra y el orden lo impone `depende_de`.

| # | Archivo(s) | Tasks | Resolución |
| :-- | :-- | :-- | :-- |
| C1 | `api/routers/arco_router.py`, `api/routers/terceros_router.py`, `features/derechos_arco/**`, `features/terceros/**`, `features/transferencias/**` | `ADPA-01` · `RM-02` | `RM-02` antes que `ADPA-01` (depende_de) |
| C2 | `features/roadmap/**` | `RM-01` · `RM-07` | `RM-01` antes que `RM-07` (depende_de) |
| C3 | `features/roadmap/**` | `RM-01` · `RM-08` | `RM-01` antes que `RM-08` (depende_de) |
| C4 | `features/roadmap/**` | `RM-01` · `RM-09` | `RM-01` antes que `RM-09` (depende_de) |
| C5 | `features/organizacion/**` | `RM-01` · `RM-10` | `RM-01` antes que `RM-10` (depende_de) |
| C6 | `features/roadmap/**` | `RM-01` · `RM-12` | `RM-01` antes que `RM-12` (depende_de) |
| C7 | `api/routers/roadmaps.py`, `features/roadmap/**` | `RM-01` · `RM-13` | `RM-01` antes que `RM-13` (depende_de) |
| C8 | `features/organizacion/**`, `tests/test_organizacion_*.py` | `RM-01` · `RM-15` | `RM-01` antes que `RM-15` (depende_de) |
| C11 | `app_core/models_base.py` | `RM-02` · `RM-15` | `RM-02` antes que `RM-15` (depende_de) |
| C12 | `main.py` | `RM-00` · `ENT-02` | `RM-00` antes que `ENT-02` (depende_de) |
| C14 | `features/organizacion/domain/roles.py`, `features/organizacion/services/sod_engine.py`, `tests/test_rbac_rules.py`, `tests/test_organizacion_api.py` | `RM-01` · `ORG-00` · `ORG-01` · `ORG-05` | `RM-01` → `ORG-00` → `ORG-01` → `ORG-02` → `ORG-05` (depende_de) |
| C15 | `features/organizacion/services/regla_tamano_engine.py` | `RM-16` · `ORG-00` · `ORG-02` | `ORG-00` antes que `ORG-02` (depende_de) |
| S | `features/organizacion/organizacion_service.py` (secciones `#ID`) | `RM-10` · `ORG-01` · `ORG-02` · `ORG-05` · `ORG-06` · `ORG-07` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |
| S | `features/roadmap/roadmap_service.py` (secciones `#ID`) | `RM-07` · `RM-08` · `RM-09` · `RM-12` · `RM-13` | Cada task escribe solo su sección `#<ID>` de la compuerta; secciones distintas no chocan (lo comprueba el verificador). |

Archivos que solo edita un bloque por diseño: `main.py` (BL-03) y `vercel.json` (BL-11).

## Tandas de lanzamiento

Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques son independientes. Los bloques estructurales (BL-01, BL-02) van **solos**, con los demás en pausa.

| Tanda | Bloques | Nota |
| :-- | :-- | :-- |
| 0 | — | BL-01 (RM-01, estructural) ya está hecha: sin bloque pendiente. |
| 1 | — | BL-02 (RM-02, estructural) ya está hecha: sin bloque pendiente. |
| 2 | — | BL-18 (FIRMA-01) y BL-27 (CI-01) ya están hechas: sin bloque pendiente. |
| 3 | — | BL-13, BL-15 y BL-32 ya están hechas: sin bloque pendiente. |
| 4 | — | BL-52 (SEC-09) ya está hecha: sin bloque pendiente. |
| 5 | — | BL-47 (LEG-02), BL-50 (SEC-08), BL-53 (DEV-01) y BL-55 (SEC-10) ya están hechas: sin bloque pendiente. |
| 6 | — | BL-25 (QA-01), BL-38 (ORG-01), BL-39 (ORG-07) y BL-54 (ORG-09) ya están hechas: sin bloque pendiente. |
| 7 | — | BL-40 (ORG-02), BL-41 (ORG-06) y BL-42 (FE-09) ya están hechas: sin bloque pendiente. |
| 8 | — | BL-43 (ORG-05) ya está hecha: sin bloque pendiente. |
| 9 | — | BL-51 (ORG-08) ya está hecha: sin bloque pendiente. |
| 10 | — | BL-56 (SEC-11), BL-57 (FE-10) y BL-58 (QA-02) ya están hechas: sin bloque pendiente. |
| 11 | — | BL-59 (ORG-10) y BL-60 (QA-03) ya están hechas: sin bloque pendiente. |
| 12 | — | BL-61 (ORG-11), BL-62 (FE-11), BL-63 (QA-04), BL-64 (QA-05) y BL-65 (QA-06) ya están hechas: sin bloque pendiente. |
| 13 | BL-66, BL-67, BL-68 | Árbitros de los criterios 6, 7 y 8 del MVP (solo pruebas de interfaz) y el área al distribuir (ORG-12, hallazgo de QA-06). |
| 14 | — | BL-69 (DIAG-01) y BL-70 (RAT-01) ya están hechas: sin bloque pendiente. |
| 15 | BL-72, BL-73, BL-75, BL-76, BL-82 | Plantilla de salud (requiere autorización de los autores de SALUDATA), EIPD persistida, persistencia de la interfaz, informe PDF por rol y retiro del RAT en JSON. BL-74 (MTGE-01) ya está hecha; RM-19 espera la decisión de catálogo. |
| 16 | BL-77, BL-78 | Obligaciones de gran escala (depende de MTGE-01) y colores de la hoja de ruta, que crea el ayudante de contraste compartido. |
| 17 | BL-79, BL-80 | Colores del diagnóstico y de los demás módulos. |
| 18 | BL-81 | Se retira la lista de excepciones del tema claro; árbitro estático contra colores fijos. |

## Briefs

### BL-66 · ergonomia-y-ficha  (tanda 13)

**Contexto.** Sala(s): `frontend`. Depende de: `QA-03` (hecha). Especificaciones: `governance/tareas/QA-07.md`.

**Objetivo** (en este orden):

1. `QA-07` — Árbitros de la ergonomía del dashboard y de la ficha organizacional previa (criterios 6 y 7 del MVP)

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 35 coincidencias en 8 archivos.
- `¤arbitro`: 75 coincidencias en 28 archivos.

**Escribe** (lista exclusiva):

  - `frontend/tests/ergonomia/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `QA-07`: Playwright de frontend/tests/ergonomia con la API simulada; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-67 · purga-evidencias  (tanda 13)

**Contexto.** Sala(s): `frontend`. Depende de: `QA-03` (hecha). Especificaciones: `governance/tareas/QA-08.md`.

**Objetivo** (en este orden):

1. `QA-08` — Árbitro de la purga de evidencias al cambiar de normativa (criterio 8 del MVP)

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 30 coincidencias en 12 archivos.
- `¤arbitro`: 75 coincidencias en 28 archivos.

**Escribe** (lista exclusiva):

  - `frontend/tests/purga/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `QA-08`: Playwright de frontend/tests/purga con la API simulada; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-68 · area-al-distribuir  (tanda 13)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-08`, `ORG-00`, `ORG-08`, `QA-06`, `FE-01`, `FE-03`, `FE-07`, `QA-01` (todas hechas; dueñas previas de sus archivos). Especificaciones: `governance/tareas/ORG-12.md`.

**Objetivo** (en este orden):

1. `ORG-12` — El coordinador fija el área de una tarea al distribuirla (las tareas generadas no la traen)

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 49 coincidencias en 40 archivos.
- `¤rbac-tenant`: 50 coincidencias en 39 archivos.

**Escribe** (lista exclusiva):

  - `api/routers/roadmaps_asignacion.py`
  - `features/roadmap/services/tarea_asignacion_engine.py`
  - `tests/test_roadmap_tarea_asignacion.py`
  - `tests/test_e2e_hoja_de_ruta_real.py`
  - `frontend/src/components/modules/roadmap/olas/OlasView.tsx`
  - `frontend/src/lib/roadmap/cliente.ts`
  - `frontend/src/store/useRoadmapStore.ts`
  - `frontend/src/lib/roadmap/mockServer.ts`
  - `frontend/tests/roadmap/olas.spec.ts`
  - `frontend/tests/roadmap/e2e/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-12`: pytest tests/test_roadmap_tarea_asignacion.py tests/test_e2e_hoja_de_ruta_real.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/roadmap + tsc --noEmit y next build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-72 · plantilla-salud  (tanda 15)

**Contexto.** Sala(s): `rat`, `frontend`. Depende de: `DIAG-01`, `ENT-02`, `RAT-01`, `RM-00`. Especificaciones: `governance/tareas/RAT-02.md`.

**Objetivo** (en este orden):

1. `RAT-02` — Plantilla sectorial de salud: el RAT arranca de un catálogo de establecimientos de salud

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 62 coincidencias en 9 archivos.
- `¤rat`: 14 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `features/rat/domain/plantillas/salud.json`
  - `features/rat/services/plantilla_engine.py`
  - `features/rat/rat_service.py#RAT-02`
  - `api/routers/rat_plantillas.py`
  - `main.py#RAT-02`
  - `tests/test_rat_plantilla_salud.py`
  - `frontend/src/components/modules/rat/PlantillaSectorial.tsx`
  - `frontend/tests/rat/plantilla.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RAT-02`: pytest tests/test_rat_plantilla_salud.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/rat; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-73 · eipd-persistida  (tanda 15)

**Contexto.** Sala(s): `rat`. Depende de: `RAT-01`, `ENT-02`, `RM-00`. Especificaciones: `governance/tareas/RAT-03.md`.

**Objetivo** (en este orden):

1. `RAT-03` — EIPD persistida por actividad del RAT, con matriz de probabilidad e impacto 5x5

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rat`: 14 coincidencias en 9 archivos.
- `¤riesgos-eipd`: 18 coincidencias en 7 archivos.

**Escribe** (lista exclusiva):

  - `features/rat/services/mtge_engine.py`
  - `features/rat/services/eipd_engine.py`
  - `features/rat/rat_service.py#RAT-03`
  - `api/routers/rat_eipd.py`
  - `main.py#RAT-03`
  - `alembic/versions/20261024_rat_eipd.py`
  - `tests/test_rat_eipd.py`
  - `tests/test_compliance_graph.py`
  - `tests/test_eipd_drift_sensor.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RAT-03`: pytest tests/test_rat_eipd.py contra una rama Neon de revisión + suite completa; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-75 · persistencia-interfaz  (tanda 15)

**Contexto.** Sala(s): `frontend`. Depende de: `DIAG-01`, `QA-07`, `FE-06`, `FE-07`, `FE-19`. Especificaciones: `governance/tareas/FE-14.md`.

**Objetivo** (en este orden):

1. `FE-14` — El tamaño de los paneles y el tema se conservan al recargar

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 36 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/store/useAuditStore.ts`
  - `frontend/tests/ergonomia/persistencia.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-14`: Playwright de frontend/tests/ergonomia + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-76 · informe-pdf  (tanda 15)

**Contexto.** Sala(s): `roadmap`, `frontend`. Depende de: `ORG-12`, `FE-03`, `FE-12`, `ENT-02`, `RM-00`. Especificaciones: `governance/tareas/RM-20.md`.

**Objetivo** (en este orden):

1. `RM-20` — Informe PDF del estado de la implementación, por rol y para constancia

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 52 coincidencias en 42 archivos.
- `¤rbac-tenant`: 49 coincidencias en 40 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/informe_estado_engine.py`
  - `features/roadmap/roadmap_service.py#RM-20`
  - `api/routers/roadmaps_informe.py`
  - `main.py#RM-20`
  - `tests/test_roadmap_informe_pdf.py`
  - `frontend/src/components/modules/roadmap/informe/DescargarInforme.tsx`
  - `frontend/src/components/modules/roadmap/olas/OlasView.tsx`
  - `frontend/src/lib/roadmap/cliente.ts`
  - `frontend/tests/roadmap/informe.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RM-20`: pytest tests/test_roadmap_informe_pdf.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/roadmap/informe.spec.ts + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-77 · obligaciones-gran-escala  (tanda 16)

**Contexto.** Sala(s): `riesgos_mtge`, `frontend`. Depende de: `MTGE-01`, `RAT-01`, `ENT-02`, `RM-00`. Especificaciones: `governance/tareas/MTGE-02.md`.

**Objetivo** (en este orden):

1. `MTGE-02` — Obligaciones del tratamiento a gran escala: auditoría anual, informe anual, política de privacidad y plazo del DPO

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤mtge-granescala`: 20 coincidencias en 8 archivos.
- `¤rbac-tenant`: 49 coincidencias en 40 archivos.

**Escribe** (lista exclusiva):

  - `features/riesgos_mtge/services/obligaciones_engine.py`
  - `features/riesgos_mtge/riesgos_mtge_service.py#MTGE-02`
  - `api/routers/riesgos_mtge_obligaciones.py`
  - `main.py#MTGE-02`
  - `alembic/versions/20261025_gran_escala_obligaciones.py`
  - `tests/test_mtge_obligaciones.py`
  - `frontend/src/components/modules/mtge/ObligacionesGranEscala.tsx`
  - `frontend/tests/mtge/obligaciones.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `MTGE-02`: pytest tests/test_mtge_obligaciones.py contra una rama Neon de revisión (incluido RLS) + suite completa + Playwright de frontend/tests/mtge/obligaciones.spec.ts; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-78 · colores-hoja-de-ruta  (tanda 16)

**Contexto.** Sala(s): `frontend`. Depende de: `RM-20`, `FE-13`. Especificaciones: `governance/tareas/FE-15.md`.

**Objetivo** (en este orden):

1. `FE-15` — Pantallas de la hoja de ruta legibles en los dos temas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 36 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx`
  - `frontend/src/app/harness-roadmap/olas/HarnessOlas.tsx`
  - `frontend/src/app/harness-roadmap/planeacion/HarnessPlaneacion.tsx`
  - `frontend/src/components/modules/roadmap/evidencia/EvidenciaPanel.tsx`
  - `frontend/src/components/modules/roadmap/olas/KpiBar.tsx`
  - `frontend/src/components/modules/roadmap/olas/OlasView.tsx`
  - `frontend/src/components/modules/roadmap/planeacion/PlaneacionForm.tsx`
  - `frontend/tests/contraste.ts`
  - `frontend/tests/roadmap/colores-hoja-de-ruta.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-15`: Playwright de frontend/tests/roadmap/colores-hoja-de-ruta.spec.ts + suite Playwright completa + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-79 · colores-diagnostico  (tanda 17)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-15`, `QA-07`. Especificaciones: `governance/tareas/FE-16.md`.

**Objetivo** (en este orden):

1. `FE-16` — Diagnóstico, configuración y preanálisis legibles en los dos temas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 36 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/DiagnosticCanvas.tsx`
  - `frontend/src/components/PerfilOperacionForm.tsx`
  - `frontend/src/components/ProjectConfig.tsx`
  - `frontend/src/components/SelectorDesplegable.tsx`
  - `frontend/src/components/config/CargaEvidencias.tsx`
  - `frontend/src/components/config/ResumenPoda.tsx`
  - `frontend/src/components/config/SelectorNormativa.tsx`
  - `frontend/src/components/copilot/AssessmentCopilotActions.tsx`
  - `frontend/src/components/copilot/CopilotWorkspace.tsx`
  - `frontend/src/components/dashboard/AssessmentResultPanel.tsx`
  - `frontend/src/components/evidencias/DropEvidencia.tsx`
  - `frontend/src/components/modules/DiagnosticoModule.tsx`
  - `frontend/src/components/modules/EvidenciasModule.tsx`
  - `frontend/src/components/modules/ReportesModule.tsx`
  - `frontend/src/components/preanalisis/ConsentimientoEnvio.tsx`
  - `frontend/src/components/preanalisis/PanelPreanalisis.tsx`
  - `frontend/src/components/preanalisis/PrellenadoMasivo.tsx`
  - `frontend/src/components/preanalisis/TarjetaPropuesta.tsx`
  - `frontend/src/components/ui/ScoreRing.tsx`
  - `frontend/tests/ergonomia/colores-diagnostico.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-16`: Playwright de frontend/tests/ergonomia/colores-diagnostico.spec.ts + suite Playwright completa + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-80 · colores-modulos  (tanda 17)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-15`, `FE-14`, `SEC-08`, `MTGE-01`, `FE-19`. Especificaciones: `governance/tareas/FE-17.md`.

**Objetivo** (en este orden):

1. `FE-17` — Marco del dashboard y demás módulos legibles en los dos temas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 36 coincidencias en 9 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/components/AuditHistory.tsx`
  - `frontend/src/components/CapaBoard.tsx`
  - `frontend/src/components/CentralDashboard.tsx`
  - `frontend/src/components/CommandPalette.tsx`
  - `frontend/src/components/IncidentPlaybook.tsx`
  - `frontend/src/components/MitigationTracker.tsx`
  - `frontend/src/components/layout/FileMenu.tsx`
  - `frontend/src/components/layout/DashboardHeader.tsx`
  - `frontend/src/components/layout/RoadmapWorkspaceView.tsx`
  - `frontend/src/components/layout/dashboardNavigation.ts`
  - `frontend/src/components/modules/ArcoModule.tsx`
  - `frontend/src/components/modules/DpoCockpitModule.tsx`
  - `frontend/src/components/modules/MtgeModule.tsx`
  - `frontend/src/components/modules/NiifDiagnosticoView.tsx`
  - `frontend/src/components/modules/NiifDoctrinaView.tsx`
  - `frontend/src/components/modules/NiifExportView.tsx`
  - `frontend/src/components/modules/NiifIngestaView.tsx`
  - `frontend/src/components/modules/NiifMpmView.tsx`
  - `frontend/src/components/modules/NiifReclasificacionView.tsx`
  - `frontend/src/components/modules/NiifSubtotalesView.tsx`
  - `frontend/src/components/modules/RagCopilotPanel.tsx`
  - `frontend/src/components/modules/TercerosModule.tsx`
  - `frontend/tests/ergonomia/colores-modulos.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-17`: Playwright de frontend/tests/ergonomia/colores-modulos.spec.ts + suite Playwright completa + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-81 · sin-colores-fijos  (tanda 18)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-15`, `FE-16`, `FE-17`, `FE-13`. Especificaciones: `governance/tareas/FE-18.md`.

**Objetivo** (en este orden):

1. `FE-18` — Sin colores fijos del tema oscuro: se retira la lista de excepciones del tema claro y un árbitro lo vigila

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 36 coincidencias en 9 archivos.
- `¤arbitro`: 79 coincidencias en 32 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/globals.css`
  - `tests/test_sin_colores_fijos.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-18`: pytest tests/test_sin_colores_fijos.py + suite Playwright completa (incluidas las pruebas de contraste de FE-12, FE-13, FE-15, FE-16 y FE-17) + next build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-82 · un-solo-rat  (tanda 15)

**Contexto.** Sala(s): `frontend`. Depende de: `RAT-01`, `MTGE-01` (hechas). Especificaciones: `governance/tareas/RAT-04.md`.

**Objetivo** (en este orden):

1. `RAT-04` — Retirar el RAT paralelo guardado en un archivo JSON del frontend

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rat`: 61 coincidencias en 16 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/actions/ratActions.ts`
  - `frontend/data/rat_master.json`
  - `tests/test_sin_rat_paralelo.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RAT-04`: pytest tests/test_sin_rat_paralelo.py + tsc --noEmit + suite Playwright completa; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

## Sin agente (solo el propietario)

- `RM-19` está bloqueada: el propietario decide cómo se relacionan las 80 preguntas del diagnóstico con el catálogo P1-P73 de la hoja de ruta (véase la ficha).- Crear el cliente OAuth de Google y cargar sus secretos (SEC-03, BL-15).
- Cargar las variables en Vercel y revisar la lista (OPS-01, BL-27); medir una generación completa dentro de 300 s (OPS-02, BL-29).
- Verificar el dominio en Resend (NOTIF-01, BL-17).
- Crear las ramas de Neon por agente de desarrollo (OPS-04, BL-27).
- Aplicar la protección de `main` que decida (CI-01, BL-27) y cualquier parche a archivos de gobernanza reservada que un bloque entregue.
- Aprobar los bocetos de firma electrónica y notificaciones (BL-17, BL-18).
- Decidir el antivirus de la evidencia, tras leer el boceto (SEC-05, BL-32), y pasar la CSP de modo informe a modo obligatorio cuando haya observado los informes (SEC-06, BL-33).
- Crear el cliente OAuth de Google, registrar sus orígenes y cargar NEXT_PUBLIC_GOOGLE_CLIENT_ID (FE-07, BL-34).
- Aplicar el job de Playwright al workflow del CI, que es de gobernanza reservada (TEST-02, BL-36).
- Antes de aplicar la migración de ORG-00, volver a medir cuántas personas tienen el rol `encargado` en producción (el 2026-10-18 eran 0); si hubiera alguna, se aplica en un momento sin uso.
- Las decisiones de diseño de ORG-01, ORG-02, ORG-06 y ORG-07 se asumieron con su base legal (véase «Decisiones asumidas» de cada especificación) y se revisan si la Superintendencia emite normativa adicional, que la propia norma prevé.
- Los plazos (notificación de vulneraciones, inscripción del delegado, vigencia de las excepciones) quedan aplazados por decisión del propietario.
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
