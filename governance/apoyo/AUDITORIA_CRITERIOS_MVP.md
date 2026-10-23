# Auditoría de criterios de aceptación del MVP

Auditoría QA-03 (BL-60) contra `governance/artefactos/PRD.md`, §9. Fecha: 2026-10-22. La clasificación distingue comportamiento demostrado de mera presencia, compilación o simulación. Recuento: **3 cubiertos, 10 parciales, 0 sin árbitro**.

## Matriz de cobertura

| # | Criterio abreviado | Árbitro localizado | Qué demuestra realmente | Estado |
|---:|---|---|---|---|
| 1 | SoD del DPO en BD e interfaz | `tests/test_sod_dpo.py::test_sod_bloquea_dpo_asignar_dueno_control`; `tests/test_sod_dpo.py::test_api_sod_dpo_mutate_rat_forbidden` | La regla de dominio rechaza al DPO como dueño de control y ejecutor de remediación; existe además una prueba HTTP de mutación RAT. No hay una prueba de interfaz ni una prueba de restricción persistente en BD para la asignación como dueño de control/EIPD. | **parcial** |
| 2 | Evidencia antes de conformidad o madurez ≥ 2 | `tests/test_assessment_matriz.py::test_nivel_efectivo_es_el_minimo_entre_declaracion_y_evidencia`; `tests/test_assessment_matriz.py::test_criticidad_alta_sin_evidencia_suficiente_topa_el_nivel_en_tres`; `frontend/tests/assessmentDashboard.spec.ts` | El motor reduce el nivel efectivo y la interfaz explica evidencia insuficiente. No bloquea de forma demostrada marcar “Conforme” o madurez ≥ 2 sin E1+ ni prueba la alternativa de rationale formalmente validado. | **parcial** |
| 3 | Diagnóstico ≤ 80 preguntas e informe ejecutivo automático | `tests/test_diagnostico_timebox.py::test_diagnostico_cota_superior_80_preguntas`; `tests/test_diagnostico_timebox.py::test_generador_informes_diagnostico_markdown_y_html` | Falla si el caso de máxima complejidad supera 80 preguntas o si dejan de generarse los informes ejecutivo/técnico con contenido mínimo. Comando: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_diagnostico_timebox.py -q`. | **cubierto** |
| 4 | Grafo único RAT → riesgos, transferencias y EIPD | `tests/test_compliance_graph.py::test_compliance_graph_recalculo_modificacion`; `tests/test_compliance_graph.py::test_compliance_graph_eliminacion_atomica` | Las pruebas construyen `RiesgosStoreMock` y funciones orquestadoras dentro del propio archivo de prueba. Solo simulan RAT → riesgo/EIPD; no prueban transferencias ni ausencia de matrices paralelas del producto. | **parcial** |
| 5 | RAG: cita oficial o incertidumbre | `tests/test_rag_engine.py::test_rag_off_topic_query_rejected`; `tests/test_rag_engine.py::test_rag_on_topic_query_accepted`; `tests/test_api_gateway.py::test_rag_endpoint` | Falla si una consulta fuera de corpus inventa fuente o si una consulta normativa conocida carece de citas y bandera de fuente oficial. Comando: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_rag_engine.py -q`. | **cubierto** |
| 6 | Ergonomía IDE: Ctrl+K, paneles divididos, tema claro/oscuro y ecosistema | `frontend/tests/commandPalette.spec.ts::se abre con el atajo y se cierra con Escape`; `frontend/package.json`; `frontend/src/app/dashboard/page.tsx` | Playwright prueba Ctrl+K y navegación. Las dependencias `cmdk`, `react-resizable-panels`, `react-dropzone` y Zustand, los paneles y ambos temas existen, pero no hay árbitro conductual de redimensionamiento, tema ni conexión completa del ecosistema al store/validación. | **parcial** |
| 7 | Perfil organizacional antecedente y desacoplado mediante `useAuditStore` | `frontend/tests/utiles.ts::configurarProyecto`; `frontend/tests/roadmap/e2e/criterio12_roles.spec.ts::completarFichaOrganizacional` | Los recorridos completan la ficha antes de entrar a módulos y el código usa `useAuditStore`, pero el helper no es un árbitro y las pruebas no fallan específicamente si el cuestionario aparece antes, si la ficha deja de ser pestaña independiente o si se desacopla del store. | **parcial** |
| 8 | Whitelist y purga de evidencia por dominio normativo | `tests/test_evidencia_validacion_servidor.py::test_tipo_fuera_de_la_lista_blanca_se_rechaza_con_415`; `tests/test_evidencia_validacion_servidor.py::test_reglas_del_servidor_alineadas_con_las_de_la_interfaz`; `frontend/tests/roadmap/evidencia.spec.ts::rechaza una extensión no permitida y dice cuáles se admiten` | Hay whitelist de tipo/extensión en servidor e interfaz. No se localizó una prueba que cambie dominio/normativa y demuestre la purga atómica e irreversible del arreglo de evidencias. | **parcial** |
| 9 | Arnés físico exógeno con salida 0 antes de producción | `ejecutar_arnes_verificacion.bat`; `verificadores/arnes_cero_regresiones.py`; `tests/test_entorno_arnes.py` | Existe el arnés, emite `.test_verdict.json` y la prueba de entorno protege la resolución del intérprete. No se ejecutó el arnés completo porque dispara toda la suite, incluida BD; tampoco se localizó una compuerta de despliegue que pruebe que producción exige su certificado PASS vigente. | **parcial** |
| 10 | Matriz rol × endpoint completa, sin filas pendientes | `tests/test_matriz_permisos.py::test_matriz_permisos_rol_accion` | La matriz está parametrizada y compara dependencias RBAC, pero los endpoints ausentes se marcan `xfail(strict=False)`: por diseño puede terminar sin error con filas pendientes. En este entorno no se pudo ni colectar sin `DATABASE_URL`. | **parcial** |
| 11 | RLS efectivo para las tablas tenant y rol sin BYPASSRLS | `tests/test_rls_app_role.py::test_rol_app_sin_bypassrls`; `tests/test_rls_app_role.py::test_tenant_ajeno_ve_cero_filas`; `tests/test_rls_app_role.py::test_sin_tenant_fijado_no_ve_filas` | Comprueba el rol y aislamiento real solo sobre `user_tenant_roles`. El texto del criterio está desactualizado: las 7 tablas de `20261008_app_role_rls.py::RLS_TABLES` eran una foto histórica; migraciones posteriores agregan FORCE RLS al menos a `audit_events`, `area_responsable_requests`, `designaciones_formales`, `cargos_organicos`, `derechos_arco_solicitudes` y `sod_exceptions` (13 en total contando aquellas 7). No existe matriz conductual para todas. | **parcial** |
| 12 | E2E por rol con audit log en cada transición | `frontend/tests/roadmap/e2e/criterio12_roles.spec.ts::recorrido completo: implementador genera -> coordinador distribuye -> responsable_area sube evidencia -> dpo valida, con audit log en cada paso` | Recorre toda la UI y aserta llamadas/eventos, pero `page.route` implementa en memoria generación, asignación, evidencia, validación y audit log. Fallaría ante una regresión de interfaz, no ante una regresión del backend o de persistencia real. | **parcial** |
| 13 | Verificación posterior al despliegue: health 200 y routers cargados | `scripts/verificar_despliegue.py`; `tests/test_verificar_despliegue.py::test_despliegue_operativo_exitoso`; `tests/test_verificar_despliegue.py::test_falla_si_health_no_responde_200`; `tests/test_verificar_despliegue.py::test_falla_si_hay_routers_fallidos` | El verificador falla ante HTTP distinto de 200, estado no operacional, routers fallidos o rutas OpenAPI ausentes; su suite positiva y negativa pasó. Comando: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_verificar_despliegue.py -q`. La ejecución contra un despliegue real queda en “No verificado”. | **cubierto** |

## Pruebas ejecutadas sin base de datos

- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_diagnostico_timebox.py -q` → código 0; `3 passed in 0.45s`.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_assessment_matriz.py -q` → código 0; `22 passed in 0.38s`.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_rag_engine.py -q` → código 0; `2 passed in 0.36s`.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_sod_dpo.py::test_sod_bloquea_dpo_asignar_dueno_control -q` → código 0; `1 passed in 2.81s`.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_verificar_despliegue.py -q` → dentro del sandbox: código 1, `10 failed, 3 passed`, todos los fallos relevantes por `WinError 10013` al abrir sockets locales; repetido fuera del sandbox → código 0, `13 passed in 9.80s`.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_evidencia_validacion_servidor.py -q` → código 1 en colección: `RuntimeError: DATABASE_URL no definida`; no se configuró una URL ficticia porque el encargo prohíbe URLs de conexión.
- `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_matriz_permisos.py --collect-only -q` → código 1 en colección: `RuntimeError: DATABASE_URL no definida`.
- `npm run test:e2e -- tests/commandPalette.spec.ts tests/assessmentDashboard.spec.ts tests/roadmap/e2e/criterio12_roles.spec.ts --reporter=line` (desde `frontend/`) → código 1: `playwright no se reconoce`; no se instalaron dependencias ni se modificó el entorno.
- Dos intentos agrupados que incluían `tests/test_sod_dpo.py` completo no concluyeron y fueron interrumpidos; las tres primeras pruebas habían avanzado (`...`) pero no se atribuye aprobación a esa salida parcial. Después se ejecutó aisladamente la prueba de dominio consignada arriba.

## Comandos para el coordinador (requieren infraestructura)

- Matriz RBAC: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_matriz_permisos.py -q -rxX` con `TEST_DATABASE_URL`/`DATABASE_URL` de pruebas. Debe revisarse que haya **cero** `xfailed` y `xpassed`, no solo código 0.
- RLS: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_rls_app_role.py -q -rs` con PostgreSQL migrado. Los `skip` por ausencia de `lopdp_app` invalidan la evidencia.
- Flujo backend real por roles: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m pytest tests/test_roadmap_generacion_en_linea.py tests/test_roadmap_tarea_asignacion.py tests/test_evidencia_http.py tests/test_roadmap_auditoria_consulta.py -q` con PostgreSQL de pruebas.
- Arnés completo: `cmd /c ejecutar_arnes_verificacion.bat`; conservar salida final y ambos certificados `.test_verdict.json` con `status: PASS`.
- Frontend simulado: `npm ci` y luego `npm run test:e2e -- tests/commandPalette.spec.ts tests/assessmentDashboard.spec.ts tests/roadmap/e2e/criterio12_roles.spec.ts --reporter=line` desde `frontend/`.
- Despliegue real: `"C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" scripts/verificar_despliegue.py https://<dominio-del-despliegue>` sustituyendo el marcador por el dominio real autorizado.

