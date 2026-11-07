# Tablero Maestro de Ejecución Constitucional (`TASKS_EVYDENTIA_REVENTA_NUBE.md`)
# EVYDENTIA: Reventa de Nube Certificada y 10 Dimensiones LOPDP (Carril Fuera del PMV)
`¤tasks` `¤bbap` `¤adpa` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤gemini-vertex` `¤boveda-cloud` `¤videovigilancia-cctv` `¤motor-go-hibrido` `¤grado-productivo`

> **CONSTITUCIÓN DE REFERENCIA:** [`PRD_EVYDENTIA_REVENTA_NUBE.md`](./PRD_EVYDENTIA_REVENTA_NUBE.md)  
> **CATÁLOGO DE INVARIANTES:** [`INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`](./INVARIANTS_EVYDENTIA_REVENTA_NUBE.md)  
> **MAPA ESTIGMÉRGICO:** [`VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`](./VPA_MAP_EVYDENTIA_REVENTA_NUBE.md)  
> **PROPÓSITO:** Este tablero gobierna la ejecución ordenada, ortogonal y sin colisiones de todas las tareas de **EVYDENTIA: Reventa de Nube** fuera del PMV (Cimiento ADPA, Infraestructura Google Cloud Run / Cloud SQL, Modelos **Google Gemini en Vertex AI**, Bóveda Cloud Dual, Satélites en Go, Videovigilancia LOPDP y Estructura Funcional Completa de las 10 Dimensiones).

---

## 1. Resumen Ejecutivo de Estado del Carril «EVYDENTIA: Reventa de Nube»
<!-- ¤adpa -->
* **Arquitectura Objetivo:** 33 Salas ADPA Políglotas (`Python 3.12+ Core` + `Go 1.23+ Satélites` + `Next.js 15.5+ Standalone`) sobre **Google Cloud Platform** y **Google Gemini en Vertex AI**.
* **Cimiento y Firma Completados en esta Serie:**
  * `[x]` **`FIRMA-01..06`**: Integración completa de Firma Electrónica Real con **ANF AC Ecuador STB v2** (`PAdES`/`XAdES`/`CAdES`), custodia de firmados, webhook/polling y suite E2E verificada (`34 passed`).
  * `[x]` **`ADPA-01`**: Compuertas estancas de `derechos_arco`, `terceros` y `transferencias`.
  * `[x]` **`ADPA-02`** *(Tanda 18)*: Reubicación canónica de `ErrorNegocio` en `app_core/errors.py` y prohibición AST de imports `features.* -> api.*`.
  * `[x]` **`ADPA-03`** *(Tanda 19)*: Retiro de deuda lateral ADPA Lote 1 (`auditoria_capa`, `plataforma`, `rat`, `ai_copilot`) vía `app_core/pasillo/` (`TOPE_DEUDA_LATERAL` reducido de `11` a `5`).

<!-- ¤adpa/ -->

---

## 2. Olas Constitucionales de Ejecución (Secuencia de Tandas para Juan Carlos)
<!-- ¤adpa -->

### 🟢 OLA 1: Sellado del Cimiento ADPA y Secciones `#ID` (`DEUDA_LATERAL = 0`)
`¤adpa`

> **Objetivo:** Erradicar el 100% de las importaciones laterales restantes, andamiar los catálogos de errores por sala (`domain/errores.py`), abrir las secciones `#ID` en pasillos, compuertas y registros de frontend, y activar las salas `terceros`, `transferencias`, `formacion` y `conservacion`.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Depende de |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[x]` | — | — | [`ADPA-01`](../tareas/ADPA-01.md) | Compuertas de las salas Derechos ARCO, Terceros y Transferencias | `derechos_arco, terceros, transferencias` | `RM-02` |
| `[x]` | 18 | `BL-164` | [`ADPA-02`](../tareas/ADPA-02.md) | Reubicar `ErrorNegocio` en `app_core/errors.py` y prohibir imports `features -> api` | `auditoria_capa, biblioteca, dpo_cockpit, organizacion, rat, roadmap` | `ADPA-01`, `DIAG-08`, `BIB-112` |
| `[x]` | 19 | `BL-165` | [`ADPA-03`](../tareas/ADPA-03.md) | Retirar deuda lateral ADPA lote 1 (`auditoria_capa`, `plataforma`, `rat`, `ai_copilot`) vía pasillo | `auditoria_capa, plataforma, rat, ai_copilot` | `ADPA-02` |
| `[ ]` | **20** | `BL-166` | [`ADPA-04`](../tareas/ADPA-04.md) | Retirar deuda lateral ADPA lote 2 (`riesgos_mtge`, `roadmap`) y sellar `TOPE_DEUDA_LATERAL = 0` | `riesgos_mtge, roadmap` | `ADPA-03`, `DIAG-08` |
| `[ ]` | **21** | `BL-167` | [`ADPA-05`](../tareas/ADPA-05.md) | Andamiar `domain/errores.py` por sala y secciones `#ID` en compuertas y routers compartidos | 15 salas de dominio | `ADPA-04`, `NOTIF-01`, `FIRMA-01`, `INC-01` |
| `[ ]` | **22** | `BL-169` | [`ADPA-06`](../tareas/ADPA-06.md) | Andamiar módulos y secciones `#ID` en `app_core/pasillo/` para integraciones entre salas | `pasillo_central` | `ADPA-04`, `ADPA-05` |
| `[ ]` | **20** | `BL-168` | [`ADPA-07`](../tareas/ADPA-07.md) | Sembrar secciones `#ID` en registros y componentes Frontend compartidos para eliminar contención | `plataforma, diagnostico, evidencias, biblioteca` | `FE-22`, `BIB-101`, `DIAG-09` |
| `[ ]` | **23** | `BL-170` | [`ADPA-08`](../tareas/ADPA-08.md) | Restaurar migración base de `terceros_encargados` y `transferencias_terceros` con RLS y separar salas | `terceros, transferencias` | `SEC-09`, `ADPA-01`, `ADPA-05`, `ADPA-06` |
| `[ ]` | **23** | `BL-171` | [`ADPA-09`](../tareas/ADPA-09.md) | Andamiar las salas `features/formacion` y `features/conservacion` y sus pasillos | `formacion, conservacion` | `ADPA-05`, `ADPA-06` |

