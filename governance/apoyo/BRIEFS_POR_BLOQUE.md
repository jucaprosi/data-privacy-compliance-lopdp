# Briefs por bloque de trabajo — EVYDENTIA
`¤adpa` `¤roadmap` `¤arbitro`

> **Qué es:** reparto de las tasks abiertas de `governance/tareas/` en bloques que se pueden asignar a agentes distintos sin que se pisen. **Fuente única:** cada task vive en `governance/tareas/<ID>.md`; aquí solo se referencian IDs, nunca se copian. Si algo no cuadra, se corrige en la task y se regenera este reparto.
> **Comprobado** con `python scripts/verificar_reparto.py`, que la suite ejecuta en `tests/test_reparto.py`: R1 cada task no hecha figura en un solo bloque o tiene `agente = "ninguno"` en su ficha y ninguna hecha figura; R2 «Escribe» es exactamente la `propiedad` de las tasks del bloque; R3 ningún archivo lo escriben dos bloques de la misma tanda; R4 toda dependencia está hecha, va antes en su bloque o cae en una tanda anterior. Y con `python scripts/generar_indice_tareas.py --verificar`. Hasta el 2026-10-10 este documento declaraba esa comprobación y el verificador no existía en el repositorio. **No se implementó ninguna task.**

**Recuento (2026-10-28, reparto del propietario en tandas de hasta cuatro sin archivos enteros en común):** 51 tareas abiertas de 221; 170 hechas (BIB-100 cerrada el 2026-10-29, #220; BIB-109 cerrada el 2026-10-29, #223; RM-21 cerrada el 2026-10-29, #222; DIAG-08 cerrada el 2026-10-30, #235; RM-22 cerrada el 2026-10-31, #269; DIAG-09 cerrada el 2026-10-31, #273 y #279; BIB-101 cerrada el 2026-10-31, #236; REG-02 cerrada el 2026-10-31, #241; GOB-03 cerrada el 2026-10-31, #244; CAPA-02 cerrada el 2026-10-31, #284; RAT-05 cerrada el 2026-11-01, #288; RM-23 cerrada el 2026-11-01, #287; ORG-16 cerrada el 2026-11-01, #281 y #294 (pruebas de la alta corregidas el 2026-11-02, #299); RAT-06 cerrada el 2026-11-01, #295). Tanda 21 terminada: FE-22, FE-23 y RM-21 hechas. Escala SMARTCIDI 1-5 (decisión del propietario del 2026-10-29): DIAG-08 y DIAG-09 la implantan; FE-24 sale de la tanda 21 y espera a DIAG-08; EVI-01, vinculada al almacenamiento en Cloud Storage, pasa detrás de DIAG-09. tanda 22 (EVY): DIAG-08, DPO-02, SEC-12, CAPA-02; tanda 23 (EVY): FE-24, DIAG-09, ORG-16, RM-22; tanda 27 (EVY): EVI-01, DIAG-04, DIAG-06, ORG-15; tanda 28 (EVY): EVI-02, DIAG-05, ORG-17 (RAT-05 hecha); tanda 29 (EVY): CAPA-03, DIAG-07, RAT-07 (RAT-06 hecha); tanda 30 (EVY): ORG-18, INC-02, DER-01, DPO-03; tanda 31 (EVY): FOR-01, DER-02, MTGE-03, CAPA-04; tanda 32 (EVY): TER-01, REG-02, ORG-20; tanda 33 (EVY): TER-02, FE-25; tanda 34 (BIB): BIB-100, BIB-109, BIB-101, GOB-03; tanda 35 (BIB): BIB-201, BIB-102, BIB-110; tanda 36 (BIB): BIB-107, BIB-202; tanda 37 (EVY): FIRMA-02; tanda 38 (BIB): BIB-301, BIB-103, BIB-203, BIB-204; tanda 39 (BIB): BIB-401, BIB-104, BIB-205, BIB-302; tanda 40 (BIB): BIB-402, BIB-106, BIB-206, BIB-207; tanda 41 (BIB): BIB-208, BIB-303, BIB-304; tanda 42 (BIB): BIB-305, BIB-306; tanda 43 (BIB): BIB-307. En backlog, sin agente, por decisión del propietario: LEG-03 y REG-01.

## Preámbulo común (aplica a todos los bloques)

- Lee primero `governance/tareas/<ID>.md` de cada task de tu bloque (es la fuente de verdad), el PRD Módulo 5 (`governance/artefactos/PRD.md`, §7.1 catálogo de salas) y `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`.
- **Escribe solo en tu sala** y solo los archivos de la lista «Escribe» de tu bloque. Fuera de esa lista, no edites nada.
- **Cruza salas solo por compuertas** (`<sala>_service.py`): sin imports directos entre salas. Si tu sala no tiene compuerta, créala.
- **No edites** el índice generado de `governance/artefactos/TASKS.md` (lo produce `scripts/generar_indice_tareas.py --escribir`), `FUENTES_Y_BIBLIOGRAFIA.md` ni `APORTES_INEDITOS.md`. Los aportes los registra el coordinador.
- **Excepciones propias** (decisión del CTO, 2026-11-13): una ficha puede retirar, en su propio PR, las líneas `<SU-ID>|…` de `governance/tareas/_exenciones_propiedad.txt` que ese mismo PR resuelve al sembrar su marca. No puede añadir líneas ni tocar las de otra ficha. El árbitro es `generar_indice_tareas.py --verificar`.
- **Claves del auditor por sección** (decisión del CTO, 2026-11-13): cada ficha que añade acciones declara sus claves en su sección `tests/matriz/roles/auditor.py#<ID>`, con `_seccion("<ID>", {...})`. Una clave repetida rompe la carga (`tests/test_auditor_secciones.py`).
- **Archivos de gobernanza reservada** (`.github/workflows/`, `verificadores/`, `ejecutar_arnes_*.bat`, `AGENTS.md`, `.claude/`, hooks, `scripts/entorno.bat`, `governance/artefactos/data/`): no los edites. Si tu task lo exigiera, prepara el parche y su prueba y entrégalos en el informe; el propietario los aplica. Con este reparto ninguna task de agente los toca (comprobado contra la `propiedad` de cada task); solo GOB-01, que va en «Sin agente».
- **Propiedad, no git:** el aislamiento es que cada archivo tenga un solo dueño (la `propiedad` de su task). Un archivo que no es tuyo no lo modificas, ni lo reviertes ni lo «limpias»: si el árbol aparece sucio con archivos ajenos es lo esperado, ignóralos; si algo ajeno te impide avanzar, PARA y repórtalo. No hace falta prohibir comandos de git: basta con no tener nada que revertir fuera de lo propio. Un árbol de trabajo propio (`git worktree`) es una comodidad, no la frontera.
- **Pruebas mínimas pero decisivas:** una prueba que falle si el comportamiento falta; no añadas pruebas ni tasks para alcanzar un número. Cada prueba nueva debe matar una mutación que ninguna otra mata: la que pasa aunque la función devuelva siempre verdadero no cuenta. Lo que entregues debe estar **conectado** a un árbitro que se ejecute (un verificador que nadie invoca no cuenta como entregado). Las exenciones de un verificador son datos declarados con su motivo, nunca exclusiones por directorio dentro del código.
- **El estado documentado no supera al verificado:** lo que no comprobaste con la salida de un árbitro lo marcas «no verificado»; no escribas «verificado» ni «integrado» sin ella. No copies a un documento lo que ya dice la task: referencia su ID.
- **El avance se mide por el diff, no por el mensaje del commit.** El mensaje declara solo lo que el diff contiene. Antes de integrar una rama, el coordinador ejecuta `python scripts/verificar_reparto.py --rama <rama> --bloque <ID>` (R5: todo archivo del diff cabe en «Escribe»); si sobra uno, la rama no se integra.
- **El éxito lo decide un árbitro exógeno**, no tu opinión: el comando de «Hecho si» con código de salida 0. En Windows con Git Bash lanza el arnés con `cmd //c ".\ejecutar_arnes_tres_pilares.bat"` (o ruta absoluta) y acéptalo **solo** si la salida contiene `[ARNES] Los tres pilares pasaron exitosamente.` (`cmd /c` con una sola barra devuelve 0 sin ejecutar nada; ver Aporte 106). El intérprete lo resuelve `scripts\entorno.bat`; ver `governance/operaciones/ENTORNO_LOCAL.md`.
- **Rama y commit:** trabaja en una rama `tarea/<persona>/<id>` creada desde `origin/main`, al día con `main` y en el orden del bloque; cada task en sus propios commits con su id en el mensaje. El PR a `main` es el de esa persona, en la ventana nocturna (regla 10 de `governance/tareas/README.md`, que manda sobre este documento). Añade siempre los archivos por su ruta (`git add <archivo>`), nunca `git add -A` ni `git add .`. Antes de cada commit comprueba la rama con `git branch --show-current`. No empujes ni abras PR sin que el coordinador lo pida.
- **Secciones `#ID` de una compuerta compartida** (`organizacion_service.py`, `diagnostico_service.py`, `roadmap_service.py`…): añade tu sección **al final del archivo**, en el orden de su id, y no toques ninguna línea fuera de tus marcas `=== <ID> ===` … `=== fin <ID> ===`. Así dos fusiones de la misma noche no chocan en líneas vecinas.
- **Backend primero dentro de la ficha (decisión del propietario, 2026-11-07):** las fichas que llevan backend y frontend no se parten. El ingeniero termina primero la API con sus pruebas pytest en verde y después hace la pantalla con sus pruebas de Playwright, todo en el mismo PR. **Orden de lanzamiento dentro de cada tanda:** primero las fichas solo de backend, después las mixtas y al final las solo de frontend, siempre que las dependencias y R3 lo permitan. El Tech Lead aplica ese orden al armar la frase «Lanza la tanda». **Orden de etapas:** antes de las salas van GCP-01, SEC-16 y CI-17; después, la Etapa I (salas) en su orden; al final, la Etapa II (Google Cloud GCP-03…07, el entorno de pruebas EP-03…09 y la demo).
- **Migraciones y rama al día (desde 2026-11-07, `main` no exige la rama al día):** si tu task crea una migración, la cuelga de la rama de su sala según `governance/operaciones/FUSION_ALEMBIC.md` y corre `pytest tests/test_alembic_cabeza_por_sala.py` (una cabeza por sala); solo si otra task de la misma sala dejó dos cabezas en esa rama, añade en tu propio PR una migración de fusión de la sala, y lo avisa en el PR. Esa task sí usa «Update branch» si su PR quedó atrás. Una task sin migración se fusiona sin actualizar la rama. Si falla el push a `main`, se corrige con un PR inmediato y se detienen las fusiones hasta que pase.
- **Rastros `¤`:** búscalos con `git grep --untracked -F "<rastro>"` antes de buscar en lenguaje natural. No inventes rastros; si el de tu bloque no existe, tu primera task crea `¦tag` y lo indexa.
- **Los tokens `¤` no van en la interfaz de usuario** (solo en metadatos y código de gobernanza).

### Informe final (formato fijo)

```
BLOQUE: <ID> <nombre>
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

Archivo que solo edita un bloque por diseño: `main.py`.

## Tandas de lanzamiento

La tanda de cada bloque va en la cabecera de su brief (`### <ID> · título (tanda N)`); `python scripts/verificar_reparto.py --tandas` imprime la vista de tandas, calculada al leer (CI-31). Lanza una tanda cuando la anterior esté **integrada en `main`**. Dentro de una tanda los bloques son independientes.

## Briefs

Los bloques de cada ficha viven en `governance/apoyo/briefs/<ID>.md`, uno por archivo (CI-29); `ID` es la primera ficha del «Objetivo» del bloque. Esta portada no lleva bloques.

## Decisiones del propietario (ningún árbitro lo lee)

- IA-03b (con bloque en la tanda 65) (evidencia de humo de la compuerta de inferencia con Vertex real; la corre el propietario, `governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md`; hija de IA-03, cierre del CTO 2026-11-13).
- Revisar variables y secretos en Cloud Run y Secret Manager (OPS-01); medir una generación completa dentro de 300 s (OPS-02).
- Definir proveedor corporativo de correo cuando se habilite (NOTIF-01).
- Preparar la base local de pruebas por agente de desarrollo (OPS-04).
- Aplicar la protección de `main` que decida (CI-01) y cualquier parche a archivos de gobernanza reservada que un bloque entregue.
- Aprobar los bocetos de firma electrónica y notificaciones.
- Decidir el antivirus de la evidencia, tras leer el boceto (SEC-05), y pasar la CSP de modo informe a modo obligatorio cuando haya observado los informes (SEC-06).
- Crear el cliente OAuth de Google, registrar sus orígenes y cargar NEXT_PUBLIC_GOOGLE_CLIENT_ID (FE-07).
- Aplicar el job de Playwright al workflow del CI, que es de gobernanza reservada (TEST-02).
- Antes de aplicar la migración de ORG-00, volver a medir cuántas personas tienen el rol `encargado` en producción (el 2026-10-18 eran 0); si hubiera alguna, se aplica en un momento sin uso.
- Las decisiones de diseño de ORG-01, ORG-02, ORG-06 y ORG-07 se asumieron con su base legal (véase «Decisiones asumidas» de cada especificación) y se revisan si la Superintendencia emite normativa adicional, que la propia norma prevé.
- Los plazos (notificación de vulneraciones, inscripción del delegado, vigencia de las excepciones) quedan aplazados por decisión del propietario.
- Verificar con el texto oficial los artículos y plazos marcados (*) en el PRD y fijar la fuente única de citas legales: LEG-03 hecha (#499), borrador que el propietario aprueba con su abogado.
- Derechos: DER-04 (con bloque en la tanda 64) (contracción de la migración de DER-03; espera a DER-03; diseño del Arquitecto hecho; el despliegue lo autoriza el propietario).
- Derechos: DER-05, DER-07, DER-06a y DER-06b van en las tandas 29, 31, 33 y 34, con DER-01 en la 35 y DER-02 en la 36 (decisión del CTO, 2026-11-09: la corrección legal visible en la demo va primero).
- Estructura funcional EVYDENTIA en backlog, hasta que el propietario la lance: REG-01 (con bloque en la tanda 65) (paquete normativo como dato, con plazos como parámetros; espera a LEG-03).
- Optimización de los tiempos de prueba, pendiente de asignación de tanda por el propietario; CI-15 hecha (#504) y CI-17 hecha (#453 y #455; corrida verde 42422811800); CI-18 hecha (#525); las que comparten el flujo de CI van en serie.
- Conectar `scripts/verificar_bundle_frontend.py` (SEC-14) al workflow del CI tras `npm run build`, que es gobernanza reservada, y fijar los topes de gasto de IA (SEC-13) y de presupuesto (OPS-07).
- Entorno de pruebas de EVYDENTIA (`PRD.md` §5.5): decidir el borde (sin balanceador con IAP en el frontend, o balanceador con Cloud Armor y CDN), Memorystore, el horario de Cloud SQL y la firma de pruebas con ANF; crear el proyecto de Google Cloud de pruebas y guardar la lista de quienes prueban en `herramientas\testers-entorno-pruebas.txt`, fuera del repositorio.
- Diagnóstico: DIAG-16 (con bloque en la tanda 64) (citas normativas del banco contrastadas con el texto oficial; corrige la cita falsa de P73; prioridad alta, aprobada por el CTO; la base legal la confirma el abogado del propietario).
- Integrar cada tanda en `main`, registrar aportes y cerrar la sesión (`mcp_close_session`).

### Biblioteca repartida en tandas

Desde el 2026-10-28 las 24 tareas de Biblioteca y GOB-03 tienen bloque y tanda (serie «Biblioteca (PMV)» de la tabla), en el orden del PMV (`governance/tareas/BIB-100.md`): hasta cuatro por tanda, sin archivos enteros en común, con las dependencias en tandas anteriores. La serie de Biblioteca corre en paralelo a la de la estructura EVYDENTIA (otra persona), sin pisar archivos.

Refactor ADPA del 2026-11-02 (coordinador): cinco fichas nuevas (BIB-111, BIB-112, BIB-113, BIB-114 y RM-24), dependencias artificiales retiradas y archivos internos de otras salas devueltos a su sala; las tandas 32 a 41 de Biblioteca se reparten de nuevo. Detalle en `BIBLIOTECA_PLAN.md`, «Refactor ADPA del 2026-11-02».

## No verificado

- Que cada agente externo respete las listas «Escribe»: el árbitro es `python scripts/verificar_reparto.py --rama <rama> --bloque <ID>` (R5), pero **no está conectado** al arnés ni a la CI —eso exige tocar archivos de gobernanza reservada— y lo ejecuta el coordinador antes de integrar.
- El tiempo y el costo de cada bloque: no se estimaron.
- Los nombres de rama `feat/<id-de-la-task>` y el reparto de OPS-01, OPS-04 y CI-01 en un mismo bloque son convención de este documento, no una regla del repositorio.
- No existen en este repositorio un manifiesto de gobernanza vigilada ni un `preparar_parche_gobernanza.py`; la regla de «parche para el propietario» es por tanto documental. `tests/test_adpa_bulkhead.py` aún no existe (lo declara RM-01).

