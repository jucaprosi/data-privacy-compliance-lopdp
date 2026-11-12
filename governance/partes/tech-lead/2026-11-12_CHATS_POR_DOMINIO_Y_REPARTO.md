# Parte del Tech Lead: chats por dominio y reparto de fichas, 2026-11-12

Parte de relevo del chat del Tech Lead (tandas 27 a 29, la de fichas libres y el cierre de la tanda 30). Tema principal: organizar el trabajo en chats por dominio y fijar cómo se escriben, reparten y cierran las fichas sin romper los árbitros. Otros temas del chat: doble validación de la evidencia (RM-25), rol auditor (ORG-22), MARCA y PRD único, purga de la demo, balanceador de EVYDENTIA y partes por rol. Complementa a `2026-11-12_tech-lead.md` (ya en `main`, no se toca). Sin secretos; las fichas y los PR se citan por identificador. Si este parte y una ficha se contradicen, manda la ficha.

Estado al corte: `main` en `063a1c30` (PR #640). Fusionados #605 (MARCA y PRD), #609 (RM-25), #629 y #635 (BIB-110), #619, #621 y #639 (cierre de tanda). Abierto: #641 (parte del CTO). Fichas: 260 hechas, 12 en curso y 68 pendientes, de 340.

## Rol de quien escribe
- **Rol:** Tech Lead de EVYDENTIA, asignado por el propietario. Una sesión nueva de este rol empieza esperando el mensaje «Lanza la tanda: …» del propietario o el aviso del CTO; antes lee este parte y el de su carpeta.
- **Lugar en la cadena:** CTO → Arquitecto → UX/UI (si hay frontend) → **Tech Lead** → sesiones de ingeniería. Recibe el diseño ya aprobado y lo convierte en fichas y tandas.
- **Función:** escribe fichas (`governance/tareas/`), mantiene `BRIEFS_POR_BLOQUE.md` y `TASKS.md`, reparte en tandas, asigna los briefs a los chats de cada dominio y hace la primera revisión de cada PR de código.
- **Límites:** no fusiona PR (lo hace el CTO), no actúa en Google Cloud ni contra producción, no toca `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`, no usa el `.env` de la carpeta principal y no escribe código de producto; sus commits son de gobernanza, en una rama por tanda.
- **Entregas y escalado:** entrega fichas y briefs a las sesiones, una línea de estado al CTO por cada PR de gobernanza, y las dudas de diseño al Arquitecto. Lo legal va al abogado del propietario (marcado **ESTIMADO** mientras no responda). Todo en español.

## Lo decidido
**Chats por dominio (propuesta, pendiente del visto bueno del propietario)**
- Diez chats: `demo`, `nube`, `diagnostico`, `evidencias-roadmap`, `organizacion`, `derechos-y-cumplimiento`, `ia`, `biblioteca`, `modulos-nuevos` y `marca-y-gobernanza`. Frontend no tiene chat propio: sus 20 fichas pertenecen a un dominio. Una ficha que cruza dominios va al dueño de su primer archivo. `modulos-nuevos` y `marca-y-gobernanza` se crean cuando haya tanda para ellos. Reparto de fichas en «Lo que falta».
- Archivados el 2026-11-12: «demo · DEMO-03e» y «pruebas · CI-23». Siguen los que llevan fichas pendientes (ORG-22, DIAG-07, DIAG-12, DER-06a, IA-07, ADPA-09).
- Cada brief va por `SendMessage` al chat de su dominio, que se renombra («dominio · ficha»); sesión nueva solo para trabajo independiente.

**Proceso de reparto**
- **Escribir una ficha:** `governance/tareas/<ID>.md` (TOML: `id`, `titulo`, `ola`, `estado`, `sala`, `depende_de`, `propiedad`, `crea`, `arbitro`, `rastros`) y su bloque en `BRIEFS_POR_BLOQUE.md`. Propiedad con archivos concretos. Cada rastro `¤` existe en `VPA_MAP.md`.
- **Marcas de sección:** `# === ID ===` … `# === fin ID ===` (`// ===` en TS) deben estar en `HEAD` antes de cambiar la ficha: primero un commit que siembra las marcas, luego el de las fichas y la exención.
- **Exenciones** (`_exenciones_propiedad.txt`): solo decrecen (CI-19); la dueña no las quita desde código (R5), las quita el Tech Lead en un PR de gobernanza.
- **Árbitros** (`scripts/verificar_reparto.py`): R1 cada ficha no hecha en un bloque o en «Sin agente», una hecha en ninguno; R2 «Escribe» igual a la propiedad; R3 sin archivos compartidos en una tanda; R4 dependencias hechas o en tanda anterior; R5 el diff cabe en «Escribe». Máximo cuatro bloques por tanda. `generar_indice_tareas.py --verificar` exige que dos dueñas del mismo archivo dependan una de otra.
- **Una migración por tanda** (`governance/operaciones/FUSION_ALEMBIC.md`); la simulación sobre `main` debe dar una sola cabeza (error de #611, arreglado en #616).
- **Playwright:** un spec con `fijarAjustes` o `window.__LOPDP_AUTH_PRUEBAS__` exige que la ficha asuma `frontend/playwright.config.ts` por PR de gobernanza y lo añada a `SOLO_DESARROLLO`, o que se llame `*-activa.spec.ts`. Falló en ORG-15, ORG-17, ORG-18 y BIB-110 (#594, #601, #607, #620, #629).
- **Un PR de gobernanza por tanda**; no abrir otro que toque `BRIEFS_POR_BLOQUE.md` o `TASKS.md` con dos abiertos. Al traer `main` chocan las filas de tandas: se conservan las dos partes y se busca que no queden filas duplicadas.
- **Cierre de tanda** (#625, #639): fichas a `hecha`, se retira su bloque y su referencia en la fila de la tanda, se quita su mención de «Sin agente» y se regeneran los índices.
- **MARCA-01 antes de RM-25a:** las dos poseen `main.py` (confirmado por el CTO). RM-25a sigue sin tanda y debe entrar después de la 25; la alternativa contraria falla R4.
- **Primera revisión de código:** lectura del PR frente a ficha, propiedad y reglas; no sustituye a las pruebas ni a la simulación del CTO. Revisados en lectura, sin ejecutar pruebas: #590, #591, #592, #600, #604, #606, #611, #613, #614, #618, #621, #623, #626, #630, #631, #632 y #635.

**Balanceador (CTO, 2026-11-12)**
- Se aceptó el reparto: la ampliación de SEC-21 (contar entradas de `X-Forwarded-For`, solo el número) y la ficha de GCP para `min-instances` y `timeoutSec` van por el Arquitecto; la corrección de `cloud_load_balancer.yaml` y del brief del balanceador va en el PR de gobernanza de la próxima tanda; el flag de ingress del paso 7 lo prepara el CTO como brief del propietario, sin ficha. No se abre `app.evydentia.com` a usuarios antes de fusionar SEC-21 y medir.

**Decisiones por ficha** (detalle en `2026-11-12_tech-lead.md`): doble validación de evidencia (RM-25a, RM-25b, RM-25c), rol auditor (ORG-22a y ORG-22), DIAG-07 partida, MARCA-01 a 06 y PRD-01 a 03, ORG-17b, CI-23, FE-25 con «No disponible» (**ESTIMADO**, sin cita legal verificada), DER-07 sin artículo ni cifra de plazo, DEMO-03e solo estructura y metadatos, purga de la demo (DEMO-05c y DEMO-05d).

## Lo que falta
- **Tanda de RM-25a** (tras MARCA-01) y **próxima tanda de fichas libres** (máximo cuatro bloques; MARCA-01 incluida si ya no choca). Responsable: Tech Lead. Cada ficha nueva pasa antes por el Arquitecto y, si toca frontend, por UX/UI.
- **Aprobación de los diez chats** y renombrado de los existentes. Responsable: Tech Lead, tras el visto bueno.
- **Fichas por escribir** (cada una por el Arquitecto): ampliación de SEC-21; GCP de `min-instances` y `timeoutSec`; organización (fila de cartera con `dpo_nombre` e `implementador_nombre`; va con FE-25); EVI-01c (retirar el repositorio en memoria, las rutas antiguas y la escala E0 a E3; `huella_registrada` a la base; probada contra la base de pruebas de EVYDENTIA); BIB-110b (editores a `marcarCambiosBiblioteca`); generador del manifiesto E2E de la biblioteca emitiendo `base_pruebas`, sin alias; subir el contrato como archivo (ORG-17 y ORG-18); DIAG-15 («Revisar Respuestas» tras el sello real, fecha en formato de EE. UU., simulador con 65 brechas fijas); DEMO-04b (pendiente de lanzar).
- **Rama `tarea/juan-carlos/ampliaciones-gcp05-der07`** (sin PR): propiedad de GCP-05, DER-07 (solo quitar seis filas de `CITAS_LEGALES_VERIFICADAS.md`), DEMO-05c, DEMO-05d, enmienda de DEMO-03e y ficha GCP-10. Se abre cuando no haya otro PR de gobernanza abierto.
- **Pendiente de revisión o respuesta:** PR de código de EVI-02, DEMO-01, FE-25 y SEC-21; estado de ADPA-09 (código empujado, sin PR confirmado); si DEMO-05 pasa a `hecha` para lanzar DEMO-05c y DEMO-05d.
- **Mensajes sin enviar** (la mensajería se pausa tras 20 envíos sin respuesta del usuario): FE-25 (opción (a); `plantillas-cuenta` es deuda de BIB-401; el spec `cambio-organizacion` es de BIB-110), EVI-02 (renombrar su spec a `vigencia-activa.spec.ts`), DEMO-02 (no tocar `jobs/purga_demo`), GCP-02 (pregunta al Arquitecto sobre capas), y avisar a Arquitecto y UX/UI del nuevo formato de partes.
- **Informes de los sub chats:** este parte no incorpora sus informes completos, solo los avisos recibidos; antes de la próxima tanda conviene leer el último informe de cada chat vivo.
- **Reparto propuesto de fichas pendientes por chat:**
  - `demo`: DEMO-01, DEMO-04b, DEMO-03f, DEMO-05b, DEMO-05c, DEMO-05d.
  - `nube`: DEMO-05, DEMO-07, GCP-05, GCP-06, GCP-10, EP-07, EP-09, SEC-21.
  - `diagnostico`: DIAG-07a, DIAG-07b, DIAG-07, DIAG-15, ORG-23.
  - `evidencias-roadmap`: EVI-02, EVI-01c, RM-25a, RM-25b, RM-25c, IA-06, CAPA-03, CAPA-04, DPO-03.
  - `organizacion`: ORG-22a, ORG-22, ORG-20, FE-25, PLAT-01.
  - `derechos-y-cumplimiento`: DER-01, DER-02, DER-04, DER-06b, DER-07, INC-02, RAT-07, TER-01, TER-02, MTGE-03, FIRMA-02, FOR-01, ADPA-09.
  - `ia`: IA-03, IA-04, IA-05, IA-07, IA-08, IA-09, NORM-01, NORM-02, NORM-03, REG-01, VTX-01.
  - `biblioteca`: BIB-401, BIB-110b.
  - `modulos-nuevos`: BOV-01 a BOV-04, CCTV-01, CCTV-02, CON-01, DLP-01, GOCA-01, GOVW-01.
  - `marca-y-gobernanza`: MARCA-01 a MARCA-06, PRD-01 a PRD-03, CI-20, REP-01, fichas 01, 02 y 04 de la serie de retiro del proveedor remoto de pruebas, LEG-05, API-02.
- **Del Arquitecto y de UX/UI:** ver sus partes del 2026-11-12; DEMO-05c y DEMO-05d esperan que el CTO confirme la forma estrecha de las políticas.

## Lo que no se toca
- Producción, `.github/workflows/`, `verificadores/`, `AGENTS.md`, `.claude/`, secretos y el `.env` de la carpeta principal (apunta a producción): del propietario o del CTO. Google Cloud solo en lectura para la IA; los cambios van por brief.
- `BRIEFS_POR_BLOQUE.md` y `TASKS.md`: solo el Tech Lead. Un PR fusionado no recibe commits; la corrección va en un PR nuevo desde `main`. Un parte ya en `main` no se edita.
- Archivos con dueña viva: la propiedad se amplía por PR de gobernanza, no a mano. `app_core/db/session.py` fuera de la sección de GCP-05.
- El nombre del proveedor retirado y los identificadores de sus fichas, fuera de `governance/tareas/` (lo vigila su guardia de pruebas).
- Las pruebas no importan `yaml`: usan `tests/_lector_yaml.py`. SQL con parámetros ligados. Valores simulados y correos `.invalid`. Nunca `AUTH_MODE=headers`.
- Las citas legales no verificadas no entran en `CITAS_LEGALES_VERIFICADAS.md`.
- La inmutabilidad de la biblioteca y la RLS no se relajan; DEMO-05d solo actúa en la base de la demo. El auditor mantiene su segregación de funciones hasta ORG-22.
- Se comprueba la rama antes de cada commit; los PR de gobernanza no se mezclan con código.

## Pendientes del usuario
**Decidir o aportar**
1. Visto bueno a los diez chats por dominio y a cuáles de los existentes se archivan.
2. Preguntas al abogado: días hábiles frente a corridos y el «Art. 62, diez días» (DER-07), nombre del DPO e implementador visible a los miembros (FE-25, **ESTIMADO**), Vertex en us-central1, retención frente a supresión.
3. Fijar con diagnóstico qué significan «alto», «parcial» y «bajo» en el respaldo con documentos (ORG-15).
4. Decidir si se abre una ficha de rediseño visual (UX/UI la tiene sin ficha).

**Ejecutar solo él**
1. Briefs de Google Cloud con Antigravity, un bloque por vez (`governance/operaciones/BRIEF_PROPIETARIO_GOOGLE_CLOUD_2026-11-11.md`): secreto `INVENTARIO_CLAVE_CIFRADO` antes de cualquier despliegue, bucket de evidencias, bucket de la demo y Job de purga, brief de DEMO-05 y el SQL de DEMO-05c y DEMO-05d cuando lleguen, `max_connections` de la base para GCP-05 (solo lectura), y el paso 7 del balanceador (ingress del backend) con el brief que prepara el CTO.
2. `.github/workflows/`: en CI-23, `--destino "${{ github.base_ref }}"` y `--estricto-sin-ficha`; y el flag de ingress en `deploy-gcp.yml` junto con el paso 7.
3. Sustituir el generador del manifiesto E2E de la biblioteca antes de la aceptación real, cuando exista su ficha.
4. Lecturas de producción de solo lectura que pidan las fichas (solicitudes ARCO huérfanas, estructura de `terceros_encargados`, alertas de Cloud Logging con nombres de la marca anterior).
5. Su carpeta, tras fusionar el PR de partes: borrar la copia local de este parte y hacer `git pull --ff-only`.