---

### 🔵 OLA 2: Chasis Nativo Google Cloud, Modelos Google Gemini en Vertex AI y Cloud DLP
`¤cloud-run-perf` `¤gemini-vertex` `¤vertex-cache` `¤dlp-muestreo` `¤grado-productivo` `¤limite-peticiones` `¤observabilidad` `¤escalabilidad` `¤cache-aplicacion` `¤empaquetado-seguro` `¤versionado-despliegue` `¤api-integraciones`

> **Objetivo:** Aprovechar el bono de Google Cloud para desplegar, con **grado productivo comercial desde el origen** (Ley Fundacional 14 y §5.4 del PRD):
> * el chasis de alta concurrencia en Cloud Run (Backend Python ASGI + Frontend Next.js Standalone) y la base de datos Cloud SQL PostgreSQL 16 con RLS en 1-RTT sobre PgBouncer;
> * el acelerador CI/CD TIA determinista;
> * la observabilidad sin datos personales con alertas de SLO y de presupuesto;
> * el límite de peticiones y la cuota de IA por organización;
> * el frontend sin mapas de fuente ni secretos;
> * el escalado acotado con caché de borde;
> * el despliegue progresivo reversible y la API de integración versionada;
> * el motor de **Google Gemini (`gemini-2.5-pro`, `gemini-2.5-flash`, `text-embedding-005`) con Vertex AI Context Caching** y el descubrimiento muestreado con **Google Cloud DLP**.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Especificación SDD |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **30** | `BL-173` | [`GCP-01`](../tareas/GCP-01.md) | Chasis Cloud Run ASGI (`uvloop`), sesión RLS en 1-RTT con PgBouncer y Secret Manager ADC | `pasillo_central, operaciones` | [`especificaciones/GCP-01.md`](../especificaciones/GCP-01.md) |
| `[ ]` | **30** | `BL-174` | [`GCP-02`](../tareas/GCP-02.md) | Acelerador CI/CD con Test Impact Analysis (TIA) determinista por grafo ADPA y sharding | `pruebas, operaciones` | [`especificaciones/GCP-02.md`](../especificaciones/GCP-02.md) |
| `[ ]` | **46** | `BL-185` | [`GCP-03`](../tareas/GCP-03.md) | Migración del Frontend a Cloud Run: empaquetado standalone de Next.js 15.5+, Dockerfile multi-stage y proxy regional | `frontend, operaciones` | [`especificaciones/GCP-03.md`](../especificaciones/GCP-03.md) |
| `[ ]` | **46** | `BL-186` | [`GCP-04`](../tareas/GCP-04.md) | Migración de Base de Datos y Enrutamiento Unificado: Cloud SQL PostgreSQL 16 con RLS forzado y Cloud Load Balancing | `pasillo_central, operaciones` | [`especificaciones/GCP-04.md`](../especificaciones/GCP-04.md) |
| `[ ]` | **42** | `BL-176` | [`DLP-01`](../tareas/DLP-01.md) | Sala Descubrimiento DLP Muestreado: escaneo de archivos y tablas con Cloud DLP Sampling y validador Módulo 10 para poblar el RAT | `dlp_discovery` | [`especificaciones/DLP-01.md`](../especificaciones/DLP-01.md) |
| `[ ]` | **42** | `BL-177` | [`VTX-01`](../tareas/VTX-01.md) | Modelos **Google Gemini (`gemini-2.5-pro`, `gemini-2.5-flash`)** y **Vertex AI Context Caching** sobre el corpus normativo LOPDP/SPDP con filtro DLP Módulo 10 pre-vuelo | `regulacion_rag, ai_copilot` | [`especificaciones/VTX-01.md`](../especificaciones/VTX-01.md) |
| `[ ]` | **42** | `BL-187` | [`NORM-01`](../tareas/NORM-01.md) | Sala Inteligencia Normativa: modelos relacionales, conector HTTP resiliente para SPDP, validación SHA-256 y persistencia en GCS | `inteligencia_normativa` | [`especificaciones/NORM-01.md`](../especificaciones/NORM-01.md) |
| `[ ]` | **43** | `BL-188` | [`NORM-02`](../tareas/NORM-02.md) | Centro de Vigilancia Normativa y Resoluciones SPDP (Frontend Next.js): catálogo, filtros, visor PDF, trigger manual y bitácora | `inteligencia_normativa, frontend` | [`especificaciones/NORM-02.md`](../especificaciones/NORM-02.md) |
| `[ ]` | **43** | `BL-189` | [`NORM-03`](../tareas/NORM-03.md) | Integración HITL con Copiloto Gemini 2.5 Pro: análisis de impacto en Assessment, RAT y regeneración de Context Caching | `inteligencia_normativa, ai_copilot` | [`especificaciones/NORM-03.md`](../especificaciones/NORM-03.md) |
| `[ ]` | **21** | `BL-190` | [`SEC-13`](../tareas/SEC-13.md) | Límite de peticiones en la API por IP, usuario y organización, con tope de gasto de IA | `pasillo_central` | [`especificaciones/SEC-13.md`](../especificaciones/SEC-13.md) |
| `[ ]` | **22** | `BL-191` | [`SEC-14`](../tareas/SEC-14.md) | El frontend no publica mapas de fuente ni secretos en variables públicas | `frontend, pruebas` | [`especificaciones/SEC-14.md`](../especificaciones/SEC-14.md) |
| `[ ]` | **47** | `BL-192` | [`GCP-05`](../tareas/GCP-05.md) | Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga | `operaciones` | [`especificaciones/GCP-05.md`](../especificaciones/GCP-05.md) |
| `[ ]` | **45** | `BL-193` | [`OPS-07`](../tareas/OPS-07.md) | Observabilidad: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto | `pasillo_central, operaciones` | [`especificaciones/OPS-07.md`](../especificaciones/OPS-07.md) |
| `[ ]` | **48** | `BL-194` | [`GCP-06`](../tareas/GCP-06.md) | Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore | `pasillo_central, operaciones` | [`especificaciones/GCP-06.md`](../especificaciones/GCP-06.md) |
| `[ ]` | **47** | `BL-195` | [`GCP-07`](../tareas/GCP-07.md) | Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract) | `operaciones, pruebas` | [`especificaciones/GCP-07.md`](../especificaciones/GCP-07.md) |
| `[ ]` | **46** | `BL-196` | [`API-02`](../tareas/API-02.md) | API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256 | `pasillo_central, frontend` | [`especificaciones/API-02.md`](../especificaciones/API-02.md) |

