# Brief de Lanzamiento: Tanda de Tareas Ortogonales (Paralelo)
`¤adpa` `¤arbitro` `¤roadmap`

> **Objetivo:** Ejecutar concurrentemente 14 tareas 100% ortogonales sin riesgo de colisión en Git ni cruces de mamparos ADPA.
> **Fuente de Verdad:** Cada tarea reside en `governance/tareas/<ID>.md`. Cada agente debe operar confinado exclusivamente en los archivos de su lista `propiedad`.
>
> **Briefs (GOB-06):** el brief de cada ficha no está en el repositorio: vive en la carpeta local `C:\Users\Juan Carlos\compartido\evydentia\`, en `briefs\<ID>.md` (la versión más alta, `<ID>.v2.md`, si la hay). Antes de lanzar una tanda, `python scripts/verificar_briefs_locales.py --tanda N` comprueba que cada brief coincide con su ficha.

## Matriz de Independencia y Concurrencia

| Tarea | Sala | Dependencias | Árbitro Principal |
| :--- | :--- | :--- | :--- |
| **`CI-26`** | `gobernanza` | CI-25, REP-01, CI-19, CI-23, PRD-01, PRD-03, BIB-100, CI-22, GOB-04, BIB-106, BIB-110, BIB-118, BIB-119, BIB-401, CI-04, CI-16, ORG-15, ORG-17, ORG-18, TEST-03, ORG-20, CI-29, CI-30, CI-31 | `pytest tests/test_verificar_alcance_pr.py tes...` |
| **`PLAT-01`** | `plataforma` | EP-03, ORG-11, ORG-20 | `pytest tests/test_plat01_organizacion_sinteti...` |
| **`IA-06`** | `roadmap` | ADPA-04, IA-03, IA-10, RM-12, RM-19, RM-26, RET-03, RET-05, RET-04 | `pytest tests/test_ia06_roadmap_inferencia.py ...` |
| **`NORM-02b`** | `inteligencia_normativa` | NORM-02 | `pytest tests/test_norm02b_avisos_organizacion...` |
| **`BOV-03`** | `boveda_cloud` | BOV-02 | `pytest tests/test_bov03_forensic_preview.py +...` |
| **`GOCA-01`** | `go_cctv_agent` | CCTV-01, BOV-02 | `pytest tests/test_goca01_cctv_edge_agent_cont...` |
| **`GOVW-01`** | `go_vault_worker` | GCP-01, BOV-01, CON-01, ADPA-09 | `pytest tests/test_govw01_vault_worker_contrac...` |
| **`QA-09`** | `pruebas` | RET-00, RET-01, RET-06, ADPA-12, CI-21, GCP-05 | `suite completa en el CI; mutación documentada...` |
| **`QA-10`** | `biblioteca` | RET-00, RET-01, RET-06 | `suite completa en el CI; mutación documentada...` |
| **`QA-13`** | `pruebas` | RET-00, RET-01, RET-06, ORG-22, RET-02, SEC-24, DEMO-03d, DEMO-08, DER-06b, DER-07, DIAG-16, IA-07, RET-04 | `suite completa en el CI; mutación documentada...` |
| **`DEMO-05b`** | `operaciones` | DEMO-05 | `pytest tests/test_demo_purga_usuarios.py test...` |
| **`INC-03f`** | `frontend` | INC-03, FE-17, INC-01, INC-04 | `Playwright frontend/tests/incidentes/estado.s...` |
| **`DIAG-15`** | `frontend` | DIAG-07, DIAG-11, DIAG-14, EVI-01, EVI-01b, FE-27, FE-28 | `npx playwright test frontend/tests/textos/sin...` |
| **`MARCA-04`** | `frontend` | DIAG-07, BIB-118, FE-28, DER-07 | `Playwright frontend/tests/marca/marca.spec.ts...` |

## Reglas de Concurrencia y Aislamiento
1. **Rama propia:** Cada tarea se desarrolla en una rama `tarea/<persona>/<id>` creada desde `origin/main` al día.
2. **Propiedad Estricta:** Ningún agente puede tocar archivos fuera de la lista `Escribe (lista exclusiva)` de su ficha.
3. **Base de Datos de Pruebas:** Tareas con persistencia local deben usar variables aisladas (e.g. `TEST_DATABASE_URL` propia o sqlite en memoria donde aplique).
4. **Cierre:** Un PR por tarea. La tarea pasa a `hecha` únicamente en el PR de cierre del coordinador.

## Fichas de Tarea Detalladas

### CI-26 · Rutas con tilde en los árbitros de alcance y de reparto: lector común de git diff

- **Ficha:** [`governance/tareas/CI-26.md`](../tareas/CI-26.md)
- **Sala:** `gobernanza`
- **Rama recomendada:** `tarea/juan-carlos/ci-26`
- **Árbitro:** `pytest tests/test_verificar_alcance_pr.py tests/test_reparto.py + python scripts/verificar_reparto.py + python scripts/generar_indice_tareas.py --verificar; mutaciones m1 a m3`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `scripts/_git_diff.py`
  - `scripts/verificar_alcance_pr.py`
  - `scripts/verificar_reparto.py`
  - `tests/test_verificar_alcance_pr.py`
  - `tests/test_reparto.py`
  - `frontend/playwright.config.ts`
  - `tests/test_ci16_pruebas_sin_proyecto.py`
- **Resumen de Entrega:**
  - Lector común `scripts/_git_diff.py` (especificación R1 y §2), usado por los dos árbitros (R2).
  - Pruebas m1 a m3 en un repositorio temporal (R4 y §5).
  - `frontend/playwright.config.ts` y `tests/test_ci16_pruebas_sin_proyecto.py` quedan con esta ficha como dueña y no cambian (R5).
  ## Límites

### PLAT-01 · Alta idempotente de organizaciones sintéticas en plataforma_service, sin invitación

- **Ficha:** [`governance/tareas/PLAT-01.md`](../tareas/PLAT-01.md)
- **Sala:** `plataforma`
- **Rama recomendada:** `tarea/juan-carlos/plat-01`
- **Árbitro:** `pytest tests/test_plat01_organizacion_sintetica.py tests/test_ep03_sembrar_entorno.py + suite completa; mutación documentada; revisión de Seguridad antes del reparto`
- **Rastros:** `¤seguridad-tenant`, `¤adpa`
- **Escribe (lista exclusiva):**
  - `features/plataforma/plataforma_service.py`
  - `features/plataforma/services/organizacion_sintetica_engine.py`
  - `scripts/datos_sinteticos/organizaciones.py`
  - `tests/test_plat01_organizacion_sintetica.py`
  - `tests/test_ep03_sembrar_entorno.py`
- **Resumen de Entrega:**
  - `asegurar_organizacion_sintetica(datos)` en `plataforma_service.py`, con la lógica en `services/organizacion_sintetica_engine.py`:
    - es idempotente: crea la organización o devuelve la existente;
    - no emite invitación ni correo;
    - solo se permite con `APP_ENV` en `pruebas` o `demo`; en cualquier otro entorno lanza un error.

### IA-06 · El cliente del roadmap sobre la compuerta de inferencia en Vertex AI

- **Ficha:** [`governance/tareas/IA-06.md`](../tareas/IA-06.md)
- **Sala:** `roadmap`
- **Rama recomendada:** `tarea/juan-carlos/ia-06`
- **Árbitro:** `pytest tests/test_ia06_roadmap_inferencia.py + suites existentes del roadmap; mutaciones`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `features/roadmap/ai/client.py`
  - `features/roadmap/ai/roadmap_prompts.py`
  - `features/roadmap/services/generacion_engine.py`
  - `features/roadmap/services/generacion_en_linea.py`
  - `tests/test_ia06_roadmap_inferencia.py`
- **Resumen de Entrega:**
  - `features/roadmap/ai/client.py` pasa a la compuerta con el modelo de generación del pasillo. Cambia el comportamiento de la generación del roadmap, así que lleva su propia revisión de calidad de salida; las pruebas del roadmap existentes siguen siendo árbitro.
  - `features/roadmap/ai/client.py`: invoca directamente `app_core/pasillo/inferencia.py` sobre Vertex AI.
  ## Dónde importa cada cosa
  Solo desde `app_core.pasillo.inferencia`.

### NORM-02b · Aviso a las organizaciones de resoluciones nuevas o modificadas

- **Ficha:** [`governance/tareas/NORM-02b.md`](../tareas/NORM-02b.md)
- **Sala:** `inteligencia_normativa`
- **Rama recomendada:** `tarea/juan-carlos/norm-02b`
- **Árbitro:** `pytest tests/test_norm02b_avisos_organizaciones.py contra un PostgreSQL 16 local en contenedor`
- **Rastros:** `¤inteligencia-normativa`, `¤vigilancia-spdp`
- **Escribe (lista exclusiva):**
  - `tests/test_norm02b_avisos_organizaciones.py`
- **Resumen de Entrega:**
  - Un puerto `DestinatariosNormativos` en una sección `#NORM-02b` de un pasillo de plataforma, que lista por organización el administrador y el DPO.
  - Aviso por la compuerta de notificaciones (NOTIF-01) cuando una corrida encuentra resoluciones nuevas o modificadas.
  - Prueba de que cada organización recibe un aviso y ninguna recibe datos de otra.
  **Propiedad por concretar:** el Arquitecto fija el pasillo y las secciones antes de repartirla. Hasta entonces, la ficha queda en «Sin agente».

