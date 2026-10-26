# Briefs por bloque de trabajo — EVYDENTIA
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento:** 37 tareas abiertas de 115; 78 hechas. Biblioteca aporta 23 pendientes: dos en BL-83 y 21 sin asignar.

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
| 13 | — | BL-66 (QA-07), BL-67 (QA-08) y BL-68 (ORG-12) ya están hechas: sin bloque pendiente. |
| 14 | — | BL-69 (DIAG-01) y BL-70 (RAT-01) ya están hechas: sin bloque pendiente. |
| 15 | — | BL-72 (RAT-02), BL-73 (RAT-03), BL-75 (FE-14), BL-76 (RM-20) y BL-82 (RAT-04) ya están hechas. |
| 16 | BL-77, BL-78, BL-84, BL-86 | Obligaciones de gran escala, colores de la hoja de ruta (crea el ayudante de contraste), retiro de los datos inventados del frontend y banco de las 80 preguntas en el servidor. |
| 17 | BL-79, BL-80, BL-85 | Colores del diagnóstico y de los demás módulos (esperan a FE-15 por el ayudante de contraste y a API-01 por los módulos que comparten) y contexto real para la IA con el catálogo P1-P80 del banco (espera a DIAG-02). |
| 18 | BL-81 | Se retira la lista de excepciones del tema claro; árbitro estático contra colores fijos. |
| 19 | BL-83 | Biblioteca: BIB-105 y después BIB-108; preparado, sin lanzar. BL-82 de RAT-04 se conserva. |

## Briefs

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

**Contexto.** Sala(s): `frontend`. Depende de: `FE-15`, `QA-07`, `API-01`. Especificaciones: `governance/tareas/FE-16.md`.

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

**Contexto.** Sala(s): `frontend`. Depende de: `FE-15`, `FE-14`, `SEC-08`, `MTGE-01`, `FE-19`, `API-01`. Especificaciones: `governance/tareas/FE-17.md`.

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

### BL-83 · biblioteca-base-e-inventario  (tanda 19)

**Contexto.** Sala Biblioteca declarada como planificada en PRD §7.1; fichas adscritas a Biblioteca y áreas colaboradoras. Declaración documental resuelta; decisiones editoriales y autorización de implementación pendientes (ver plan). Plan de coordinación: `governance/apoyo/BIBLIOTECA_PLAN.md`. Bloque preparado, no lanzado. No modifica documentos originales del kit ni implementa formularios/generación.

**Objetivo** (en este orden; una rama y un PR por task):

1. `BIB-105` — Administración editorial y base de la sala; revisiones y publicación controlada.
2. `BIB-108` — Catálogo inicial e importación idempotente; solo después de integrar la anterior.

**Rastro ¤** (existentes; sin afirmar un nuevo rastro de Biblioteca):

- Reutilizar `¤adpa`, `¤rbac-tenant` y `¤arbitro`. Buscar sus definiciones antes de desarrollar.

**Escribe** (unión exacta de propiedad de sus fichas):

  - `features/biblioteca/__init__.py`
  - `features/biblioteca/biblioteca_service.py`
  - `features/biblioteca/domain/base.py`
  - `features/biblioteca/domain/editorial.py`
  - `features/biblioteca/services/editorial.py`
  - `features/biblioteca/services/autorizacion.py`
  - `api/routers/biblioteca_editorial.py`
  - `alembic/versions/*_biblioteca_base.py`
  - `app_core/errors.py#BIB-105`
  - `frontend/src/lib/biblioteca/http.ts`
  - `frontend/src/lib/biblioteca/editorial.ts`
  - `frontend/src/components/biblioteca/editorial/**`
  - `frontend/src/app/harness-biblioteca/editorial/**`
  - `tests/test_bib_105_editorial.py`
  - `frontend/tests/biblioteca/editorial.spec.ts`
  - `scripts/importar_catalogo_biblioteca.py`
  - `features/biblioteca/services/importacion.py`
  - `features/biblioteca/biblioteca_service.py#BIB-108`
  - `data/biblioteca/manifiesto_inicial.json`
  - `tests/test_bib_108_importacion.py`

**No hagas:**

- No ejecutar este bloque por el solo hecho de registrarlo. No escribir fuera de la propiedad de la task activa; la unión del bloque no amplía esa propiedad.
- No publicar v0.1, ofrecer planificadas como descargas, crear datos de clientes, migrar producción ni copiar secretos.
- No editar gobernanza reservada ni implementar las otras 21 tasks. No marcar hecha ninguna tarea.

**Hecho si** (futuro; no ejecutado en este registro):

- Pasa el árbitro de cada ficha, incluido RLS real donde proceda y mutación documentada.
- Importador: 50 entradas = 8 archivos en revisión + 2 salidas por mapear + 40 planificadas; segunda ejecución sin duplicados.
- Índice y reparto con código 0. Antes de integrar cada rama: `python scripts/verificar_reparto.py --rama feat/bib-105 --bloque BL-83 --base origin/main` o la rama de la segunda task.
- BIB-105/BIB-108 no completan por sí solas la Entrega 1; faltan acceso, catálogo/ficha, descarga y documentos externos/historial.

### BL-84 · sin-datos-inventados  (tanda 16)

**Contexto.** Sala(s): `frontend`. Depende de: `MTGE-01`, `RAT-02`, `FE-11`, `LEG-01` (hechas). Especificaciones: `governance/tareas/API-01.md`.