**Entorno de pruebas en Google Cloud** (`¤entorno-pruebas`, PRD §5.5, 2026-11-05). `EP-01`…`EP-08` no dependen entre sí ni comparten archivos; `EP-04` y `EP-05` esperan los manifiestos base de `GCP-01`, `GCP-03` y `GCP-04`. `EP-09` las junta.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Especificación SDD |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **30** | `BL-197` | [`EP-01`](../tareas/EP-01.md) | Identidad del entorno y guardias de arranque del backend | `pasillo_central` | PRD §5.5 |
| `[ ]` | **45** | `BL-198` | [`EP-02`](../tareas/EP-02.md) | Aviso fijo y robots `noindex` fuera de producción | `frontend` | PRD §5.5 |
| `[ ]` | **46** | `BL-199` | [`EP-03`](../tareas/EP-03.md) | Siembra de organizaciones, evidencias y clips sintéticos | `operaciones` | PRD §5.5 |
| `[ ]` | **47** | `BL-200` | [`EP-06`](../tareas/EP-06.md) | Ciclo de una versión: migrar, desplegar el digest y reiniciar | `operaciones` | PRD §5.5 |
| `[ ]` | **48** | `BL-201` | [`EP-04`](../tareas/EP-04.md) | Proyecto, Cloud Run, IAP y presupuesto del entorno de pruebas | `operaciones` | PRD §5.5 |
| `[ ]` | **48** | `BL-202` | [`EP-05`](../tareas/EP-05.md) | Cloud SQL, buckets sin bloqueo de retención y secretos del entorno de pruebas | `operaciones` | PRD §5.5 |
| `[ ]` | **47** | `BL-203` | [`EP-07`](../tareas/EP-07.md) | Verificador del entorno y flujo de GitHub | `operaciones, pruebas` | PRD §5.5 |
| `[ ]` | **45** | `BL-204` | [`EP-08`](../tareas/EP-08.md) | El correo sale solo hacia destinatarios permitidos | `notificaciones` | PRD §5.5 |
| `[ ]` | **51** | `BL-205` | [`EP-09`](../tareas/EP-09.md) | Puesta en marcha y primer verificador en verde | `operaciones` | PRD §5.5 |
| `[ ]` | **52** | `BL-237` | [`SEC-13a`](../tareas/SEC-13a.md) | Tope total de generaciones de IA por organización, configurable por tenant | `pasillo_central` | PRD §5.6.7 |

