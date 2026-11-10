# Briefs por bloque de trabajo — EVYDENTIA
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento (2026-10-28, reparto del propietario en tandas de hasta cuatro sin archivos enteros en común):** 51 tareas abiertas de 221; 170 hechas (BIB-100 cerrada el 2026-10-29, #220; BIB-109 cerrada el 2026-10-29, #223; RM-21 cerrada el 2026-10-29, #222; DIAG-08 cerrada el 2026-10-30, #235; RM-22 cerrada el 2026-10-31, #269; DIAG-09 cerrada el 2026-10-31, #273 y #279; BIB-101 cerrada el 2026-10-31, #236; REG-02 cerrada el 2026-10-31, #241; GOB-03 cerrada el 2026-10-31, #244; CAPA-02 cerrada el 2026-10-31, #284; RAT-05 cerrada el 2026-11-01, #288; RM-23 cerrada el 2026-11-01, #287; ORG-16 cerrada el 2026-11-01, #281 y #294 (pruebas de la alta corregidas el 2026-11-02, #299); RAT-06 cerrada el 2026-11-01, #295). Tanda 21 terminada: FE-22, FE-23 y RM-21 hechas. Escala SMARTCIDI 1-5 (decisión del propietario del 2026-10-29): DIAG-08 y DIAG-09 la implantan; FE-24 sale de la tanda 21 y espera a DIAG-08; EVI-01 (BL-94), pausada hasta configurar R2, pasa detrás de DIAG-09. tanda 22 (EVY): DIAG-08, DPO-02, SEC-12, CAPA-02; tanda 23 (EVY): FE-24, DIAG-09, ORG-16, RM-22; tanda 27 (EVY): EVI-01, DIAG-04, DIAG-06, ORG-15; tanda 28 (EVY): EVI-02, DIAG-05, ORG-17 (RAT-05 hecha); tanda 29 (EVY): CAPA-03, DIAG-07, RAT-07 (RAT-06 hecha); tanda 30 (EVY): ORG-18, INC-02, DER-01, DPO-03; tanda 31 (EVY): FOR-01, DER-02, MTGE-03, CAPA-04; tanda 32 (EVY): TER-01, REG-02, ORG-20; tanda 33 (EVY): TER-02, FE-25; tanda 34 (BIB): BIB-100, BIB-109, BIB-101, GOB-03; tanda 35 (BIB): BIB-201, BIB-102, BIB-110; tanda 36 (BIB): BIB-107, BIB-202; tanda 37 (EVY): FIRMA-02; tanda 38 (BIB): BIB-301, BIB-103, BIB-203, BIB-204; tanda 39 (BIB): BIB-401, BIB-104, BIB-205, BIB-302; tanda 40 (BIB): BIB-402, BIB-106, BIB-206, BIB-207; tanda 41 (BIB): BIB-208, BIB-303, BIB-304; tanda 42 (BIB): BIB-305, BIB-306; tanda 43 (BIB): BIB-307. En backlog, sin agente, por decisión del propietario: LEG-03 y REG-01.

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
- **Rama y commit:** trabaja en una rama `tarea/<persona>/<id>` creada desde `origin/main`, al día con `main` y en el orden del bloque; cada task en sus propios commits con su id en el mensaje. El PR a `main` es el de esa persona, en la ventana nocturna (regla 10 de `governance/tareas/README.md`, que manda sobre este documento). Añade siempre los archivos por su ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`. Antes de cada commit comprueba la rama con `git branch --show-current`. No empujes ni abras PR sin que el coordinador lo pida.
- **Secciones `#ID` de una compuerta compartida** (`organizacion_service.py`, `diagnostico_service.py`, `roadmap_service.py`…): añade tu sección **al final del archivo**, en el orden de su id, y no toques ninguna línea fuera de tus marcas `=== <ID> ===` … `=== fin <ID> ===`. Así dos fusiones de la misma noche no chocan en líneas vecinas.
- **Backend primero dentro de la ficha (decisión del propietario, 2026-11-07):** las fichas que llevan backend y frontend no se parten. El ingeniero termina primero la API con sus pruebas pytest en verde y después hace la pantalla con sus pruebas de Playwright, todo en el mismo PR. **Orden de lanzamiento dentro de cada tanda:** primero las fichas solo de backend, después las mixtas y al final las solo de frontend, siempre que las dependencias y R3 lo permitan. El Tech Lead aplica ese orden al armar la frase «Lanza la tanda». **Orden de etapas:** antes de las salas van GCP-01, SEC-16 y CI-17; después, la Etapa I (salas) en su orden; al final, la Etapa II (Google Cloud GCP-03…07, el entorno de pruebas EP-03…09 y la demo).
- **Migraciones y rama al día (desde 2026-11-07, `main` no exige la rama al día):** si tu task crea una migración, antes de fusionar trae `main`, corre `alembic heads` y, si hay más de una cabeza, aplica `governance/operaciones/FUSION_ALEMBIC.md` en tu propio PR, y lo avisa en el PR. Esa task sí usa «Update branch» si su PR quedó atrás. Una task sin migración se fusiona sin actualizar la rama. Si falla el push a `main`, se corrige con un PR inmediato y se detienen las fusiones hasta que pase.
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
| 18 | — | **Cimiento ADPA (ZERAG):** ADPA-02 hecha (BL-164 retirado). BL-89 (CAPA-01) hecha. |
| 19 | — | **Cimiento ADPA (ZERAG):** ADPA-03 hecha (BL-165 retirado). BL-83, BL-90, BL-92 y BL-93 hechas. |
| 20 | — | **Etapa I · Clean-Room (Ola 1A — Cimiento ADPA, Plataforma y Seguridad):** `BIB-117` (capacidades de la Biblioteca por script; Seguridad revisa la migración antes del reparto), `BIB-118` (menú «Administración editorial» por capacidades y GET de capacidades propias). *(Cerradas previas: ADPA-04 #463, ADPA-07 #459, ORG-21 #430, FE-21, DIAG-13 #416, BIB-115 #417, SEC-15 #428, CI-16 #420).* ADPA-10 hecha (#466 y #474). SEC-16 hecha (#479). `SEC-19` (la descarga con token exige sesión; Seguridad revisa antes del reparto). BIB-118 hecha (#491). |
| 21 | — | **Etapa I · Clean-Room (Ola 1A — Compuertas ADPA, CORS, Biblioteca y Rate Limit):** `SEC-17` (Configuración mínima en la nube: `DATABASE_URL` y `CORS_ORIGINS`). *(Cerradas previas: FE-22, FE-23, RM-21, FE-26 #424, BIB-116 #419).* ADPA-05 hecha (#470). BIB-106 hecha (#469). SEC-13 hecha (#468). CI-19 hecha (#495). SEC-17 hecha (#484). |
| 22 | — | **Etapa I · Clean-Room (Ola 1A — Pasillos ADPA, Diagnóstico y Empaquetado Seguro):** `ADPA-06` (Andamiar módulos y secciones `#ID` en `app_core/pasillo/`), `DIAG-05` («No aplica» exige justificación en el assessment), `SEC-13a` (Tope total de generaciones de IA por organización). *(Cerradas previas: DIAG-08, DPO-02, SEC-12, CAPA-02).* SEC-14 hecha (#467). SEC-13a hecha (#483). DIAG-05 hecha (#487). ADPA-06 hecha (#486). |
| 23 | BL-171, BL-101 | **Etapa I · Clean-Room (Ola 1B — Salas Nuevas ADPA, Sellos Diagnóstico y Cartera):** `ADPA-08` (Migración base de `terceros_encargados` y `transferencias_terceros` con RLS), `ADPA-09` (Andamiar salas `formacion` y `conservacion`), `DIAG-11` (Diagnóstico de prueba y real: dos sellos como máximo), `ORG-15` (Cartera de organizaciones por pertenencia con semáforos por dimensión). *(Cerradas previas: FE-24 #378, DIAG-09, ORG-16, RM-22).* ADPA-08 hecha (#547). DIAG-11 hecha (#546). |
| 24 | BL-225 | **Etapa II · Cloud & Entornos (Ola 2B — Identidad y Plantilla Demo, Zona de Negocio y Exenciones):** `DEMO-08` (Gancho de identidad demo en `usuario_verificado()`), `SEC-13b` y `DEMO-03` (fijar_tope; siembra de la plantilla «Cooperativa Demo»), `CORE-01` (Una sola zona de negocio), `CI-22` (Árbitro de secciones en `_exenciones_propiedad.txt`). CORE-01 hecha (#554). CI-22 hecha (#551). SEC-13b y DEMO-03 hechas (#550). |
| 25 | BL-233 | **Etapa II · Cloud & Entornos (Ola 2B — Armazón, Motivo Neutro de IA y Purga Demo):** `FE-27` (armazón responsive del tablero; tras la revisión de textos de UX/UI), `IA-01` (motivo neutro del preanálisis), `IA-02` (motivo neutro del asistente), `DEMO-05` (Cloud Run Job de purga nocturna). Orden del CTO, 2026-11-09: lo que muestra nombres de variables al cliente va primero. FE-27 hecha (#574), IA-01 hecha (#569) e IA-02 hecha (#571). El árbitro de la retirada del proveedor (BL-263) hecho (#578). `DEP-01` (dependencias de Cloud Storage y de Vertex AI en requirements.txt, con versión exacta; va primero, y EVI-01 e IA-03 dependen de ella). |
| 26 | — | **Etapa II · Cloud & Entornos (Ola 2B — Plazos por Tipo y Clonación Demo):** `DER-05` (plazo por tipo de solicitud de derechos), `DEMO-03c` (clonar desde plantilla: hoja de ruta), `DEMO-03d` (clonar desde plantilla: biblioteca) y `DEMO-03a` (clonar desde plantilla: organización). Lanzada por el propietario el 2026-11-09. IA-03 pasa a la tanda 29 y API-02 a la 37. DER-05 hecha (#581), DEMO-03a hecha (#579), DEMO-03c hecha (#580) y DEMO-03d hecha (#582). Las cuatro vienen de la tanda 27 (lanzadas con DEP-01 e IA-03 el 2026-11-09): `EVI-01` (evidencias en el servidor, solo backend), `DIAG-04` (asignación de dominios), `DIAG-06` (comparativo con línea base) y `ORG-17` (inventario de activos). |
| 27 | BL-265, BL-109, BL-207, BL-138 | **Etapa I · Clean-Room (Ola 1B — Evidencias en Servidor, Dominios y Activos):** `EVI-01` (Custodia de evidencias en el servidor con SHA-256), `DIAG-04` (Asignación de dominios del assessment a encargados), `DIAG-06` (Comparativo de un assessment con la línea base por dimensión), `ORG-17` (Inventario de activos y sistemas, soportes y personas mínimas). `EVI-01b` (pantalla de evidencias guardadas en el servidor) se lanza con `DIAG-12`, `DIAG-07` y `ORG-18`, que salen de la tanda 28 al quedar libres sus dependencias; EVI-01, DIAG-04, DIAG-06 y ORG-17 ya están hechas. |
| 28 | BL-107 | **Etapa I · Clean-Room (Ola 1B — Paquetes de Inspección, Grilla DPO y Sedes):** `EVI-02` (Vigencia y visibilidad de evidencias y paquete para inspección SPDP; espera a EVI-01b). `DIAG-12`, `DIAG-07` y `ORG-18` pasaron a la tanda 27. *(Cerrada previa: RAT-05 #288).* |
| 29 | BL-108, BL-143, BL-137, BL-258 | **Etapa I · Clean-Room (Ola 1B — Controles CAPA, RAT, Incidentes y ARCOP+):** `CAPA-03` (La evidencia vencida reabre el control periódico y produce un hallazgo), `RAT-07` (Colectivos de titulares y registro de consentimientos por finalidad), `INC-02` (Asistente de vulneración en 8 secciones con decisión de notificar), `DER-01` (Solicitudes de titulares ARCOP+ con verificación y respuesta como evidencia). *(Cerrada previa: RAT-06 #295).* `DER-05` (plazo por tipo de solicitud de derechos) viene aquí por decisión del CTO (2026-11-09); DER-01 pasa a la tanda 35. `IA-03` (compuerta de inferencia Gemini en Vertex AI; viene de la tanda 26) ocupa el cupo que deja DER-05, que pasa a la 26. |
| 30 | BL-141, BL-144, BL-146, BL-147 | **Etapa I · Clean-Room (Ola 1B — Consultas DPO, Auditoría, Formación y EIPD):** `DPO-03` (Consultas de la organización al DPO con historial como evidencia), `CAPA-04` (Auditoría con grilla de verificación por dominio y acta por área), `FOR-01` (Formación: contenidos, acciones formativas con examen y seguimiento), `MTGE-03` (EIPD guiada de 8 pasos con asistente de obligatoriedad e informe final). |
| 31 | BL-148, BL-151, BL-172, BL-262 | **Etapa I · Clean-Room (Ola 1B — Portal ARCOP+, Papelera, Terceros y Conservación):** `DER-02` (Portal público de solicitudes de titulares por organización), `ORG-20` (Papelera y exportación completa de datos de la organización), `TER-01` (Hallazgos automáticos de terceros y transferencias sin garantía), `CON-01` (Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO). *(Cerradas previas: RM-23 #287, REG-02 #241).* `DER-07` (textos legales de la interfaz de derechos ARCO) viene aquí; DER-02 pasa a la tanda 36. |
| 32 | BL-153, BL-152, BL-154, BL-155 | **Etapa I · Clean-Room (Ola 1B — Portal Encargados, Ficha Resumen, Acuse y Plantillas):** `TER-02` (Cuestionario de garantías del encargado por portal externo), `FE-25` (Ficha resumen de la organización fija bajo la barra superior), `FIRMA-02` (Aceptación simple con acuse y verificación por hash), `BIB-401` (Plantillas de la cuenta profesional: tercera capa). |
| 33 | BL-118, BL-174, BL-260 | **Etapa I · Clean-Room (Ola 1C — Biblioteca Multi-Org, Chasis ASGI, TIA CI/CD y Guardia Entorno):** `BIB-110` (Biblioteca al cambiar de organización), `GCP-02` (Acelerador CI/CD TIA por grafo ADPA). GCP-01 hecha (#448) y EP-01 hecha (#443). SEC-18 hecha (#460) y TEST-05 hecha (#462). `DER-06a` (tipos nuevos de solicitud: expandir el enum sin activarlos). |
| 34 | BL-261 | **Biblioteca (PMV):** BIB-100 hecha (#220, BL-110 retirado); BIB-109 hecha (#223, BL-117 retirado); BIB-101 hecha (#236, BL-111 retirado); GOB-03 hecha (#244, BL-134 retirado). `DER-06b` (activar los tipos nuevos y sus formularios; compuerta humana). |
| 35 | BL-140 | **Biblioteca (PMV):** BIB-111 hecha (#335, BL-159 retirado); BIB-112 hecha (#347, BL-160 retirado); RM-24 hecha (#345, BL-163 retirado). DER-01 viene de la tanda 29 y espera a DER-06b para cubrir los ocho tipos. |
| 36 | BL-145 | **Biblioteca (PMV):** BIB-107 hecha (#359, BL-116 retirado); BIB-201 hecha (#358, BL-119 retirado); BIB-102 hecha (#360, BL-112 retirado); BIB-103 hecha (#361, BL-113 retirado). DER-02 viene de la tanda 31. |
| 37 | BL-196 | **Estructura EVYDENTIA:** `FIRMA-02` (BL-154) agrupada en tanda 32 para maximizar paralelismo de 4 bloques. `API-02` (API de integración versionada; viene de la tanda 26) y `NEON-00` (árbitro sin Neon; lanzada el 2026-11-09). NEON-00 pasa a la tanda 25. |
| 38 | — | **Biblioteca (PMV):** BIB-113 hecha (#363, BL-161 retirado); BIB-114 hecha (#364, BL-162 retirado); BIB-104 hecha (#365, BL-114 retirado); BIB-204 hecha (#366, BL-122 retirado). |
| 39 | — | **Biblioteca (PMV):** BIB-301 hecha (#373, BL-127 retirado); BIB-302 hecha (#376, BL-128 retirado); BIB-304 hecha (#375, BL-130 retirado); BIB-306 hecha (#374, BL-132 retirado). |
| 40 | — | **Biblioteca (PMV):** BIB-202 hecha (#387, BL-120 retirado); BIB-203 hecha (#389, BL-121 retirado); `BIB-106` (BL-115, tanda 21) y `BIB-401` (BL-155, tanda 32) reubicadas en tandas de 4 bloques. |
| 41 | — | **Biblioteca (PMV):** BIB-303 hecha (#388, BL-129 retirado); BIB-402 hecha (#386, BL-156 retirado); BIB-205 hecha (#393, BL-123 retirado); `BIB-110` (BL-118, tanda 33) reubicada en tanda de 4 bloques. |
| 42 | — | **Biblioteca (PMV):** BIB-206 hecha (#396, BL-124 retirado); BIB-207 hecha (#397, BL-125 retirado); BIB-305 hecha (#392, BL-131 retirado). |
| 43 | — | **Biblioteca (PMV):** BIB-208 hecha (#403, BL-126 retirado). |
| 44 | — | **Biblioteca (PMV):** BIB-307 hecha (#398, BL-133 retirado). |
| 45 | BL-175, BL-176, BL-177, BL-187 | **Etapa I · Clean-Room (Ola 1C — Bóveda Cloud, DLP, Vertex AI y Vigilancia SPDP):** `BOV-01` (Sala Bóveda Cloud: paquetes de reventa y cuotas GB/Egress), `DLP-01` (Descubrimiento DLP muestreado y Módulo 10 para poblar el RAT), `VTX-01` (Vertex AI Context Caching con Gemini sobre el corpus LOPDP/SPDP), `NORM-01` (Sala Inteligencia Normativa: ingesta SPDP, SHA-256 y custodia del original). |
| 46 | BL-178, BL-180, BL-188, BL-189 | **Etapa I · Clean-Room (Ola 1C — Bóveda Dual GCS, Videovigilancia y Copiloto Normativo):** `BOV-02` (Bóveda Dual GCS `short-ttl` vs `long-retention` WORM y Signed URLs V4), `CCTV-01` (Sala Videovigilancia LOPDP: cámaras H.265, eventos, sin audio y retención 15 días), `NORM-02` (Centro de Vigilancia Normativa en Frontend), `NORM-03` (Impacto normativo con Gemini validado por el DPO). |
| 47 | BL-179, BL-181, BL-182, BL-183 | **Etapa I · Clean-Room (Ola 1C — Satélites en Go, Carril Forense Dual y Hold Legal):** `GOVW-01` (Microservicio Go `vault_worker` para Eventarc, SHA-256 en streaming y purga), `BOV-03` (Carril Forense Dual: original SHA-256 intacto + derivados `WebP`/`AVIF`/`WebM`), `CCTV-02` (Hold Legal forense por incidente/ARCOP+ y actas quincenales SHA-256), `GOCA-01` (Agente Edge en Go `cctv_agent` para cámaras/NVR con subida directa TLS). |
| 48 | BL-184 | **Etapa I · Clean-Room (Ola 1C — Orquestador 10 Dimensiones, Observabilidad y Guardias de Salida):** `BOV-04` (Orquestador comercial de las 10 Dimensiones, retenciones, actas SHA-256 y telemetría). EP-02 hecha (#444), EP-08 hecha (#446) y OPS-07 hecha (#480). |
| 49 | — | **Etapa II · Cloud & Entornos (Ola 2A — Cutover Cloud Run/Cloud SQL, API Integraciones y Siembra):** `GCP-03` (Migración Frontend Next.js standalone a Cloud Run), `GCP-04` (Migración Base de Datos Cloud SQL PostgreSQL 16 y Load Balancer), `API-02` (API de integración versionada con claves por organización y webhooks HMAC-SHA256), `EP-03` (Siembra de organizaciones, evidencias y clips sintéticos). API-02 pasa a la tanda 26. GCP-03 hecha (#488) y GCP-04 hecha (#490). |
| 50 | BL-192, BL-203 | **Etapa II · Cloud & Entornos (Ola 2A — Escalado, Despliegue Canario y Verificador Staging):** `GCP-05` (Escalado verificable en Cloud Run y prueba de carga), `EP-06` (Ciclo de una versión por digest en pruebas), `EP-07` (Verificador del entorno de pruebas y flujo de GitHub). GCP-07 hecha (#514). |
| 51 | BL-194, BL-201 | **Etapa II · Cloud & Entornos (Ola 2A — Cloud CDN/Memorystore, Infraestructura Pruebas y Contrato Demo):** `GCP-06` (Cloud CDN solo para activos estáticos y caché de lectura por tenant), `EP-04` (Proyecto, Cloud Run, IAP y presupuesto del entorno de pruebas), `EP-05` (Cloud SQL, buckets sin bloqueo y secretos del entorno de pruebas), `DEMO-00` (Contrato de la sala demo: compuerta, dominio, repositorio y migración). |
| 52 | — | **Etapa II · Cloud & Entornos (Ola 2B — Identidad, Plantilla, Interfaz y Purga Demo):** `DEMO-08` (Gancho de identidad demo en `usuario_verificado()`), `DEMO-03` (Siembra de la plantilla «Cooperativa Demo» con 6 personas), `DEMO-04` (Interfaz demo: «Ver como», «Terminar demo» y errores), `DEMO-05` (Cloud Run Job de purga nocturna). DEMO-04 hecha (#485). DEMO-08 y DEMO-03 pasan a la tanda 24 y DEMO-05 a la 25. |
| 53 | BL-228 | **Etapa II · Cloud & Entornos (Ola 2B — Clonación Paralela de Salas Demo Lote 1):** `DEMO-03a` (Clonar desde plantilla: organización), `DEMO-03b` (Clonar desde plantilla: diagnóstico), `DEMO-03c` (Clonar desde plantilla: hoja de ruta), `DEMO-03d` (Clonar desde plantilla: biblioteca). | DEMO-03c y DEMO-03d pasan a la tanda 26. DEMO-03a pasa a la tanda 26. |
| 54 | BL-231, BL-235, BL-205 | **Etapa II · Cloud & Entornos (Ola 2B — Clonación Evidencias, Guardia Correo, «Ver como» y Puesta en Marcha Pruebas):** `DEMO-03e` (Clonar desde plantilla: evidencias y objetos), `DEMO-06` (Prueba de que con `APP_ENV=demo` no sale ningún correo), `DEMO-01` (Persona activa y «Ver como»), `EP-09` (Puesta en marcha del entorno de pruebas y primer verificador en verde). |
| 55 | BL-236 | **Etapa II · Cloud & Entornos (Ola 2B — Orquestador Final de Sesión Demo):** `DEMO-02` (Ciclo de sesión y orquestador de la copia que invoca `DEMO-03a`…`DEMO-03e`). Después: `DEMO-03f` (bloqueada hasta la sala videovigilancia) y `DEMO-07` sin agente. |

## Briefs

### BL-265 · evidencias-pantalla-servidor  (tanda 27)

**Contexto.** Sala(s): `frontend`. Depende de: `CI-15`, `EVI-01`, `DIAG-04`, `FE-14`, `FE-16`, `FE-26`, `DIAG-09`, `DIAG-11`, `ADPA-07`, `ADPA-11`. Especificaciones: `governance/tareas/EVI-01b.md`.

**Objetivo** (en este orden):

1. `EVI-01b` — Pantalla de evidencias guardadas en el servidor: subida firmada, store desde el servidor y specs adaptados

**Rastro ¤**:

- `¤frontend-ide`: registrado en `VPA_MAP.md`.
- `¤evidencias`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/evidencias/**`
  - `frontend/src/components/evidencias/**`
  - `frontend/src/components/modules/EvidenciasModule.tsx#EVI-01`
  - `frontend/src/components/config/CargaEvidencias.tsx`
  - `frontend/src/components/DiagnosticCanvas.tsx#EVI-01`
  - `frontend/src/store/useAuditStore.ts`
  - `frontend/tests/evidencias/**`
  - `frontend/tests/utiles.ts`
  - `frontend/tests/diagnostico/escala-activa.spec.ts`
  - `frontend/tests/purga/purga-normativa-activa.spec.ts`
  - `frontend/tests/roadmap/e2e/criterio12_roles-activa.spec.ts`
  - `frontend/tests/firma/aceptacion.spec.ts`
  - `frontend/tests/ergonomia/colores-diagnostico-activa.spec.ts`
  - `frontend/tests/pmv/sin-subida.spec.ts`
  - `frontend/tests/pmv/sin-subida-activa.spec.ts`
  - `frontend/tests/roadmap/integracion-activa.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.
- No se lanza hasta que EVI-01 esté fusionada. Textos nuevos de interfaz pasan por UX/UI.

**Hecho si** (árbitro exógeno):

- `EVI-01b`: npx playwright test frontend/tests/evidencias + los ocho specs adaptados + tsc --noEmit + npm run build; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-101 · cartera-por-pertenencia  (tanda 23)

**Contexto.** Sala(s): `organizacion`, `frontend`. Depende de: `ORG-13`, `ORG-14`, `FE-21`, `FE-22` (pendiente), `FE-24` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/ORG-15.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `ORG-15` — Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 78 coincidencias en 66 archivos.
- `¤cartera`: 2 coincidencias en 2 archivos.
- `¤tablero-dimensiones`: 4 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `features/organizacion/services/cartera_engine.py`
  - `app_core/pasillo/roadmap.py#ORG-15`
  - `features/roadmap/roadmap_service.py#ORG-15`
  - `app_core/pasillo/diagnostico.py#ORG-15`
  - `features/organizacion/organizacion_service.py#ORG-15`
  - `api/routers/organizacion_cartera.py`
  - `tests/test_organizacion_cartera.py`
  - `tests/matriz/ORG-15.py`
  - `frontend/src/app/cartera/**`
  - `frontend/src/lib/cartera/**`
  - `frontend/tests/cartera/**`
  - `frontend/src/components/layout/menus/ORG-15.ts`
  - `features/organizacion/domain/errores.py#ORG-15`
  - `app_core/pasillo/organizacion.py#ORG-15`
  - `app_core/pasillo/biblioteca.py#ORG-15`
  - `frontend/src/components/layout/pantallas/ORG-15.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No uses `BYPASSRLS` ni consultas sin contexto de organización.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-15`: pytest tests/test_organizacion_cartera.py y tests/test_organizaciones_por_persona.py contra una rama Neon de revisión con lopdp_app, con la prueba de INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP (la cartera lista solo organizaciones con rol vigente) + suite completa + Playwright de frontend/tests/cartera + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-107 · evidencias-vigencia-inspeccion  (tanda 28)

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
  - `frontend/src/components/modules/EvidenciasModule.tsx#EVI-02`
  - `frontend/tests/evidencias/vigencia.spec.ts`
  - `features/evidencias/domain/errores.py#EVI-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Espera a que EVI-01 esté en `main`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EVI-02`: pytest tests/test_evidencias_vigencia.py y tests/test_evidencias_persistencia.py contra una rama Neon de revisión con el almacén simulado + suite completa + Playwright de frontend/tests/evidencias + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-108 · reapertura-por-evidencia-vencida  (tanda 29)

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
  - `features/auditoria_capa/domain/errores.py#CAPA-03`
  - `app_core/pasillo/auditoria_capa.py#CAPA-03`
  - `app_core/pasillo/evidencias.py#CAPA-03`
  - `app_core/pasillo/roadmap.py#CAPA-03`
  - `app_core/pasillo/notificaciones.py#CAPA-03`
  - `app_core/pasillo/dpo_cockpit.py#CAPA-03`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No guardes vigencias en `auditoria_capa`: se leen de `evidencias`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CAPA-03`: pytest tests/test_controles_reapertura.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-109 · quien-responde-y-quien-sella  (tanda 27)

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
  - `features/diagnostico/domain/errores.py#DIAG-07`
  - `app_core/pasillo/diagnostico.py#DIAG-07`
  - `app_core/pasillo/roadmap.py#DIAG-07`
  - `app_core/pasillo/organizacion.py#DIAG-07`
  - `app_core/pasillo/regulacion_rag.py#DIAG-07`
  - `frontend/src/components/DiagnosticCanvas.tsx#DIAG-07`
  - `frontend/src/components/layout/menus/index.ts#DIAG-07`
  - `frontend/src/components/layout/pantallas/index.tsx#DIAG-07`

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

### BL-118 · biblioteca-al-cambiar-de-organizacin-cach-cambio  (tanda 33)

**Contexto.** Sala(s): `biblioteca`, `frontend`. Depende de: `BIB-101`, `FE-21`, `EVI-01` (pendiente), `BIB-111` (pendiente). Especificaciones: `governance/tareas/BIB-110.md`.

**Objetivo** (en este orden):

1. `BIB-110` — Biblioteca al cambiar de organización: caché, cambios pendientes y store de auditoría

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.
- `¤rbac-tenant`: 158 coincidencias en 119 archivos.
- `¤arbitro`: 162 coincidencias en 81 archivos.

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

### BL-137 · asistente-de-vulneracin-en-ocho-secciones-con-de  (tanda 29)

**Contexto.** Sala(s): `incidentes`, `frontend`. Depende de: `INC-01`, `FE-23` (pendiente), `RM-21` (pendiente), `EVI-02` (pendiente). Especificaciones: `governance/tareas/INC-02.md`, `governance/especificaciones/INC-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `INC-02` — Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤incidentes`: 15 coincidencias en 13 archivos.
- `¤hallazgos`: 5 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_incidentes_asistente.py`
  - `features/incidentes/domain/vulneracion.py`
  - `features/incidentes/services/asistente_engine.py`
  - `features/incidentes/services/informes_engine.py`
  - `features/incidentes/incidentes_service.py#INC-02`
  - `api/routers/incidentes_asistente.py`
  - `tests/test_incidentes_asistente.py`
  - `tests/matriz/INC-02.py`
  - `frontend/src/components/incidentes/**`
  - `frontend/src/lib/incidentes/asistente.ts`
  - `frontend/tests/incidentes/asistente.spec.ts`
  - `frontend/src/components/layout/menus/INC-02.ts`
  - `frontend/src/components/layout/pantallas/INC-02.tsx`
  - `features/incidentes/domain/errores.py#INC-02`
  - `app_core/pasillo/incidentes.py#INC-02`
  - `app_core/pasillo/evidencias.py#INC-02`
  - `app_core/pasillo/notificaciones.py#INC-02`
  - `app_core/pasillo/dpo_cockpit.py#INC-02`
  - `frontend/src/components/layout/menus/index.ts#INC-02`
  - `frontend/src/components/layout/pantallas/index.tsx#INC-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/INC-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `INC-02`: pytest tests/test_incidentes_asistente.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/incidentes/asistente.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-138 · sedes-de-la-organizacin-y-clientes-cuando-acta-c  (tanda 27)

**Contexto.** Sala(s): `organizacion`, `frontend`. Depende de: `ORG-16` (pendiente), `ORG-17` (pendiente). Especificaciones: `governance/tareas/ORG-18.md`, `governance/especificaciones/ORG-18.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `ORG-18` — Sedes de la organización y clientes cuando actúa como encargada

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 103 coincidencias en 66 archivos.
- `¤inventario`: 2 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261102_sedes_clientes.py`
  - `features/organizacion/services/sedes_engine.py`
  - `features/organizacion/organizacion_service.py#ORG-18`
  - `api/routers/organizacion_sedes.py`
  - `tests/test_organizacion_sedes.py`
  - `tests/matriz/ORG-18.py`
  - `frontend/src/components/organizacion/sedes/**`
  - `frontend/tests/organizacion/sedes.spec.ts`
  - `frontend/src/components/layout/menus/ORG-18.ts`
  - `frontend/src/components/layout/pantallas/ORG-18.tsx`
  - `features/organizacion/domain/errores.py#ORG-18`
  - `app_core/pasillo/organizacion.py#ORG-18`
  - `app_core/pasillo/biblioteca.py#ORG-18`
  - `frontend/src/components/layout/menus/index.ts#ORG-18`
  - `frontend/src/components/layout/pantallas/index.tsx#ORG-18`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/ORG-18.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-18`: pytest tests/test_organizacion_sedes.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/organizacion/sedes.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-140 · solicitudes-de-titulares-verificacin-de-identida  (tanda 35)

**Contexto.** Sala(s): `derechos_arco`, `frontend`. Depende de: `EVI-02` (pendiente), `FE-22` (pendiente). Especificaciones: `governance/tareas/DER-01.md`, `governance/especificaciones/DER-01.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DER-01` — Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 35 coincidencias en 13 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_derechos_respuestas.py`
  - `features/derechos_arco/services/respuestas_engine.py`
  - `features/derechos_arco/derechos_arco_service.py#DER-01`
  - `api/routers/derechos_respuestas.py`
  - `tests/test_derechos_respuestas.py`
  - `tests/matriz/DER-01.py`
  - `frontend/src/components/derechos/**`
  - `frontend/src/lib/derechos/respuestas.ts`
  - `frontend/tests/derechos/respuestas.spec.ts`
  - `features/derechos_arco/domain/errores.py#DER-01`
  - `app_core/pasillo/derechos_arco.py#DER-01`
  - `app_core/pasillo/evidencias.py#DER-01`
  - `app_core/pasillo/firma_electronica.py#DER-01`
  - `app_core/pasillo/notificaciones.py#DER-01`
  - `app_core/pasillo/dpo_cockpit.py#DER-01`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/DER-01.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DER-01`: pytest tests/test_derechos_respuestas.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/derechos/respuestas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-141 · consultas-de-la-organizacin-al-dpo-con-historial  (tanda 30)

**Contexto.** Sala(s): `dpo_cockpit`, `frontend`. Depende de: `DPO-02` (pendiente), `EVI-02` (pendiente). Especificaciones: `governance/tareas/DPO-03.md`, `governance/especificaciones/DPO-03.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DPO-03` — Consultas de la organización al DPO con historial como evidencia de asesoría

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤dpo-cockpit`: 12 coincidencias en 10 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_dpo_consultas.py`
  - `features/dpo_cockpit/domain/consulta.py`
  - `features/dpo_cockpit/services/consultas_engine.py`
  - `features/dpo_cockpit/dpo_cockpit_service.py#DPO-03`
  - `api/routers/dpo_consultas.py`
  - `tests/test_dpo_consultas.py`
  - `tests/matriz/DPO-03.py`
  - `frontend/src/components/dpo/Consultas.tsx`
  - `frontend/src/lib/dpo/consultas.ts`
  - `frontend/tests/dpo/consultas.spec.ts`
  - `frontend/src/components/layout/menus/DPO-03.ts`
  - `frontend/src/components/layout/pantallas/DPO-03.tsx`
  - `features/dpo_cockpit/domain/errores.py#DPO-03`
  - `app_core/pasillo/dpo_cockpit.py#DPO-03`
  - `app_core/pasillo/auditoria_capa.py#DPO-03`
  - `app_core/pasillo/derechos_arco.py#DPO-03`
  - `app_core/pasillo/diagnostico.py#DPO-03`
  - `app_core/pasillo/incidentes.py#DPO-03`
  - `app_core/pasillo/rat.py#DPO-03`
  - `app_core/pasillo/riesgos_mtge.py#DPO-03`
  - `app_core/pasillo/roadmap.py#DPO-03`
  - `app_core/pasillo/terceros.py#DPO-03`
  - `app_core/pasillo/transferencias.py#DPO-03`
  - `app_core/pasillo/formacion.py#DPO-03`
  - `app_core/pasillo/conservacion.py#DPO-03`
  - `frontend/src/components/layout/menus/index.ts#DPO-03`
  - `frontend/src/components/layout/pantallas/index.tsx#DPO-03`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/DPO-03.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DPO-03`: pytest tests/test_dpo_consultas.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/dpo/consultas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-143 · colectivos-de-titulares-y-registro-de-consentimi  (tanda 29)

**Contexto.** Sala(s): `rat`. Depende de: `RAT-05`, `EVI-02` (pendiente). Especificaciones: `governance/tareas/RAT-07.md`, `governance/especificaciones/RAT-07.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `RAT-07` — Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rat`: 62 coincidencias en 18 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261102_consentimientos.py`
  - `features/rat/domain/consentimiento.py`
  - `features/rat/services/consentimientos_engine.py`
  - `features/rat/rat_service.py#RAT-07`
  - `api/routers/rat_consentimientos.py`
  - `tests/test_rat_consentimientos.py`
  - `tests/matriz/RAT-07.py`
  - `frontend/src/components/modules/rat/Consentimientos.tsx`
  - `frontend/src/lib/rat/consentimientos.ts`
  - `frontend/tests/rat/consentimientos.spec.ts`
  - `features/rat/domain/errores.py#RAT-07`
  - `app_core/pasillo/rat.py#RAT-07`
  - `app_core/pasillo/organizacion.py#RAT-07`
  - `app_core/pasillo/biblioteca.py#RAT-07`
  - `app_core/pasillo/firma_electronica.py#RAT-07`
  - `app_core/pasillo/dpo_cockpit.py#RAT-07`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/RAT-07.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `RAT-07`: pytest tests/test_rat_consentimientos.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/rat/consentimientos.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-144 · auditora-con-grilla-de-verificacin-por-dominio-y  (tanda 30)

**Contexto.** Sala(s): `auditoria_capa`, `frontend`. Depende de: `CAPA-02` (pendiente), `RM-21` (pendiente), `EVI-02` (pendiente), `DIAG-03`. Especificaciones: `governance/tareas/CAPA-04.md`, `governance/especificaciones/CAPA-04.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `CAPA-04` — Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤auditoria-capa`: 4 coincidencias en 4 archivos.
- `¤hallazgos`: 5 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261106_auditoria_grilla.py`
  - `features/auditoria_capa/domain/auditoria.py`
  - `features/auditoria_capa/services/grilla_engine.py`
  - `features/auditoria_capa/auditoria_capa_service.py#CAPA-04`
  - `api/routers/auditoria_grilla.py`
  - `tests/test_auditoria_grilla.py`
  - `tests/matriz/CAPA-04.py`
  - `frontend/src/components/auditoria/**`
  - `frontend/src/lib/auditoria/**`
  - `frontend/tests/auditoria/**`
  - `frontend/src/components/layout/menus/CAPA-04.ts`
  - `frontend/src/components/layout/pantallas/CAPA-04.tsx`
  - `features/auditoria_capa/domain/errores.py#CAPA-04`
  - `app_core/pasillo/auditoria_capa.py#CAPA-04`
  - `frontend/src/components/layout/menus/index.ts#CAPA-04`
  - `frontend/src/components/layout/pantallas/index.tsx#CAPA-04`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/CAPA-04.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CAPA-04`: pytest tests/test_auditoria_grilla.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/auditoria + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-145 · portal-pblico-de-solicitudes-de-titulares-por-or  (tanda 36)

**Contexto.** Sala(s): `derechos_arco`, `frontend`. Depende de: `DER-01` (pendiente), `SEC-12` (pendiente). Especificaciones: `governance/tareas/DER-02.md`, `governance/especificaciones/DER-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `DER-02` — Portal público de solicitudes de titulares por organización, con enlace de seguimiento

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 78 coincidencias en 47 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261105_derechos_portal.py`
  - `features/derechos_arco/services/portal_engine.py`
  - `features/derechos_arco/derechos_arco_service.py#DER-02`
  - `api/routers/publico_derechos.py`
  - `tests/test_derechos_portal.py`
  - `frontend/src/app/solicitud/**`
  - `frontend/tests/derechos/portal.spec.ts`
  - `features/derechos_arco/domain/errores.py#DER-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/DER-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DER-02`: pytest tests/test_derechos_portal.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/derechos/portal.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-146 · formacin-contenidos-acciones-formativas-con-exam  (tanda 30)

**Contexto.** Sala(s): `formacion`, `frontend`. Depende de: `ORG-17` (pendiente), `EVI-02` (pendiente), `FE-22` (pendiente). Especificaciones: `governance/tareas/FOR-01.md`, `governance/especificaciones/FOR-01.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FOR-01` — Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 35 coincidencias en 13 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `features/formacion/models.py`
  - `features/formacion/schemas.py`
  - `features/formacion/formacion_service.py#FOR-01`
  - `features/formacion/domain/formacion.py`
  - `features/formacion/services/**`
  - `alembic/versions/20261105_formacion.py`
  - `api/routers/formacion.py`
  - `tests/test_formacion.py`
  - `tests/matriz/FOR-01.py`
  - `frontend/src/components/formacion/**`
  - `frontend/src/lib/formacion/**`
  - `frontend/tests/formacion/**`
  - `frontend/src/components/layout/menus/FOR-01.ts`
  - `frontend/src/components/layout/pantallas/FOR-01.tsx`
  - `features/formacion/domain/errores.py#FOR-01`
  - `app_core/pasillo/formacion.py#FOR-01`
  - `app_core/pasillo/evidencias.py#FOR-01`
  - `app_core/pasillo/dpo_cockpit.py#FOR-01`
  - `frontend/src/components/layout/menus/index.ts#FOR-01`
  - `frontend/src/components/layout/pantallas/index.tsx#FOR-01`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/FOR-01.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FOR-01`: pytest tests/test_formacion.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/formacion + tsc --noEmit + npm run build; adpa_linter (sala nueva con compuerta formacion_service.py); prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-147 · eipd-guiada-de-ocho-pasos-con-asistente-de-oblig  (tanda 30)

**Contexto.** Sala(s): `riesgos_mtge`, `frontend`. Depende de: `MTGE-02`, `FE-23` (pendiente), `RM-21` (pendiente), `EVI-02` (pendiente). Especificaciones: `governance/tareas/MTGE-03.md`, `governance/especificaciones/MTGE-03.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `MTGE-03` — EIPD guiada de ocho pasos con asistente de obligatoriedad, decisión documentada e informe final

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤riesgos-eipd`: 18 coincidencias en 7 archivos.
- `¤mtge-granescala`: 22 coincidencias en 10 archivos.
- `¤hallazgos`: 5 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261105_eipd_guiada.py`
  - `features/riesgos_mtge/domain/eipd.py`
  - `features/riesgos_mtge/services/eipd_engine.py`
  - `features/riesgos_mtge/riesgos_mtge_service.py#MTGE-03`
  - `api/routers/eipd_guiada.py`
  - `tests/test_eipd_guiada.py`
  - `tests/matriz/MTGE-03.py`
  - `frontend/src/components/eipd/**`
  - `frontend/src/lib/eipd/**`
  - `frontend/tests/eipd/**`
  - `frontend/src/components/layout/menus/MTGE-03.ts`
  - `frontend/src/components/layout/pantallas/MTGE-03.tsx`
  - `features/riesgos_mtge/domain/errores.py#MTGE-03`
  - `app_core/pasillo/riesgos_mtge.py#MTGE-03`
  - `app_core/pasillo/rat.py#MTGE-03`
  - `app_core/pasillo/organizacion.py#MTGE-03`
  - `app_core/pasillo/firma_electronica.py#MTGE-03`
  - `app_core/pasillo/dpo_cockpit.py#MTGE-03`
  - `frontend/src/components/layout/menus/index.ts#MTGE-03`
  - `frontend/src/components/layout/pantallas/index.tsx#MTGE-03`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/MTGE-03.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `MTGE-03`: pytest tests/test_eipd_guiada.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/eipd + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-148 · papelera-archivar-y-restaurar-y-exportacin-compl  (tanda 31)

**Contexto.** Sala(s): `organizacion`, `plataforma`, `frontend`. Depende de: `ORG-17` (pendiente), `EVI-02` (pendiente). Especificaciones: `governance/tareas/ORG-20.md`, `governance/especificaciones/ORG-20.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `ORG-20` — Papelera (archivar y restaurar) y exportación completa de los datos de la organización

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 103 coincidencias en 66 archivos.
- `¤seguridad`: 78 coincidencias en 47 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261107_papelera.py`
  - `features/organizacion/services/papelera_engine.py`
  - `features/organizacion/services/exportacion_engine.py`
  - `features/organizacion/organizacion_service.py#ORG-20`
  - `features/plataforma/plataforma_service.py#ORG-20`
  - `api/routers/organizacion_papelera.py`
  - `tests/test_organizacion_papelera.py`
  - `tests/matriz/ORG-20.py`
  - `frontend/src/components/organizacion/papelera/**`
  - `frontend/tests/organizacion/papelera.spec.ts`
  - `frontend/src/components/layout/menus/ORG-20.ts`
  - `frontend/src/components/layout/pantallas/ORG-20.tsx`
  - `features/organizacion/domain/errores.py#ORG-20`
  - `app_core/pasillo/organizacion.py#ORG-20`
  - `app_core/pasillo/biblioteca.py#ORG-20`
  - `frontend/src/components/layout/menus/index.ts#ORG-20`
  - `frontend/src/components/layout/pantallas/index.tsx#ORG-20`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/ORG-20.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-20`: pytest tests/test_organizacion_papelera.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/organizacion/papelera.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-151 · hallazgos-automticos-de-terceros-encargado-sin-c  (tanda 31)

**Contexto.** Sala(s): `terceros`, `transferencias`. Depende de: `RM-21` (pendiente), `EVI-02` (pendiente). Especificaciones: `governance/tareas/TER-01.md`, `governance/especificaciones/TER-01.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `TER-01` — Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤hallazgos`: 5 coincidencias en 2 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261106_terceros_garantias.py`
  - `features/terceros/services/garantias_engine.py`
  - `features/terceros/terceros_service.py#TER-01`
  - `features/transferencias/transferencias_service.py#TER-01`
  - `api/routers/terceros_garantias.py`
  - `tests/test_terceros_garantias.py`
  - `tests/matriz/TER-01.py`
  - `frontend/src/components/modules/TercerosModule.tsx`
  - `frontend/src/lib/terceros/garantias.ts`
  - `frontend/tests/terceros/garantias.spec.ts`
  - `features/terceros/domain/errores.py#TER-01`
  - `app_core/pasillo/terceros.py#TER-01`
  - `app_core/pasillo/rat.py#TER-01`
  - `frontend/tests/textos/excepciones/TER-01.txt`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/TER-01.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `TER-01`: pytest tests/test_terceros_garantias.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/terceros/garantias.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-152 · ficha-resumen-de-la-organizacin-fija-bajo-la-bar  (tanda 32)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-22` (pendiente), `FE-24` (pendiente), `ORG-15` (pendiente), `RM-21` (pendiente). Especificaciones: `governance/tareas/FE-25.md`, `governance/especificaciones/FE-25.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FE-25` — Ficha resumen de la organización fija bajo la barra superior, con las cuatro dimensiones y las alertas abiertas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤frontend-ide`: 49 coincidencias en 17 archivos.
- `¤tablero-dimensiones`: 4 coincidencias en 2 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/layout/FichaResumen.tsx`
  - `frontend/src/lib/fichaResumen.ts`
  - `frontend/tests/layout/ficha-resumen.spec.ts`
  - `frontend/src/components/layout/DashboardHeader.tsx#FE-25`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/FE-25.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FE-25`: Playwright de frontend/tests/layout/ficha-resumen.spec.ts con la API simulada + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada (sin cifra única)
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-153 · cuestionario-de-garantas-del-encargado-por-porta  (tanda 32)

**Contexto.** Sala(s): `terceros`, `frontend`. Depende de: `TER-01` (pendiente), `SEC-12` (pendiente), `FE-23` (pendiente). Especificaciones: `governance/tareas/TER-02.md`, `governance/especificaciones/TER-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `TER-02` — Cuestionario de garantías del encargado por portal externo, con revisión e informe

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: 78 coincidencias en 47 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261107_terceros_cuestionario.py`
  - `features/terceros/services/cuestionario_engine.py`
  - `features/terceros/terceros_service.py#TER-02`
  - `api/routers/publico_terceros.py`
  - `api/routers/terceros_cuestionario.py`
  - `tests/test_terceros_cuestionario.py`
  - `tests/matriz/TER-02.py`
  - `frontend/src/app/proveedor/**`
  - `frontend/src/components/terceros/**`
  - `frontend/tests/terceros/cuestionario.spec.ts`
  - `features/transferencias/domain/errores.py#TER-02`
  - `app_core/pasillo/transferencias.py#TER-02`
  - `app_core/pasillo/terceros.py#TER-02`
  - `app_core/pasillo/rat.py#TER-02`
  - `app_core/pasillo/dpo_cockpit.py#TER-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/TER-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `TER-02`: pytest tests/test_terceros_cuestionario.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/terceros/cuestionario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-154 · aceptacin-simple-con-acuse-nombre-correo-fecha-i  (tanda 32)

**Contexto.** Sala(s): `firma_electronica`, `frontend`. Depende de: `FIRMA-01`, `EVI-02` (pendiente), `BIB-107` (pendiente). Especificaciones: `governance/tareas/FIRMA-02.md`, `governance/especificaciones/FIRMA-02.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FIRMA-02` — Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤firma-electronica`: 9 coincidencias en 7 archivos.
- `¤evidencias`: 35 coincidencias en 13 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261103_aceptaciones.py`
  - `features/firma_electronica/domain/aceptacion.py`
  - `features/firma_electronica/services/aceptacion_engine.py`
  - `features/firma_electronica/firma_electronica_service.py#FIRMA-02`
  - `api/routers/firma_aceptaciones.py`
  - `api/routers/publico_aceptacion.py`
  - `tests/test_firma_aceptaciones.py`
  - `tests/matriz/FIRMA-02.py`
  - `frontend/src/app/aceptar/**`
  - `frontend/src/components/firma/**`
  - `frontend/src/lib/firma/aceptaciones.ts`
  - `frontend/tests/firma/aceptacion.spec.ts`
  - `features/firma_electronica/domain/errores.py#FIRMA-02`
  - `app_core/pasillo/firma_electronica.py#FIRMA-02`
  - `app_core/pasillo/evidencias.py#FIRMA-02`
  - `app_core/pasillo/rat.py#FIRMA-02`
  - `app_core/pasillo/riesgos_mtge.py#FIRMA-02`
  - `app_core/pasillo/derechos_arco.py#FIRMA-02`
  - `frontend/src/components/layout/menus/index.ts#FIRMA-02`
  - `frontend/src/components/layout/menus/FIRMA-02.ts`
  - `frontend/src/components/layout/pantallas/FIRMA-02.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#FIRMA-02`
  - `frontend/tests/biblioteca/acceso.spec.ts#FIRMA-02`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Cumple el contrato de `governance/especificaciones/FIRMA-02.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `FIRMA-02`: pytest tests/test_firma_aceptaciones.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/firma/aceptacion.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.

### BL-155 · plantillas-de-la-cuenta-profesional-tercera-capa  (tanda 32)

**Contexto.** Sala(s): `biblioteca`, `frontend`. Depende de: `BIB-103` (pendiente), `ORG-15` (pendiente), `BIB-111` (pendiente), `BIB-112` (pendiente). Especificaciones: `governance/tareas/BIB-401.md`.

**Objetivo** (en este orden):

1. `BIB-401` — Plantillas de la cuenta profesional: tercera capa entre la maestra y la de la organización

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: 158 coincidencias en 119 archivos.
- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261103_biblioteca_cuenta_profesional.py`
  - `features/biblioteca/services/plantillas_cuenta_engine.py`
  - `features/biblioteca/biblioteca_service.py#BIB-401`
  - `api/routers/biblioteca_plantillas_cuenta.py`
  - `tests/test_bib_401_plantillas_cuenta.py`
  - `tests/matriz/BIB-401.py`
  - `frontend/src/components/biblioteca/plantillas-cuenta/**`
  - `frontend/src/lib/biblioteca/plantillasCuenta.ts`
  - `frontend/tests/biblioteca/plantillas-cuenta.spec.ts`
  - `frontend/src/components/biblioteca/vistas/index.ts#BIB-401`
  - `features/biblioteca/domain/errores.py#BIB-401`
  - `app_core/pasillo/biblioteca.py#BIB-401`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-401`: pytest tests/test_bib_401_plantillas_cuenta.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/biblioteca/plantillas-cuenta.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-171 · andamiar-salas-formacion-y-conservacion-prd  (tanda 23)

**Contexto.** Sala(s): `formacion`, `conservacion`. Depende de: `ADPA-05`, `ADPA-06`. Especificaciones: `governance/tareas/ADPA-09.md`.

**Objetivo** (en este orden):

1. `ADPA-09` — Andamiar las salas faltantes del PRD §7.1 (features/formacion y features/conservacion) y sus pasillos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `features/formacion/__init__.py`
  - `features/formacion/formacion_service.py`
  - `features/formacion/domain/__init__.py`
  - `features/formacion/domain/errores.py`
  - `features/conservacion/__init__.py`
  - `features/conservacion/conservacion_service.py`
  - `features/conservacion/domain/__init__.py`
  - `features/conservacion/domain/errores.py`
  - `app_core/pasillo/formacion.py`
  - `app_core/pasillo/conservacion.py`
  - `tests/test_adpa09_salas_prd.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-09`: pytest tests/test_adpa09_salas_prd.py tests/test_adpa_dependencias.py
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-172 · sala-conservacion-y-bloqueo-politicas-retencion  (tanda 31)

**Contexto.** Sala(s): `conservacion`. Depende de: `ADPA-07`, `ADPA-09`, `RAT-07`. Especificaciones: `governance/tareas/CON-01.md`.

**Objetivo** (en este orden):

1. `CON-01` — Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260429_01_con01_politicas_conservacion.py`
  - `features/conservacion/models.py`
  - `features/conservacion/schemas.py`
  - `features/conservacion/conservacion_service.py#CON-01`
  - `features/conservacion/domain/errores.py#CON-01`
  - `features/conservacion/routes/__init__.py`
  - `features/conservacion/routes/conservacion_routes.py`
  - `app_core/pasillo/conservacion.py#CON-01`
  - `app_core/pasillo/rat.py#CON-01`
  - `app_core/pasillo/dpo_cockpit.py#CON-01`
  - `main.py#CON-01`
  - `frontend/src/components/layout/menus/index.ts#CON-01`
  - `frontend/src/components/layout/pantallas/index.tsx#CON-01`
  - `frontend/src/components/layout/pantallas/CON-01.tsx`
  - `tests/test_con01_conservacion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CON-01`: pytest tests/test_con01_conservacion.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-174 · acelerador-cicd-tia-determinista-grafo-adpa  (tanda 33)

**Contexto.** Sala(s): `pruebas, operaciones`. Depende de: `ADPA-06`, `CI-10`. Especificaciones: `governance/tareas/GCP-02.md`, `governance/especificaciones/GCP-02.md`.

**Objetivo** (en este orden):

1. `GCP-02` — Acelerador CI/CD con Test Impact Analysis (TIA) determinista por grafo ADPA y sharding

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/cloud/tia_adpa_selector.py`
  - `governance/operaciones/ci_tia_matrix.json`
  - `tests/test_gcp02_tia_adpa_selector.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-02`: pytest tests/test_gcp02_tia_adpa_selector.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-175 · sala-boveda-cloud-paquetes-y-cuotas-egress  (tanda 45)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `ADPA-06`, `ADPA-07`, `GCP-01`. Especificaciones: `governance/tareas/BOV-01.md`, `governance/especificaciones/BOV-01.md`.

**Objetivo** (en este orden):

1. `BOV-01` — Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260501_01_bov01_boveda_paquetes_cuotas.py`
  - `features/boveda_cloud/__init__.py`
  - `features/boveda_cloud/models.py`
  - `features/boveda_cloud/schemas.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-01`
  - `features/boveda_cloud/domain/__init__.py`
  - `features/boveda_cloud/domain/errores.py#BOV-01`
  - `features/boveda_cloud/routes/__init__.py`
  - `features/boveda_cloud/routes/boveda_paquetes_routes.py`
  - `app_core/pasillo/boveda_cloud.py#BOV-01`
  - `main.py#BOV-01`
  - `frontend/src/components/layout/menus/index.ts#BOV-01`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-01`
  - `frontend/src/components/layout/pantallas/BOV-01.tsx`
  - `tests/test_bov01_paquetes_cuotas.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-01`: pytest tests/test_bov01_paquetes_cuotas.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-176 · sala-descubrimiento-dlp-muestreado-y-modulo10  (tanda 45)

**Contexto.** Sala(s): `dlp_discovery`. Depende de: `ADPA-06`, `ADPA-07`, `GCP-01`. Especificaciones: `governance/tareas/DLP-01.md`, `governance/especificaciones/DLP-01.md`.

**Objetivo** (en este orden):

1. `DLP-01` — Sala Descubrimiento DLP Muestreado: escaneo de archivos y tablas con Cloud DLP Sampling y validador Módulo 10 para poblar el RAT

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤dlp-muestreo`: registrado en `VPA_MAP.md`.
- `¤rat`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260501_03_dlp01_escaneos_muestreados.py`
  - `features/dlp_discovery/__init__.py`
  - `features/dlp_discovery/models.py`
  - `features/dlp_discovery/schemas.py`
  - `features/dlp_discovery/dlp_discovery_service.py#DLP-01`
  - `features/dlp_discovery/domain/__init__.py`
  - `features/dlp_discovery/domain/errores.py#DLP-01`
  - `features/dlp_discovery/services/__init__.py`
  - `features/dlp_discovery/services/cloud_dlp_sampler.py`
  - `features/dlp_discovery/routes/__init__.py`
  - `features/dlp_discovery/routes/dlp_discovery_routes.py`
  - `app_core/pasillo/dlp_discovery.py#DLP-01`
  - `app_core/pasillo/rat.py#DLP-01`
  - `main.py#DLP-01`
  - `frontend/src/components/layout/menus/index.ts#DLP-01`
  - `frontend/src/components/layout/pantallas/index.tsx#DLP-01`
  - `frontend/src/components/layout/pantallas/DLP-01.tsx`
  - `tests/test_dlp01_sampling_discovery.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DLP-01`: pytest tests/test_dlp01_sampling_discovery.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-177 · vertex-ai-context-caching-corpus-lopdp  (tanda 45)

**Contexto.** Sala(s): `regulacion_rag, ai_copilot`. Depende de: `ADPA-03`, `ADPA-05`, `ADPA-06`, `GCP-01`, `REG-02`, `RM-02`, `SEC-03`. Especificaciones: `governance/tareas/VTX-01.md`, `governance/especificaciones/VTX-01.md`.

**Objetivo** (en este orden):

1. `VTX-01` — Vertex AI Context Caching sobre el corpus normativo LOPDP/SPDP e inferencia con filtro DLP pre-vuelo

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤gemini-vertex`: registrado en `VPA_MAP.md`.
- `¤vertex-cache`: registrado en `VPA_MAP.md`.
- `¤copiloto-ia`: registrado en `VPA_MAP.md`.
- `¤regulation-code`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/regulacion_rag/services/vertex_context_cache.py`
  - `features/regulacion_rag/regulacion_rag_service.py#VTX-01`
  - `features/regulacion_rag/domain/errores.py#VTX-01`
  - `features/ai_copilot/services/vertex_cached_rag_engine.py`
  - `features/ai_copilot/ai_copilot_service.py#VTX-01`
  - `features/ai_copilot/domain/errores.py#VTX-01`
  - `app_core/pasillo/regulacion_rag.py#VTX-01`
  - `app_core/pasillo/ai_copilot.py#VTX-01`
  - `tests/test_vtx01_vertex_context_caching.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `VTX-01`: pytest tests/test_vtx01_vertex_context_caching.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-178 · boveda-dual-gcs-short-ttl-vs-long-retention-worm  (tanda 46)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-01`. Especificaciones: `governance/tareas/BOV-02.md`, `governance/especificaciones/BOV-02.md`.

**Objetivo** (en este orden):

1. `BOV-02` — Bóveda Dual en Google Cloud Storage (short-ttl Standard vs long-retention Autoclass WORM) e ingesta Direct-to-GCS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.
- `¤evidencias`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/__init__.py`
  - `features/boveda_cloud/services/gcs_dual_vault_engine.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-02`
  - `features/boveda_cloud/domain/errores.py#BOV-02`
  - `features/boveda_cloud/routes/boveda_objetos_routes.py`
  - `app_core/pasillo/boveda_cloud.py#BOV-02`
  - `tests/test_bov02_gcs_dual_vault.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-02`: pytest tests/test_bov02_gcs_dual_vault.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-179 · satelite-go-vault-worker-eventarc-y-purga  (tanda 47)

**Contexto.** Sala(s): `go_vault_worker`. Depende de: `GCP-01`, `BOV-01`, `CON-01`. Especificaciones: `governance/tareas/GOVW-01.md`, `governance/especificaciones/GOVW-01.md`.

**Objetivo** (en este orden):

1. `GOVW-01` — Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤motor-go-hibrido`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `services_go/vault_worker/go.mod`
  - `services_go/vault_worker/main.go`
  - `services_go/vault_worker/vault_worker_service.go`
  - `services_go/vault_worker/Dockerfile`
  - `app_core/pasillo/go_vault_worker.py#GOVW-01`
  - `app_core/pasillo/conservacion.py#GOVW-01`
  - `tests/test_govw01_vault_worker_contract.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOVW-01`: pytest tests/test_govw01_vault_worker_contract.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-180 · sala-videovigilancia-lopdp-camaras-h265-15dias  (tanda 46)

**Contexto.** Sala(s): `videovigilancia`. Depende de: `ADPA-06`, `ADPA-07`, `BOV-01`. Especificaciones: `governance/tareas/CCTV-01.md`, `governance/especificaciones/CCTV-01.md`.

**Objetivo** (en este orden):

1. `CCTV-01` — Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤rat`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260501_02_cctv01_camaras_y_politicas.py`
  - `features/videovigilancia/__init__.py`
  - `features/videovigilancia/models.py`
  - `features/videovigilancia/schemas.py`
  - `features/videovigilancia/videovigilancia_service.py#CCTV-01`
  - `features/videovigilancia/domain/__init__.py`
  - `features/videovigilancia/domain/errores.py#CCTV-01`
  - `features/videovigilancia/routes/__init__.py`
  - `features/videovigilancia/routes/videovigilancia_routes.py`
  - `app_core/pasillo/videovigilancia.py#CCTV-01`
  - `app_core/pasillo/rat.py#CCTV-01`
  - `main.py#CCTV-01`
  - `frontend/src/components/layout/menus/index.ts#CCTV-01`
  - `frontend/src/components/layout/pantallas/index.tsx#CCTV-01`
  - `frontend/src/components/layout/pantallas/CCTV-01.tsx`
  - `tests/test_cctv01_inventario_y_perfil_camaras.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CCTV-01`: pytest tests/test_cctv01_inventario_y_perfil_camaras.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-181 · carril-forense-dual-sha256-original-y-preview-webp  (tanda 47)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-02`. Especificaciones: `governance/tareas/BOV-03.md`, `governance/especificaciones/BOV-03.md`.

**Objetivo** (en este orden):

1. `BOV-03` — Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤evidencias`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/forensic_preview_engine.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-03`
  - `features/boveda_cloud/domain/errores.py#BOV-03`
  - `app_core/pasillo/boveda_cloud.py#BOV-03`
  - `frontend/src/components/layout/pantallas/BOV-03.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-03`
  - `tests/test_bov03_forensic_preview.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-03`: pytest tests/test_bov03_forensic_preview.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-182 · congelamiento-forense-hold-legal-cctv-y-acta-quincenal  (tanda 47)

**Contexto.** Sala(s): `videovigilancia`. Depende de: `CCTV-01`, `BOV-02`, `CON-01`. Especificaciones: `governance/tareas/CCTV-02.md`, `governance/especificaciones/CCTV-02.md`.

**Objetivo** (en este orden):

1. `CCTV-02` — Congelamiento Forense (Hold Legal) de clips de videovigilancia por incidente o derecho ARCOP y actas quincenales de destrucción SHA-256

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤incidentes`: registrado en `VPA_MAP.md`.
- `¤derechos`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/videovigilancia/services/__init__.py`
  - `features/videovigilancia/services/cctv_legal_hold_engine.py`
  - `features/videovigilancia/videovigilancia_service.py#CCTV-02`
  - `features/videovigilancia/domain/errores.py#CCTV-02`
  - `features/videovigilancia/routes/cctv_hold_routes.py`
  - `app_core/pasillo/videovigilancia.py#CCTV-02`
  - `app_core/pasillo/incidentes.py#CCTV-02`
  - `app_core/pasillo/derechos_arco.py#CCTV-02`
  - `frontend/src/components/layout/pantallas/CCTV-02.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#CCTV-02`
  - `tests/test_cctv02_legal_hold_y_acta_purga.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `CCTV-02`: pytest tests/test_cctv02_legal_hold_y_acta_purga.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-183 · agente-edge-go-cctv-recorte-eventos-y-subida-tls  (tanda 47)

**Contexto.** Sala(s): `go_cctv_agent`. Depende de: `CCTV-01`, `BOV-02`. Especificaciones: `governance/tareas/GOCA-01.md`, `governance/especificaciones/GOCA-01.md`.

**Objetivo** (en este orden):

1. `GOCA-01` — Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤motor-go-hibrido`: registrado en `VPA_MAP.md`.
- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `services_go/cctv_agent/go.mod`
  - `services_go/cctv_agent/main.go`
  - `services_go/cctv_agent/cctv_agent_service.go`
  - `services_go/cctv_agent/config_schema.json`
  - `app_core/pasillo/go_cctv_agent.py#GOCA-01`
  - `app_core/pasillo/videovigilancia.py#GOCA-01`
  - `features/videovigilancia/services/cctv_provisioning_bundle.py`
  - `tests/test_goca01_cctv_edge_agent_contract.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GOCA-01`: pytest tests/test_goca01_cctv_edge_agent_contract.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-184 · orquestador-comercial-diez-dimensiones-y-boveda-cloud  (tanda 48)

**Contexto.** Sala(s): `boveda_cloud`. Depende de: `BOV-03`, `CCTV-02`, `GOVW-01`, `GOCA-01`, `DLP-01`, `VTX-01`. Especificaciones: `governance/tareas/BOV-04.md`, `governance/especificaciones/BOV-04.md`.

**Objetivo** (en este orden):

1. `BOV-04` — Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤boveda-cloud`: registrado en `VPA_MAP.md`.
- `¤videovigilancia-cctv`: registrado en `VPA_MAP.md`.
- `¤dpo-cockpit`: registrado en `VPA_MAP.md`.
- `¤conservacion`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/boveda_cloud/services/orquestador_diez_dimensiones.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-04`
  - `features/boveda_cloud/domain/errores.py#BOV-04`
  - `features/boveda_cloud/routes/orquestador_routes.py`
  - `app_core/pasillo/boveda_cloud.py#BOV-04`
  - `app_core/pasillo/dpo_cockpit.py#BOV-04`
  - `frontend/src/components/layout/menus/index.ts#BOV-04`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-04`
  - `frontend/src/components/layout/pantallas/BOV-04.tsx`
  - `tests/test_bov04_orquestador_diez_dimensiones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BOV-04`: pytest tests/test_bov04_orquestador_diez_dimensiones.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-187 · sala-inteligencia-normativa-ingesta-spdp-y-sha256  (tanda 45)

**Contexto.** Sala(s): `inteligencia_normativa`. Depende de: `ADPA-05`, `ADPA-06`, `GCP-01`. Especificaciones: `governance/tareas/NORM-01.md`, `governance/especificaciones/NORM-01.md`.

**Objetivo** (en este orden):

1. `NORM-01` — Sala Inteligencia Normativa: modelos, conector resiliente a la SPDP, validación SHA-256 y custodia del original

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤inteligencia-normativa`: registrado en `VPA_MAP.md`.
- `¤vigilancia-spdp`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_norm01_inteligencia_normativa.py`
  - `features/inteligencia_normativa/__init__.py`
  - `features/inteligencia_normativa/models.py`
  - `features/inteligencia_normativa/schemas.py`
  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-01`
  - `features/inteligencia_normativa/domain/__init__.py`
  - `features/inteligencia_normativa/domain/errores.py#NORM-01`
  - `features/inteligencia_normativa/services/__init__.py`
  - `features/inteligencia_normativa/services/conector_spdp.py`
  - `features/inteligencia_normativa/services/deduplicacion.py`
  - `features/inteligencia_normativa/services/monitoreo.py`
  - `app_core/pasillo/inteligencia_normativa.py#NORM-01`
  - `tests/test_norm01_inteligencia_normativa.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `NORM-01`: pytest tests/test_norm01_inteligencia_normativa.py contra una rama Neon de prueba + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-188 · centro-de-vigilancia-normativa-spdp  (tanda 46)

**Contexto.** Sala(s): `inteligencia_normativa, frontend`. Depende de: `NORM-01`, `NOTIF-01`, `FE-22`. Especificaciones: `governance/tareas/NORM-02.md`, `governance/especificaciones/NORM-02.md`.

**Objetivo** (en este orden):

1. `NORM-02` — Centro de Vigilancia Normativa: catálogo de resoluciones SPDP, filtros, visor PDF, disparo manual, bitácora y avisos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤inteligencia-normativa`: registrado en `VPA_MAP.md`.
- `¤vigilancia-spdp`: registrado en `VPA_MAP.md`.
- `¤navegacion-menus`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-02`
  - `features/inteligencia_normativa/domain/errores.py#NORM-02`
  - `features/inteligencia_normativa/services/revision.py`
  - `app_core/pasillo/notificaciones.py#NORM-02`
  - `api/routers/inteligencia_normativa.py`
  - `tests/test_norm02_centro_vigilancia.py`
  - `tests/matriz/NORM-02.py`
  - `frontend/src/components/normativa/**`
  - `frontend/src/components/layout/menus/NORM-02.ts`
  - `frontend/src/components/layout/pantallas/NORM-02.tsx`
  - `frontend/tests/normativa/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `NORM-02`: pytest tests/test_norm02_centro_vigilancia.py contra una rama Neon de prueba + suite completa + Playwright de frontend/tests/normativa + tsc --noEmit + npm run build
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-189 · impacto-normativo-gemini-hitl-y-cache  (tanda 46)

**Contexto.** Sala(s): `inteligencia_normativa, ai_copilot`. Depende de: `NORM-01`, `VTX-01`. Especificaciones: `governance/tareas/NORM-03.md`, `governance/especificaciones/NORM-03.md`.

**Objetivo** (en este orden):

1. `NORM-03` — Análisis de impacto de una resolución con Gemini, validado por persona, y regeneración de la caché de contexto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤inteligencia-normativa`: registrado en `VPA_MAP.md`.
- `¤copiloto-ia`: registrado en `VPA_MAP.md`.
- `¤vertex-cache`: registrado en `VPA_MAP.md`.
- `¤dpo-independencia`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261104_norm03_analisis_impacto.py`
  - `features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-03`
  - `features/inteligencia_normativa/domain/errores.py#NORM-03`
  - `features/inteligencia_normativa/services/impacto.py`
  - `features/inteligencia_normativa/services/extraccion.py`
  - `features/ai_copilot/ai_copilot_service.py#NORM-03`
  - `app_core/pasillo/ai_copilot.py#NORM-03`
  - `app_core/pasillo/regulacion_rag.py#NORM-03`
  - `api/routers/inteligencia_normativa_impacto.py`
  - `tests/test_norm03_impacto_hitl.py`
  - `frontend/src/components/normativa_impacto/**`
  - `frontend/tests/normativa_impacto/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `NORM-03`: pytest tests/test_norm03_impacto_hitl.py contra una rama Neon de prueba + suite completa + Playwright de frontend/tests/normativa_impacto + tsc --noEmit + npm run build
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-192 · escalado-verificable-cloud-run-y-prueba-de-carga  (tanda 50)

**Contexto.** Sala(s): `operaciones`. Depende de: `GCP-01`, `GCP-03`, `GCP-04`. Especificaciones: `governance/tareas/GCP-05.md`, `governance/especificaciones/GCP-05.md`.

**Objetivo** (en este orden):

1. `GCP-05` — Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/cloudrun_service.yaml`
  - `governance/operaciones/cloudrun_frontend_service.yaml`
  - `governance/operaciones/PRUEBA_DE_CARGA.md`
  - `scripts/prueba_carga.py`
  - `tests/test_gcp05_escalado.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-05`: pytest tests/test_gcp05_escalado.py + suite completa + vigilantes; prueba de carga contra el entorno de pruebas con su informe en PRUEBA_DE_CARGA.md
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-194 · cloud-cdn-estatico-y-cache-de-lectura-por-tenant  (tanda 51)

**Contexto.** Sala(s): `pasillo_central, operaciones`. Depende de: `GCP-04`, `GCP-05`. Especificaciones: `governance/tareas/GCP-06.md`, `governance/especificaciones/GCP-06.md`.

**Objetivo** (en este orden):

1. `GCP-06` — Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/cache/__init__.py`
  - `app_core/cache/cache_lectura.py`
  - `governance/operaciones/cloud_cdn.yaml`
  - `tests/test_gcp06_cache.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-06`: pytest tests/test_gcp06_cache.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-196 · api-integracion-versionada-claves-y-webhooks-firmados  (tanda 37)

**Contexto.** Sala(s): `pasillo_central, frontend`. Depende de: `SEC-13`, `OPS-07`. Especificaciones: `governance/tareas/API-02.md`, `governance/especificaciones/API-02.md`.

**Objetivo** (en este orden):

1. `API-02` — API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤frontend-ide`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/integraciones/__init__.py`
  - `app_core/integraciones/claves.py`
  - `app_core/integraciones/webhooks.py`
  - `alembic/versions/20261120_api02_claves_integracion.py`
  - `frontend/src/components/integraciones/IntegracionesView.tsx`
  - `tests/test_api02_integraciones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `API-02`: pytest tests/test_api02_integraciones.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-201 · proyecto-cloud-run-iap-y-presupuesto-de-pruebas  (tanda 51)

**Contexto.** Sala(s): `operaciones`. Depende de: `GCP-01`, `GCP-03`. Especificaciones: `governance/tareas/EP-04.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-04` — Entorno de pruebas: proyecto de Google Cloud propio, servicios de Cloud Run, IAP y presupuesto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/entornos/pruebas/proyecto.yaml`
  - `governance/operaciones/entornos/pruebas/cloudrun_backend.yaml`
  - `governance/operaciones/entornos/pruebas/cloudrun_frontend.yaml`
  - `governance/operaciones/entornos/pruebas/cloudrun_vault_worker.yaml`
  - `governance/operaciones/entornos/pruebas/acceso_iap.yaml`
  - `governance/operaciones/entornos/pruebas/presupuesto.yaml`
  - `tests/test_ep04_computo_pruebas.py`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-04`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-04`: pytest tests/test_ep04_computo_pruebas.py + suite completa
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-203 · verificador-del-entorno-de-pruebas  (tanda 50)

**Contexto.** Sala(s): `operaciones, pruebas`. Depende de: ninguna. Especificaciones: `governance/tareas/EP-07.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-07` — Entorno de pruebas: verificador del entorno y flujo de GitHub tras cada despliegue en pruebas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `scripts/verificar_entorno_pruebas.py`
  - `tests/test_ep07_verificar_entorno.py`
  - `governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-07`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- `governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md` es gobernanza reservada: entrégalo en el PR para que el propietario lo revise; no toques otro flujo.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-07`: pytest tests/test_ep07_verificar_entorno.py + suite completa; el flujo nuevo no cambia los checks obligatorios del PR
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-205 · puesta-en-marcha-del-entorno-de-pruebas  (tanda 54)

**Contexto.** Sala(s): `operaciones`. Depende de: `EP-01`, `EP-02`, `EP-03`, `EP-04`, `EP-05`, `EP-06`, `EP-07`, `EP-08`. Especificaciones: `governance/tareas/EP-09.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-09` — Entorno de pruebas: puesta en marcha en Google Cloud y primer verificador en verde

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-09`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- La hace una persona (Juan Carlos, Aleczandra o José), no una sesión de IA: crea el proyecto de Google Cloud, carga secretos y despliega en Google Cloud.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-09`: python scripts/verificar_entorno_pruebas.py <frontend> con código 0 contra el entorno desplegado, y el flujo entorno-pruebas.yml en verde en GitHub
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-207 · estados-el-assessment-actual  (tanda 27)

**Contexto.** Sala(s): `diagnostico, frontend`. Depende de: `DIAG-11`, `DIAG-06`, `EVI-01`, `ADPA-05`, `ADPA-06`, `ADPA-07`. Especificaciones: `governance/tareas/DIAG-12.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` Módulo 1 e invariantes 58 y 59 de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`.

**Objetivo** (en este orden):

1. `DIAG-12` — Estados: el assessment actual, como cortes sellados que parten del diagnóstico real y suman las tareas cerradas con evidencia validada

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: registrado en `VPA_MAP.md`.
- `¤diagnostico-comparativo`: registrado en `VPA_MAP.md`.
- `¤roadmap`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261107_diagnostico_estados.py`
  - `features/diagnostico/services/estados_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-12`
  - `api/routers/diagnostico_estados.py`
  - `app_core/pasillo/roadmap.py#DIAG-12`
  - `features/diagnostico/domain/errores.py#DIAG-12`
  - `tests/test_diag12_estados.py`
  - `frontend/src/components/diagnostico/Estados.tsx`
  - `frontend/src/lib/diagnostico/estados.ts`
  - `frontend/src/components/layout/menus/DIAG-12.ts`
  - `frontend/src/components/layout/pantallas/DIAG-12.tsx`
  - `frontend/tests/diagnostico/estados.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-12`: pytest tests/test_diag12_estados.py contra una base de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico/estados.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-225 · demo-gancho-identidad  (tanda 24)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `pasillo_central`. Depende de: `DEMO-00`, `EP-01`, `SEC-15`. Especificaciones: `governance/tareas/DEMO-08.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-08` — Gancho de identidad demo en usuario_verificado()

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.
- `¤seguridad`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `app_core/security.py#DEMO-08`
  - `tests/test_demo_gancho_identidad.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-08`: pytest tests/test_demo_gancho_identidad.py + suite de seguridad existente en verde + linter ADPA sin cruces; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-258 · compuerta-inferencia-vertex  (tanda 29)

**Contexto.** Sala(s): `inferencia`. Depende de: `DEP-01`, `GCP-01`, `SEC-13a`, `SEC-13b`, `IA-01`. Especificaciones: `governance/tareas/IA-03.md`.

**Objetivo** (en este orden):

1. `IA-03` — Compuerta de inferencia Gemini en Vertex AI sin clave: sala inferencia con DLP previo, tope de organización y falla cerrada

**Rastro ¤**:

- `¤gemini-vertex`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/inferencia/inferencia_service.py`
  - `features/inferencia/domain/errores.py`
  - `features/inferencia/domain/modelos_permitidos.py`
  - `features/inferencia/services/cliente_vertex.py`
  - `app_core/pasillo/inferencia.py`
  - `tests/test_ia03_inferencia_vertex.py`
  - `tests/test_ia03_humo_vertex.py`
  - `features/inferencia/domain/regiones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.
- No pidas fusión antes de que DEP-01 esté en `main`. No ejecutes llamadas reales a Vertex: la prueba de humo `VERTEX_HUMO=1` la corre el propietario tras `BRIEF_PROPIETARIO_VERTEX.md`; esta ficha no pasa a hecha sin su sección «Evidencia de humo».

**Hecho si** (árbitro exógeno):

- `IA-03`: pytest tests/test_ia03_inferencia_vertex.py + guardia ADPA de imports cruzados; mutaciones documentadas; sección Evidencia de humo rellena en esta ficha antes de pasar a hecha
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-262 · derechos-textos-legales-interfaz  (tanda 31)

**Contexto.** Sala: `frontend`. Depende de: `BIB-118`, `DER-05`, `FE-28`. Especificaciones: `governance/tareas/DER-07.md`.

**Objetivo** (en este orden):

1. `DER-07` — Textos legales de la interfaz de derechos ARCO: plazo legal estimado y sin Art. 37, laborables, SLA ni 72h

**Rastro ¤**:

- `¤regulation-code`: registrado en `VPA_MAP.md`.
- `¤frontend-ide`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/types/arco.ts`
  - `frontend/src/components/modules/ArcoModule.tsx`
  - `frontend/src/components/CommandPalette.tsx`
  - `frontend/tests/derechos/arco-plazo-aviso.spec.ts`
  - `tests/test_der07_textos_legales.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.
- Los textos son los de UX/UI que recoge la ficha; cualquier texto nuevo pasa por UX/UI. `CommandPalette.tsx` tiene la sección `#BIB-118`: no la toques.

**Hecho si** (árbitro exógeno):

- `DER-07`: python scripts/verificar_citas_legales.py + pytest tests/test_der07_textos_legales.py + npx playwright test frontend/tests/derechos/arco-plazo-aviso.spec.ts + tsc --noEmit + build; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-260 · derechos-tipos-nuevos-expandir  (tanda 33)

**Contexto.** Sala: `derechos_arco`. Depende de: `DER-05`. Especificaciones: `governance/tareas/DER-06a.md`.

**Objetivo** (en este orden):

1. `DER-06a` — Tipos nuevos de solicitud (suspensión, decisiones automatizadas, queja): expandir el enum sin activarlos

**Rastro ¤**:

- `¤regulation-code`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261123_der06a_tipos_solicitud.py`
  - `features/derechos_arco/domain/models.py`
  - `features/derechos_arco/domain/plazos.py`
  - `features/derechos_arco/derechos_arco_service.py`
  - `api/routers/arco_router.py`
  - `tests/test_der06a_tipos_expandir.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.
- Trae migración: aplica FUSION_ALEMBIC antes de fusionar. Los tipos nuevos no se activan aquí. El rechazo de creación vive en `crear_solicitud_arco`.

**Hecho si** (árbitro exógeno):

- `DER-06a`: pytest tests/test_der06a_tipos_expandir.py contra el PostgreSQL 16 del arnés + tests/test_alembic_una_cabeza.py; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-261 · derechos-tipos-nuevos-activar  (tanda 34)

**Contexto.** Sala: `derechos_arco, frontend`. Depende de: `DER-06a`, `DER-07`. Especificaciones: `governance/tareas/DER-06b.md`.

**Objetivo** (en este orden):

1. `DER-06b` — Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz

**Rastro ¤**:

- `¤regulation-code`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/derechos_arco/domain/plazos.py`
  - `frontend/src/components/modules/ArcoModule.tsx`
  - `frontend/src/types/arco.ts`
  - `tests/test_der06b_tipos_activos.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.
- Compuerta humana: no se reparte hasta que el propietario confirme con `BRIEF_PROPIETARIO_DER06B.md` que la revisión que sirve y la estable son posteriores al despliegue de DER-06a.

**Hecho si** (árbitro exógeno):

- `DER-06b`: pytest tests/test_der06b_tipos_activos.py + Playwright de los formularios + node scripts de citas legales (verificar_citas_legales.py); mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-228 · demo-clon-diagnostico  (tanda 53)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `diagnostico`. Depende de: `DEMO-00`, `ADPA-06`. Especificaciones: `governance/tareas/DEMO-03b.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-03b` — Clonar desde plantilla en la sala diagnostico

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.
- `¤adpa`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `features/diagnostico/services/clon_plantilla_engine.py`
  - `features/diagnostico/diagnostico_service.py#DEMO-03b`
  - `app_core/pasillo/diagnostico.py#DEMO-03b`
  - `tests/test_demo_clon_diagnostico.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-03b`: pytest tests/test_demo_clon_diagnostico.py contra una base de prueba + suite existente de diagnostico en verde + linter ADPA sin cruces
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-231 · demo-clon-evidencias  (tanda 54)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `evidencias`. Depende de: `DEMO-00`, `ADPA-06`, `EVI-01`. Especificaciones: `governance/tareas/DEMO-03e.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-03e` — Clonar desde plantilla en la sala evidencias

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.
- `¤adpa`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `features/evidencias/services/clon_plantilla_engine.py`
  - `features/evidencias/evidencias_service.py#DEMO-03e`
  - `app_core/pasillo/evidencias.py#DEMO-03e`
  - `tests/test_demo_clon_evidencias.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-03e`: pytest tests/test_demo_clon_evidencias.py contra una base de prueba + suite existente de evidencias en verde + linter ADPA sin cruces
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-233 · demo-purga  (tanda 25)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `operaciones`. Depende de: `DEMO-00`, `EP-01`. Especificaciones: `governance/tareas/DEMO-05.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-05` — Cloud Run Job de purga nocturna: filas y objetos de las demos vencidas

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `jobs/purga_demo/**`
  - `tests/test_demo_purga.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-05`: pytest tests/test_demo_purga.py contra una base de prueba; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-235 · demo-persona  (tanda 54)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `demo`. Depende de: `DEMO-00`, `DEMO-08`, `EP-01`. Especificaciones: `governance/tareas/DEMO-01.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-01` — Persona activa y «Ver como»: resolver, 403 si es ajena y auditoría con el vendedor real

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.
- `¤seguridad`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `features/demo/services/resolutor_engine.py`
  - `features/demo/services/persona_engine.py`
  - `api/routers/demo_persona.py`
  - `tests/test_demo_persona.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-01`: pytest tests/test_demo_persona.py + suite de seguridad y de segregación del DPO existente en verde + linter ADPA sin cruces; mutaciones documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-236 · demo-ciclo  (tanda 55)

**Contexto.** Proyecto EVYDENTIA (Google Cloud). Sala: `demo`. Depende de: `DEMO-00`, `DEMO-08`, `DEMO-03`, `DEMO-03a`, `DEMO-03b`, `DEMO-03c`, `DEMO-03d`, `DEMO-03e`, `GCP-01`. Especificaciones: `governance/tareas/DEMO-02.md`, `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`, `governance/apoyo/UX_DEMO_EVYDENTIA.md`, PRD EVYDENTIA §5.6.

**Objetivo** (en este orden):

1. `DEMO-02` — Ciclo de sesión demo: entrar, tope, reemplazo, terminar, vencimiento y orquestador de la copia

**Rastro ¤**:

- `¤demo`: registrado en `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`.

**Escribe** (lista exclusiva):

  - `features/demo/domain/vendedores.py`
  - `features/demo/services/entrada_engine.py`
  - `features/demo/services/cierre_engine.py`
  - `api/routers/demo_sesion.py`
  - `tests/test_demo_ciclo.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS.
- No cambies el contrato de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 ni las firmas de `demo_service.py`: si hace falta, para y consulta a Tech Lead.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas (§5.5).
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `DEMO-02`: pytest tests/test_demo_ciclo.py contra una base de prueba + linter ADPA sin cruces; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

## Sin agente (decisiones del propietario y trabajo por asignar)

- Demo de EVYDENTIA en Google Cloud (`DEMO-07`): proyecto demo, despliegue del digest, Secret Manager, Cloud Scheduler del job de purga, cuenta de servicio y OAuth; la hacen Juan Carlos, Aleczandra o José, tras DEMO-02, DEMO-04, DEMO-05 y DEMO-06.
- `DEMO-03f` (clonar clips en la sala `videovigilancia`): bloqueada hasta que exista la sala; se asigna entonces.
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
- Verificar con el texto oficial los artículos y plazos marcados (*) en el PRD y fijar la fuente única de citas legales: LEG-03 hecha (#499), borrador que el propietario aprueba con su abogado.
- Derechos: `DER-04` (contracción de la migración de DER-03; espera a DER-03; diseño del Arquitecto hecho; el despliegue lo autoriza el propietario).
- IA de EVYDENTIA sobre Gemini en Vertex AI (diseño del Arquitecto, 2026-11-09): IA-01, IA-02 e IA-03 van en las tandas 25 y 26. Después, `IA-04` (preanálisis), `IA-05` (motor del copiloto), `IA-06` (roadmap) e `IA-07` (asistente, tras IA-02) sobre la compuerta, cuando IA-03 esté hecha con su «Evidencia de humo»; y `IA-08` (guardia sin claves) la última. `IA-09` (aviso de consentimiento del preanálisis con la ubicación real; tras IA-04; UX/UI).
- Gobernanza: `LEG-05` (citas legales sobre transferencia internacional en el Reglamento General y tratamiento de datos en Vertex AI; propuesta del Arquitecto y del CTO, 2026-11-09; no bloquea a IA-03; el dictamen es del propietario).
- Derechos: DER-05, DER-07, DER-06a y DER-06b van en las tandas 29, 31, 33 y 34, con DER-01 en la 35 y DER-02 en la 36 (decisión del CTO, 2026-11-09: la corrección legal visible en la demo va primero); `CI-23` (alcance de PR sin ficha).
- Demo: `DEMO-05b` (purga de las personas ficticias de `users`; tras DEMO-05; revisión de Seguridad).
- Gobernanza: `REP-01` (árbitro de copias en este documento: «Hecho si», «Depende de», «Objetivo» y «Sala(s)»; diseño del Arquitecto, 2026-11-09; va antes que NEON-04).
- Seguridad: `SEC-21` (límite por IP en GET /api/v1/entorno; diseño del Arquitecto, 2026-11-09; revisión de Seguridad).
- Organización: `ORG-23` (lectura del auditor en diagnóstico, incidentes y hoja de ruta; espera a ORG-22, DIAG-11, DIAG-07 y EVI-01).
- Organización: `ORG-22` (rol auditor; diseño del Arquitecto, 2026-11-09; espera a DEMO-03; revisión de Seguridad; trae migración).
- Retiro de Neon (diseño del Arquitecto, 2026-11-09): NEON-00 primero y sola (árbitro y listas); después `NEON-01`, `NEON-02` y `NEON-03`, en paralelo, y `NEON-04` (gobernanza, Tech Lead). FIRMA-02 quita su línea en su PR.
- Estructura funcional EVYDENTIA en backlog, hasta que el propietario la lance: `REG-01` (paquete normativo como dato, con plazos como parámetros; espera a LEG-03).
- Optimización de los tiempos de prueba, pendiente de asignación de tanda por el propietario; CI-15 hecha (#504) y CI-17 hecha (#453 y #455; corrida verde 42422811800); CI-18 hecha (#525); las que comparten el flujo de CI van en serie.
- Conectar `scripts/verificar_bundle_frontend.py` (SEC-14) al workflow del CI tras `npm run build`, que es gobernanza reservada, y fijar los topes de gasto de IA (SEC-13) y de presupuesto (OPS-07).
- Entorno de pruebas de EVYDENTIA (`PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5): decidir el borde (sin balanceador con IAP en el frontend, o balanceador con Cloud Armor y CDN), Memorystore, el horario de Cloud SQL y la firma de pruebas con ANF; crear el proyecto de Google Cloud de pruebas y guardar la lista de quienes prueban en `herramientas\testers-entorno-pruebas.txt`, fuera del repositorio.
- Agregar `npx tsc --noEmit` del frontend al workflow del CI, que es gobernanza reservada (`CI-20`; brief en `governance/apoyo/BRIEF_PROPIETARIO_CI_TSC.md`).
- Plataforma: `PLAT-01` (alta idempotente de organizaciones sintéticas, que retira la excepción de tablas de EP-03); espera a Seguridad y a la asignación de tanda.
- Diagnóstico (backlog): `DIAG-15` (textos sin jerga fuera de las secciones de DiagnosticCanvas; se abre cuando EVI-01, DIAG-07 y DIAG-11 estén hechas).
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

### Biblioteca repartida en tandas

Desde el 2026-10-28 las 24 tareas de Biblioteca y GOB-03 tienen bloque y tanda (serie «Biblioteca (PMV)» de la tabla), en el orden del PMV (`governance/tareas/BIB-100.md`): hasta cuatro por tanda, sin archivos enteros en común, con las dependencias en tandas anteriores. La serie de Biblioteca corre en paralelo a la de la estructura EVYDENTIA (otra persona), sin pisar archivos.

Refactor ADPA del 2026-11-02 (coordinador): cinco fichas nuevas (BIB-111, BIB-112, BIB-113, BIB-114 y RM-24), dependencias artificiales retiradas y archivos internos de otras salas devueltos a su sala; las tandas 32 a 41 de Biblioteca se reparten de nuevo. Detalle en `BIBLIOTECA_PLAN.md`, «Refactor ADPA del 2026-11-02».

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