**Objetivo** (en este orden):

1. `API-01` — Sin datos inventados cuando el servidor falla: el frontend muestra el error

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 47 coincidencias en 13 archivos.
- `¤arbitro`: 85 coincidencias en 36 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/api.ts`
  - `frontend/src/components/modules/RatModule.tsx`
  - `frontend/src/components/modules/CapaModule.tsx`
  - `frontend/src/components/modules/DiagnosticoModule.tsx`
  - `frontend/src/components/modules/DpoCockpitModule.tsx`
  - `frontend/src/components/modules/RagCopilotPanel.tsx`
  - `tests/test_sin_respaldos_inventados.py`
  - `frontend/tests/api/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `API-01`: pytest tests/test_sin_respaldos_inventados.py + Playwright de frontend/tests/api + suite Playwright completa + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-85 · contexto-real-ia  (tanda 17)

**Contexto.** Sala(s): `roadmap`, `diagnostico`, `frontend`. Depende de: `DIAG-01`, `RAT-01`, `RM-17` (hechas) y `DIAG-02` (BL-86). Especificaciones: `governance/tareas/RM-19.md` (decisión del propietario: P1-P80 = las 80 preguntas del banco de la plataforma, no el Excel).

**Objetivo** (en este orden):

1. `RM-19` — La IA genera la hoja de ruta con el diagnóstico y el RAT reales; catálogo P1-P80 = las 80 preguntas del banco de la plataforma

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 50 coincidencias en 42 archivos.
- `¤copiloto-ia`: 33 coincidencias en 11 archivos.
- `¤diagnostico`: 64 coincidencias en 11 archivos.

**Escribe** (lista exclusiva):

  - `features/roadmap/services/generacion_en_linea.py`
  - `features/roadmap/services/contexto_generacion.py`
  - `features/roadmap/ai/roadmap_prompts.py`
  - `features/roadmap/domain/models.py`
  - `features/roadmap/workers/roadmap_worker.py`
  - `features/roadmap/roadmap_service.py#RM-19`
  - `features/diagnostico/diagnostico_service.py#RM-19`
  - `frontend/src/components/modules/roadmap/planeacion/validacion.ts`
  - `tests/test_catalogo_controles.py`
  - `tests/test_roadmap_contexto_real.py`
  - `tests/test_roadmap_control_ref.py`
  - `tests/test_roadmap_generacion.py`
  - `tests/test_roadmap_schema.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RM-19`: pytest tests/test_catalogo_controles.py tests/test_roadmap_contexto_real.py tests/test_roadmap_control_ref.py tests/test_roadmap_generacion.py tests/test_roadmap_schema.py contra una rama Neon de revisión + suite completa + tsc --noEmit; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-86 · banco-preguntas-servidor  (tanda 16)

**Contexto.** Sala(s): `diagnostico`. Depende de: `DIAG-01`, `MTGE-01`, `RAT-01` (hechas). Especificaciones: `governance/tareas/DIAG-02.md` (decisión del propietario: la fuente es el banco de la plataforma, no el Excel).

**Objetivo** (en este orden):

1. `DIAG-02` — El banco de 80 preguntas de la plataforma vive en el servidor (hoy el backend usa 48 preguntas de relleno)

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 64 coincidencias en 11 archivos.

**Escribe** (lista exclusiva):

  - `features/diagnostico/domain/banco_preguntas.json`
  - `features/diagnostico/domain/models.py`
  - `features/diagnostico/services/engine.py`
  - `features/diagnostico/services/report_generator.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-02`
  - `api/routers/diagnostico.py`
  - `scripts/exportar_banco_preguntas.mjs`
  - `tests/test_banco_preguntas.py`
  - `tests/test_diagnostico_timebox.py`
  - `tests/test_api_gateway.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No cambies las preguntas ni el banco del frontend (`frontend/src/lib/bancoPreguntas/`): solo se leen.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-02`: pytest tests/test_banco_preguntas.py tests/test_diagnostico_timebox.py tests/test_api_gateway.py + suite completa; node scripts/exportar_banco_preguntas.mjs --verificar con código 0; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

## Sin agente (decisiones del propietario y trabajo por asignar)

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

### Biblioteca pendiente de asignación posterior

Estas tasks quedan registradas, sin autorización de implementación ni tanda de lanzamiento. Se asignarán después según sus dependencias; solo BL-83 está preparado ahora.

- `BIB-101` — Contexto y acceso.
- `BIB-102` — Catálogo y búsqueda.
- `BIB-103` — Ficha de plantilla.
- `BIB-104` — Descarga controlada.
- `BIB-106` — Documentos externos del cliente.
- `BIB-107` — Documentos por empresa.
- `BIB-201` — Formulario por versión.
- `BIB-202` — Reutilización y procedencia.
- `BIB-203` — Tablas de captura.
- `BIB-204` — Aplicabilidad explicable.
- `BIB-205` — Generación de Word y Excel.
- `BIB-206` — Vista previa y fidelidad.
- `BIB-207` — Concurrencia y trabajos de generación.
- `BIB-208` — Cobertura de ocho fichas.
- `BIB-301` — Revisión y aprobación.
- `BIB-302` — Integración con acciones.
- `BIB-303` — Evidencias y verificación.
- `BIB-304` — Actualización normativa y documental.
- `BIB-305` — Indicadores verificables.
- `BIB-306` — Historial y conservación.
- `BIB-307` — Aceptación de extremo a extremo.

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