### BOV-03 · Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM

- **Ficha:** [`governance/tareas/BOV-03.md`](../tareas/BOV-03.md)
- **Sala:** `boveda_cloud`
- **Rama recomendada:** `tarea/juan-carlos/bov-03`
- **Árbitro:** `pytest tests/test_bov03_forensic_preview.py + suite completa + vigilantes`
- **Rastros:** `¤boveda-cloud`, `¤evidencias`, `¤adpa`
- **Escribe (lista exclusiva):**
  - `features/boveda_cloud/services/forensic_preview_engine.py`
  - `features/boveda_cloud/boveda_cloud_service.py#BOV-03`
  - `features/boveda_cloud/domain/errores.py#BOV-03`
  - `app_core/pasillo/boveda_cloud.py#BOV-03`
  - `frontend/src/components/layout/pantallas/BOV-03.tsx`
  - `frontend/src/components/layout/pantallas/index.tsx#BOV-03`
  - `tests/test_bov03_forensic_preview.py`
- **Resumen de Entrega:**
  - Motor `features/boveda_cloud/services/forensic_preview_engine.py` que preserva inalterado el objeto original con su hash `sha256_original` para inspecciones de la SPDP y registra por separado la ruta del derivado optimizado (`preview_uri` en `.webp`, `.avif` o `.webm`) para carga instantánea en la UI.
  - Validador de integridad forense que rechaza con `BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA` (409) cualquier intento de sobrescribir el blob original con un archivo recomprimido.
  - Visor `frontend/src/components/layout/pantallas/BOV-03.tsx` que carga por defecto la vista previa ligera (`WebP`/`WebM`) y ofrece descarga verificada del original con comprobación `SHA-256`.

