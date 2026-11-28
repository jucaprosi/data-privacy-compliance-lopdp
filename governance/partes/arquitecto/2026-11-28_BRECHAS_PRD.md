# Brechas del PRD contra `main`: tanda 129
<!-- © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita. -->

**Arquitecto ADPA**, 2026-11-28, sobre `origin/main` a4549e7d. Encargo del CTO (brief ARQUITECTO_TANDA_129_BRECHAS_PRD).

**Método.** Se leyó el código y las pruebas. No se ejecutó ninguna suite. «Cumplido» quiere decir que existe una prueba que afirma lo que pide el criterio. Las pruebas con base de datos corren en el CI (servicio PostgreSQL, `zero-regression-pipeline.yml:50`); en local, sin `TEST_DATABASE_URL`, se saltan.

## 1. Criterios del PRD (§7)

| # | Criterio | Estado | Evidencia | Falta |
| :-- | :--- | :--- | :--- | :--- |
| 1 | ADPA sin imports cruzados | cumplido | `tests/test_adpa_dependencias.py:77`, `:130`, `:147`; `tests/test_adpa_bulkhead.py:74` | — |
| 2 | RLS en 1-RTT | cumplido | `tests/test_rls_todas_las_tablas.py:103`, `:109`; `tests/test_gcp01_cloudrun_rls_single_rtt.py:23` | Revisar las exenciones de `test_rls_todas_las_tablas.py:94` |
| 3 | Matriz de permisos y SoD del DPO | parcial | `tests/test_matriz_permisos.py:642`, `:715`; `tests/test_sod_dpo.py` | El operador de la plataforma no se recorre en la matriz → **SEC-26** |
| 4 | Escala 1-5 sin porcentaje global | cumplido | `tests/test_diagnostico_escala_1_5.py:107`, `:115`; `tests/test_diagnostico_resultados.py:52` | — |
| 5 | Poda ≤ 80 y «No aplica» justificado | parcial | `tests/test_diagnostico_no_aplica.py:94`, `:114`, `:148`; `tests/test_diagnostico_timebox.py:17` | La poda solo se prueba con dos perfiles |
| 6 | Declarado contra verificado y sello del DPO | cumplido | `tests/test_diagnostico_resultados.py:170`, `:281`; `tests/test_diag11_prueba_y_real.py:224`; `tests/test_diag13_evidencia_declarada.py:85` | — |
| 7 | MTGE (Res. SPDP-SPD-2026-0005-R) | cumplido | `tests/test_mtge_resolucion_0005.py:41-115`; `tests/test_mtge_obligaciones.py` | El PRD citaba una ruta que no existe; corregida en este PR |
| 8 | RAT: versionado, colectivos, XLSX y PDF | cumplido | `tests/test_rat_persistencia.py:134`; `tests/test_rat_validaciones.py:170`; `tests/test_rat_consentimientos.py:119`; `tests/test_rat_exportacion.py:137` | — |
| 9 | Vulneraciones: 8 secciones y reloj | parcial | `tests/test_incidentes_asistente.py:214`, `:252`; `tests/test_incidentes.py:199` | Los plazos están aplazados por decisión del propietario (LEG-02; `features/incidentes/domain/models.py:8`) |
| 10 | ARCOP+ y portal público | cumplido | `tests/test_derechos_respuestas.py:187`, `:219`; `tests/test_derechos_portal.py:84`, `:160` | — |
| 11 | Terceros y transferencias | cumplido | `tests/test_terceros_garantias.py:108-259`; `tests/test_terceros_cuestionario.py:133` | — |
| 12 | EIPD en 8 pasos y matriz 5×5 | parcial | `features/riesgos_mtge/domain/eipd.py:15`; `tests/test_eipd_guiada.py:161-273` | Falta un recorrido de los pasos 1 a 8 hasta el dictamen |
| 13 | Hallazgos → tareas y cierre de cuatro ojos | **parcial, riesgo** | Doble validación de la evidencia: `tests/test_rm25b_validacion_final.py:204-432` | `completada` no exige esa evidencia (`tarea_estado_engine.py:37`; `cierre_verificado_engine.py:45`) → **RM-28** |
| 14 | Gemini y Context Caching en Vertex | parcial | `tests/test_vtx01_vertex_context_caching.py:129-220` | Solo con dobles; sin prueba de `text-embedding-005` |
| 15 | Cloud DLP muestreado | parcial | `tests/test_dlp01_sampling_discovery.py:104`, `:157` | Solo con dobles; no se prueba la inyección como borradores del RAT |
| 16 | Biblioteca de 3 capas, Word y Excel | sin verificar a fondo | `tests/test_bib_101` … `test_bib_403` | Revisión pendiente |
| 17 | Firma ANF STB v2 y acuse | **parcial, simulada** | `tests/test_firma_anf_stb.py:83` (`MockTransport`); la prueba real `:455` solo corre con `ANF_STB_PRUEBA_REAL=1` | Una ejecución real acreditada; `test_firma_acuse.py` no existe |
| 18 | Bóveda dual, cuotas y carril forense | **parcial, riesgo** | `tests/test_bov01_paquetes_cuotas.py:211`; `tests/test_bov02_gcs_dual_vault.py:49` | El WORM es una bandera (`entornos/*/buckets.yaml: locked: false`). `forensic_preview_engine.py:52` no transcodifica |
| 19 | CCTV: 15 días, H.265 sin audio y retención WORM | **parcial, riesgo** | `tests/test_cctv02_legal_hold_y_acta_purga.py:110-254`; `tests/test_cctv01_inventario_y_perfil_camaras.py:84` | La promoción cambia una columna (`cctv_legal_hold_engine.py:211`); la purga no está programada |
| 20 | Satélites en Go | parcial | `tests/test_govw01_vault_worker_contract.py` (pasillo en Python) | No hay `go test` del binario |
| 21 | Conservación y formación | sin verificar a fondo | `tests/test_con01_conservacion.py`; `tests/test_formacion.py` | Revisión pendiente |
| 22 | NIIF 18 exacta | parcial | `tests/test_niif18.py:41`, `:81`, `:97` | Compara con tolerancia; el criterio pide igualdad exacta |
| 23 | Contraste AA, 9 menús y `Ctrl+K` | parcial | `frontend/tests/contraste/rutas.spec.ts`; `navegacion/menus.spec.ts:72`; `commandPalette.spec.ts:23` | Quedan 3 vistas pendientes, con dueño (FE-34, FE-41 y FE-43); los menús se prueban contra una API simulada |
| 24 | Cloud Run y Cloud SQL | cumplido, en manifiestos | `tests/test_gcp03_frontend_cloudrun.py:129-193`; `tests/test_gcp04_cloudsql_migration_cutover.py:40-71` | — |
| 25 | UTF-8 sin BOM, huellas y grafo | cumplido | `tests/test_verificar_bom_huellas.py:37`, `:42`; `tests/test_vpa_map.py:46` | — |
| 26 | Vigilancia normativa SPDP | cumplido | `tests/test_norm01_inteligencia_normativa.py:126-283` | — |
| 27 | Sin mapas de fuente ni secretos | cumplido | `tests/test_sec14_frontend_sin_mapas.py:27-72` | — |
| 28 | Límite de peticiones y cuota de IA | cumplido | `tests/test_sec13_limite_peticiones.py:87-118` | — |
| 29 | Observabilidad sin datos personales | parcial | `tests/test_ops07_observabilidad.py:47-99` | Falta comprobar que no se registran cuerpos ni la cabecera `Authorization`. La cita de `alertas` está corregida en este PR |
| 30 | Escalado, caché y prueba de carga | parcial | `tests/test_gcp05_escalado.py:55`; `tests/test_gcp06_cache.py:28-43`; `governance/operaciones/PRUEBA_DE_CARGA.md` §4 | La única corrida (p95 1127 ms) no es válida: dos rutas, una sola IP, casi todo 429 |
| 31 | Despliegue progresivo y migraciones | cumplido | `tests/test_gcp07_despliegue_progresivo.py:33-132` | — |
| 32 | API versionada y claves con alcance | parcial | `tests/test_api02_integraciones.py:70-142`; `tests/test_api02b_webhooks.py:217` | No se prueba que el OpenAPI solo se sirva a clientes autenticados |

