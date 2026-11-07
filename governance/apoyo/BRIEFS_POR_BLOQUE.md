# Briefs por bloque de trabajo — EVYDENTIA
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o en «Sin agente» y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento (2026-10-28, reparto del propietario en tandas de hasta cuatro sin archivos enteros en común):** 51 tareas abiertas de 221; 170 hechas (BIB-100 cerrada el 2026-10-29, #220; BIB-109 cerrada el 2026-10-29, #223; RM-21 cerrada el 2026-10-29, #222; DIAG-08 cerrada el 2026-10-30, #235; RM-22 cerrada el 2026-10-31, #269; DIAG-09 cerrada el 2026-10-31, #273 y #279; BIB-101 cerrada el 2026-10-31, #236; REG-02 cerrada el 2026-10-31, #241; GOB-03 cerrada el 2026-10-31, #244; CAPA-02 cerrada el 2026-10-31, #284; RAT-05 cerrada el 2026-11-01, #288; RM-23 cerrada el 2026-11-01, #287; ORG-16 cerrada el 2026-11-01, #281 y #294 (pruebas de la alta corregidas el 2026-11-02, #299); RAT-06 cerrada el 2026-11-01, #295). Tanda 21 terminada: FE-22, FE-23 y RM-21 hechas. Escala SMARTCIDI 1-5 (decisión del propietario del 2026-10-29): DIAG-08 y DIAG-09 la implantan; FE-24 sale de la tanda 21 y espera a DIAG-08; EVI-01 (BL-94), pausada hasta configurar R2, pasa detrás de DIAG-09. tanda 22 (EVY): DIAG-08, DPO-02, SEC-12, CAPA-02; tanda 23 (EVY): FE-24, DIAG-09, ORG-16, RM-22; tanda 24 (EVY): EVI-01, DIAG-04, DIAG-06, ORG-15; tanda 25 (EVY): EVI-02, DIAG-05, ORG-17 (RAT-05 hecha); tanda 26 (EVY): CAPA-03, DIAG-07, RAT-07 (RAT-06 hecha); tanda 27 (EVY): ORG-18, INC-02, DER-01, DPO-03; tanda 28 (EVY): FOR-01, DER-02, MTGE-03, CAPA-04; tanda 29 (EVY): TER-01, REG-02, ORG-20; tanda 30 (EVY): TER-02, FE-25; tanda 31 (BIB): BIB-100, BIB-109, BIB-101, GOB-03; tanda 32 (BIB): BIB-201, BIB-102, BIB-110; tanda 33 (BIB): BIB-107, BIB-202; tanda 34 (EVY): FIRMA-02; tanda 35 (BIB): BIB-301, BIB-103, BIB-203, BIB-204; tanda 36 (BIB): BIB-401, BIB-104, BIB-205, BIB-302; tanda 37 (BIB): BIB-402, BIB-106, BIB-206, BIB-207; tanda 38 (BIB): BIB-208, BIB-303, BIB-304; tanda 39 (BIB): BIB-305, BIB-306; tanda 40 (BIB): BIB-307. En backlog, sin agente, por decisión del propietario: LEG-03 y REG-01.

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
| 20 | BL-166, BL-216 | **Cimiento ADPA (ZERAG):** ADPA-04 (Retirar deuda lateral ADPA lote 2 y sellar DEUDA_LATERAL = 0). BL-91 (FE-21) hecha. **PMV (2026-11-05):** DIAG-13 hecha (#416, BL-208 retirado). BIB-115 hecha (#417, BL-210 retirado). **Seguridad (2026-11-05):** SEC-15 hecha (#428, BL-211 retirado). **CI (2026-11-05):** CI-16 hecha (#420, BL-212 retirado). **Plataforma (2026-11-06):** ORG-21 (el operador entra sin pertenecer a ninguna organización). |
| 21 | BL-167, BL-168, BL-214 | **Cimiento ADPA (ZERAG):** ADPA-05 (Andamiar domain/errores.py por sala y secciones #ID en compuertas); ADPA-07 (Sembrar secciones #ID en registros y componentes Frontend compartidos). FE-22, FE-23 y RM-21 hechas. **PMV (2026-11-05):** FE-26 hecha (#424, BL-209 retirado). **Biblioteca (2026-11-05):** BIB-116 hecha (#419, BL-213 retirado). **Seguridad (2026-11-05):** SEC-16 (secretos obligatorios en la nube). |
| 22 | BL-169, BL-215 | **Cimiento ADPA (ZERAG):** ADPA-06 (Andamiar módulos y secciones #ID en app_core/pasillo/). DIAG-08, DPO-02, SEC-12 y CAPA-02 hechas. **Seguridad (2026-11-05):** SEC-17 (configuración mínima en la nube: `DATABASE_URL` y `CORS_ORIGINS`). |
| 23 | BL-170, BL-171, BL-206 | **Estructura EVYDENTIA + ADPA:** ADPA-08 (Restaurar migración base de terceros_encargados y transferencias_terceros con RLS); ADPA-09 (Andamiar las salas faltantes del PRD §7.1: formacion y conservacion). FE-24 hecha (#378, BL-97 retirado); DIAG-09, ORG-16 y RM-22 hechas. **Diagnóstico (2026-11-05):** DIAG-11 (diagnóstico de prueba y real, dos sellos como máximo). |
| 24 | BL-94, BL-104, BL-105, BL-101 | **Estructura EVYDENTIA:** EVI-01 (Las evidencias se guardan en el servidor); DIAG-04 (El administrador asigna los dominios del assessment a encarg); DIAG-06 (Comparativo de un assessment con la línea base, por dimensió); ORG-15 (Cartera de organizaciones por pertenencia, con semáforos por). |
| 25 | BL-107, BL-106, BL-135, BL-207 | **Estructura EVYDENTIA:** EVI-02 (Vigencia y visibilidad de las evidencias y paquete para insp); DIAG-05 («No aplica» exige justificación en el assessment); ORG-17 (Inventario de activos y sistemas, soportes y personas mínima); RAT-05 hecha (#288, BL-139 retirado). **Diagnóstico (2026-11-05):** DIAG-12 (estados: el assessment actual). |
| 26 | BL-108, BL-109, BL-143 | **Estructura EVYDENTIA:** CAPA-03 (La evidencia vencida reabre el control periódico y produce u); DIAG-07 (Responden el administrador y los encargados del diagnóstico); RAT-07 (Colectivos de titulares y registro de consentimientos por fi). |
| 27 | BL-138, BL-137, BL-140, BL-141 | **Estructura EVYDENTIA:** ORG-18 (Sedes de la organización y clientes cuando actúa como encarg); INC-02 (Asistente de vulneración en ocho secciones con decisión de n); DER-01 (Solicitudes de titulares); DPO-03 (Consultas de la organización al DPO con historial como evide). |
| 28 | BL-146, BL-145, BL-147, BL-144 | **Estructura EVYDENTIA:** FOR-01 (Formación); DER-02 (Portal público de solicitudes de titulares por organización,); MTGE-03 (EIPD guiada de ocho pasos con asistente de obligatoriedad, d); CAPA-04 (Auditoría con grilla de verificación por dominio y acta por ). |
| 29 | BL-151, BL-148 | **Estructura EVYDENTIA:** TER-01 (Hallazgos automáticos de terceros); RM-23 hecha (#287, BL-150 retirado); REG-02 hecha (#241, BL-149 retirado); ORG-20 (Papelera (archivar y restaurar) y exportación completa de lo). |
| 30 | BL-153, BL-152, BL-172 | **Estructura EVYDENTIA:** TER-02 (Cuestionario de garantías del encargado por portal externo, ); FE-25 (Ficha resumen de la organización fija bajo la barra superior); CON-01 (Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit). |
| 31 | — | **Biblioteca (PMV):** BIB-100 hecha (#220, BL-110 retirado); BIB-109 hecha (#223, BL-117 retirado); BIB-101 hecha (#236, BL-111 retirado); GOB-03 hecha (#244, BL-134 retirado). |
| 32 | — | **Biblioteca (PMV):** BIB-111 hecha (#335, BL-159 retirado); BIB-112 hecha (#347, BL-160 retirado); RM-24 hecha (#345, BL-163 retirado). |
| 33 | — | **Biblioteca (PMV):** BIB-107 hecha (#359, BL-116 retirado); BIB-201 hecha (#358, BL-119 retirado); BIB-102 hecha (#360, BL-112 retirado); BIB-103 hecha (#361, BL-113 retirado). |
| 34 | BL-154 | **Estructura EVYDENTIA:** FIRMA-02 (Aceptación simple con acuse (nombre, correo, fecha, IP y sel). |
| 35 | — | **Biblioteca (PMV):** BIB-113 hecha (#363, BL-161 retirado); BIB-114 hecha (#364, BL-162 retirado); BIB-104 hecha (#365, BL-114 retirado); BIB-204 hecha (#366, BL-122 retirado). |
| 36 | — | **Biblioteca (PMV):** BIB-301 hecha (#373, BL-127 retirado); BIB-302 hecha (#376, BL-128 retirado); BIB-304 hecha (#375, BL-130 retirado); BIB-306 hecha (#374, BL-132 retirado). |
| 37 | BL-115, BL-155 | **Biblioteca (PMV):** BIB-202 hecha (#387, BL-120 retirado); BIB-203 hecha (#389, BL-121 retirado); BIB-106 (Documentos externos del cliente; en pausa hasta EVI-01 y decisiones del propietario); BIB-401 (Plantillas de la cuenta profesional; espera ORG-15). |
| 38 | BL-118 | **Biblioteca (PMV):** BIB-303 hecha (#388, BL-129 retirado); BIB-402 hecha (#386, BL-156 retirado); BIB-205 hecha (#393, BL-123 retirado); BIB-110 (Biblioteca al cambiar de organización; espera EVI-01). |
| 39 | — | **Biblioteca (PMV):** BIB-206 hecha (#396, BL-124 retirado); BIB-207 hecha (#397, BL-125 retirado); BIB-305 hecha (#392, BL-131 retirado). |
| 40 | — | **Biblioteca (PMV):** BIB-208 hecha (#403, BL-126 retirado). |
| 41 | — | **Biblioteca (PMV):** BIB-307 hecha (#398, BL-133 retirado). |
| 42 | BL-173, BL-174 | **Migración a Google Cloud (Backend y CI/CD):** GCP-01 (Chasis Cloud Run ASGI backend); GCP-02 (Acelerador CI/CD TIA por grafo ADPA). |
| 43 | BL-185, BL-186 | **Migración a Google Cloud (Frontend y Base de Datos):** GCP-03 (Migración Frontend Next.js standalone a Cloud Run); GCP-04 (Migración Base de Datos Cloud SQL PostgreSQL 16 y Load Balancer). |
| 44 | BL-175, BL-176, BL-177, BL-187 | **Nube Híbrida + IA (GCP):** BOV-01 (Sala Bóveda Cloud: paquetes de reventa y cuotas GB/Egress); DLP-01 (Descubrimiento DLP muestreado y Módulo 10 para el RAT); VTX-01 (Vertex AI Context Caching sobre el corpus normativo LOPDP/SPDP); NORM-01 (Sala Inteligencia Normativa: ingesta SPDP, SHA-256 y custodia del original). |
| 45 | BL-178, BL-179, BL-180, BL-188, BL-189 | **Bóveda Dual + Satélite Go + CCTV:** BOV-02 (Bóveda Dual GCS short-ttl vs long-retention WORM y Signed URLs V4); GOVW-01 (Microservicio Go vault_worker para Eventarc, SHA-256 en streaming y purga); CCTV-01 (Sala Videovigilancia LOPDP: cámaras H.265, eventos, sin audio y retención 15 días).; NORM-02 (Centro de Vigilancia Normativa); NORM-03 (Impacto normativo con Gemini validado por el DPO). |
| 46 | BL-181, BL-182, BL-183 | **Forense Dual + Hold Legal + Edge Go:** BOV-03 (Carril Forense Dual: original SHA-256 intacto + previews WebP/AVIF/WebM); CCTV-02 (Hold Legal forense por incidente/ARCOP y actas quincenales SHA-256); GOCA-01 (Agente Edge en Go para cámaras/NVR con subida directa TLS). |
| 47 | BL-184 | **Orquestador 10 Dimensiones + Bóveda Cloud:** BOV-04 (Centro de mando comercial de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete). |
| 48 | BL-190, BL-191, BL-192, BL-193 | **Requisitos de una aplicación vendible (revisión del 2026-11-04):** SEC-13 (Límite de peticiones y tope de gasto de IA); SEC-14 (Frontend sin mapas de fuente ni secretos públicos); GCP-05 (Escalado verificable y prueba de carga); OPS-07 (Observabilidad sin datos personales). SEC-13 y SEC-14 no dependen de Google Cloud: el propietario puede adelantarlas. |
| 49 | BL-194, BL-195, BL-196 | **Requisitos de una aplicación vendible (segunda parte):** GCP-06 (Cloud CDN solo para activos estáticos y caché de lectura por tenant); GCP-07 (Despliegue progresivo reversible y migraciones compatibles); API-02 (API de integración versionada con claves por organización y webhooks firmados). |
| 50 | BL-197, BL-198, BL-199, BL-200 | **Entorno de pruebas de EVYDENTIA en Google Cloud (2026-11-05, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5):** EP-01 (identidad y guardias del backend); EP-02 (aviso y `noindex`); EP-03 (datos y clips sintéticos); EP-06 (ciclo de una versión por digest). Ninguna depende de otra ni de Google Cloud. |
| 51 | BL-201, BL-202, BL-203, BL-204 | **Entorno de pruebas (segunda parte):** EP-04 (proyecto, Cloud Run, IAP y presupuesto; tras GCP-01 y GCP-03); EP-05 (Cloud SQL, buckets sin bloqueo y secretos; tras GCP-04); EP-07 (verificador); EP-08 (correo solo a destinatarios permitidos). No dependen de la tanda 50: EP-07 y EP-08 pueden lanzarse a la vez que ella. |
| 52 | BL-205 | **Entorno de pruebas (puesta en marcha):** EP-09, con EP-01…EP-08 integradas; la hace una persona. |
| 53 | BL-217, BL-220 | **Demo comercial (2026-11-06, PRD Módulo 9; tandas ortogonales: ningún archivo en común dentro de una tanda):** DEMO-01 (modo demo seguro; dueña de la migración, `app_core/security.py`, `api/routers/demo.py` y la compuerta) y DEMO-04 (solo `frontend/`, contra el contrato escrito), en paralelo. |
| 54 | BL-218 | **Demo comercial:** DEMO-03 (plantilla; usa `tenants.es_demo` de la migración de DEMO-01). |
| 55 | BL-219 | **Demo comercial:** DEMO-02 (organización por sesión, vencimiento y purga; tras DEMO-01 y DEMO-03; router propio y sección `#DEMO-02` de la compuerta). |

## Briefs

### BL-94 · evidencias-en-el-servidor  (tanda 24)

**Contexto.** Sala(s): `evidencias`, `frontend`. Depende de: `DIAG-03` (BL-92), `DIAG-01`, `FE-14`, `FE-16`, `SEC-05`, y de las dueñas de las pruebas que adapta (`CAPA-01`, `DIAG-02`, `DPO-01`, `MTGE-01`, `RAT-01`, `ORG-00`, `ORG-08`, `TEST-01`), y de `DIAG-08` y `DIAG-09` (pendientes: escala SMARTCIDI, que reescribe el formulario del diagnóstico), y de `FE-26`, que puso la evidencia física tras `EVIDENCIA_FISICA` / `NEXT_PUBLIC_EVIDENCIA_FISICA` (EVI-01 la enciende). Especificaciones: `governance/tareas/EVI-01.md`.

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
  - `api/routers/diagnostico_resultados.py#EVI-01`
  - `tests/test_evidencias_persistencia.py`
  - `tests/test_evidencias_contrato.py`
  - `tests/test_evidencia_http.py`
  - `tests/test_api_gateway.py`
  - `frontend/src/lib/evidencias/**`
  - `frontend/src/components/evidencias/**`
  - `frontend/src/components/modules/EvidenciasModule.tsx#EVI-01`
  - `frontend/src/components/config/CargaEvidencias.tsx`
  - `frontend/src/components/DiagnosticCanvas.tsx#EVI-01`
  - `frontend/src/store/useAuditStore.ts`
  - `frontend/tests/evidencias/**`
  - `features/evidencias/evidencias_service.py#EVI-01`
  - `features/evidencias/domain/errores.py#EVI-01`
  - `app_core/pasillo/diagnostico.py#EVI-01`

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
  - `features/organizacion/domain/errores.py#ORG-15`
  - `app_core/pasillo/organizacion.py#ORG-15`
  - `app_core/pasillo/biblioteca.py#ORG-15`
  - `frontend/src/components/pantallas/ORG-15.tsx`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No uses `BYPASSRLS` ni consultas sin contexto de organización.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-15`: pytest tests/test_organizacion_cartera.py y tests/test_organizaciones_por_persona.py contra una rama Neon de revisión con lopdp_app, con la prueba de INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP (la cartera lista solo organizaciones con rol vigente) + suite completa + Playwright de frontend/tests/cartera + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-104 · asignacion-de-dominios  (tanda 24)

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
  - `features/diagnostico/domain/errores.py#DIAG-04`
  - `app_core/pasillo/diagnostico.py#DIAG-04`
  - `app_core/pasillo/evidencias.py#DIAG-04`
  - `app_core/pasillo/organizacion.py#DIAG-04`
  - `app_core/pasillo/regulacion_rag.py#DIAG-04`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No toques `DiagnosticCanvas.tsx` (EVI-01, DIAG-05).
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-04`: pytest tests/test_diagnostico_asignaciones.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/diagnostico/asignaciones.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-105 · comparativo-linea-base  (tanda 24)

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
  - `features/diagnostico/domain/errores.py#DIAG-06`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No muestres un «avance global».
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-06`: pytest tests/test_diagnostico_comparativo.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico/comparativo.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS).
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-106 · no-aplica-justificado  (tanda 25)

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
  - `frontend/src/components/DiagnosticCanvas.tsx#DIAG-05`
  - `frontend/tests/diagnostico/no-aplica.spec.ts`
  - `features/diagnostico/domain/errores.py#DIAG-05`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- Espera a que EVI-01 esté en `main`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-05`: pytest tests/test_diagnostico_no_aplica.py y tests/test_diagnostico_respuestas.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/diagnostico + tsc --noEmit + npm run build; prueba de mutación documentada.
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-107 · evidencias-vigencia-inspeccion  (tanda 25)

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

### BL-108 · reapertura-por-evidencia-vencida  (tanda 26)

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

### BL-109 · quien-responde-y-quien-sella  (tanda 26)

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
  - `frontend/src/components/pantallas/index.tsx#DIAG-07`

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

### BL-115 · documentos-externos-del-cliente  (tanda 37)

**Contexto.** Sala(s): `biblioteca`, `frontend`, `pasillo_central`. Depende de: `BIB-107` (pendiente), `BIB-111` (pendiente), `BIB-112` (pendiente). Especificaciones: `governance/tareas/BIB-106.md`.

**Objetivo** (en este orden):

1. `BIB-106` — Documentos externos del cliente

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.
- `¤rbac-tenant`: 158 coincidencias en 119 archivos.
- `¤arbitro`: 162 coincidencias en 81 archivos.

**Escribe** (lista exclusiva):

  - `features/biblioteca/services/carga_externa.py`
  - `features/biblioteca/services/analisis_archivos.py`
  - `features/biblioteca/biblioteca_service.py#BIB-106`
  - `api/routers/biblioteca_cargas.py`
  - `frontend/src/lib/biblioteca/cargas.ts`
  - `frontend/src/components/biblioteca/cargas/**`
  - `tests/test_bib_106_externos.py`
  - `frontend/tests/biblioteca/externos.spec.ts`
  - `frontend/src/components/biblioteca/vistas/index.ts#BIB-106`
  - `features/biblioteca/domain/errores.py#BIB-106`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `BIB-106`: pytest tests/test_bib_106_externos.py; npx playwright test tests/biblioteca/externos.spec.ts; suite pytest tests --ignore=tests/e2e en rama propia; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-118 · biblioteca-al-cambiar-de-organizacin-cach-cambio  (tanda 38)

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

### BL-135 · inventario-de-activos-y-sistemas-soportes-y-pers  (tanda 25)

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
  - `features/organizacion/domain/errores.py#ORG-17`
  - `app_core/pasillo/organizacion.py#ORG-17`
  - `app_core/pasillo/biblioteca.py#ORG-17`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `=== <ID> ===` … `=== fin <ID> ===`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-17`: pytest tests/test_organizacion_inventario.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/inventario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-137 · asistente-de-vulneracin-en-ocho-secciones-con-de  (tanda 27)

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
  - `frontend/src/components/pantallas/index.tsx#INC-02`

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
  - `frontend/src/components/pantallas/index.tsx#ORG-18`

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

### BL-140 · solicitudes-de-titulares-verificacin-de-identida  (tanda 27)

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

### BL-141 · consultas-de-la-organizacin-al-dpo-con-historial  (tanda 27)

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
  - `frontend/src/components/pantallas/index.tsx#DPO-03`

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

### BL-143 · colectivos-de-titulares-y-registro-de-consentimi  (tanda 26)

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

### BL-144 · auditora-con-grilla-de-verificacin-por-dominio-y  (tanda 28)

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
  - `frontend/src/components/pantallas/index.tsx#CAPA-04`

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

### BL-145 · portal-pblico-de-solicitudes-de-titulares-por-or  (tanda 28)

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

### BL-146 · formacin-contenidos-acciones-formativas-con-exam  (tanda 28)

**Contexto.** Sala(s): `formacion`, `frontend`. Depende de: `ORG-17` (pendiente), `EVI-02` (pendiente), `FE-22` (pendiente). Especificaciones: `governance/tareas/FOR-01.md`, `governance/especificaciones/FOR-01.md` y `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Objetivo** (en este orden):

1. `FOR-01` — Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: 35 coincidencias en 13 archivos.
- `¤rbac-tenant`: 103 coincidencias en 66 archivos.

**Escribe** (lista exclusiva):

  - `features/formacion/**`
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
  - `frontend/src/components/pantallas/index.tsx#FOR-01`

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

### BL-147 · eipd-guiada-de-ocho-pasos-con-asistente-de-oblig  (tanda 28)

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
  - `frontend/src/components/pantallas/index.tsx#MTGE-03`

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

### BL-148 · papelera-archivar-y-restaurar-y-exportacin-compl  (tanda 29)

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
  - `frontend/src/components/pantallas/index.tsx#ORG-20`

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

### BL-151 · hallazgos-automticos-de-terceros-encargado-sin-c  (tanda 29)

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

### BL-152 · ficha-resumen-de-la-organizacin-fija-bajo-la-bar  (tanda 30)

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

### BL-153 · cuestionario-de-garantas-del-encargado-por-porta  (tanda 30)

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

### BL-154 · aceptacin-simple-con-acuse-nombre-correo-fecha-i  (tanda 34)

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

### BL-155 · plantillas-de-la-cuenta-profesional-tercera-capa  (tanda 37)

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

### BL-166 · retirar-deuda-lateral-adpa-lote-2-deuda-cero  (tanda 20)

**Contexto.** Sala(s): `riesgos_mtge`, `roadmap`. Depende de: `ADPA-03`, `DIAG-08`. Especificaciones: `governance/tareas/ADPA-04.md`.

**Objetivo** (en este orden):

1. `ADPA-04` — Retirar deuda lateral ADPA lote 2 (riesgos_mtge, roadmap) y sellar DEUDA_LATERAL = 0

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `app_core/pasillo/rat.py#ADPA-04`
  - `app_core/pasillo/organizacion.py#ADPA-04`
  - `features/riesgos_mtge/riesgos_mtge_service.py#ADPA-04`
  - `features/roadmap/generador_service.py#ADPA-04`
  - `features/roadmap/recalculo_service.py#ADPA-04`
  - `features/roadmap/roadmap_service.py#ADPA-04`
  - `tests/deuda_adpa/riesgos_mtge.txt`
  - `tests/deuda_adpa/roadmap.txt`
  - `tests/test_adpa_dependencias.py#ADPA-04`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-04`: pytest tests/test_adpa_dependencias.py + suite completa
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-167 · andamiar-domain-errores-y-secciones-compuertas  (tanda 21)

**Contexto.** Sala(s): `auditoria_capa`, `derechos_arco`, `diagnostico`, `dpo_cockpit`, `evidencias`, `firma_electronica`, `incidentes`, `notificaciones`, `organizacion`, `rat`, `regulacion_rag`, `riesgos_mtge`, `roadmap`, `terceros`, `transferencias`. Depende de: `ADPA-04`, `NOTIF-01`, `FIRMA-01`, `INC-01`. Especificaciones: `governance/tareas/ADPA-05.md`.

**Objetivo** (en este orden):

1. `ADPA-05` — Andamiar domain/errores.py por sala y secciones #ID en compuertas y routers compartidos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `features/auditoria_capa/domain/errores.py#ADPA-05`
  - `features/derechos_arco/domain/errores.py#ADPA-05`
  - `features/diagnostico/domain/errores.py#ADPA-05`
  - `features/dpo_cockpit/domain/errores.py#ADPA-05`
  - `features/evidencias/domain/errores.py#ADPA-05`
  - `features/firma_electronica/domain/errores.py#ADPA-05`
  - `features/incidentes/domain/errores.py#ADPA-05`
  - `features/notificaciones/domain/errores.py#ADPA-05`
  - `features/organizacion/domain/errores.py#ADPA-05`
  - `features/rat/domain/errores.py#ADPA-05`
  - `features/regulacion_rag/domain/errores.py#ADPA-05`
  - `features/riesgos_mtge/domain/errores.py#ADPA-05`
  - `features/roadmap/domain/errores.py#ADPA-05`
  - `features/terceros/domain/errores.py#ADPA-05`
  - `features/transferencias/domain/errores.py#ADPA-05`
  - `features/auditoria_capa/auditoria_capa_service.py#ADPA-05`
  - `features/derechos_arco/derechos_arco_service.py#ADPA-05`
  - `features/diagnostico/diagnostico_service.py#ADPA-05`
  - `api/routers/diagnostico_respuestas.py#ADPA-05`
  - `api/routers/diagnostico_resultados.py#ADPA-05`
  - `features/dpo_cockpit/dpo_cockpit_service.py#ADPA-05`
  - `features/evidencias/evidencias_service.py#ADPA-05`
  - `features/firma_electronica/firma_electronica_service.py#ADPA-05`
  - `features/incidentes/incidentes_service.py#ADPA-05`
  - `features/notificaciones/notificaciones_service.py#ADPA-05`
  - `features/organizacion/organizacion_service.py#ADPA-05`
  - `features/rat/rat_service.py#ADPA-05`
  - `features/riesgos_mtge/riesgos_mtge_service.py#ADPA-05`
  - `features/roadmap/roadmap_service.py#ADPA-05`
  - `features/terceros/terceros_service.py#ADPA-05`
  - `features/transferencias/transferencias_service.py#ADPA-05`
  - `tests/test_adpa05_secciones_y_errores.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-05`: pytest tests/test_adpa05_secciones_y_errores.py + python scripts/verificar_reparto.py
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-168 · secciones-id-en-registros-y-componentes-frontend  (tanda 21)

**Contexto.** Sala(s): `plataforma`, `diagnostico`, `evidencias`, `biblioteca`. Depende de: `FE-22`, `BIB-101`, `DIAG-09`. Especificaciones: `governance/tareas/ADPA-07.md`.

**Objetivo** (en este orden):

1. `ADPA-07` — Sembrar secciones #ID en registros y componentes Frontend compartidos para eliminar contención

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `frontend/src/components/layout/menus/index.ts#ADPA-07`
  - `frontend/src/components/pantallas/index.tsx#ADPA-07`
  - `frontend/src/components/layout/DashboardHeader.tsx#ADPA-07`
  - `frontend/src/store/useBibliotecaStore.ts#ADPA-07`
  - `frontend/src/components/DiagnosticCanvas.tsx#ADPA-07`
  - `frontend/src/components/modules/EvidenciasModule.tsx#ADPA-07`
  - `tests/test_adpa07_secciones_frontend.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-07`: pytest tests/test_adpa07_secciones_frontend.py + npm --prefix frontend run build
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-169 · andamiar-modulos-y-secciones-en-pasillo-central  (tanda 22)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `ADPA-04`, `ADPA-05`. Especificaciones: `governance/tareas/ADPA-06.md`.

**Objetivo** (en este orden):

1. `ADPA-06` — Andamiar módulos y secciones #ID en app_core/pasillo/ para integraciones entre salas pendientes

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `app_core/pasillo/auditoria_capa.py#ADPA-06`
  - `app_core/pasillo/biblioteca.py#ADPA-06`
  - `app_core/pasillo/derechos_arco.py#ADPA-06`
  - `app_core/pasillo/diagnostico.py#ADPA-06`
  - `app_core/pasillo/dpo_cockpit.py#ADPA-06`
  - `app_core/pasillo/evidencias.py#ADPA-06`
  - `app_core/pasillo/firma_electronica.py#ADPA-06`
  - `app_core/pasillo/incidentes.py#ADPA-06`
  - `app_core/pasillo/notificaciones.py#ADPA-06`
  - `app_core/pasillo/organizacion.py#ADPA-06`
  - `app_core/pasillo/rat.py#ADPA-06`
  - `app_core/pasillo/regulacion_rag.py#ADPA-06`
  - `app_core/pasillo/riesgos_mtge.py#ADPA-06`
  - `app_core/pasillo/roadmap.py#ADPA-06`
  - `app_core/pasillo/terceros.py#ADPA-06`
  - `app_core/pasillo/transferencias.py#ADPA-06`
  - `tests/test_adpa06_pasillos_secciones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-06`: pytest tests/test_adpa06_pasillos_secciones.py tests/test_adpa_dependencias.py
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-170 · restaurar-migracion-terceros-transferencias-rls  (tanda 23)

**Contexto.** Sala(s): `terceros`, `transferencias`. Depende de: `SEC-09`, `ADPA-01`, `ADPA-05`, `ADPA-06`. Especificaciones: `governance/tareas/ADPA-08.md`.

**Objetivo** (en este orden):

1. `ADPA-08` — Restaurar migración base de terceros_encargados y transferencias_terceros con RLS y separar salas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `alembic/versions/20260420_01_restaurar_terceros_transferencias_rls.py`
  - `db/models/terceros.py#ADPA-08`
  - `features/terceros/models.py#ADPA-08`
  - `features/transferencias/models.py`
  - `tests/test_adpa08_terceros_transferencias_schema.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni la rama Neon `test` compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ADPA-08`: pytest tests/test_adpa08_terceros_transferencias_schema.py against rama Neon de revisión con lopdp_app
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-171 · andamiar-salas-formacion-y-conservacion-prd  (tanda 23)

**Contexto.** Sala(s): `formacion`, `conservacion`. Depende de: `ADPA-05`, `ADPA-06`. Especificaciones: `governance/tareas/ADPA-09.md`.

**Objetivo** (en este orden):

1. `ADPA-09` — Andamiar las salas faltantes del PRD §7.1 (features/formacion y features/conservacion) y sus pasillos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤adpa`: 407 coincidencias en 96 archivos.

**Escribe** (lista exclusiva):

  - `features/formacion/__init__.py`
  - `features/formacion/formacion_service.py#ADPA-09`
  - `features/formacion/domain/__init__.py`
  - `features/formacion/domain/errores.py#ADPA-09`
  - `features/conservacion/__init__.py`
  - `features/conservacion/conservacion_service.py#ADPA-09`
  - `features/conservacion/domain/__init__.py`
  - `features/conservacion/domain/errores.py#ADPA-09`
  - `app_core/pasillo/formacion.py#ADPA-09`
  - `app_core/pasillo/conservacion.py#ADPA-09`
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

### BL-172 · sala-conservacion-y-bloqueo-politicas-retencion  (tanda 30)

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
  - `api/main.py#CON-01`
  - `frontend/src/components/layout/menus/index.ts#CON-01`
  - `frontend/src/components/pantallas/index.tsx#CON-01`
  - `frontend/src/components/pantallas/CON-01.tsx`
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

### BL-173 · chasis-cloud-run-asgi-y-rls-1rtt-pgbouncer  (tanda 42)

**Contexto.** Sala(s): `pasillo_central, operaciones`. Depende de: `RM-00`, `RM-02`, `ENT-02`, `ADPA-02`. Especificaciones: `governance/tareas/GCP-01.md`, `governance/especificaciones/GCP-01.md`.

**Objetivo** (en este orden):

1. `GCP-01` — Chasis Cloud Run ASGI, sesión RLS en 1 RTT con PgBouncer y Secret Manager ADC

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤adpa`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/db/session.py#GCP-01`
  - `app_core/cloud/__init__.py`
  - `app_core/cloud/gcp_runtime.py`
  - `governance/operaciones/Dockerfile.cloudrun`
  - `governance/operaciones/cloudrun_service.yaml`
  - `tests/test_gcp01_cloudrun_rls_single_rtt.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-01`: pytest tests/test_gcp01_cloudrun_rls_single_rtt.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-174 · acelerador-cicd-tia-determinista-grafo-adpa  (tanda 42)

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

### BL-175 · sala-boveda-cloud-paquetes-y-cuotas-egress  (tanda 44)

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
  - `api/main.py#BOV-01`
  - `frontend/src/components/layout/menus/index.ts#BOV-01`
  - `frontend/src/components/pantallas/index.tsx#BOV-01`
  - `frontend/src/components/pantallas/BOV-01.tsx`
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

### BL-176 · sala-descubrimiento-dlp-muestreado-y-modulo10  (tanda 44)

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
  - `api/main.py#DLP-01`
  - `frontend/src/components/layout/menus/index.ts#DLP-01`
  - `frontend/src/components/pantallas/index.tsx#DLP-01`
  - `frontend/src/components/pantallas/DLP-01.tsx`
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

### BL-177 · vertex-ai-context-caching-corpus-lopdp  (tanda 44)

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
  - `features/ai_copilot/copilot_service.py#VTX-01`
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

### BL-178 · boveda-dual-gcs-short-ttl-vs-long-retention-worm  (tanda 45)

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

### BL-179 · satelite-go-vault-worker-eventarc-y-purga  (tanda 45)

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

### BL-180 · sala-videovigilancia-lopdp-camaras-h265-15dias  (tanda 45)

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
  - `api/main.py#CCTV-01`
  - `frontend/src/components/layout/menus/index.ts#CCTV-01`
  - `frontend/src/components/pantallas/index.tsx#CCTV-01`
  - `frontend/src/components/pantallas/CCTV-01.tsx`
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

### BL-181 · carril-forense-dual-sha256-original-y-preview-webp  (tanda 46)

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
  - `frontend/src/components/pantallas/BOV-03.tsx`
  - `frontend/src/components/pantallas/index.tsx#BOV-03`
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

### BL-182 · congelamiento-forense-hold-legal-cctv-y-acta-quincenal  (tanda 46)

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
  - `frontend/src/components/pantallas/CCTV-02.tsx`
  - `frontend/src/components/pantallas/index.tsx#CCTV-02`
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

### BL-183 · agente-edge-go-cctv-recorte-eventos-y-subida-tls  (tanda 46)

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

### BL-184 · orquestador-comercial-diez-dimensiones-y-boveda-cloud  (tanda 47)

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
  - `frontend/src/components/pantallas/index.tsx#BOV-04`
  - `frontend/src/components/pantallas/BOV-04.tsx`
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

### BL-185 · migracion-frontend-nextjs-standalone-cloudrun  (tanda 43)

**Contexto.** Sala(s): `frontend, operaciones`. Depende de: `GCP-01`, `FE-21`, `FE-22`. Especificaciones: `governance/tareas/GCP-03.md`, `governance/especificaciones/GCP-03.md`.

**Objetivo** (en este orden):

1. `GCP-03` — Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤frontend-ide`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/Dockerfile.cloudrun`
  - `frontend/next.config.cloudrun.ts`
  - `governance/operaciones/cloudrun_frontend_service.yaml`
  - `tests/test_gcp03_frontend_cloudrun.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-03`: pytest tests/test_gcp03_frontend_cloudrun.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-186 · migracion-basedatos-cloudsql-postgres-y-loadbalancer  (tanda 43)

**Contexto.** Sala(s): `pasillo_central, operaciones`. Depende de: `GCP-01`, `SEC-10`. Especificaciones: `governance/tareas/GCP-04.md`, `governance/especificaciones/GCP-04.md`.

**Objetivo** (en este orden):

1. `GCP-04` — Migración de Base de Datos y Enrutamiento Unificado: Cloud SQL PostgreSQL 16 con RLS forzado y Cloud Load Balancing

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤ci-cd`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md`
  - `governance/operaciones/cloud_sql_instance.yaml`
  - `governance/operaciones/cloud_load_balancer.yaml`
  - `scripts/verificar_cloudsql_conexion.py`
  - `tests/test_gcp04_cloudsql_migration_cutover.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-04`: pytest tests/test_gcp04_cloudsql_migration_cutover.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-187 · sala-inteligencia-normativa-ingesta-spdp-y-sha256  (tanda 44)

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

### BL-188 · centro-de-vigilancia-normativa-spdp  (tanda 45)

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

### BL-189 · impacto-normativo-gemini-hitl-y-cache  (tanda 45)

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
  - `features/ai_copilot/copilot_service.py#NORM-03`
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

### BL-190 · limite-de-peticiones-y-tope-de-ia  (tanda 48)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `ENT-02`, `SEC-03`, `SEC-10`. Especificaciones: `governance/tareas/SEC-13.md`, `governance/especificaciones/SEC-13.md`.

**Objetivo** (en este orden):

1. `SEC-13` — Límite de peticiones en la API por IP, usuario y organización, con tope de gasto de IA

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤copiloto-ia`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/limites/__init__.py`
  - `app_core/limites/limitador.py`
  - `app_core/limites/politicas.py`
  - `api/middleware/limite_peticiones.py`
  - `main.py#SEC-13`
  - `app_core/errors.py#SEC-13`
  - `tests/test_sec13_limite_peticiones.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-13`: pytest tests/test_sec13_limite_peticiones.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-191 · frontend-sin-mapas-de-fuente-ni-secretos  (tanda 48)

**Contexto.** Sala(s): `frontend, pruebas`. Depende de: ninguna. Especificaciones: `governance/tareas/SEC-14.md`, `governance/especificaciones/SEC-14.md`.

**Objetivo** (en este orden):

1. `SEC-14` — El frontend no publica mapas de fuente ni secretos en variables públicas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `scripts/verificar_bundle_frontend.py`
  - `tests/test_sec14_frontend_sin_mapas.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-14`: pytest tests/test_sec14_frontend_sin_mapas.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-192 · escalado-verificable-cloud-run-y-prueba-de-carga  (tanda 48)

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

### BL-193 · observabilidad-sin-datos-personales  (tanda 48)

**Contexto.** Sala(s): `pasillo_central, operaciones`. Depende de: `GCP-01`. Especificaciones: `governance/tareas/OPS-07.md`, `governance/especificaciones/OPS-07.md`.

**Objetivo** (en este orden):

1. `OPS-07` — Observabilidad: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤observabilidad`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.
- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/observabilidad/__init__.py`
  - `app_core/observabilidad/registro.py`
  - `api/middleware/correlacion.py`
  - `main.py#OPS-07`
  - `governance/operaciones/monitoreo/alertas.yaml`
  - `governance/operaciones/OBSERVABILIDAD.md`
  - `tests/test_ops07_observabilidad.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `OPS-07`: pytest tests/test_ops07_observabilidad.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-194 · cloud-cdn-estatico-y-cache-de-lectura-por-tenant  (tanda 49)

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

### BL-195 · despliegue-progresivo-revisiones-cloudrun-y-migraciones-compatibles  (tanda 49)

**Contexto.** Sala(s): `operaciones, pruebas`. Depende de: `GCP-03`, `GCP-04`, `OPS-07`. Especificaciones: `governance/tareas/GCP-07.md`, `governance/especificaciones/GCP-07.md`.

**Objetivo** (en este orden):

1. `GCP-07` — Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract)

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤cloud-run-perf`: registrado en `VPA_MAP.md`.
- `¤ci-cd`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/despliegue_progresivo.yaml`
  - `scripts/verificar_migracion_compatible.py`
  - `tests/test_gcp07_despliegue_progresivo.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas `# --- INICIO <ID> ---` … `# --- FIN <ID> ---`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No modifiques ninguna tarea del PMV que permanece en plataformas independientes.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-07`: pytest tests/test_gcp07_despliegue_progresivo.py + suite completa + vigilantes
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-196 · api-integracion-versionada-claves-y-webhooks-firmados  (tanda 49)

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

### BL-197 · identidad-y-guardias-del-entorno-de-pruebas  (tanda 50)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `RM-00`, `ENT-02`. Especificaciones: `governance/tareas/EP-01.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-01` — Entorno de pruebas: identidad del entorno y guardias de arranque del backend

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/entorno/__init__.py`
  - `app_core/entorno/guardias.py`
  - `api/routers/entorno.py`
  - `main.py#EP-01`
  - `tests/test_ep01_guardias_entorno.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-01`: pytest tests/test_ep01_guardias_entorno.py + suite completa; prueba de que con APP_ENV distinto de pruebas el arranque y las respuestas no cambian, salvo la cabecera X-Entorno
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-198 · aviso-de-entorno-de-pruebas-y-noindex  (tanda 50)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-19`. Especificaciones: `governance/tareas/EP-02.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-02` — Entorno de pruebas: aviso fijo en toda pantalla y robots noindex fuera de producción

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤interfaz`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/entorno.ts`
  - `frontend/src/components/entorno/**`
  - `frontend/src/app/robots.ts`
  - `frontend/src/app/layout.tsx`
  - `frontend/tests/entorno/**`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-02`: cd frontend; npx playwright test tests/entorno; npx tsc --noEmit; npm run build; las pruebas de Playwright existentes siguen en verde sin cambios
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-199 · siembra-de-datos-y-clips-sinteticos  (tanda 50)

**Contexto.** Sala(s): `operaciones`. Depende de: ninguna. Especificaciones: `governance/tareas/EP-03.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-03` — Entorno de pruebas: siembra idempotente de organizaciones, evidencias y clips sintéticos, y de las cuentas de quienes prueban

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `scripts/sembrar_entorno_pruebas.py`
  - `scripts/datos_sinteticos/**`
  - `tests/test_ep03_sembrar_entorno.py`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-03`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-03`: pytest tests/test_ep03_sembrar_entorno.py + suite completa; dos corridas seguidas contra una base de desarrollo dejan el mismo estado
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-200 · ciclo-de-una-version-por-digest-y-reinicio  (tanda 50)

**Contexto.** Sala(s): `operaciones`. Depende de: ninguna. Especificaciones: `governance/tareas/EP-06.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-06` — Entorno de pruebas: ciclo de una versión, de migrar y desplegar el digest en pruebas a reiniciar el entorno

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤ci-cd`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `scripts/desplegar_entorno_pruebas.ps1`
  - `scripts/reiniciar_entorno_pruebas.ps1`
  - `scripts/digest_verificado.py`
  - `tests/test_ep06_ciclo_version.py`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-06`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-06`: pytest tests/test_ep06_ciclo_version.py + suite completa; ensayo de los dos scripts con -SoloMostrar, que imprime los pasos sin ejecutarlos
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

### BL-202 · cloud-sql-buckets-sin-bloqueo-y-secretos-de-pruebas  (tanda 51)

**Contexto.** Sala(s): `operaciones`. Depende de: `GCP-04`. Especificaciones: `governance/tareas/EP-05.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-05` — Entorno de pruebas: Cloud SQL propio, buckets sin bloqueo de retención y secretos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤boveda-cloud`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/entornos/pruebas/cloud_sql.yaml`
  - `governance/operaciones/entornos/pruebas/buckets.yaml`
  - `governance/operaciones/entornos/pruebas/secretos.yaml`
  - `tests/test_ep05_datos_pruebas.py`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-05`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-05`: pytest tests/test_ep05_datos_pruebas.py + suite completa
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-203 · verificador-del-entorno-de-pruebas  (tanda 51)

**Contexto.** Sala(s): `operaciones, pruebas`. Depende de: ninguna. Especificaciones: `governance/tareas/EP-07.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-07` — Entorno de pruebas: verificador del entorno y flujo de GitHub tras cada despliegue en pruebas

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `scripts/verificar_entorno_pruebas.py`
  - `tests/test_ep07_verificar_entorno.py`
  - `.github/workflows/entorno-pruebas.yml`
  - `governance/operaciones/ENTORNO_DE_PRUEBAS.md#EP-07`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- `.github/workflows/entorno-pruebas.yml` es gobernanza reservada: entrégalo en el PR para que el propietario lo revise; no toques otro flujo.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-07`: pytest tests/test_ep07_verificar_entorno.py + suite completa; el flujo nuevo no cambia los checks obligatorios del PR
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-204 · correo-solo-a-destinatarios-permitidos  (tanda 51)

**Contexto.** Sala(s): `notificaciones`. Depende de: `NOTIF-01`, `RM-23`. Especificaciones: `governance/tareas/EP-08.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 (contrato del entorno de pruebas).

**Objetivo** (en este orden):

1. `EP-08` — Entorno de pruebas: el correo sale solo hacia destinatarios permitidos

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤entorno-pruebas`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/notificaciones/services/destinatarios_entorno.py`
  - `features/notificaciones/notificaciones_service.py#EP-08`
  - `features/notificaciones/notificaciones_service.py#RM-23`
  - `tests/test_ep08_destinatarios_entorno.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EP-08`: pytest tests/test_ep08_destinatarios_entorno.py tests/test_notificaciones.py + suite completa
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-205 · puesta-en-marcha-del-entorno-de-pruebas  (tanda 52)

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

### BL-206 · diagnostico-de-prueba-y-diagnostico-real  (tanda 23)

**Contexto.** Sala(s): `diagnostico, frontend`. Depende de: `DIAG-03`, `DIAG-08`, `ADPA-05`, `ADPA-06`, `ADPA-07`. Especificaciones: `governance/tareas/DIAG-11.md`, `PRD_EVYDENTIA_REVENTA_NUBE.md` Módulo 1 e invariantes 58 y 59 de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`.

**Objetivo** (en este orden):

1. `DIAG-11` — Diagnóstico de prueba y diagnóstico real: el diagnóstico se sella dos veces como máximo y el real es la línea base

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤diagnostico`: registrado en `VPA_MAP.md`.
- `¤dpo-independencia`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `alembic/versions/20261106_diagnostico_prueba_y_real.py`
  - `features/diagnostico/services/resultados_engine.py`
  - `features/diagnostico/diagnostico_service.py#DIAG-11`
  - `api/routers/diagnostico_resultados.py#DIAG-11`
  - `app_core/pasillo/diagnostico.py#DIAG-11`
  - `features/diagnostico/domain/errores.py#DIAG-11`
  - `tests/test_diag11_prueba_y_real.py`
  - `frontend/src/components/DiagnosticCanvas.tsx#DIAG-11`
  - `frontend/tests/diagnostico/prueba-y-real.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas, claves ni correos reales.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DIAG-11`: pytest tests/test_diag11_prueba_y_real.py tests/test_diagnostico_resultados.py contra una base de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico/prueba-y-real.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-207 · estados-el-assessment-actual  (tanda 25)

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

### BL-214 · secretos-obligatorios-en-la-nube  (tanda 21)

**Contexto.** Sala(s): `pasillo_central`, `biblioteca`. Depende de: `SEC-15` (tanda 20), `FIRMA-06`, `BIB-104`, `SEC-06`, `RM-13` (hechas). Especificaciones: `governance/tareas/SEC-16.md` e `INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD`.

**Objetivo** (en este orden):

1. `SEC-16` — Secretos obligatorios en la nube: el backend no arranca con JWT_SECRET o SESSION_SECRET por defecto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/config.py#SEC-16`
  - `api/index.py`
  - `features/biblioteca/services/archivos.py#SEC-16`
  - `tests/test_sec16_secretos_obligatorios.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas secretos, URL de conexión, contraseñas ni correos reales; en las pruebas, solo valores generados.
- No cargues variables en Vercel ni en Google Cloud: lo hacen las personas.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-16`: pytest tests/test_sec16_secretos_obligatorios.py + suite completa + vigilantes; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-215 · configuracion-minima-en-la-nube  (tanda 22)

**Contexto.** Sala(s): `pasillo_central`. Depende de: `SEC-15` (tanda 20), `SEC-16` (tanda 21), `FIRMA-06`, `SEC-06`, `RM-13` (hechas). Especificaciones: `governance/tareas/SEC-17.md` e `INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED`.

**Objetivo** (en este orden):

1. `SEC-17` — Configuración mínima en la nube: DATABASE_URL de PostgreSQL con lopdp_app y CORS_ORIGINS explícito, sin valores por defecto

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤rbac-tenant`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/config.py#SEC-17`
  - `api/index.py`
  - `tests/test_sec17_configuracion_nube.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas URL de conexión, contraseñas ni dominios reales de clientes; en las pruebas, solo valores ficticios.
- No cargues variables en Vercel ni en Google Cloud: lo hacen las personas.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `SEC-17`: pytest tests/test_sec17_configuracion_nube.py + suite completa + vigilantes; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-216 · operador-sin-organizacion  (tanda 20)

**Contexto.** Sala(s): `plataforma`. Depende de: `ORG-09`, `ORG-11`, `FE-07`, `FE-10`, `FE-20`, `FE-21`, `BIB-115` (hechas). Especificaciones: `governance/tareas/ORG-21.md`.

**Objetivo** (en este orden):

1. `ORG-21` — El operador de la plataforma entra aunque no pertenezca a ninguna organización

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤rbac-tenant`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/app/login/page.tsx#ORG-21`
  - `frontend/src/lib/plataforma/cliente.ts#ORG-21`
  - `frontend/src/lib/auth/sesion.ts#ORG-21`
  - `frontend/src/lib/auth/cabeceras.ts#ORG-21`
  - `frontend/tests/auth/organizaciones.spec.ts#ORG-21`
  - `frontend/tests/auth/operador-sin-organizacion-activa.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No cambies el backend: la autoridad es `verificar_operador`.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No escribas correos reales ni tokens reales; en las pruebas, solo valores simulados.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `ORG-21`: Playwright frontend/tests/auth/operador-sin-organizacion-activa.spec.ts en un proyecto del CI + tsc --noEmit + vigilantes; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-217 · demo-modo-seguro  (tanda 53)

**Contexto.** Sala(s): `demo`, `pasillo_central`. Depende de: `SEC-03`, `SEC-07`, `SEC-15`, `ENT-02`, `RM-00`, `NOTIF-01` (hechas). Especificaciones: `governance/tareas/DEMO-01.md`, `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`, `governance/apoyo/UX_DEMO_COMERCIAL.md`.

**Objetivo** (en este orden):

1. `DEMO-01` — Modo demo seguro: barrera contra producción, vendedores autorizados y persona decidida por el servidor

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤demo`: registrado en `VPA_MAP.md`.
- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/demo/__init__.py`
  - `features/demo/demo_service.py#DEMO-01`
  - `features/demo/domain/`
  - `features/demo/services/identidad_engine.py`
  - `features/demo/services/vendedores_engine.py`
  - `app_core/security.py#DEMO-01`
  - `main.py#DEMO-01`
  - `api/routers/demo.py`
  - `features/notificaciones/notificaciones_service.py#DEMO-01`
  - `alembic/versions/20261121_demo_sesiones.py`
  - `tests/demo/test_demo_modo_seguro.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS: la demo los respeta tal cual.
- Nunca uses la base de producción ni el `.env` de la carpeta principal: solo tu rama Neon de prueba.
- No edites archivos de gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No escribas correos reales ni tokens reales; en las pruebas, solo valores simulados y dominios `.invalid`.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-01`: pytest tests/demo/test_demo_modo_seguro.py + suite de seguridad y RLS existente en verde + linter ADPA sin cruces; pruebas de mutación documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-218 · demo-plantilla  (tanda 54)

**Contexto.** Sala(s): `demo`. Depende de: `DEMO-01` (tanda anterior). Especificaciones: `governance/tareas/DEMO-03.md`, `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`, `governance/apoyo/UX_DEMO_COMERCIAL.md`.

**Objetivo** (en este orden):

1. `DEMO-03` — Plantilla de datos «Cooperativa Demo» con cuatro personas ficticias

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤demo`: registrado en `VPA_MAP.md`.
- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `data/demo/cooperativa_demo.json`
  - `scripts/demo/sembrar_plantilla_demo.py`
  - `tests/demo/test_plantilla_demo.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS: la demo los respeta tal cual.
- Nunca uses la base de producción ni el `.env` de la carpeta principal: solo tu rama Neon de prueba.
- No edites archivos de gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No escribas correos reales ni tokens reales; en las pruebas, solo valores simulados y dominios `.invalid`.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-03`: pytest tests/demo/test_plantilla_demo.py contra una rama Neon de prueba: la plantilla se siembra dos veces sin duplicar y cumple la segregación
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-219 · demo-organizacion-por-sesion  (tanda 55)

**Contexto.** Sala(s): `demo`, `organizacion`. Depende de: `SEC-10` (hechas); `DEMO-01`, `DEMO-03` (tandas anteriores). Especificaciones: `governance/tareas/DEMO-02.md`, `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`, `governance/apoyo/UX_DEMO_COMERCIAL.md`.

**Objetivo** (en este orden):

1. `DEMO-02` — Una organización demo por sesión: copia de la plantilla, vencimiento lógico y purga nocturna

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤demo`: registrado en `VPA_MAP.md`.
- `¤rbac-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `features/demo/demo_service.py#DEMO-02`
  - `features/demo/services/sesiones_engine.py`
  - `api/routers/demo_sesiones.py`
  - `features/organizacion/organizacion_service.py#DEMO-02`
  - `features/organizacion/services/plantilla_engine.py`
  - `scripts/demo/purgar_demos_vencidas.py`
  - `tests/demo/test_demo_sesiones.py`
  - `tests/demo/test_demo_purga.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS: la demo los respeta tal cual.
- Nunca uses la base de producción ni el `.env` de la carpeta principal: solo tu rama Neon de prueba.
- No edites archivos de gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No escribas correos reales ni tokens reales; en las pruebas, solo valores simulados y dominios `.invalid`.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-02`: pytest tests/demo/test_demo_sesiones.py tests/demo/test_demo_purga.py contra una rama Neon de prueba + linter ADPA sin cruces; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

### BL-220 · demo-selector-y-franja  (tanda 53)

**Contexto.** Sala(s): `frontend`. Depende de: `FE-17`, `FE-19`, `FE-20`, `FE-21` (hechas); `ORG-21` (tanda anterior). Contrato de la API en `FLUJOS_DEMO_COMERCIAL.md` §3, con la API simulada. Especificaciones: `governance/tareas/DEMO-04.md`, `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`, `governance/apoyo/UX_DEMO_COMERCIAL.md`.

**Objetivo** (en este orden):

1. `DEMO-04` — Selector «Ver como», franja de demostración y «Terminar demo» en el frontend

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤demo`: registrado en `VPA_MAP.md`.
- `¤interfaz`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/src/lib/demo/`
  - `frontend/src/components/demo/`
  - `frontend/src/lib/auth/fetchAutenticado.ts#DEMO-04`
  - `frontend/src/components/layout/DashboardHeader.tsx#DEMO-04`
  - `frontend/src/app/login/page.tsx#DEMO-04`
  - `frontend/tests/demo/demo-activa.spec.ts`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- En archivos con secciones `#ID`, escribe solo dentro de tus marcas.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod` ni la RLS: la demo los respeta tal cual.
- Nunca uses la base de producción ni el `.env` de la carpeta principal: solo tu rama Neon de prueba.
- No edites archivos de gobernanza reservada (`.github/workflows/` incluido), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No escribas correos reales ni tokens reales; en las pruebas, solo valores simulados y dominios `.invalid`.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `DEMO-04`: Playwright frontend/tests/demo/demo-activa.spec.ts en el proyecto «desarrollo» del CI (CI-16) + tsc --noEmit + eslint; los 8 criterios de la ficha
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

## Sin agente (decisiones del propietario y trabajo por asignar)

- Infraestructura de la demo comercial (`DEMO-05`): rama Neon `demo`, proyectos Vercel de la demo, orígenes OAuth y el flujo nocturno de purga; la hace el responsable de operación cuando DEMO-02, DEMO-03 y DEMO-04 estén integradas.
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
- Optimización de los tiempos de prueba, pendiente de asignación de tanda por el propietario; siguen abiertas `CI-15` (residuo de una prueba de identidad) y `CI-14` (espera de turno de Neon, libre al cerrarse las tres tareas de las que dependía); las que comparten el flujo de CI van en serie.
- Conectar `scripts/verificar_bundle_frontend.py` (SEC-14) al workflow del CI tras `npm run build`, que es gobernanza reservada, y fijar los topes de gasto de IA (SEC-13) y de presupuesto (OPS-07).
- Entorno de pruebas de EVYDENTIA (`PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5): decidir el borde (sin balanceador con IAP en el frontend, o balanceador con Cloud Armor y CDN), Memorystore, el horario de Cloud SQL y la firma de pruebas con ANF; crear el proyecto de Google Cloud de pruebas y guardar la lista de quienes prueban en `herramientas\testers-entorno-pruebas.txt`, fuera del repositorio.
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

### Biblioteca repartida en tandas

Desde el 2026-10-28 las 24 tareas de Biblioteca y GOB-03 tienen bloque y tanda (serie «Biblioteca (PMV)» de la tabla), en el orden del PMV (`governance/tareas/BIB-100.md`): hasta cuatro por tanda, sin archivos enteros en común, con las dependencias en tandas anteriores. La serie de Biblioteca corre en paralelo a la de la estructura EVYDENTIA (otra persona), sin pisar archivos.

Refactor ADPA del 2026-11-02 (coordinador): cinco fichas nuevas (BIB-111, BIB-112, BIB-113, BIB-114 y RM-24), dependencias artificiales retiradas y archivos internos de otras salas devueltos a su sala; las tandas 32 a 41 de Biblioteca se reparten de nuevo. Detalle en `BIBLIOTECA_PLAN.md`, «Refactor ADPA del 2026-11-02».

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).