### GOCA-01 · Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS

- **Ficha:** [`governance/tareas/GOCA-01.md`](../tareas/GOCA-01.md)
- **Sala:** `go_cctv_agent`
- **Rama recomendada:** `tarea/juan-carlos/goca-01`
- **Árbitro:** `pytest tests/test_goca01_cctv_edge_agent_contract.py + suite completa + vigilantes`
- **Rastros:** `¤motor-go-hibrido`, `¤videovigilancia-cctv`, `¤boveda-cloud`
- **Escribe (lista exclusiva):**
  - `services_go/cctv_agent/go.mod`
  - `services_go/cctv_agent/main.go`
  - `services_go/cctv_agent/cctv_agent_service.go`
  - `services_go/cctv_agent/config_schema.json`
  - `app_core/pasillo/go_cctv_agent.py#GOCA-01`
  - `app_core/pasillo/videovigilancia.py#GOCA-01`
  - `features/videovigilancia/services/cctv_provisioning_bundle.py`
  - `tests/test_goca01_cctv_edge_agent_contract.py`
- **Resumen de Entrega:**
  - Agente local multiplataforma en Go (`services_go/cctv_agent/`) compilable a binario único de ~10 MB sin dependencias externas, que toma los segmentos de movimiento del NVR local, verifica ausencia de pista de audio (`-an`), calcula el `SHA-256` en origen y sube el clip `.mp4` (H.265) directamente a Google Cloud Storage usando la `Signed URL V4` emitida para el `tenant_id`.
  - Generador de paquete de aprovisionamiento `features/videovigilancia/services/cctv_provisioning_bundle.py` y pasillo `app_core/pasillo/go_cctv_agent.py#GOCA-01`.