## Borradores de ficha

### Criterio 1 — SoD DPO en todas las capas

- **Objetivo:** demostrar rechazo en persistencia y UI de toda asignación del DPO como dueño de control o ejecutor de EIPD.
- **Propiedad propuesta:** prueba de integración BD y spec Playwright nuevos, sin cambiar la regla funcional.
- **Árbitro propuesto:** casos negativos por ambas vías que exijan 409/403 y ausencia de asignación persistida/botón habilitado.
- **Dependencias:** PostgreSQL migrado, fixtures de roles y pantallas de control/EIPD.

### Criterio 2 — Precondición fuerte de evidencia

- **Objetivo:** impedir la transición a Conforme o madurez ≥ 2 salvo E1+ o rationale con validación formal.
- **Propiedad propuesta:** pruebas de dominio, API y UI de la transición y de las dos excepciones válidas.
- **Árbitro propuesto:** matriz estado × evidencia × estado del rationale que falle si se acepta un caso prohibido.
- **Dependencias:** contrato explícito para “rationale formalmente validado”.

### Criterio 4 — Grafo de cumplimiento real

- **Objetivo:** probar que una actividad RAT real alimenta riesgos, transferencias y EIPD sin almacenes paralelos.
- **Propiedad propuesta:** prueba de integración del servicio/producto, eliminando orquestadores definidos dentro del test.
- **Árbitro propuesto:** alta, cambio y baja RAT con aserciones sobre las tres proyecciones y claves foráneas/identidad común.
- **Dependencias:** PostgreSQL y definición canónica de la relación con transferencias.