**Demo comercial en Google Cloud** (`¤demo`, PRD §5.6, 2026-11-07). Corte ortogonal del §5.6.8: una sala dueña por ficha; lo común es el contrato de `DEMO-00`. Seguridad revisa `DEMO-00`, `DEMO-08` y `DEMO-01` antes del reparto. Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Especificación SDD |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **48** | `BL-224` | [`DEMO-00`](../tareas/DEMO-00.md) | Contrato de la sala demo: compuerta, dominio, repositorio, pasillo y migración | `demo` | PRD §5.6 |
| `[ ]` | **49** | `BL-225` | [`DEMO-08`](../tareas/DEMO-08.md) | Gancho de identidad demo en `usuario_verificado()` | `pasillo_central` | PRD §5.6 |
| `[ ]` | **49** | `BL-226` | [`DEMO-03`](../tareas/DEMO-03.md) | Siembra de la plantilla «Cooperativa Demo» con seis personas | `operaciones` | PRD §5.6 |
| `[ ]` | **54** | `BL-227` | [`DEMO-03a`](../tareas/DEMO-03a.md) | Clonar desde plantilla: organización | `organizacion` | PRD §5.6 |
| `[ ]` | **54** | `BL-228` | [`DEMO-03b`](../tareas/DEMO-03b.md) | Clonar desde plantilla: diagnóstico | `diagnostico` | PRD §5.6 |
| `[ ]` | **54** | `BL-229` | [`DEMO-03c`](../tareas/DEMO-03c.md) | Clonar desde plantilla: hoja de ruta | `roadmap` | PRD §5.6 |
| `[ ]` | **54** | `BL-230` | [`DEMO-03d`](../tareas/DEMO-03d.md) | Clonar desde plantilla: biblioteca | `biblioteca` | PRD §5.6 |
| `[ ]` | **54** | `BL-231` | [`DEMO-03e`](../tareas/DEMO-03e.md) | Clonar desde plantilla: evidencias y objetos | `evidencias` | PRD §5.6 |
| `[ ]` | **49** | `BL-232` | [`DEMO-04`](../tareas/DEMO-04.md) | Interfaz demo: «Ver como», «Terminar demo» y errores | `frontend` | PRD §5.6 |
| `[ ]` | **49** | `BL-233` | [`DEMO-05`](../tareas/DEMO-05.md) | Cloud Run Job de purga nocturna | `operaciones` | PRD §5.6 |
| `[ ]` | **51** | `BL-234` | [`DEMO-06`](../tareas/DEMO-06.md) | Prueba de que con `APP_ENV=demo` no sale ningún correo | `pruebas` | PRD §5.6 |
| `[ ]` | **51** | `BL-235` | [`DEMO-01`](../tareas/DEMO-01.md) | Persona activa y «Ver como» | `demo` | PRD §5.6 |
| `[ ]` | **52** | `BL-236` | [`DEMO-02`](../tareas/DEMO-02.md) | Ciclo de sesión y orquestador de la copia | `demo` | PRD §5.6 |
| `[ ]` | — | sin agente | [`DEMO-03f`](../tareas/DEMO-03f.md) | Clonar desde plantilla: clips (bloqueada hasta la sala) | `videovigilancia` | PRD §5.6 |
| `[ ]` | — | sin agente | [`DEMO-07`](../tareas/DEMO-07.md) | Infraestructura de la demo en Google Cloud (personas) | `operaciones` | PRD §5.6 |

---

### 🟣 OLA 3: Reventa de Bóveda Cloud Certificada, Videovigilancia LOPDP y Satélites en Go
`¤boveda-cloud` `¤videovigilancia-cctv` `¤motor-go-hibrido` `¤conservacion`

> **Objetivo:** Materializar el motor comercial de Reventa de Nube Certificada en Google Cloud Storage (`short-ttl` vs `long-retention` WORM), el Carril Forense Dual (`SHA-256` intacto + derivados `WebP`/`AVIF`/`WebM`), la gobernanza de Videovigilancia LOPDP a 15 días con *Hold Legal*, los dos satélites compilados en Go (`vault_worker` y `cctv_agent`) y el Orquestador Comercial de las 10 Dimensiones.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Especificación SDD |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **28** | `BL-172` | [`CON-01`](../tareas/CON-01.md) | Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit | `conservacion` | [`especificaciones/CON-01.md`](../especificaciones/CON-01.md) |
| `[ ]` | **42** | `BL-175` | [`BOV-01`](../tareas/BOV-01.md) | Sala Bóveda Cloud: paquetes de reventa de almacenamiento (`Inicial`, `Profesional`, `Corporativo`), cuotas de GB/Egress y aprovisionamiento Multi-Tenant | `boveda_cloud` | [`especificaciones/BOV-01.md`](../especificaciones/BOV-01.md) |
| `[ ]` | **43** | `BL-178` | [`BOV-02`](../tareas/BOV-02.md) | Bóveda Dual en Google Cloud Storage (`short-ttl` Standard vs `long-retention` Autoclass WORM) e ingesta Direct-to-GCS con Signed URLs V4 | `boveda_cloud` | [`especificaciones/BOV-02.md`](../especificaciones/BOV-02.md) |
| `[ ]` | **44** | `BL-179` | [`GOVW-01`](../tareas/GOVW-01.md) | Microservicio en Go (`services_go/vault_worker`): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run | `go_vault_worker` | [`especificaciones/GOVW-01.md`](../especificaciones/GOVW-01.md) |
| `[ ]` | **43** | `BL-180` | [`CCTV-01`](../tareas/CCTV-01.md) | Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días | `videovigilancia` | [`especificaciones/CCTV-01.md`](../especificaciones/CCTV-01.md) |
| `[ ]` | **44** | `BL-181` | [`BOV-03`](../tareas/BOV-03.md) | Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización `WebP`/`AVIF`/`WebM` | `boveda_cloud` | [`especificaciones/BOV-03.md`](../especificaciones/BOV-03.md) |
| `[ ]` | **44** | `BL-182` | [`CCTV-02`](../tareas/CCTV-02.md) | Congelamiento Forense (*Hold Legal* WORM) de clips de videovigilancia por incidente o derecho ARCOP+ y actas quincenales de destrucción SHA-256 | `videovigilancia` | [`especificaciones/CCTV-02.md`](../especificaciones/CCTV-02.md) |
| `[ ]` | **44** | `BL-183` | [`GOCA-01`](../tareas/GOCA-01.md) | Agente Edge en Go (`services_go/cctv_agent`): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS | `go_cctv_agent` | [`especificaciones/GOCA-01.md`](../especificaciones/GOCA-01.md) |
| `[ ]` | **45** | `BL-184` | [`BOV-04`](../tareas/BOV-04.md) | Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete | `boveda_cloud` | [`especificaciones/BOV-04.md`](../especificaciones/BOV-04.md) |