### GOVW-01 · Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run

- **Ficha:** [`governance/tareas/GOVW-01.md`](../tareas/GOVW-01.md)
- **Sala:** `go_vault_worker`
- **Rama recomendada:** `tarea/juan-carlos/govw-01`
- **Árbitro:** `pytest tests/test_govw01_vault_worker_contract.py + suite completa + vigilantes`
- **Rastros:** `¤motor-go-hibrido`, `¤boveda-cloud`, `¤conservacion`
- **Escribe (lista exclusiva):**
  - `services_go/vault_worker/go.mod`
  - `services_go/vault_worker/main.go`
  - `services_go/vault_worker/vault_worker_service.go`
  - `services_go/vault_worker/Dockerfile`
  - `app_core/pasillo/go_vault_worker.py#GOVW-01`
  - `app_core/pasillo/conservacion.py#GOVW-01`
  - `tests/test_govw01_vault_worker_contract.py`
- **Resumen de Entrega:**
  - Microservicio compilado en Go (`services_go/vault_worker/`) con `Dockerfile` multi-stage `distroless` (< 25 MB, Cold Start < 50 ms, `min-instances=0`) que recibe webhooks CloudEvents de *Eventarc* al finalizar subidas en Google Cloud Storage, calcula el hash `SHA-256` en streaming de memoria constante O(1) y ejecuta lotes de purga física.
  - Contrato de pasillo en `app_core/pasillo/go_vault_worker.py#GOVW-01` y `app_core/pasillo/conservacion.py#GOVW-01` con verificación de firma HMAC entre el satélite Go y el Core Python.

### QA-09 · Parametrizaciones de tabla y comprobaciones de rol repetidas

- **Ficha:** [`governance/tareas/QA-09.md`](../tareas/QA-09.md)
- **Sala:** `pruebas`
- **Rama recomendada:** `tarea/juan-carlos/qa-09`
- **Árbitro:** `suite completa en el CI; mutación documentada por cada tabla recorrida (una celda rota hace fallar la prueba y el mensaje la nombra) y por cada comprobación de rol retirada (la celda de la matriz falla); conteo de casos recogidos antes y después en el PR`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `tests/test_adpa05_secciones_y_errores.py`
  - `tests/test_adpa06_pasillos_secciones.py`
  - `tests/test_adpa07_secciones_frontend.py`
  - `tests/test_adpa_bulkhead.py`
  - `tests/test_pasillo_central.py`
  - `tests/test_ci21_sin_import_yaml.py`
  - `tests/test_roadmaps_api.py`
  - `tests/test_roadmap_generacion_en_linea.py`
  - `tests/test_organizacion_api.py`
  - `tests/test_organizacion_configuracion.py`

### QA-10 · Biblioteca sin pruebas de parche

