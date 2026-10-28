# Briefs por bloque de trabajo — EVYDENTIA
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento (2026-10-28, reparto del propietario en tandas de hasta cuatro sin archivos enteros en común):** 45 tareas abiertas de 150; 105 hechas. EVI-01 (BL-94) sigue en la tanda 20, pausada hasta configurar R2. tanda 21 (EVY): FE-22, FE-23, FE-24, RM-21; tanda 22 (EVY): DPO-02, SEC-12, DIAG-04, CAPA-02; tanda 23 (EVY): ORG-16, DIAG-06, RM-22, EVI-02; tanda 24 (EVY): ORG-15, DIAG-05, CAPA-03, ORG-17; tanda 25 (EVY): DIAG-07; tanda 26 (BIB): BIB-100, BIB-109, BIB-101, GOB-03; tanda 27 (BIB): BIB-201, BIB-102, BIB-110; tanda 28 (BIB): BIB-107, BIB-202; tanda 29 (BIB): BIB-301, BIB-103, BIB-203, BIB-204; tanda 30 (BIB): BIB-104, BIB-205, BIB-302, BIB-304; tanda 31 (BIB): BIB-106, BIB-206, BIB-207, BIB-303; tanda 32 (BIB): BIB-208, BIB-305, BIB-306; tanda 33 (BIB): BIB-307. En backlog, sin agente, por decisión del propietario: LEG-03 y REG-01.

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
- **Rama y commit:** trabaja en la rama de la persona que te lanzó (`dev/juan-carlos`, `dev/aleczandra` o `dev/jose`), al día con `main` y en el orden del bloque; cada task en sus propios commits con su id en el mensaje. El PR a `main` es el de esa persona, en la ventana nocturna (regla 10 de `governance/tareas/README.md`, que manda sobre este documento). Añade siempre los archivos por su ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`. Antes de cada commit comprueba la rama con `git branch --show-current`. No empujes ni abras PR sin que el coordinador lo pida.
- **Secciones `#ID` de una compuerta compartida** (`organizacion_service.py`, `diagnostico_service.py`, `roadmap_service.py`…): añade tu sección **al final del archivo**, en el orden de su id, y no toques ninguna línea fuera de tus marcas `=== <ID> ===` … `=== fin <ID> ===`. Así dos fusiones de la misma noche no chocan en líneas vecinas.
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
| S | `frontend/src/app/dashboard/page.tsx` y `frontend/src/components/layout/dashboardNavigation.ts` | `FE-22` · `BIB-101` · `ORG-15` · `ORG-16` · `ORG-17` · `CAPA-02` · `DIAG-04` · `DIAG-06` | `FE-22` reescribe los dos archivos y crea `menus/` y `pantallas/` con un archivo vacío por tarea; las demás dependen de `FE-22` y escriben solo su archivo. BIB-101 conserva su sección `#BIB-101`. Así no se tocan líneas vecinas al fusionar varias en la misma noche. |
| S | `tests/test_matriz_permisos.py` | `RM-21` · `ORG-15` · `ORG-16` · `ORG-17` · `CAPA-02` · `DIAG-04` | `RM-21` (tras `ORG-14`) hace que la matriz lea sus filas de `tests/matriz/<ID>.py`; las demás dependen de `RM-21` y escriben solo su archivo de filas. |

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
| 16 | — | BL-77 (MTGE-02), BL-78 (FE-15), BL-84 (API-01) y BL-86 (DIAG-02) ya están hechas: sin bloque pendiente. |
| 17 | — | BL-79 (FE-16), BL-80 (FE-17), BL-81 (FE-18), BL-85 (RM-19), BL-87 (DPO-01) y BL-88 (LIM-01) ya están hechas: sin bloque pendiente. |
| 18 | — | BL-89 (CAPA-01) ya está hecha: sin bloque pendiente. |
| 19 | — | BL-83 (BIB-105 y BIB-108), BL-90 (ORG-13), BL-92 (DIAG-03) y BL-93 (INC-01) ya están hechas: sin bloque pendiente. |
| 20 | BL-94 | BL-91 (FE-21) ya está hecha. Las evidencias se guardan y se comprueban en el servidor (EVI-01); **pausada** hasta que el propietario configure R2 (variables en el backend de Vercel, CORS y país del bucket). BIB-110 espera a EVI-01, que también toca `useAuditStore.ts`. |
| 21 | BL-95, BL-96, BL-97, BL-98 | **Estructura EVYDENTIA:** FE-22 (Navegación por los nueve menús de la estructura funcional, c); FE-23 (Un solo patrón de asistente (progreso, guardado, saltar paso); FE-24 (Tablero de la organización con las cuatro dimensiones y las ); RM-21 (Hallazgos con origen y una sola compuerta que convierte hall). |
| 22 | BL-99, BL-100, BL-104, BL-103 | **Estructura EVYDENTIA:** DPO-02 (Informe anual del DPO generado desde su bitácora y estado de); SEC-12 (Diseño de seguridad de los portales externos (titulares y en); DIAG-04 (El administrador asigna los dominios del assessment a encarg); CAPA-02 (Controles periódicos con frecuencia y responsable). |
| 23 | BL-102, BL-105, BL-136, BL-107 | **Estructura EVYDENTIA:** ORG-16 (Alta de la organización en el servidor con el asistente de s); DIAG-06 (Comparativo de un assessment con la línea base, por dimensió); RM-22 (Vistas de lista, tablero y cronograma de las tareas, con su ); EVI-02 (Vigencia y visibilidad de las evidencias y paquete para insp). |
| 24 | BL-101, BL-106, BL-108, BL-135 | **Estructura EVYDENTIA:** ORG-15 (Cartera de organizaciones por pertenencia, con semáforos por); DIAG-05 («No aplica» exige justificación en el assessment); CAPA-03 (La evidencia vencida reabre el control periódico y produce u); ORG-17 (Inventario de activos y sistemas, soportes y personas mínima). |
| 25 | BL-109 | **Estructura EVYDENTIA:** DIAG-07 (Responden el administrador y los encargados del diagnóstico). |
| 26 | BL-110, BL-117, BL-111, BL-134 | **Biblioteca (PMV):** BIB-100 (PMV de Biblioteca); BIB-109 (Plantillas Markdown del PMV en el catálogo); BIB-101 (Contexto y acceso); GOB-03 (Kit y documentación de Biblioteca versionados). |
| 27 | BL-119, BL-112, BL-118 | **Biblioteca (PMV):** BIB-201 (Formulario por versión); BIB-102 (Catálogo y búsqueda); BIB-110 (Biblioteca al cambiar de organización). |
| 28 | BL-116, BL-120 | **Biblioteca (PMV):** BIB-107 (Documentos por empresa); BIB-202 (Reutilización y procedencia). |
| 29 | BL-127, BL-113, BL-121, BL-122 | **Biblioteca (PMV):** BIB-301 (Revisión y aprobación); BIB-103 (Ficha de plantilla); BIB-203 (Tablas de captura); BIB-204 (Aplicabilidad explicable). |
| 30 | BL-114, BL-123, BL-128, BL-130 | **Biblioteca (PMV):** BIB-104 (Descarga controlada); BIB-205 (Generación de Word y Excel); BIB-302 (Integración con acciones); BIB-304 (Actualización normativa y documental). |
| 31 | BL-115, BL-124, BL-125, BL-129 | **Biblioteca (PMV):** BIB-106 (Documentos externos del cliente); BIB-206 (Vista previa y fidelidad); BIB-207 (Concurrencia y trabajos de generación); BIB-303 (Evidencias y verificación). |
| 32 | BL-126, BL-131, BL-132 | **Biblioteca (PMV):** BIB-208 (Cobertura de ocho fichas); BIB-305 (Indicadores verificables); BIB-306 (Historial y conservación). |
| 33 | BL-133 | **Biblioteca (PMV):** BIB-307 (Aceptación de extremo a extremo). |

## Briefs

### BL-94 · evidencias-en-el-servidor  (tanda 20)

**Contexto.** Sala(s): `evidencias`, `frontend`. Depende de: `DIAG-03` (BL-92), `DIAG-01`, `FE-14`, `FE-16`, `SEC-05`, y de las dueñas de las pruebas que adapta (`CAPA-01`, `DIAG-02`, `DPO-01`, `MTGE-01`, `RAT-01`, `ORG-00`, `ORG-08`, `TEST-01`). Especificaciones: `governance/tareas/EVI-01.md`.

**Objetivo** (en este orden):

1. `EVI-01` — Las evidencias se guardan en el servidor: el documento en el almacén de archivos, su registro en la base y la huella calculada por el servidor

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 30 coincidencias en 12 archivos.
- `¤diagnostico`: 74 coincidencias en 12 archivos.
- `¤rbac-tenant`: 63 coincidencias en 50 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261029_evidencias_documentales.py`
  - `features/evidencias/**`
  - `app_core/storage/r2.py`
  - `api/routers/evidencias.py`
  - `api/routers/diagnostico_resultados.py`
  - `tests/test_evidencias_persistencia.py`
  - `tests/test_evidencias_contrato.py`
  - `tests/test_evidencia_http.py`
  - `tests/test_api_gateway.py`
  - `frontend/src/lib/evidencias/**`
  - `frontend/src/components/evidencias/**`
  - `frontend/src/components/modules/EvidenciasModule.tsx`
  - `frontend/src/components/config/CargaEvidencias.tsx`
  - `frontend/src/components/DiagnosticCanvas.tsx`
  - `frontend/src/store/useAuditStore.ts`
  - `frontend/tests/evidencias/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- No aceptes la huella del navegador como la del documento: la calcula el servidor con el archivo descargado.
- No toques las evidencias de la Hoja de Ruta (`api/routers/roadmaps.py`) ni añadas antivirus.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción, la rama Neon `test` compartida ni el bucket real: en las pruebas el almacén se simula.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EVI-01`: pytest tests/test_evidencias_persistencia.py contra una rama Neon de revisión (incluido RLS con lopdp_app y el almacén de archivos simulado) + suite completa + vigilantes + Playwright de frontend/tests/evidencias + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-95 · navegacion-nueve-menus  (tanda 21)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-17`, `FE-19`, `FE-14`, `FE-06`, `FE-07`, `CAPA-01`, `TEST-02`, `FE-21`. Especificaciones: `governance/tareas/FE-22.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FE-22` — Navegación por los nueve menús de la estructura funcional, con submenús, y Ctrl+K sobre todas las pantallas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 49 coincidencias en 17 archivos.
- `¤navegacion-menus`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/components/layout/dashboardNavigation.ts`
  - `frontend/src/components/layout/MenuLateral.tsx`
  - `frontend/src/components/CommandPalette.tsx`
  - `frontend/tests/utiles.ts#FE-22`
  - `frontend/tests/navegacion/**`
  - `frontend/src/components/layout/menus/index.ts`
  - `frontend/src/components/layout/menus/base.ts`
  - `frontend/src/components/layout/pantallas/index.tsx`
  - `frontend/src/components/layout/pantallas/base.tsx`
  - `frontend/src/components/layout/menus/ORG-15.ts`
  - `frontend/src/components/layout/menus/ORG-16.ts`
  - `frontend/src/components/layout/menus/ORG-17.ts`
  - `frontend/src/components/layout/menus/CAPA-02.ts`
  - `frontend/src/components/layout/menus/DIAG-04.ts`
  - `frontend/src/components/layout/menus/DIAG-06.ts`
  - `frontend/src/components/layout/pantallas/ORG-15.tsx`
  - `frontend/src/components/layout/pantallas/ORG-16.tsx`
  - `frontend/src/components/layout/pantallas/ORG-17.tsx`
  - `frontend/src/components/layout/pantallas/CAPA-02.tsx`
  - `frontend/src/components/layout/pantallas/DIAG-04.tsx`
  - `frontend/src/components/layout/pantallas/DIAG-06.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No cambies salas, compuertas ni rutas de API, ni el contenido de las vistas.
- No crees pantallas nuevas: deja vacíos los archivos por tarea de `menus/` y `pantallas/`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-22`: Playwright de frontend/tests/navegacion + suite Playwright completa (las 25 pruebas que usan irASala siguen verdes) + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-96 · patron-asistente  (tanda 21)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-17`. Especificaciones: `governance/tareas/FE-23.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FE-23` — Un solo patrón de asistente (progreso, guardado, saltar pasos) para los flujos guiados

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 49 coincidencias en 17 archivos.
- `¤asistente`: 3 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/asistente/**`
  - `frontend/tests/asistente/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No implementes ningún flujo concreto.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-23`: Playwright de frontend/tests/asistente (página de prueba del componente) + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-97 · tablero-sin-cifra-unica  (tanda 21)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-17`, `DIAG-03`. Especificaciones: `governance/tareas/FE-24.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FE-24` — Tablero de la organización con las cuatro dimensiones y las brechas críticas, sin cifra única

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 49 coincidencias en 17 archivos.
- `¤tablero-dimensiones`: 4 coincidencias en 2 archivos.
- `¤diagnostico`: 80 coincidencias en 17 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/CentralDashboard.tsx`
  - `frontend/src/components/tableros/**`
  - `frontend/src/lib/tableros/**`
  - `frontend/tests/tableros/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No muestres ningún porcentaje ni puntaje global de la organización.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-24`: Playwright de frontend/tests/tableros con la API simulada + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-98 · hallazgos-plan-unico  (tanda 21)

**Contexto.** Sala(s): `roadmap`. Depende de: `RM-20`, `RM-19`, `DIAG-03`, `ORG-14`. Especificaciones: `governance/tareas/RM-21.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `RM-21` — Hallazgos con origen y una sola compuerta que convierte hallazgos en tareas del plan de acción

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 55 coincidencias en 44 archivos.
- `¤hallazgos`: 3 coincidencias en 2 archivos.
- `¤rbac-tenant`: 78 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261030_hallazgos.py`
  - `features/roadmap/domain/hallazgo.py`
  - `features/roadmap/services/hallazgo_engine.py`
  - `features/roadmap/roadmap_service.py#RM-21`
  - `api/routers/roadmaps_hallazgos.py`
  - `tests/test_roadmap_hallazgos.py`
  - `tests/test_matriz_permisos.py`
  - `tests/matriz/__init__.py`
  - `tests/matriz/RM-21.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No escribas otras secciones de `roadmap_service.py` ni el frontend de la hoja de ruta.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RM-21`: pytest tests/test_roadmap_hallazgos.py contra una rama Neon de revisión (incluido RLS con lopdp_app), con la prueba de INV_LOPDP_SINGLE_ACTION_PLAN (todo hallazgo abierto tiene tarea con origen) + suite completa + vigilantes; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-99 · dpo-informe-anual  (tanda 22)

**Contexto.** Sala(s): `dpo_cockpit`, `frontend`. Depende de: `DPO-01`, `FE-17`. Especificaciones: `governance/tareas/DPO-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DPO-02` — Informe anual del DPO generado desde su bitácora y estado de inscripción ante la SPDP

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤dpo-cockpit`: 12 coincidencias en 10 archivos.
- `¤dpo-informe-anual`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261030_dpo_inscripcion.py`
  - `features/dpo_cockpit/domain/inscripcion.py`
  - `features/dpo_cockpit/services/informe_anual_engine.py`
  - `features/dpo_cockpit/services/inscripcion_engine.py`
  - `features/dpo_cockpit/dpo_cockpit_service.py#DPO-02`
  - `api/routers/dpo_informe_anual.py`
  - `tests/test_dpo_informe_anual.py`
  - `frontend/src/components/modules/DpoCockpitModule.tsx`
  - `frontend/src/lib/dpo/informeAnual.ts`
  - `frontend/tests/dpo/informe-anual.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No calcules plazos ni calendarios de obligaciones (aplazados).
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DPO-02`: pytest tests/test_dpo_informe_anual.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/dpo + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-100 · seguridad-portales-externos  (tanda 22)

**Contexto.** Sala(s): `gobernanza`. Depende de: ninguna. Especificaciones: `governance/tareas/SEC-12.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `SEC-12` — Diseño de seguridad de los portales externos (titulares y encargados) antes de implementarlos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 77 coincidencias en 47 archivos.
- `¤portales-externos`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `governance/apoyo/DISENO_PORTALES_EXTERNOS.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Solo el documento de diseño: ni código ni rutas públicas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-12`: Revisión del propietario sobre el documento; python scripts/generar_indice_tareas.py --verificar con código 0.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-101 · cartera-por-pertenencia  (tanda 24)

**Contexto.** Sala(s): `organizacion`, `frontend`. Depende de: `ORG-13`, `ORG-14`, `FE-21`, `FE-22` (pendiente), `FE-24` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/ORG-15.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `ORG-15` — Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 78 coincidencias en 66 archivos.
- `¤cartera`: 2 coincidencias en 2 archivos.
- `¤tablero-dimensiones`: 4 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/organizacion/services/cartera_engine.py`
  - `features/organizacion/organizacion_service.py#ORG-15`
  - `api/routers/organizacion_cartera.py`
  - `tests/test_organizacion_cartera.py`
  - `tests/matriz/ORG-15.py`
  - `frontend/src/app/cartera/**`
  - `frontend/src/lib/cartera/**`
  - `frontend/tests/cartera/**`
  - `frontend/src/components/layout/menus/ORG-15.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No uses `BYPASSRLS` ni consultas sin contexto de organización.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-15`: pytest tests/test_organizacion_cartera.py y tests/test_organizaciones_por_persona.py contra una rama Neon de revisión con lopdp_app, con la prueba de INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP (la cartera lista solo organizaciones con rol vigente) + suite completa + Playwright de frontend/tests/cartera + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-102 · alta-organizacion-servidor  (tanda 23)

**Contexto.** Sala(s): `organizacion`, `frontend`. Depende de: `ORG-14`, `ORG-07`, `FE-08`, `FE-16`, `FE-22` (pendiente), `FE-23` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/ORG-16.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `ORG-16` — Alta de la organización en el servidor con el asistente de siete pasos, en lugar de la configuración local

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 78 coincidencias en 66 archivos.
- `¤alta-organizacion`: 2 coincidencias en 2 archivos.
- `¤asistente`: 3 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/organizacion/services/alta_engine.py`
  - `features/organizacion/organizacion_service.py#ORG-16`
  - `api/routers/organizacion_alta.py`
  - `tests/test_organizacion_alta.py`
  - `tests/matriz/ORG-16.py`
  - `frontend/src/components/ProjectConfig.tsx`
  - `frontend/src/components/organizacion/alta/**`
  - `frontend/src/lib/organizacion/alta.ts`
  - `frontend/tests/organizacion/alta.spec.ts`
  - `frontend/src/components/layout/menus/ORG-16.ts`
  - `frontend/src/components/layout/pantallas/ORG-16.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No toques `frontend/src/store/useAuditStore.ts` (EVI-01, BIB-110).
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-16`: pytest tests/test_organizacion_alta.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/alta.spec.ts + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-103 · controles-periodicos  (tanda 22)

**Contexto.** Sala(s): `auditoria_capa`, `frontend`. Depende de: `CAPA-01`, `RM-21` (pendiente), `FE-22` (pendiente). Especificaciones: `governance/tareas/CAPA-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `CAPA-02` — Controles periódicos con frecuencia y responsable; el control vencido genera un hallazgo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤auditoria-capa`: 4 coincidencias en 4 archivos.
- `¤controles-periodicos`: 2 coincidencias en 2 archivos.
- `¤hallazgos`: 3 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261030_controles_periodicos.py`
  - `features/auditoria_capa/domain/control_periodico.py`
  - `features/auditoria_capa/services/controles_engine.py`
  - `features/auditoria_capa/auditoria_capa_service.py#CAPA-02`
  - `api/routers/auditoria_capa_controles.py`
  - `tests/test_controles_periodicos.py`
  - `tests/matriz/CAPA-02.py`
  - `frontend/src/components/controles/**`
  - `frontend/src/lib/controles/**`
  - `frontend/tests/controles/**`
  - `frontend/src/components/layout/menus/CAPA-02.ts`
  - `frontend/src/components/layout/pantallas/CAPA-02.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No crees tareas desde `auditoria_capa`: solo hallazgos por la compuerta de `roadmap`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CAPA-02`: pytest tests/test_controles_periodicos.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes + Playwright de frontend/tests/controles + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-104 · asignacion-de-dominios  (tanda 22)

**Contexto.** Sala(s): `diagnostico`, `frontend`. Depende de: `DIAG-03`, `ORG-07`, `ORG-14`, `FE-22` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/DIAG-04.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DIAG-04` — El administrador asigna los dominios del assessment a encargados del diagnóstico

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 80 coincidencias en 17 archivos.
- `¤diagnostico-asignacion`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261030_diagnostico_asignaciones.py`
  - `features/diagnostico/services/asignacion_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-04`
  - `api/routers/diagnostico_asignaciones.py`
  - `tests/test_diagnostico_asignaciones.py`
  - `tests/matriz/DIAG-04.py`
  - `frontend/src/components/diagnostico/AsignacionDominios.tsx`
  - `frontend/src/lib/diagnostico/asignaciones.ts`
  - `frontend/tests/diagnostico/asignaciones.spec.ts`
  - `frontend/src/components/layout/menus/DIAG-04.ts`
  - `frontend/src/components/layout/pantallas/DIAG-04.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No toques `DiagnosticCanvas.tsx` (EVI-01, DIAG-05).
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-04`: pytest tests/test_diagnostico_asignaciones.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/diagnostico/asignaciones.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-105 · comparativo-linea-base  (tanda 23)

**Contexto.** Sala(s): `diagnostico`, `frontend`. Depende de: `DIAG-03`, `FE-22` (pendiente), `FE-24` (pendiente). Especificaciones: `governance/tareas/DIAG-06.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DIAG-06` — Comparativo de un assessment con la línea base, por dimensión y dominio

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 80 coincidencias en 17 archivos.
- `¤diagnostico-comparativo`: 2 coincidencias en 2 archivos.
- `¤tablero-dimensiones`: 4 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/diagnostico/services/comparativo_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-06`
  - `api/routers/diagnostico_comparativo.py`
  - `tests/test_diagnostico_comparativo.py`
  - `frontend/src/components/diagnostico/Comparativo.tsx`
  - `frontend/src/lib/diagnostico/comparativo.ts`
  - `frontend/tests/diagnostico/comparativo.spec.ts`
  - `frontend/src/components/layout/menus/DIAG-06.ts`
  - `frontend/src/components/layout/pantallas/DIAG-06.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No muestres un «avance global».
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-06`: pytest tests/test_diagnostico_comparativo.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico/comparativo.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-106 · no-aplica-justificado  (tanda 24)

**Contexto.** Sala(s): `diagnostico`, `frontend`. Depende de: `DIAG-01`, `DIAG-03`, `EVI-01` (pendiente). Especificaciones: `governance/tareas/DIAG-05.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DIAG-05` — «No aplica» exige justificación en el assessment

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 80 coincidencias en 17 archivos.
- `¤diagnostico-no-aplica`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261030_diagnostico_no_aplica.py`
  - `features/diagnostico/services/respuestas_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-05`
  - `api/routers/diagnostico_respuestas.py`
  - `tests/test_diagnostico_no_aplica.py`
  - `frontend/src/lib/diagnostico/clienteRespuestas.ts`
  - `frontend/src/components/DiagnosticCanvas.tsx`
  - `frontend/tests/diagnostico/no-aplica.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Espera a que EVI-01 esté en `main`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-05`: pytest tests/test_diagnostico_no_aplica.py y tests/test_diagnostico_respuestas.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-107 · evidencias-vigencia-inspeccion  (tanda 23)

**Contexto.** Sala(s): `evidencias`, `frontend`. Depende de: `EVI-01` (pendiente). Especificaciones: `governance/tareas/EVI-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `EVI-02` — Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 34 coincidencias en 13 archivos.
- `¤evidencias-vigencia`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261031_evidencias_vigencia.py`
  - `features/evidencias/domain/vigencia.py`
  - `features/evidencias/services/vigencia_engine.py`
  - `features/evidencias/services/paquete_inspeccion_engine.py`
  - `features/evidencias/evidencias_service.py#EVI-02`
  - `api/routers/evidencias_inspeccion.py`
  - `tests/test_evidencias_vigencia.py`
  - `frontend/src/lib/evidencias/vigencia.ts`
  - `frontend/src/components/evidencias/PaqueteInspeccion.tsx`
  - `frontend/src/components/modules/EvidenciasModule.tsx`
  - `frontend/tests/evidencias/vigencia.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Espera a que EVI-01 esté en `main`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EVI-02`: pytest tests/test_evidencias_vigencia.py y tests/test_evidencias_persistencia.py contra una rama Neon de revisión con el almacén simulado + suite completa + Playwright de frontend/tests/evidencias + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-108 · reapertura-por-evidencia-vencida  (tanda 24)

**Contexto.** Sala(s): `auditoria_capa`. Depende de: `CAPA-02` (pendiente), `EVI-02` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/CAPA-03.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `CAPA-03` — La evidencia vencida reabre el control periódico y produce un hallazgo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤controles-periodicos`: 2 coincidencias en 2 archivos.
- `¤evidencias-vigencia`: 2 coincidencias en 2 archivos.
- `¤hallazgos`: 3 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/auditoria_capa/services/reapertura_engine.py`
  - `features/auditoria_capa/auditoria_capa_service.py#CAPA-03`
  - `tests/test_controles_reapertura.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No guardes vigencias en `auditoria_capa`: se leen de `evidencias`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CAPA-03`: pytest tests/test_controles_reapertura.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-109 · quien-responde-y-quien-sella  (tanda 25)

**Contexto.** Sala(s): `diagnostico`, `frontend`. Depende de: `DIAG-04` (pendiente), `DIAG-05` (pendiente). Especificaciones: `governance/tareas/DIAG-07.md`, `governance/especificaciones/DIAG-07.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DIAG-07` — Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: 80 coincidencias en 17 archivos.
- `¤dpo-independencia`: 10 coincidencias en 10 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261101_diagnostico_objeciones.py`
  - `features/diagnostico/services/objeciones_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-07`
  - `api/routers/diagnostico_respuestas.py#DIAG-07`
  - `api/routers/diagnostico_resultados.py#DIAG-07`
  - `tests/test_diagnostico_quien_responde.py`
  - `tests/matriz/DIAG-07.py`
  - `frontend/src/components/diagnostico/GrillaRevision.tsx`
  - `frontend/src/lib/diagnostico/objeciones.ts`
  - `frontend/tests/diagnostico/revision.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No toques `DiagnosticCanvas.tsx` (DIAG-05 y EVI-01) ni el scoring.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-07`: pytest tests/test_diagnostico_quien_responde.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-110 · pmv-de-biblioteca-especificacin-seguimiento-y-no  (tanda 26)

**Contexto.** Sala(s): `biblioteca`, `gobernanza`. Depende de: ninguna. Especificaciones: `governance/tareas/BIB-100.md`.

**Objetivo** (en este orden):

1. `BIB-100` — PMV de Biblioteca: especificación, seguimiento y notas de entrega

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `docs/biblioteca-pmv.md`
  - `docs/biblioteca-entregas.md`
  - `governance/tareas/BIB-100.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-100`: python scripts/generar_indice_tareas.py --verificar; pytest tests/test_indice_tareas.py tests/test_reparto.py
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-111 · contexto-y-acceso  (tanda 26)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`, `organizacion`. Depende de: `BIB-105`, `FE-17`, `FE-10`, `FE-19`, `ORG-09`, `CAPA-01`, `FE-22` (pendiente). Especificaciones: `governance/tareas/BIB-101.md`.

**Objetivo** (en este orden):

1. `BIB-101` — Contexto y acceso

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/app/dashboard/page.tsx#BIB-101`
  - `frontend/src/components/layout/dashboardNavigation.ts#BIB-101`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx`
  - `frontend/src/lib/biblioteca/contexto.ts`
  - `frontend/src/store/useBibliotecaStore.ts`
  - `tests/test_bib_101_acceso.py`
  - `frontend/tests/biblioteca/acceso.spec.ts`
  - `frontend/src/components/layout/DashboardHeader.tsx#BIB-101`
  - `frontend/src/components/biblioteca/panel/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-101`: pytest tests/test_bib_101_acceso.py; npx playwright test tests/biblioteca/acceso.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-112 · catlogo-y-bsqueda  (tanda 27)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-101` (pendiente), `BIB-109` (pendiente). Especificaciones: `governance/tareas/BIB-102.md`.

**Objetivo** (en este orden):

1. `BIB-102` — Catálogo y búsqueda

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/catalogo.py`
  - `features/biblioteca/biblioteca_service.py#BIB-102`
  - `api/routers/biblioteca_catalogo.py`
  - `frontend/src/lib/biblioteca/catalogo.ts`
  - `frontend/src/components/biblioteca/catalogo/**`
  - `tests/test_bib_102_catalogo.py`
  - `frontend/tests/biblioteca/catalogo.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-102`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-102`: pytest tests/test_bib_102_catalogo.py; npx playwright test tests/biblioteca/catalogo.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-113 · ficha-de-plantilla  (tanda 29)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-102` (pendiente), `BIB-107` (pendiente). Especificaciones: `governance/tareas/BIB-103.md`.

**Objetivo** (en este orden):

1. `BIB-103` — Ficha de plantilla

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/ficha.py`
  - `features/biblioteca/biblioteca_service.py#BIB-103`
  - `api/routers/biblioteca_fichas.py`
  - `frontend/src/lib/biblioteca/fichas.ts`
  - `frontend/src/components/biblioteca/fichas/**`
  - `tests/test_bib_103_ficha.py`
  - `frontend/tests/biblioteca/ficha.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-103`
  - `features/biblioteca/services/mis_plantillas.py`
  - `alembic/versions/*_biblioteca_mis_plantillas.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-103`: pytest tests/test_bib_103_ficha.py; npx playwright test tests/biblioteca/ficha.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-114 · descarga-controlada  (tanda 30)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-103` (pendiente). Especificaciones: `governance/tareas/BIB-104.md`.

**Objetivo** (en este orden):

1. `BIB-104` — Descarga controlada

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/archivos.py`
  - `features/biblioteca/services/descarga.py`
  - `features/biblioteca/biblioteca_service.py#BIB-104`
  - `api/routers/biblioteca_descargas.py`
  - `frontend/src/lib/biblioteca/descargas.ts`
  - `frontend/src/components/biblioteca/descargas/**`
  - `tests/test_bib_104_descarga.py`
  - `frontend/tests/biblioteca/descarga.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-104`
  - `alembic/versions/*_biblioteca_descargas.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-104`: pytest tests/test_bib_104_descarga.py; npx playwright test tests/biblioteca/descarga.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-115 · documentos-externos-del-cliente  (tanda 31)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-107` (pendiente), `BIB-104` (pendiente). Especificaciones: `governance/tareas/BIB-106.md`.

**Objetivo** (en este orden):

1. `BIB-106` — Documentos externos del cliente

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/carga_externa.py`
  - `features/biblioteca/services/analisis_archivos.py`
  - `features/biblioteca/biblioteca_service.py#BIB-106`
  - `api/routers/biblioteca_cargas.py`
  - `frontend/src/lib/biblioteca/cargas.ts`
  - `frontend/src/components/biblioteca/cargas/**`
  - `tests/test_bib_106_externos.py`
  - `frontend/tests/biblioteca/externos.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-106`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-106`: pytest tests/test_bib_106_externos.py; npx playwright test tests/biblioteca/externos.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-116 · documentos-por-empresa  (tanda 28)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-101` (pendiente), `BIB-201` (pendiente). Especificaciones: `governance/tareas/BIB-107.md`.

**Objetivo** (en este orden):

1. `BIB-107` — Documentos por empresa

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/documentos_consulta.py`
  - `features/biblioteca/biblioteca_service.py#BIB-107`
  - `api/routers/biblioteca_documentos.py`
  - `frontend/src/lib/biblioteca/documentos.ts`
  - `frontend/src/components/biblioteca/documentos/**`
  - `tests/test_bib_107_documentos.py`
  - `frontend/tests/biblioteca/documentos.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-107`
  - `features/biblioteca/domain/documentos.py`
  - `alembic/versions/*_biblioteca_documentos.py`
  - `features/biblioteca/services/documentos.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-107`: pytest tests/test_bib_107_documentos.py; npx playwright test tests/biblioteca/documentos.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-117 · plantillas-markdown-del-pmv-en-el-catlogo  (tanda 26)

**Contexto.** Sala(s): `biblioteca`, `pasillo_central`. Depende de: `BIB-105`, `BIB-108`. Especificaciones: `governance/tareas/BIB-109.md`.

**Objetivo** (en este orden):

1. `BIB-109` — Plantillas Markdown del PMV en el catálogo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_biblioteca_plantillas_md.py`
  - `features/biblioteca/domain/plantillas_md.py`
  - `features/biblioteca/services/plantillas_md.py`
  - `features/biblioteca/domain/editorial.py#BIB-109`
  - `features/biblioteca/services/editorial.py#BIB-109`
  - `features/biblioteca/biblioteca_service.py#BIB-109`
  - `scripts/cargar_plantillas_pmv.py`
  - `data/biblioteca/pmv/**`
  - `tests/test_bib_109_plantillas_md.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-109`: pytest tests/test_bib_109_plantillas_md.py; python scripts/cargar_plantillas_pmv.py --verificar; suite pytest tests --ignore=tests/e2e en rama propia; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-118 · biblioteca-al-cambiar-de-organizacin-cach-cambio  (tanda 27)

**Contexto.** Sala(s): `biblioteca`, `frontend`. Depende de: `BIB-101` (pendiente), `FE-21`, `EVI-01` (pendiente). Especificaciones: `governance/tareas/BIB-110.md`.

**Objetivo** (en este orden):

1. `BIB-110` — Biblioteca al cambiar de organización: caché, cambios pendientes y store de auditoría

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/store/useAuditStore.ts`
  - `frontend/src/store/audit/**`
  - `frontend/src/store/useBibliotecaStore.ts#BIB-110`
  - `frontend/tests/biblioteca/cambio-organizacion.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-110`: npx playwright test tests/biblioteca/cambio-organizacion.spec.ts + suite Playwright completa + tsc --noEmit + npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-119 · formulario-por-versin  (tanda 27)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-101` (pendiente), `BIB-109` (pendiente), `ORG-14`, `RAT-01`. Especificaciones: `governance/tareas/BIB-201.md`.

**Objetivo** (en este orden):

1. `BIB-201` — Formulario por versión

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/domain/esquemas.py`
  - `features/biblioteca/services/borradores.py`
  - `features/biblioteca/services/validacion.py`
  - `features/biblioteca/biblioteca_service.py#BIB-201`
  - `api/routers/biblioteca_borradores.py`
  - `alembic/versions/*_biblioteca_borradores.py`
  - `frontend/src/lib/biblioteca/borradores.ts`
  - `frontend/src/components/biblioteca/editor/**`
  - `tests/test_bib_201_formularios.py`
  - `frontend/tests/biblioteca/formularios.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-201`
  - `features/biblioteca/services/rellenado.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-201`: pytest tests/test_bib_201_formularios.py; npx playwright test tests/biblioteca/formularios.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-120 · reutilizacin-y-procedencia  (tanda 28)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-201` (pendiente), `DIAG-01`, `RAT-01`. Especificaciones: `governance/tareas/BIB-202.md`.

**Objetivo** (en este orden):

1. `BIB-202` — Reutilización y procedencia

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/domain/procedencia.py`
  - `features/biblioteca/services/procedencia.py`
  - `features/biblioteca/biblioteca_service.py#BIB-202`
  - `api/routers/biblioteca_fuentes.py`
  - `frontend/src/lib/biblioteca/fuentes.ts`
  - `frontend/src/components/biblioteca/procedencia/**`
  - `tests/test_bib_202_procedencia.py`
  - `frontend/tests/biblioteca/procedencia.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-202`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-202`: pytest tests/test_bib_202_procedencia.py; npx playwright test tests/biblioteca/procedencia.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-121 · tablas-de-captura  (tanda 29)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-201` (pendiente), `BIB-202` (pendiente). Especificaciones: `governance/tareas/BIB-203.md`.

**Objetivo** (en este orden):

1. `BIB-203` — Tablas de captura

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/filas.py`
  - `features/biblioteca/biblioteca_service.py#BIB-203`
  - `api/routers/biblioteca_filas.py`
  - `frontend/src/lib/biblioteca/filas.ts`
  - `frontend/src/components/biblioteca/tablas/**`
  - `tests/test_bib_203_tablas.py`
  - `frontend/tests/biblioteca/tablas.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-203`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-203`: pytest tests/test_bib_203_tablas.py; npx playwright test tests/biblioteca/tablas.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-122 · aplicabilidad-explicable  (tanda 29)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-202` (pendiente), `MTGE-01`. Especificaciones: `governance/tareas/BIB-204.md`.

**Objetivo** (en este orden):

1. `BIB-204` — Aplicabilidad explicable

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/domain/reglas.py`
  - `features/biblioteca/services/aplicabilidad.py`
  - `features/biblioteca/biblioteca_service.py#BIB-204`
  - `api/routers/biblioteca_aplicabilidad.py`
  - `alembic/versions/*_biblioteca_reglas.py`
  - `frontend/src/lib/biblioteca/aplicabilidad.ts`
  - `frontend/src/components/biblioteca/recomendados/**`
  - `tests/test_bib_204_aplicabilidad.py`
  - `frontend/tests/biblioteca/aplicabilidad.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-204`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-204`: pytest tests/test_bib_204_aplicabilidad.py; npx playwright test tests/biblioteca/aplicabilidad.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-123 · generacin-de-word-y-excel  (tanda 30)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-201` (pendiente), `BIB-202` (pendiente), `BIB-203` (pendiente). Especificaciones: `governance/tareas/BIB-205.md`.

**Objetivo** (en este orden):

1. `BIB-205` — Generación de Word y Excel

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/domain/generacion.py`
  - `features/biblioteca/services/generacion.py`
  - `features/biblioteca/services/salida.py`
  - `features/biblioteca/services/generador_docx.py`
  - `features/biblioteca/services/generador_xlsx.py`
  - `features/biblioteca/biblioteca_service.py#BIB-205`
  - `api/routers/biblioteca_generacion.py`
  - `alembic/versions/*_biblioteca_generacion.py`
  - `requirements.txt`
  - `frontend/src/lib/biblioteca/generacion.ts`
  - `frontend/src/components/biblioteca/generacion/**`
  - `tests/test_bib_205_generacion.py`
  - `frontend/tests/biblioteca/generacion.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-205`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-205`: pytest tests/test_bib_205_generacion.py; npx playwright test tests/biblioteca/generacion.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-124 · vista-previa-y-fidelidad  (tanda 31)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-205` (pendiente). Especificaciones: `governance/tareas/BIB-206.md`.

**Objetivo** (en este orden):

1. `BIB-206` — Vista previa y fidelidad

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/preview.py`
  - `features/biblioteca/biblioteca_service.py#BIB-206`
  - `api/routers/biblioteca_preview.py`
  - `frontend/src/lib/biblioteca/preview.ts`
  - `frontend/src/components/biblioteca/preview/**`
  - `tests/test_bib_206_preview.py`
  - `frontend/tests/biblioteca/preview.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-206`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-206`: pytest tests/test_bib_206_preview.py; npx playwright test tests/biblioteca/preview.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-125 · concurrencia-y-trabajos-de-generacin  (tanda 31)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-205` (pendiente). Especificaciones: `governance/tareas/BIB-207.md`.

**Objetivo** (en este orden):

1. `BIB-207` — Concurrencia y trabajos de generación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/concurrencia.py`
  - `features/biblioteca/services/trabajos.py`
  - `features/biblioteca/workers/generacion_worker.py`
  - `features/biblioteca/biblioteca_service.py#BIB-207`
  - `api/routers/biblioteca_trabajos.py`
  - `alembic/versions/*_biblioteca_trabajos.py`
  - `frontend/src/lib/biblioteca/trabajos.ts`
  - `frontend/src/components/biblioteca/recuperacion/**`
  - `tests/test_bib_207_concurrencia.py`
  - `frontend/tests/biblioteca/concurrencia.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-207`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-207`: pytest tests/test_bib_207_concurrencia.py; npx playwright test tests/biblioteca/concurrencia.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-126 · cobertura-de-ocho-fichas  (tanda 32)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`, `rat`, `roadmap`. Depende de: `BIB-203` (pendiente), `BIB-204` (pendiente), `BIB-206` (pendiente), `BIB-207` (pendiente), `RM-19`. Especificaciones: `governance/tareas/BIB-208.md`.

**Objetivo** (en este orden):

1. `BIB-208` — Cobertura de ocho fichas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/plantillas/**`
  - `features/biblioteca/services/fichas_iniciales.py`
  - `features/biblioteca/biblioteca_service.py#BIB-208`
  - `features/roadmap/services/exportacion_biblioteca.py`
  - `features/roadmap/roadmap_service.py#BIB-208`
  - `features/rat/services/datos_documentales.py`
  - `features/rat/rat_service.py#BIB-208`
  - `api/routers/biblioteca_fichas_iniciales.py`
  - `frontend/src/components/biblioteca/fichas-iniciales/**`
  - `tests/test_bib_208_fichas.py`
  - `frontend/tests/biblioteca/fichas-iniciales.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-208`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-208`: pytest tests/test_bib_208_ocho-fichas.py; npx playwright test tests/biblioteca/fichas-iniciales.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-127 · revisin-y-aprobacin  (tanda 29)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-107` (pendiente). Especificaciones: `governance/tareas/BIB-301.md`.

**Objetivo** (en este orden):

1. `BIB-301` — Revisión y aprobación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/domain/revisiones.py`
  - `features/biblioteca/services/revision_aprobacion.py`
  - `features/biblioteca/biblioteca_service.py#BIB-301`
  - `api/routers/biblioteca_revisiones.py`
  - `alembic/versions/*_biblioteca_aprobaciones.py`
  - `frontend/src/lib/biblioteca/revisiones.ts`
  - `frontend/src/components/biblioteca/expediente/**`
  - `tests/test_bib_301_revision.py`
  - `frontend/tests/biblioteca/revision.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-301`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-301`: pytest tests/test_bib_301_revision.py; npx playwright test tests/biblioteca/revision.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-128 · integracin-con-acciones  (tanda 30)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`, `roadmap`. Depende de: `BIB-301` (pendiente), `RM-19`. Especificaciones: `governance/tareas/BIB-302.md`.

**Objetivo** (en este orden):

1. `BIB-302` — Integración con acciones

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/enlaces.py`
  - `features/biblioteca/biblioteca_service.py#BIB-302`
  - `features/roadmap/services/enlaces_documentales.py`
  - `features/roadmap/roadmap_service.py#BIB-302`
  - `api/routers/biblioteca_enlaces.py`
  - `alembic/versions/*_biblioteca_enlaces.py`
  - `frontend/src/lib/biblioteca/enlaces.ts`
  - `frontend/src/components/biblioteca/enlaces/**`
  - `tests/test_bib_302_enlaces.py`
  - `frontend/tests/biblioteca/enlaces.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-302`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-302`: pytest tests/test_bib_302_enlaces.py; npx playwright test tests/biblioteca/enlaces.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-129 · evidencias-y-verificacin  (tanda 31)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`, `roadmap`. Depende de: `BIB-302` (pendiente). Especificaciones: `governance/tareas/BIB-303.md`.

**Objetivo** (en este orden):

1. `BIB-303` — Evidencias y verificación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/verificacion.py`
  - `features/biblioteca/biblioteca_service.py#BIB-303`
  - `features/roadmap/services/cierre_verificado_engine.py`
  - `features/roadmap/services/tarea_estado_engine.py`
  - `features/roadmap/roadmap_service.py#BIB-303`
  - `api/routers/biblioteca_verificaciones.py`
  - `alembic/versions/*_biblioteca_verificaciones.py`
  - `frontend/src/lib/biblioteca/verificacion.ts`
  - `frontend/src/components/biblioteca/verificacion/**`
  - `tests/test_bib_303_evidencia.py`
  - `frontend/tests/biblioteca/verificacion.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-303`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-303`: pytest tests/test_bib_303_evidencia.py; npx playwright test tests/biblioteca/verificacion.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-130 · actualizacin-normativa-y-documental  (tanda 30)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`, `notificaciones`. Depende de: `BIB-105`, `BIB-301` (pendiente), `NOTIF-01`. Especificaciones: `governance/tareas/BIB-304.md`.

**Objetivo** (en este orden):

1. `BIB-304` — Actualización normativa y documental

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/impacto.py`
  - `features/biblioteca/biblioteca_service.py#BIB-304`
  - `features/notificaciones/services/biblioteca_engine.py`
  - `features/notificaciones/notificaciones_service.py#BIB-304`
  - `api/routers/biblioteca_impactos.py`
  - `alembic/versions/*_biblioteca_impactos.py`
  - `frontend/src/lib/biblioteca/impacto.ts`
  - `frontend/src/components/biblioteca/impacto/**`
  - `tests/test_bib_304_impacto.py`
  - `frontend/tests/biblioteca/impacto.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-304`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-304`: pytest tests/test_bib_304_impacto.py; npx playwright test tests/biblioteca/impacto.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-131 · indicadores-verificables  (tanda 32)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-303` (pendiente). Especificaciones: `governance/tareas/BIB-305.md`.

**Objetivo** (en este orden):

1. `BIB-305` — Indicadores verificables

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/indicadores.py`
  - `features/biblioteca/biblioteca_service.py#BIB-305`
  - `api/routers/biblioteca_indicadores.py`
  - `frontend/src/lib/biblioteca/indicadores.ts`
  - `frontend/src/components/biblioteca/indicadores/**`
  - `tests/test_bib_305_indicadores.py`
  - `frontend/tests/biblioteca/indicadores.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-305`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-305`: pytest tests/test_bib_305_indicadores.py; npx playwright test tests/biblioteca/indicadores.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-132 · historial-y-conservacin  (tanda 32)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-303` (pendiente). Especificaciones: `governance/tareas/BIB-306.md`.

**Objetivo** (en este orden):

1. `BIB-306` — Historial y conservación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/conservacion.py`
  - `features/biblioteca/services/historial.py`
  - `features/biblioteca/biblioteca_service.py#BIB-306`
  - `api/routers/biblioteca_historial.py`
  - `alembic/versions/*_biblioteca_conservacion.py`
  - `frontend/src/lib/biblioteca/historial.ts`
  - `frontend/src/components/biblioteca/historial/**`
  - `tests/test_bib_306_conservacion.py`
  - `frontend/tests/biblioteca/conservacion.spec.ts`
  - `frontend/src/components/biblioteca/BibliotecaWorkspace.tsx#BIB-306`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-306`: pytest tests/test_bib_306_conservacion.py; npx playwright test tests/biblioteca/conservacion.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-133 · aceptacin-de-extremo-a-extremo  (tanda 33)

**Contexto.** Sala(s): `biblioteca`, `pruebas`, `gobernanza`. Depende de: `BIB-304` (pendiente), `BIB-305` (pendiente), `BIB-306` (pendiente), `TEST-03`. Especificaciones: `governance/tareas/BIB-307.md`.

**Objetivo** (en este orden):

1. `BIB-307` — Aceptación de extremo a extremo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `tests/test_bib_307_integracion.py`
  - `frontend/tests/integracion/biblioteca/**`
  - `governance/apoyo/BIBLIOTECA_ACEPTACION.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-307`: pytest tests/test_bib_307_e2e.py; npx playwright test -c playwright.integracion.config.ts tests/integracion/biblioteca; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-134 · kit-y-documentacin-de-biblioteca-versionados  (tanda 26)

**Contexto.** Sala(s): `gobernanza`, `biblioteca`. Depende de: `ORG-01`, `ORG-08`, `SEC-02`, `BIB-105`. Especificaciones: `governance/tareas/GOB-03.md`.

**Objetivo** (en este orden):

1. `GOB-03` — Kit y documentación de Biblioteca versionados

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 274 coincidencias en 60 archivos.
- `¤arbitro`: 91 coincidencias en 44 archivos.

**Escribe** (lista exclusiva):

  - `data/biblioteca/kit_v1/**`
  - `governance/apoyo/BIBLIOTECA_DISENO.md`
  - `governance/apoyo/BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md`
  - `governance/apoyo/BIBLIOTECA_PLAN.md`
  - `governance/apoyo/BIBLIOTECA_ESTADO.md`
  - `governance/apoyo/BIBLIOTECA_README.md`
  - `governance/artefactos/PRD.md`
  - `governance/artefactos/TASKS.md`
  - `governance/tareas/GOB-03.md`
  - `governance/tareas/BIB-108.md`
  - `governance/apoyo/BRIEFS_POR_BLOQUE.md`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOB-03`: shasum -a 256 -c MANIFIESTO.sha256 desde data/biblioteca/kit_v1 (15 OK); python scripts/generar_indice_tareas.py --verificar; pytest tests/test_indice_tareas.py tests/test_vpa_map.py; python scripts/verificar_reparto.py --rama <rama> --bloque BL-84 --base origin/main
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-135 · inventario-de-activos-y-sistemas-soportes-y-pers  (tanda 24)

**Contexto.** Sala(s): `organizacion`, `frontend`. Depende de: `ORG-07`, `FE-22` (pendiente), `ORG-16` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/ORG-17.md`, `governance/especificaciones/ORG-17.md`.

**Objetivo** (en este orden):

1. `ORG-17` — Inventario de activos y sistemas, soportes y personas mínimas de la organización

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 81 coincidencias en 68 archivos.
- `¤inventario`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/*_inventario_activos.py`
  - `features/organizacion/services/inventario_engine.py`
  - `features/organizacion/organizacion_service.py#ORG-17`
  - `api/routers/organizacion_inventario.py`
  - `tests/test_organizacion_inventario.py`
  - `tests/matriz/ORG-17.py`
  - `frontend/src/components/organizacion/inventario/**`
  - `frontend/tests/organizacion/inventario.spec.ts`
  - `frontend/src/components/layout/menus/ORG-17.ts`
  - `frontend/src/components/layout/pantallas/ORG-17.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-17`: pytest tests/test_organizacion_inventario.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/inventario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-136 · vistas-de-lista-tablero-y-cronograma-de-las-tare  (tanda 23)

**Contexto.** Sala(s): `roadmap`, `frontend`. Depende de: `RM-21` (pendiente), `FE-12`, `FE-15`, `RM-20`, `ORG-12`. Especificaciones: `governance/tareas/RM-22.md`, `governance/especificaciones/RM-22.md`.

**Objetivo** (en este orden):

1. `RM-22` — Vistas de lista, tablero y cronograma de las tareas, con su hallazgo de origen y las vencidas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤roadmap`: 58 coincidencias en 46 archivos.
- `¤hallazgos`: 6 coincidencias en 4 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/modules/roadmap/vistas/**`
  - `frontend/src/components/modules/roadmap/olas/TareaCard.tsx`
  - `frontend/tests/roadmap/vistas.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RM-22`: Playwright de frontend/tests/roadmap/vistas.spec.ts + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada
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
- Verificar con el texto oficial los artículos y plazos marcados (*) en el PRD y fijar la fuente única de citas legales (`LEG-03`): decisión del propietario del 2026-10-28, «nada por ahora»; queda en `backlog` hasta que la lance, coordinada con el dictamen del abogado sobre las plantillas.
- Estructura funcional EVYDENTIA en backlog, hasta que el propietario la lance: `REG-01` (paquete normativo como dato, con plazos como parámetros; espera a LEG-03).
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

### Biblioteca repartida en tandas

Desde el 2026-10-28 las 24 tareas de Biblioteca y GOB-03 tienen bloque y tanda (serie «Biblioteca (PMV)» de la tabla), en el orden del PMV (`governance/tareas/BIB-100.md`): hasta cuatro por tanda, sin archivos enteros en común, con las dependencias en tandas anteriores. La serie de Biblioteca corre en paralelo a la de la estructura EVYDENTIA (otra persona), sin pisar archivos.

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