### Criterio 6 — Ergonomía IDE completa

- **Objetivo:** cubrir redimensionamiento persistente de paneles, alternancia de tema y validación de archivos conectada al store además de Ctrl+K.
- **Propiedad propuesta:** specs Playwright del dashboard y dropzone.
- **Árbitro propuesto:** interacciones visibles y estado persistido; no inspección de imports.
- **Dependencias:** dependencias frontend instaladas y navegador Playwright.

### Criterio 7 — Antecedencia del perfil

- **Objetivo:** bloquear preguntas hasta guardar el perfil y demostrar que la pestaña independiente comparte el estado mediante `useAuditStore`.
- **Propiedad propuesta:** spec Playwright dedicada y, si existe infraestructura, prueba del store.
- **Árbitro propuesto:** arranque limpio sin cuestionario, guardado, poda observable y rehidratación del perfil.
- **Dependencias:** arnés frontend.

### Criterio 8 — Purga por dominio

- **Objetivo:** complementar la whitelist ya probada con purga atómica e irreversible al cambiar normativa/dominio.
- **Propiedad propuesta:** prueba del store y spec Playwright del selector con confirmación.
- **Árbitro propuesto:** evidencias sembradas → cambio confirmado → arreglo vacío, propuestas asociadas eliminadas y ningún dato reaparece tras recarga.
- **Dependencias:** contrato de persistencia local del store.