- **Ficha:** [`governance/tareas/QA-10.md`](../tareas/QA-10.md)
- **Sala:** `biblioteca`
- **Rama recomendada:** `tarea/juan-carlos/qa-10`
- **Árbitro:** `suite completa en el CI; mutación documentada por cada prueba textual borrada que protegía una regla viva (QA-09 R2); pruebas nuevas de las filas «NINGUNA» presentes`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `tests/test_bib115_identidad_biblioteca.py`
  - `tests/test_bib117_capacidades.py`
  - `tests/test_bib_101_acceso.py`
  - `tests/test_bib_104_descarga.py`
  - `tests/test_bib_106_externos.py`
  - `tests/test_bib_107_documentos.py`
  - `tests/test_bib_109_plantillas_md.py`
  - `tests/test_bib_201_formularios.py`
  - `tests/test_bib_202_procedencia.py`
  - `tests/test_bib_205_generacion.py`
  - `tests/test_bib_207_concurrencia.py`
  - `tests/test_bib_302_enlaces.py`
  - `tests/test_bib_303_evidencia.py`
  - `tests/test_bib_304_impacto.py`
  - `tests/test_bib_305_indicadores.py`
  - `tests/test_bib_306_conservacion.py`
  - `tests/test_bib_402_vinculos.py`
  - `tests/test_bib_estado_revision.py`
  - `frontend/tests/biblioteca/**`

### QA-13 · Dominio sin pruebas de parche

- **Ficha:** [`governance/tareas/QA-13.md`](../tareas/QA-13.md)
- **Sala:** `pruebas`
- **Rama recomendada:** `tarea/juan-carlos/qa-13`
- **Árbitro:** `suite completa en el CI; mutación documentada por cada prueba textual borrada que protegía una regla viva (QA-09 R2); pruebas nuevas de las filas «NINGUNA» presentes`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `tests/test_controles_periodicos.py`
  - `tests/test_demo_clon_biblioteca.py`
  - `tests/test_demo_contrato.py`
  - `tests/test_demo_gancho_identidad.py`
  - `tests/test_demo_siembra.py`
  - `tests/test_der03_tenant_solicitud.py`
  - `tests/test_der04_contraccion.py`
  - `tests/test_der05_plazos.py`
  - `tests/test_der06b_tipos_activos.py`
  - `tests/test_der07_textos_legales.py`
  - `tests/test_diag16_referencias_normativas.py`
  - `tests/test_evidencia_validacion_servidor.py`
  - `tests/test_evidencias_rutas_estables.py`
  - `tests/test_fe28_textos_sin_jerga.py`
  - `tests/test_ia07_asistente_inferencia.py`
  - `tests/test_rol_coordinador.py`
  - `tests/test_sin_rat_paralelo.py`
  - `tests/test_sin_respaldos_inventados.py`
  - `tests/test_sin_rol_antiguo.py`
  - `frontend/tests/arco/**`
  - `tests/test_ret03_sin_cola.py`

### DEMO-05b · Purga de las personas ficticias de users

- **Ficha:** [`governance/tareas/DEMO-05b.md`](../tareas/DEMO-05b.md)
- **Sala:** `operaciones`
- **Rama recomendada:** `tarea/juan-carlos/demo-05b`
- **Árbitro:** `pytest tests/test_demo_purga_usuarios.py tests/test_demo_purga.py contra el PostgreSQL 16 del arnés; mutaciones documentadas`
- **Rastros:** `¤arbitro`
- **Escribe (lista exclusiva):**
  - `jobs/purga_demo/usuarios.py`
  - `jobs/purga_demo/purga.py`
  - `tests/test_demo_purga_usuarios.py`

### INC-03f · Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes

- **Ficha:** [`governance/tareas/INC-03f.md`](../tareas/INC-03f.md)
- **Sala:** `frontend`
- **Rama recomendada:** `tarea/juan-carlos/inc-03f`
- **Árbitro:** `Playwright frontend/tests/incidentes/estado.spec.ts + tsc --noEmit + npm run build; mutaciones m1 a m4`
- **Rastros:** `¤incidentes`, `¤rbac-tenant`
- **Escribe (lista exclusiva):**
  - `frontend/src/components/IncidentPlaybook.tsx`
  - `frontend/src/lib/incidentes/estado.ts`
  - `frontend/tests/incidentes/estado.spec.ts`