---

### 🟠 OLA 4: Estructura Funcional Completa de las 10 Dimensiones (Módulos Avanzados fuera del PMV)
`¤cartera` `¤alta-organizacion` `¤inventario` `¤diagnostico` `¤evidencias` `¤auditoria-programa` `¤derechos` `¤incidentes` `¤transferencias` `¤riesgos-eipd` `¤dpo-asesoria` `¤firma-electronica`

> **Objetivo:** Completar todas las capacidades de las 10 Dimensiones LOPDP que complementan el núcleo: Cartera multi-organización, Alta en 7 pasos, Inventarios ampliados, Sedes/Clientes, Papelera/Exportación, Asignación y Revisión Declarado/Verificado del Assessment, Paquetes de Inspección de Evidencias, Auditorías por Dominio y Actas por Área, Colectivos/Consentimientos, Portales Externos de Titulares y Encargados, Vulneraciones en 8 Secciones, EIPD en 8 Pasos, Consultas al DPO, Formación con Examen y Aceptación Simple con Acuse Hash.

| Estado | Tanda | Bloque | ID | Tarea Constitucional | Sala(s) ADPA | Especificación SDD |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `[x]` | 13 | `BL-96` | [`ORG-16`](../tareas/ORG-16.md) | Alta de la organización en el servidor con el asistente de 7 pasos | `organizacion, frontend` | [`especificaciones/ORG-16.md`](../especificaciones/ORG-16.md) |
| `[x]` | 13 | `BL-98` | [`FE-24`](../tareas/FE-24.md) | Tablero de la organización con las 4 dimensiones y brechas críticas | `frontend` | [`especificaciones/FE-24.md`](../especificaciones/FE-24.md) |
| `[ ]` | **24** | `BL-105` | [`DIAG-06`](../tareas/DIAG-06.md) | Comparativo de un assessment con la línea base, por dimensión y dominio | `diagnostico, frontend` | [`especificaciones/DIAG-06.md`](../especificaciones/DIAG-06.md) |
| `[ ]` | **23** | `BL-206` | [`DIAG-11`](../tareas/DIAG-11.md) | Diagnóstico de prueba y diagnóstico real: dos sellos como máximo | `diagnostico, frontend` | — |
| `[ ]` | **25** | `BL-207` | [`DIAG-12`](../tareas/DIAG-12.md) | Estados: el assessment actual a partir del diagnóstico real y la evidencia validada | `diagnostico, frontend` | — |
| `[ ]` | **24** | `BL-94` | [`EVI-01`](../tareas/EVI-01.md) | Custodia de evidencias en servidor: almacén de objetos, registro en BD y huella SHA-256 calculada en servidor | `evidencias, frontend` | [`especificaciones/EVI-01.md`](../especificaciones/EVI-01.md) |
| `[ ]` | **23** | `BL-101` | [`ORG-15`](../tareas/ORG-15.md) | Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS | `organizacion, frontend` | [`especificaciones/ORG-15.md`](../especificaciones/ORG-15.md) |
| `[ ]` | **24** | `BL-135` | [`ORG-17`](../tareas/ORG-17.md) | Inventario de activos y sistemas, soportes y personas mínimas de la organización | `organizacion, frontend` | [`especificaciones/ORG-17.md`](../especificaciones/ORG-17.md) |
| `[ ]` | **24** | `BL-104` | [`DIAG-04`](../tareas/DIAG-04.md) | El administrador asigna los dominios del assessment a encargados del diagnóstico | `diagnostico, frontend` | [`especificaciones/DIAG-04.md`](../especificaciones/DIAG-04.md) |
| `[ ]` | **22** | `BL-106` | [`DIAG-05`](../tareas/DIAG-05.md) | «No aplica» exige justificación obligatoria en el assessment | `diagnostico, frontend` | [`especificaciones/DIAG-05.md`](../especificaciones/DIAG-05.md) |
| `[ ]` | **29** | `BL-152` | [`FE-25`](../tareas/FE-25.md) | Ficha resumen de la organización fija bajo la barra superior, con las 4 dimensiones y alertas abiertas | `frontend` | [`especificaciones/FE-25.md`](../especificaciones/FE-25.md) |
| `[ ]` | **25** | `BL-107` | [`EVI-02`](../tareas/EVI-02.md) | Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito | `evidencias, frontend` | [`especificaciones/EVI-02.md`](../especificaciones/EVI-02.md) |
| `[ ]` | **25** | `BL-138` | [`ORG-18`](../tareas/ORG-18.md) | Sedes de la organización y clientes cuando actúa como encargada | `organizacion, frontend` | [`especificaciones/ORG-18.md`](../especificaciones/ORG-18.md) |
| `[ ]` | **25** | `BL-109` | [`DIAG-07`](../tareas/DIAG-07.md) | Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella | `diagnostico, frontend` | [`especificaciones/DIAG-07.md`](../especificaciones/DIAG-07.md) |
| `[ ]` | **28** | `BL-148` | [`ORG-20`](../tareas/ORG-20.md) | Papelera (archivar y restaurar) y exportación completa de los datos de la organización | `organizacion, plataforma, frontend` | [`especificaciones/ORG-20.md`](../especificaciones/ORG-20.md) |
| `[ ]` | **26** | `BL-108` | [`CAPA-03`](../tareas/CAPA-03.md) | La evidencia vencida reabre el control periódico y produce un hallazgo | `auditoria_capa` | [`especificaciones/CAPA-03.md`](../especificaciones/CAPA-03.md) |
| `[ ]` | **27** | `BL-144` | [`CAPA-04`](../tareas/CAPA-04.md) | Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción | `auditoria_capa, frontend` | [`especificaciones/CAPA-04.md`](../especificaciones/CAPA-04.md) |
| `[ ]` | **26** | `BL-143` | [`RAT-07`](../tareas/RAT-07.md) | Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares | `rat` | [`especificaciones/RAT-07.md`](../especificaciones/RAT-07.md) |
| `[ ]` | **26** | `BL-140` | [`DER-01`](../tareas/DER-01.md) | Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia | `derechos_arco, frontend` | [`especificaciones/DER-01.md`](../especificaciones/DER-01.md) |
| `[ ]` | **26** | `BL-137` | [`INC-02`](../tareas/INC-02.md) | Asistente de vulneración en 8 secciones con decisión de notificar e informes de la norma técnica | `incidentes, frontend` | [`especificaciones/INC-02.md`](../especificaciones/INC-02.md) |
| `[ ]` | **27** | `BL-141` | [`DPO-03`](../tareas/DPO-03.md) | Consultas de la organización al DPO con historial como evidencia de asesoría | `dpo_cockpit, frontend` | [`especificaciones/DPO-03.md`](../especificaciones/DPO-03.md) |
| `[ ]` | **27** | `BL-146` | [`FOR-01`](../tareas/FOR-01.md) | Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación | `formacion, frontend` | [`especificaciones/FOR-01.md`](../especificaciones/FOR-01.md) |
| `[ ]` | **27** | `BL-147` | [`MTGE-03`](../tareas/MTGE-03.md) | EIPD guiada de 8 pasos con asistente de obligatoriedad, decisión documentada e informe final | `riesgos_mtge, frontend` | [`especificaciones/MTGE-03.md`](../especificaciones/MTGE-03.md) |
| `[ ]` | **28** | `BL-151` | [`TER-01`](../tareas/TER-01.md) | Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía | `terceros, transferencias` | [`especificaciones/TER-01.md`](../especificaciones/TER-01.md) |
| `[ ]` | **28** | `BL-145` | [`DER-02`](../tareas/DER-02.md) | Portal público de solicitudes de titulares por organización, con enlace de seguimiento | `derechos_arco, frontend` | [`especificaciones/DER-02.md`](../especificaciones/DER-02.md) |
| `[ ]` | **29** | `BL-153` | [`TER-02`](../tareas/TER-02.md) | Cuestionario de garantías del encargado por portal externo, con revisión e informe | `terceros, frontend` | [`especificaciones/TER-02.md`](../especificaciones/TER-02.md) |
| `[ ]` | **29** | `BL-154` | [`FIRMA-02`](../tareas/FIRMA-02.md) | Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash | `firma_electronica, frontend` | [`especificaciones/FIRMA-02.md`](../especificaciones/FIRMA-02.md) |
| `[ ]` | **29** | `BL-155` | [`BIB-401`](../tareas/BIB-401.md) | Plantillas de la cuenta profesional: tercera capa entre la maestra y la de la organización | `biblioteca, frontend` | [`especificaciones/BIB-401.md`](../especificaciones/BIB-401.md) |
| `[x]` | 41 | `BL-160` | [`BIB-402`](../tareas/BIB-402.md) | Documentos de la organización vinculados a tratamientos, controles y tareas; aviso al cambiar un tratamiento | `biblioteca, frontend` | [`especificaciones/BIB-402.md`](../especificaciones/BIB-402.md) |