### Criterio 9 — Compuerta física previa a producción

- **Objetivo:** demostrar que un despliegue no puede continuar sin certificado PASS vigente del arnés.
- **Propiedad propuesta:** verificador de compuerta/CI y prueba negativa con certificado ausente, FAIL o obsoleto.
- **Árbitro propuesto:** pipeline local reproducible que retorna distinto de cero en los tres casos y cero solo tras el arnés completo.
- **Dependencias:** suite completa, PostgreSQL y Node.

### Criterio 10 — Cero filas pendientes en RBAC

- **Objetivo:** convertir los endpoints ausentes en fallos estrictos y comprobar toda la matriz vigente.
- **Propiedad propuesta:** `tests/test_matriz_permisos.py` o un verificador separado que prohíba xfail/xpass.
- **Árbitro propuesto:** `pytest -q -rxX` más aserción automatizada de cero filas pendientes.
- **Dependencias:** todos los endpoints del PRD y PostgreSQL de pruebas.

### Criterio 11 — RLS exhaustivo y actualizado

- **Objetivo:** derivar dinámicamente el inventario tenant-scoped y probar rol, tenant propio, ajeno y ausente en cada tabla.
- **Propiedad propuesta:** prueba PostgreSQL parametrizada; actualizar después el texto del PRD por decisión del propietario.
- **Árbitro propuesto:** matriz de todas las tablas FORCE RLS con cero filas fuera del tenant y `rolbypassrls = false`.
- **Dependencias:** todas las migraciones aplicadas y fixtures mínimos por tabla.

### Criterio 12 — Flujo E2E sin API simulada

- **Objetivo:** repetir el recorrido por rol contra backend y BD reales, conservando auditoría persistida en cada paso.
- **Propiedad propuesta:** E2E de integración separado del spec de interfaz simulado.
- **Árbitro propuesto:** Playwright contra entorno efímero o prueba de integración equivalente con cuatro identidades reales y consulta final del audit log.
- **Dependencias:** PostgreSQL, almacenamiento simulado controlado y frontend levantado.

## No verificado