- **Resumen de Entrega:**
  - Insignia «Abierto» o «Cerrado», y «Cerrado, notificación pendiente» cuando `decision_notificacion = 'pendiente'`.
  - Botones Cerrar y Reabrir con un diálogo de motivo: mínimo 10 caracteres sin contar espacios; el botón de confirmar queda deshabilitado por debajo.
  - Si el servidor responde 409, se muestra su mensaje por código y se recarga el estado.
  - Los botones solo se ven con `ROLES_REGISTRO`; el DPO y el auditor solo ven la insignia.

### DIAG-15 · Textos sin jerga en DiagnosticCanvas (Poka-Yoke, timebox y etiqueta de la huella) y retiro de su excepción en FE-28

- **Ficha:** [`governance/tareas/DIAG-15.md`](../tareas/DIAG-15.md)
- **Sala:** `frontend`
- **Rama recomendada:** `tarea/juan-carlos/diag-15`
- **Árbitro:** `npx playwright test frontend/tests/textos/sin-jerga.spec.ts + pytest tests/test_fe28_textos_sin_jerga.py + suites del diagnóstico; la lista de excepciones baja`
- **Rastros:** `¤frontend-ide`, `¤arbitro`
- **Escribe (lista exclusiva):**
  - `frontend/src/components/DiagnosticCanvas.tsx`
  - `frontend/tests/textos/excepciones/DIAG-15.txt`
  - `frontend/tests/textos/sin-jerga.spec.ts`
- **Resumen de Entrega:**
  1. Los tres textos, con las redacciones de arriba (el `title` de la l.615 dice qué mide el temporizador, sin «Poka-Yoke»).
  2. Borra `frontend/tests/textos/excepciones/DIAG-15.txt`.
  ## No hagas
  - No cambies lógica del diagnóstico: solo textos.

### MARCA-04 · Nombre único EVYDENTIA en el frontend: paleta, reporte, página de la plataforma y configuración del proyecto

- **Ficha:** [`governance/tareas/MARCA-04.md`](../tareas/MARCA-04.md)
- **Sala:** `frontend`
- **Rama recomendada:** `tarea/juan-carlos/marca-04`
- **Árbitro:** `Playwright frontend/tests/marca/marca.spec.ts (la paleta muestra EVYDENTIA y no JUBYS) + tsc --noEmit + npm run build; antes, git grep de los specs que buscan esos textos (lección de FE-27); mutación documentada: JUBYS vuelve en CommandPalette.tsx y el spec falla`
- **Rastros:** `¤navegacion-menus`
- **Escribe (lista exclusiva):**
  - `frontend/src/components/CommandPalette.tsx`
  - `frontend/src/lib/reportes/generarReporteAssessment.ts`
  - `frontend/src/app/plataforma/page.tsx`
  - `frontend/src/components/ProjectConfig.tsx`
  - `frontend/src/types/index.ts`
  - `frontend/tests/marca/marca.spec.ts`
- **Resumen de Entrega:**
  - `CommandPalette.tsx` (líneas 210 y 742), `generarReporteAssessment.ts:124`, `plataforma/page.tsx:183-184` (valores de ejemplo «JUBYS Consultores»: se cambian por un ejemplo neutro), `ProjectConfig.tsx:257` (placeholder), `types/index.ts:2` (comentario).
  - Va **después de DIAG-07** (comparte `types/index.ts` y quizá specs). Mide antes las dueñas vivas de `CommandPalette.tsx` (DER-07 lo toma) y de los demás; las rutas con dueña viva van como sección `#MARCA-04` sembrada o la ficha depende de la dueña.
  - El comentario «dominio JUBYS G01-G16» de `dimensionesSGPDP.ts:113` queda fuera si el archivo tiene dueñas vivas.
  **Sin agente.** Marca y PRD único (decisión del propietario, 2026-11-11; diseño del Arquitecto): nombre único EVYDENTIA, una ficha por sala (la de plataforma, MARCA-01, ya tiene su bloque BL-270 en la tanda 25): `MARCA-04` (después de DIAG-07 y DER-07); PRD único: el aviso de inhabilitado ya tiene su bloque (BL-283). No se toca nada que hoy lea un árbitro hasta que cada ficha lo diga.

