# Catálogo Constitucional de Invariantes (`INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`)
`¤invariantes` `¤adpa` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤gemini-vertex` `¤boveda-cloud` `¤videovigilancia-cctv` `¤motor-go-hibrido`

> **CONTRATOS MATEMÁTICOS E INMUTABLES DE EVYDENTIA — REVENTA DE NUBE:**
> Toda regla aquí registrada es una ley física del sistema verificada por árbitros automatizados (`pytest`, linters AST y restricciones de base de datos en Cloud SQL PostgreSQL 16).

---

## 1. Invariantes de Dominio LOPDP, Escala SMARTCIDI y Segregación de Funciones
<!-- ¤adpa -->
1. **`INV_LOPDP_DIAG_MAX_80_QUESTIONS`**: El árbol condicional del Assessment filtra y poda el banco maestro (`P1–P80`) de modo que ningún perfil organizacional reciba más de **80 preguntas efectivas** ($\le 60$ minutos de evaluación).
2. **`INV_LOPDP_EVIDENCE_REQUIRED_FOR_CONFORMITY`**: Ningún control en diagnóstico, auditoría o plan de acción alcanza estado de conformidad verificada si su nivel de evidencia es `E0` (autodeclaración sin soporte), exigiendo evidencia válida ($E1, E2, E3$) o justificación formal auditada.
3. **`INV_LOPDP_NO_APPLICABLE_REQUIRES_JUSTIFICATION`**: Toda pregunta del assessment marcada como «No aplica» exige justificación textual obligatoria persistida junto con la respuesta y sujeta a revisión del DPO (`DIAG-05`).
4. **`INV_LOPDP_DPO_DECLARED_VERIFIED_SEAL`**: Las respuestas del assessment son registradas por el Administrador y los encargados de dominio (valor *declarado*); el DPO las revisa en la grilla Declarado/Verificado, puede objetarlas y es el único rol facultado para emitir el sello criptográfico `SHA-256` que vuelve inmutable el resultado (`DIAG-03`, `DIAG-07`).
5. **`INV_LOPDP_SMARTCIDI_MATURITY_SCALE`**: La madurez se mide exclusivamente en la **escala SMARTCIDI de 1 a 5** (`1 Inicial`, `2 Repetible`, `3 Definido`, `4 Gestionado`, `5 Optimizado`) cruzada con el nivel de evidencia (`0` a `4`) por control, dominio y cada una de las **4 Dimensiones**, sin emitir una cifra o porcentaje global único para la organización (`DIAG-08`, `DIAG-09`, `DIAG-10`, `FE-24`).
6. **`INV_LOPDP_DPO_INDEPENDENCE`**: El usuario con rol `dpo` en una organización tiene prohibido estructuralmente acumular roles operativos (`admin_organizacion`, `coordinador`, `responsable_area`, `implementador`) en esa misma organización o ser asignado como ejecutor de tareas operativas (Art. 48 LOPDP; `ORG-01`).
7. **`INV_LOPDP_SOD_EXPLICIT_TIMEBOUND_EXCEPTIONS`**: Cualquier excepción a la separación de funciones entre Coordinador y Responsable de Área requiere registro explícito, justificación motivada y fecha de expiración determinada (`ORG-02`).
8. **`INV_LOPDP_SINGLE_ROLE_GRANT_NO_SELF_ELEVATION`**: Todas las concesiones de rol atraviesan una única compuerta de autorización en `features/organizacion/`, impidiendo que cualquier usuario se autoconceda o eleve privilegios (`ORG-05`).
9. **`INV_LOPDP_OPERATOR_NO_TENANT_DATA`**: El `operador_plataforma` gobierna el alta de organizaciones, las invitaciones iniciales, los paquetes de Bóveda Cloud y el catálogo maestro, pero carece de acceso de lectura o escritura a los datos operativos de los tenants (`ORG-09`).
10. **`INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`**: La vista de Cartera (`ORG-15`) agrega indicadores exclusivamente de las organizaciones a las que el usuario pertenece legítimamente (como `dpo` o `implementador`), ejecutando cada consulta bajo el aislamiento RLS de cada organización sin usar credenciales con `BYPASSRLS`.
11. **`INV_LOPDP_MTGE_DETERMINISTIC_THRESHOLD`**: El cálculo MTGE aplica la fórmula exacta de 6 variables de la Resolución `SPDP-SPD-2026-0005-R`; todo puntaje $\ge 6$ puntos o la activación de un caso directo clasifica obligatoriamente el tratamiento como **Gran Escala** y dispara la obligatoriedad de EIPD, DPO, auditoría anual e informe anual (`MTGE-01`, `MTGE-02`).
12. **`INV_LOPDP_RAT_IMMUTABLE_VERSIONING`**: Toda modificación aprobada sobre una actividad de tratamiento del RAT genera una nueva versión numerada e inmutable de la ficha, preservando el historial íntegro para inspección de la SPDP (`RAT-05`).
13. **`INV_LOPDP_SINGLE_ACTION_PLAN`**: Todos los hallazgos generados en Diagnóstico, Controles Periódicos, Auditorías, RAT, EIPD, Terceros y Transferencias convergen a través de una única compuerta en `features/roadmap/` hacia el **Plan de Acción Único** de la organización (`RM-21`).
14. **`INV_LOPDP_FOUR_EYES_CLOSURE`**: El cierre definitivo de toda tarea del plan de acción exige validación de cuatro ojos: primera validación operativa del Coordinador con evidencia `E1+` y segunda verificación independiente del DPO o Auditor.
15. **`INV_LOPDP_EXPIRED_EVIDENCE_REOPENS_CONTROL`**: Cuando una evidencia vinculada a un control periódico alcanza su fecha de vencimiento (`valid_until < now()`), el motor reabre automáticamente el control periódico y genera el hallazgo correspondiente (`CAPA-03`).
16. **`INV_LOPDP_BREACH_SLA_TIMERS`**: El asistente de vulneraciones en 8 secciones (`INC-02`) ejecuta los cronómetros vinculantes de la Norma Técnica `SPDP-SPD-2026-0040-R` desde `detected_at` y documenta la decisión motivada de notificación a la SPDP y a los titulares.
17. **`INV_LOPDP_ARCOP_SLA_TIMERS`**: Toda solicitud ARCOP+ registra marca de tiempo inmutable de recepción e identidad verificada (`DER-01`), activando los plazos legales de respuesta (15 días para acceso/eliminación/oposición; 5 días para rectificación y actualización) y archivando la respuesta como evidencia.
18. **`INV_LOPDP_PARAMETRIC_ANTECEDENCE`**: El perfilamiento estructural de la organización ($\text{Root}(\mathcal{T}_{\text{poda}})$) antecede a toda evaluación u operación ($\text{Root}(\mathcal{T}_{\text{poda}}) \prec \mathcal{Q}_{\text{diag}}$) y gobierna la aplicabilidad de controles y plantillas.
19. **`INV_LOPDP_DOMAIN_EVIDENCE_ISOLATION`**: Cada régimen normativo (LOPDP, NIIF 18) aplica su propia lista blanca de extensiones y tipos MIME permitidos, garantizando aislamiento probatorio multidominio.

<!-- ¤adpa/ -->

---

## 2. Invariantes de Inteligencia Artificial con Google Gemini en Vertex AI y Cloud DLP
<!-- ¤adpa -->
`¤gemini-vertex` `¤vertex-cache` `¤dlp-muestreo`
20. **`INV_LOPDP_GEMINI_VERTEX_NATIVE_MODELS`**: Toda inferencia generativa y vectorial del sistema se ejecuta sobre modelos **Google Gemini en Vertex AI** (`gemini-2.5-pro` para razonamiento jurídico/financiero profundo y Hoja de Ruta con `response_schema` Pydantic v2; `gemini-2.5-flash` para preanálisis de baja latencia, asistencia en formularios e inspección multimodal; `text-embedding-005` para indexación vectorial en `pgvector`), autenticados mediante *Application Default Credentials (ADC)* sin llaves estáticas en código.
21. **`INV_LOPDP_VERTEX_CONTEXT_CACHE_SHA256`**: El corpus normativo oficial (LOPDP, RGLOPDP, Resoluciones SPDP y doctrina NIIF 18) se empaqueta en un `CachedContent` de Vertex AI indexado por su huella `corpus_sha256` (`VTX-01`). Mientras el `corpus_sha256` permanezca vigente, todas las consultas reutilizan el `cache_name` activo; cualquier actualización normativa invalida de inmediato la caché previa.
22. **`INV_LOPDP_AI_RAG_STRICT_CITATION`**: Toda respuesta del Copiloto Gemini o del motor RAG incluye citas expresas a artículos vigentes del corpus oficial en caché; ante ausencia de respaldo normativo en el corpus, el sistema declara explícitamente la incertidumbre sin extrapolar preceptos.
23. **`INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10`**: Ningún texto de usuario ni muestra de datos se envía a Vertex AI o al índice vectorial sin atravesar el filtro determinista de validación **Módulo 10** de cédulas y RUC ecuatorianos y el escáner **Google Cloud DLP**, redactando preventivamente cualquier identificador como `[CEDULA-REDACTADA]` (`VTX-01`, `DLP-01`).
24. **`INV_LOPDP_ZERO_TRAINING_TENANT_DATA`**: Ningún dato, documento, prompt o respuesta perteneciente a una organización se utiliza para entrenar o ajustar modelos compartidos o públicos.

<!-- ¤adpa/ -->

---

## 3. Invariantes de Bóveda Cloud Certificada, Videovigilancia LOPDP y Satélites en Go
<!-- ¤adpa -->
`¤boveda-cloud` `¤videovigilancia-cctv` `¤motor-go-hibrido`
25. **`INV_LOPDP_GCS_DUAL_VAULT_SEGREGATION`**: La Bóveda Cloud segrega físicamente los objetos en dos pools de Google Cloud Storage (`BOV-02`):
    * `short-ttl`: *Standard Storage* con `Autoclass = False` y regla `Object Lifecycle Management (OLM)` de borrado a los **15 días** para videovigilancia ordinaria.
    * `long-retention`: `Autoclass = True` con política de retención inmutable **WORM (*Object Lock*)** de 3 a 10 años para evidencias normativas, informes sellados, contratos firmados y clips bajo *Hold Legal*.
26. **`INV_LOPDP_DIRECT_TO_GCS_SIGNED_URL_V4`**: Toda ingesta o descarga de archivos pesados (evidencias, paquetes documentales, clips de video) se realiza directamente contra Google Cloud Storage mediante **URLs firmadas V4** acotadas por `tenant_id`, tipo MIME y longitud máxima en bytes, sin transitar por la memoria RAM de los workers de Cloud Run.
27. **`INV_LOPDP_FORENSIC_DUAL_TRACK_SHA256`**: Todo archivo probatorio se conserva en doble carril (`BOV-03`): el **original intacto** sellado con `SHA-256` calculado en streaming y el **derivado ligero de previsualización** (`WebP`, `AVIF` o `WebM`) servido por defecto en la interfaz de usuario para preservar la cuota mensual de Egress del tenant.
28. **`INV_LOPDP_VAULT_QUOTA_ENFORCEMENT`**: El motor de Bóveda Cloud verifica antes de cada aprovisionamiento o descarga masiva el consumo acumulado de almacenamiento (`storage_bytes_used`) y transferencia (`egress_bytes_month`) frente al paquete contratado (`BOV-01`), garantizando que las inspecciones oficiales para la SPDP y la visualización de derivados ligeros permanezcan siempre operativas.
29. **`INV_LOPDP_CCTV_15_DAYS_DESTRUCTION_ACT`**: Todo clip ordinario de videovigilancia se elimina automáticamente al cumplirse los **15 días** de su captura, emitiendo un **Acta Quincenal de Destrucción Segura** firmada con el hash `SHA-256` de los lotes depurados (`CCTV-01`, `CCTV-02`).
30. **`INV_LOPDP_CCTV_PRIVACY_BY_DESIGN_PROFILE`**: El perfil técnico de videovigilancia exige compresión `H.265`, grabación por eventos de movimiento y **canal de audio deshabilitado por defecto** (`audio_enabled = False`); cualquier intento de habilitar audio sin base legal y dictamen del DPO genera un hallazgo crítico inmediato (`CCTV-01`).
31. **`INV_LOPDP_CCTV_LEGAL_HOLD_WORM`**: La vinculación de un clip de videovigilancia a un incidente de seguridad (`INC-01`/`INC-02`) o a una solicitud ARCOP+ (`DER-01`) promueve atómicamente el objeto del pool `short-ttl` al pool `long-retention` con bloqueo WORM inmutable, suspendiendo su purga quincenal hasta el cierre formal del caso (`CCTV-02`).
32. **`INV_LOPDP_HYBRID_GO_CONCURRENCY`**: Las operaciones de uso intensivo de I/O, red en el borde y criptografía en streaming (recepción Eventarc, cálculo `SHA-256` de grandes volúmenes, purgas masivas y recorte RTSP/H.265 en sedes) se ejecutan en los satélites compilados en **Go 1.23+** (`services_go/vault_worker` y `services_go/cctv_agent`), comunicados con el Core Python exclusivamente a través de contratos tipados en `app_core/pasillo/` (`GOVW-01`, `GOCA-01`).

<!-- ¤adpa/ -->

---

## 4. Invariantes de Arquitectura ADPA, Base de Datos en 1-RTT, Firma Electrónica y NIIF 18
<!-- ¤adpa -->
`¤adpa` `¤cloud-run-perf` `¤firma-electronica` `¤niif18`
33. **`INV_ADPA_ZERO_LATERAL_IMPORTS`**: Ninguna sala bajo `features/<sala>/` importa directamente de otra sala (`features.<otra>`) ni de la capa HTTP (`api.*`). El contador de deuda lateral es estrictamente **`TOPE_DEUDA_LATERAL = 0`**; toda integración inter-sala ocurre vía `app_core/pasillo/<sala>.py` ➔ `features/<sala>/<sala>_service.py` (`ADPA-01..09`).
34. **`INV_CLOUD_RUN_SINGLE_RTT_RLS`**: La sesión asíncrona de base de datos en Cloud Run inyecta el contexto multi-tenant (`app.current_tenant_id`, `app.current_user_id`, `app.current_user_role`) y abre la transacción en **un único viaje de red (1-RTT)** sobre `PgBouncer` en modo `transaction pooling`, operando siempre bajo el rol `lopdp_app` con `FORCE ROW LEVEL SECURITY` (`GCP-01`, `GCP-04`).
35. **`INV_ANF_STB_CRYPTOGRAPHIC_SIGNATURE`**: Toda firma electrónica avanzada o cualificada se ejecuta contra el contrato de **ANF AC Ecuador Sign Time Box (STB v2)** en modalidades `PAdES`, `XAdES` o `CAdES`, verificando el hash `SHA-256` antes y después del sellado (`FIRMA-01..06`).
36. **`INV_NIIF18_EXACT_SUBTOTAL_RECONCILIATION`**: En la sala `features/niif18/`, la suma algebraica de las partidas clasificadas en *Operación*, *Inversión* y *Financiación* cuadra de manera exacta y determinista con el *Resultado de Operación*, el *Resultado antes de Financiación e Impuesto a las Ganancias* y las conciliaciones de *MPM*.
37. **`INV_UI_BITEMPORAL_SURFACE_TOKENS`**: Ningún componente del frontend utiliza colores fijos del tema oscuro sin su variable semántica de superficie bitemporal (`FE-18`), ni inventa datos simulados cuando el backend devuelve un error (`API-01`), ni expone tokens internos de gobernanza en la interfaz de usuario (`¤interfaz`).
38. **`INV_REPO_UTF8_NO_BOM_AND_SEALED_TRACES`**: Todos los archivos del repositorio se codifican en **UTF-8 sin BOM** y ningún archivo de código o doctrina permanece con huellas transitorias `¦` abiertas al cerrar sesión.

<!-- ¤adpa/ -->
---

## 5. Invariantes de Inteligencia Normativa y Vigilancia Regulatoria SPDP
<!-- ¤adpa -->
`¤inteligencia-normativa` `¤vigilancia-spdp`
39. **`INV_NORMATIVA_INTEGRITY_SHA256`**: Todo documento normativo descargado de las fuentes oficiales de la SPDP (`/resoluciones/`, `/marco-normativo/`, `/consultas-absueltas/`) conserva su archivo PDF original inmutable en Google Cloud Storage con huella `SHA-256` calculada en streaming antes de cualquier extracción o procesamiento posterior (`RF-04`, `RF-05`).
40. **`INV_NORMATIVA_DEDUPLICATION_TRIPLE_GATE`**: El motor de deduplicación valida de forma estricta: (1) coincidencia unívoca de `numero_resolucion` y `anio_emision`, (2) identidad de `archivo_sha256`, y (3) detección de modificaciones en la fuente oficial; cualquier documento con igual número pero diferente hash genera una versión inmutable vinculada en `normativa_versiones` sin sobreescribir el archivo precedente (`RF-03`).
41. **`INV_NORMATIVA_HUMAN_LEGAL_VALIDATION`**: Ninguna conclusión, derogatoria, reforma o propuesta de actualización regulatoria generada por IA o scraping adquiere vigencia operativa ni altera las reglas del Compliance Graph, Assessment o Plan de Acción sin validación jurídica formal humana (HITL) del Delegado de Protección de Datos o Administrador competente (`RF-05`, `INV_LOPDP_DPO_INDEPENDENCE`).
42. **`INV_NORMATIVA_SCHEDULED_MONITORING_QUOTA`**: El servicio de monitoreo automático programado (diario a las 05:00 ECT / UTC-5) respeta los límites de cortesía de los servidores oficiales de la SPDP mediante rate limiting, peticiones serializadas, reintentos con backoff exponencial y registro determinista de cada ejecución en `normativa_monitoreo_logs` (`RF-01`).

<!-- ¤adpa/ -->