<!-- ¤adpa/ -->

---

## 3. Plan Maestro de Paralelización en 22 Tandas de 4 Bloques (`R3 = 0` Archivos en Común)
<!-- ¤adpa -->
`¤adpa` `¤roadmap` `¤arbitro`

> **Regla de Oro de Paralelización Clean-Room:** Las **85 tareas abiertas** asignables a agentes se agrupan en **22 tandas** de **máximo 4 bloques simultáneos por tanda** ($\forall k : |\text{Bloques}(k)| \le 4$), garantizando **0 archivos o secciones `#ID` en común dentro de cada tanda (`R3`)** y respetando el orden topológico estricto (`R4`).
> * **Etapa I — Desarrollo Clean-Room (15 tandas de 4 bloques = 60 bloques):** Cimiento ADPA (`DEUDA_LATERAL = 0`), Seguridad de Arranque, las 10 Dimensiones LOPDP, Bóveda Cloud, Cloud DLP, Vertex AI Context Caching, Vigilancia SPDP, Videovigilancia y Satélites en Go contra dobles locales deterministas.
> * **Etapa II — Despliegue Cloud, Grado Productivo, Entorno de Pruebas (`pruebas`) y Demo Comercial (`demo`) (7 tandas = 25 bloques):** Cutover de Cloud Run/Cloud SQL, escalado, despliegue canario, aprovisionamiento y verificación del entorno `pruebas` y clonación aislada de la Demo Comercial `demo`.