## 2. Invariantes con sala (riesgo legal)

| n | Invariante | Estado | Evidencia | Falta |
| :-- | :--- | :--- | :--- | :--- |
| 6 | Independencia del DPO | cumplido | `alembic/versions/20261019_dpo_sin_roles_operativos.py:40`; `tests/test_sod_dpo.py:16-91` | — |
| 7 y 8 | SoD con excepciones con plazo; una sola compuerta de roles | cumplido | `tests/test_excepciones_sod.py:141-309`; `tests/test_alta_unica_roles.py:170` | — |
| 9 | El operador no ve datos de cliente | parcial | `tests/test_plataforma_operador.py:106`, `:163`, `:438` | Recorrido de toda la matriz → **SEC-26** |
| 14 | Cierre de cuatro ojos | **parcial** | La evidencia, sí (RM-25b). La tarea, no | → **RM-28** |
| 15 | La evidencia vencida reabre el control | parcial | `tests/test_controles_reapertura.py:252` | No hay ejecución programada (Cloud Scheduler, del propietario) |
| 16 | Relojes de vulneraciones | aplazado | `features/incidentes/domain/models.py:8` (LEG-02) | Decisión del propietario |
| 17 | Relojes ARCOP+ | parcial | `tests/test_der05_plazos.py:53` | No hay prueba de que la recepción sea inmutable |
| 25 y 31 | WORM de la bóveda y del CCTV | **parcial** | Banderas y columnas | Bloqueo real en GCS: decisión del propietario sobre la infraestructura |
| 29 | Purga de CCTV a los 15 días | parcial | `tests/test_cctv02_legal_hold_y_acta_purga.py:110`, `:340` | Ejecución programada |
| 30 | Perfil de cámara por diseño | parcial | `tests/test_cctv01_inventario_y_perfil_camaras.py:84` | Con audio da 422 en vez de un hallazgo crítico |
| 34 | RLS en 1-RTT | cumplido | ver criterio 2 | — |
| 58, 59 y 66 | Diagnóstico de prueba y real; evidencia del DPO hasta el sello; auditor con rol único | cumplido | `tests/test_diag11_prueba_y_real.py:153-224`; `tests/test_evidencias_persistencia.py:261-295`; `tests/test_org22b_sod_auditor.py:76-176` | La cita del n.º 59 está corregida en este PR |