- No se ejecutaron pruebas que necesitan PostgreSQL ni se definió `DATABASE_URL`/`TEST_DATABASE_URL`.
- No se ejecutó `ejecutar_arnes_verificacion.bat`; por tanto no hay línea final del arnés ni certificado PASS atribuible a esta auditoría.
- No se ejecutó Playwright por ausencia del binario/dependencias en `frontend/node_modules`.
- No se consultó ningún despliegue real porque no se proporcionó URL.
- ZERAG estuvo disponible y devolvió el rol `¤¤qa-engineer`; no se inventan identificadores adicionales ni certificado físico.

## Verificación del coordinador (2026-10-22)

Comprobado sobre esta misma rama antes de integrarla. Ninguna clasificación cambia.

- **Referencias:** las 31 rutas y nombres de prueba citados existen en el repositorio (comprobación automática de archivo y nombre de prueba).
- **Criterios «cubiertos» (3, 5 y 13):** `pytest tests/test_diagnostico_timebox.py tests/test_rag_engine.py tests/test_verificar_despliegue.py -q` → **18 passed**.
- **Criterio 13 contra el despliegue real:** `scripts/verificar_despliegue.py https://data-privacy-compliance-lopdp.vercel.app` → salida 0 el 2026-10-22, tras corregir el `DATABASE_URL` de producción (ver `CREDENCIALES_Y_ROLES_BD.md`).
- **Criterio 10 contra PostgreSQL (rama Neon `revision`):** `pytest tests/test_matriz_permisos.py -q -rxX` → **205 passed, 0 xfailed, 0 xpassed**. Hoy no hay filas pendientes, pero la clasificación «parcial» se mantiene: la prueba no fallaría si apareciera una, porque usa `xfail(strict=False)`.
- **Criterio 11 contra PostgreSQL (rama `revision`):** `pytest tests/test_rls_app_role.py -q -rs` → **4 passed, 0 skipped**, solo sobre `user_tenant_roles`. Consulta a `pg_class`: **13 tablas** con RLS habilitado y forzado (`area_responsable_requests`, `areas`, `audit_events`, `cargos_organicos`, `derechos_arco_solicitudes`, `designaciones_formales`, `roadmap_tasks`, `roadmap_waves`, `roadmaps`, `sod_exceptions`, `task_audit_log`, `task_evidence`, `user_tenant_roles`), no 7 como dice el PRD.
- **Pendiente de ejecutar:** el arnés completo (criterio 9) y el Playwright de los criterios 6, 7 y 12.

## Revisión del criterio 1 (coordinador, 2026-10-22)

La auditoría no localizó tres pruebas que sí cubren el bloqueo del DPO como dueño de control:

- **Base de datos:** `tests/test_organizacion_api.py::test_trigger_bd_bloquea_dpo_con_rol_operativo`: aunque se salte la API, el trigger `fn_utr_dpo_sod` rechaza que el DPO tenga un rol operativo.
- **API:** `tests/test_organizacion_api.py::test_sod_dpo_y_ciclo_de_revocacion` (409) y `tests/test_rbac_rules.py` (las dos direcciones de la incompatibilidad).
- **Interfaz:** `frontend/tests/roadmap/admin.spec.ts`, «SOD_VIOLATION se muestra con una explicación y sin botón de configuración».
- **Por qué basta:** en el producto, el dueño de un control es el responsable de una tarea de la hoja de ruta, y la asignación exige el rol `responsable_area` (`features/roadmap/services/tarea_asignacion_engine.py`), que el DPO no puede tener. Las dos pruebas de backend y `test_rbac_rules.py`: **15 passed** contra PostgreSQL (rama `revision`).

**Reclasificación:** el criterio 1 queda **cubierto para el dueño de control**. La parte del **ejecutor de EIPD** no se puede probar porque las EIPD **no se persisten**: `EIPDRepository` (`features/rat/services/mtge_engine.py`) es un repositorio en memoria y no hay tabla ni endpoint para asignar ejecutor. Es una decisión de producto (persistir las EIPD), no un hueco de pruebas.

Recuento corregido: **4 cubiertos, 9 parciales, 0 sin árbitro**.