| Etapa | Tanda | Cardinalidad | Bloques en Paralelo (Máx. 4 Chats Simultáneos) | Salas ADPA Tocadas en la Tanda |
| :--- | :---: | :---: | :--- | :--- |
| **Etapa I · Clean-Room** | **20** | `4/4` | `BL-166` ([`ADPA-04`](../tareas/ADPA-04.md)), `BL-168` ([`ADPA-07`](../tareas/ADPA-07.md)), `BL-214` ([`SEC-16`](../tareas/SEC-16.md)), `BL-216` ([`ORG-21`](../tareas/ORG-21.md)) | `riesgos_mtge, roadmap, plataforma, diagnostico, evidencias, biblioteca, pasillo_central` |
| **Etapa I · Clean-Room** | **21** | `4/4` | `BL-167` ([`ADPA-05`](../tareas/ADPA-05.md)), `BL-215` ([`SEC-17`](../tareas/SEC-17.md)), `BL-115` ([`BIB-106`](../tareas/BIB-106.md)), `BL-190` ([`SEC-13`](../tareas/SEC-13.md)) | `auditoria_capa, derechos_arco, diagnostico, dpo_cockpit, evidencias, firma_electronica, incidentes, notificaciones, organizacion, rat, regulacion_rag, riesgos_mtge, roadmap, terceros, transferencias, pasillo_central, biblioteca, frontend` |
| **Etapa I · Clean-Room** | **22** | `4/4` | `BL-169` ([`ADPA-06`](../tareas/ADPA-06.md)), `BL-106` ([`DIAG-05`](../tareas/DIAG-05.md)), `BL-237` ([`SEC-13a`](../tareas/SEC-13a.md)), `BL-191` ([`SEC-14`](../tareas/SEC-14.md)) | `pasillo_central, diagnostico, frontend, pruebas` |
| **Etapa I · Clean-Room** | **23** | `4/4` | `BL-170` ([`ADPA-08`](../tareas/ADPA-08.md)), `BL-171` ([`ADPA-09`](../tareas/ADPA-09.md)), `BL-206` ([`DIAG-11`](../tareas/DIAG-11.md)), `BL-101` ([`ORG-15`](../tareas/ORG-15.md)) | `terceros, transferencias, formacion, conservacion, diagnostico, frontend, organizacion` |
| **Etapa I · Clean-Room** | **24** | `4/4` | `BL-94` ([`EVI-01`](../tareas/EVI-01.md)), `BL-104` ([`DIAG-04`](../tareas/DIAG-04.md)), `BL-105` ([`DIAG-06`](../tareas/DIAG-06.md)), `BL-135` ([`ORG-17`](../tareas/ORG-17.md)) | `evidencias, frontend, diagnostico, organizacion` |
| **Etapa I · Clean-Room** | **25** | `4/4` | `BL-107` ([`EVI-02`](../tareas/EVI-02.md)), `BL-207` ([`DIAG-12`](../tareas/DIAG-12.md)), `BL-109` ([`DIAG-07`](../tareas/DIAG-07.md)), `BL-138` ([`ORG-18`](../tareas/ORG-18.md)) | `evidencias, frontend, diagnostico, organizacion` |
| **Etapa I · Clean-Room** | **26** | `4/4` | `BL-108` ([`CAPA-03`](../tareas/CAPA-03.md)), `BL-143` ([`RAT-07`](../tareas/RAT-07.md)), `BL-137` ([`INC-02`](../tareas/INC-02.md)), `BL-140` ([`DER-01`](../tareas/DER-01.md)) | `auditoria_capa, rat, incidentes, frontend, derechos_arco` |
| **Etapa I · Clean-Room** | **27** | `4/4` | `BL-141` ([`DPO-03`](../tareas/DPO-03.md)), `BL-144` ([`CAPA-04`](../tareas/CAPA-04.md)), `BL-146` ([`FOR-01`](../tareas/FOR-01.md)), `BL-147` ([`MTGE-03`](../tareas/MTGE-03.md)) | `dpo_cockpit, frontend, auditoria_capa, formacion, riesgos_mtge` |
| **Etapa I · Clean-Room** | **28** | `4/4` | `BL-145` ([`DER-02`](../tareas/DER-02.md)), `BL-148` ([`ORG-20`](../tareas/ORG-20.md)), `BL-151` ([`TER-01`](../tareas/TER-01.md)), `BL-172` ([`CON-01`](../tareas/CON-01.md)) | `derechos_arco, frontend, organizacion, plataforma, terceros, transferencias, conservacion` |
| **Etapa I · Clean-Room** | **29** | `4/4` | `BL-153` ([`TER-02`](../tareas/TER-02.md)), `BL-152` ([`FE-25`](../tareas/FE-25.md)), `BL-154` ([`FIRMA-02`](../tareas/FIRMA-02.md)), `BL-155` ([`BIB-401`](../tareas/BIB-401.md)) | `terceros, frontend, firma_electronica, biblioteca` |
| **Etapa I · Clean-Room** | **30** | `4/4` | `BL-118` ([`BIB-110`](../tareas/BIB-110.md)), `BL-173` ([`GCP-01`](../tareas/GCP-01.md)), `BL-174` ([`GCP-02`](../tareas/GCP-02.md)), `BL-197` ([`EP-01`](../tareas/EP-01.md)) | `biblioteca, frontend, pasillo_central, operaciones, pruebas` |
| **Etapa I · Clean-Room** | **42** | `4/4` | `BL-175` ([`BOV-01`](../tareas/BOV-01.md)), `BL-176` ([`DLP-01`](../tareas/DLP-01.md)), `BL-177` ([`VTX-01`](../tareas/VTX-01.md)), `BL-187` ([`NORM-01`](../tareas/NORM-01.md)) | `boveda_cloud, dlp_discovery, regulacion_rag, ai_copilot, inteligencia_normativa` |
| **Etapa I · Clean-Room** | **43** | `4/4` | `BL-178` ([`BOV-02`](../tareas/BOV-02.md)), `BL-180` ([`CCTV-01`](../tareas/CCTV-01.md)), `BL-188` ([`NORM-02`](../tareas/NORM-02.md)), `BL-189` ([`NORM-03`](../tareas/NORM-03.md)) | `boveda_cloud, videovigilancia, inteligencia_normativa, frontend, ai_copilot` |
| **Etapa I · Clean-Room** | **44** | `4/4` | `BL-179` ([`GOVW-01`](../tareas/GOVW-01.md)), `BL-181` ([`BOV-03`](../tareas/BOV-03.md)), `BL-182` ([`CCTV-02`](../tareas/CCTV-02.md)), `BL-183` ([`GOCA-01`](../tareas/GOCA-01.md)) | `go_vault_worker, boveda_cloud, videovigilancia, go_cctv_agent` |
| **Etapa I · Clean-Room** | **45** | `4/4` | `BL-184` ([`BOV-04`](../tareas/BOV-04.md)), `BL-193` ([`OPS-07`](../tareas/OPS-07.md)), `BL-198` ([`EP-02`](../tareas/EP-02.md)), `BL-204` ([`EP-08`](../tareas/EP-08.md)) | `boveda_cloud, pasillo_central, operaciones, frontend, notificaciones` |
| **Etapa II · Cloud / Pruebas / Demo** | **46** | `4/4` | `BL-185` ([`GCP-03`](../tareas/GCP-03.md)), `BL-186` ([`GCP-04`](../tareas/GCP-04.md)), `BL-196` ([`API-02`](../tareas/API-02.md)), `BL-199` ([`EP-03`](../tareas/EP-03.md)) | `frontend, operaciones, pasillo_central` |
| **Etapa II · Cloud / Pruebas / Demo** | **47** | `4/4` | `BL-192` ([`GCP-05`](../tareas/GCP-05.md)), `BL-195` ([`GCP-07`](../tareas/GCP-07.md)), `BL-200` ([`EP-06`](../tareas/EP-06.md)), `BL-203` ([`EP-07`](../tareas/EP-07.md)) | `operaciones, pruebas` |
| **Etapa II · Cloud / Pruebas / Demo** | **48** | `4/4` | `BL-194` ([`GCP-06`](../tareas/GCP-06.md)), `BL-201` ([`EP-04`](../tareas/EP-04.md)), `BL-202` ([`EP-05`](../tareas/EP-05.md)), `BL-224` ([`DEMO-00`](../tareas/DEMO-00.md)) | `pasillo_central, operaciones, demo` |
| **Etapa II · Cloud / Pruebas / Demo** | **49** | `4/4` | `BL-225` ([`DEMO-08`](../tareas/DEMO-08.md)), `BL-226` ([`DEMO-03`](../tareas/DEMO-03.md)), `BL-232` ([`DEMO-04`](../tareas/DEMO-04.md)), `BL-233` ([`DEMO-05`](../tareas/DEMO-05.md)) | `pasillo_central, operaciones, frontend` |
| **Etapa II · Cloud / Pruebas / Demo** | **50** | `4/4` | `BL-227` ([`DEMO-03a`](../tareas/DEMO-03a.md)), `BL-228` ([`DEMO-03b`](../tareas/DEMO-03b.md)), `BL-229` ([`DEMO-03c`](../tareas/DEMO-03c.md)), `BL-230` ([`DEMO-03d`](../tareas/DEMO-03d.md)) | `organizacion, diagnostico, roadmap, biblioteca` |
| **Etapa II · Cloud / Pruebas / Demo** | **51** | `4/4` | `BL-231` ([`DEMO-03e`](../tareas/DEMO-03e.md)), `BL-234` ([`DEMO-06`](../tareas/DEMO-06.md)), `BL-235` ([`DEMO-01`](../tareas/DEMO-01.md)), `BL-205` ([`EP-09`](../tareas/EP-09.md)) | `evidencias, pruebas, demo, operaciones` |
| **Etapa II · Cloud / Pruebas / Demo** | **52** | `1/4` | `BL-236` ([`DEMO-02`](../tareas/DEMO-02.md)) | `demo` |

<!-- ¤adpa/ -->