## 3. Flujo de punta a punta de una organización real

El alta, el assessment, las evidencias, el diagnóstico y el sello del DPO no tienen `NotImplementedError`, 501 ni TODO en `features/diagnostico` ni en `features/evidencias`.

- El paso «terceros» del alta responde 501 `PASO_NO_DISPONIBLE` y se puede saltar (`features/organizacion/services/alta_engine.py:50`). No bloquea.
- Los `NotImplementedError` de `aceptacion_engine.py:98` y `:266` solo saltan si faltan los lectores. La compuerta sí los pasa (`firma_electronica_service.py:419`, `:428`). No bloquea.
- El hueco real es el cierre de tareas sin cuatro ojos (criterio 13).

## 4. Tanda 129

| Ficha | Prioridad | Por qué | Propiedad |
| :--- | :--- | :--- | :--- |
| **RM-28** | 1 y 3 | Cierra el plan de acción con cuatro ojos (criterio 13, invariante 14) | `tarea_estado_engine.py` y su prueba |
| **DEMO-13** | 2 | La demo no puede arrancar a medias en silencio (§5.6) | `entrada_engine.py` y su prueba |
| **SEC-26** | 3 | El operador no ve datos de cliente en ninguna ruta (criterio 3, invariante 9) | `tests/matriz/roles/operador_plataforma.py` y la sección SEC-26 de la matriz |

Las tres son ortogonales: salas distintas, ningún archivo compartido y ninguna migración.

**Fuera de la tanda, para el propietario y el CTO:**
- WORM real en GCS (invariantes 25 y 31).
- Ejecuciones programadas de la reapertura de controles y de la purga de CCTV (invariantes 15 y 29).
- Plazos de vulneraciones (LEG-02).
- Ejecución real contra ANF (criterio 17).
- Una prueba de carga válida (criterio 30).
- Transcodificación real del carril forense (criterio 18). Su sala es `boveda_cloud`; queda para una tanda siguiente.
