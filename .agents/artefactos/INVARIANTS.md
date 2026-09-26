# Catálogo Central de Invariantes y Leyes Inmutables de Plataforma LOPDP 360
`¤invariantes`
## Fuente Única de Verdad (SSOT) de Reglas Absolutas del Negocio, Cumplimiento y Arquitectura

> **REGISTRO CANÓNICO DE INVARIANTES:**
> Cada invariante define una ley inviolable que el código fuente, la lógica de negocio y las pruebas físicas ejecutables deben preservar bajo cualquier condición ($\neg R$). Cada ley está anclada a su **Rastro de Doctrina (`¤`)** y a su **Invariante Coercitiva (`¤¦`)**.

---

## 1. 🏛️ Catálogo de Invariantes Activas

| Código Invariante | Nombre Formal de la Ley | Rastro de Doctrina (`¤`) | Invariante Coercitiva (`¤¦`) | Sala / Módulo | Verificación Física Observable |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `INV_LOPDP_DPO_INDEPENDENCE` | Independencia Operativa y SoD del DPO | `¤dpo-cockpit` `¤dpo-independencia` | `¤¦dpo` | `features/dpo_cockpit/` | Prohibición estricta en base de datos y UI de asignar roles de implementador o dueño de control al usuario con rol DPO. |
| `INV_LOPDP_EVIDENCE_BEFORE_COMPLIANCE` | Precondición de Evidencia para Conformidad | `¤evidencias` `¤implementacion` | `¤¦evidencias` | `features/evidencias/` | Ningún control puede marcarse con estado "Conforme" o nivel de madurez $\ge 2$ sin al menos una evidencia documental válida asociada ($E1+$) o rationale explícito. |
| `INV_LOPDP_COMPLIANCE_GRAPH_SSOT` | Una Sola Fuente de Verdad (Compliance Graph) | `¤rat` `¤implementacion` | `¤¦rat` | `features/rat/` | Las actividades de tratamiento del RAT alimentan unívocamente la matriz de riesgos, transferencias, EIPD y avisos; cero duplicación de matrices paralelas. |
| `INV_LOPDP_60MIN_TIMEBOX_LIMIT` | Cota Superior de Diagnóstico Inicial (Límite 80 Preguntas) | `¤diagnostico-motor` | `¤¦diagnostico` | `features/diagnostico/` | La interfaz del diagnóstico rápido nunca muestra más de 80 preguntas en una sesión. Ruta operativa típica $\le 68$ mediante salto condicional. |
| `INV_LOPDP_MULTIDIMENSIONAL_METRICS` | Cuadratura Multidimensional (No Dilución de Brechas) | `¤diagnostico-scoring` | `¤¦diagnostico` | `features/scoring/` | El sistema debe mostrar por separado: Madurez SPDP (0-3), Estado de Conformidad Jurídica, Cobertura de Evidencia y Riesgo Residual. Prohibido unificar en un solo porcentaje engañoso. |
| `INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER` | Determinismo de Tratamiento a Gran Escala | `¤mtge-granescala` `¤riesgos-eipd` | `¤¦riesgos` | `features/riesgos/` | Si un tratamiento supera el umbral MTGE o cae en casos directos normativos, se activan forzosamente como obligatorios la EIPD previa y el DPO. |
| `INV_LOPDP_INCIDENT_TIMELOCK` | Reloj Normativo de Incidentes de Seguridad | `¤incidentes` | `¤¦incidentes` | `features/incidentes/` | Trazabilidad del cronómetro legal para notificaciones a la SPDP y CSIRT nacional conforme a la Ley de Ciberseguridad 2026. |
| `INV_LOPDP_AI_RAG_STRICT_CITATION` | Anclaje Normativo Estricto de IA (No Alucinación) | `¤copiloto-ia` `¤regulation-code` | `¤¦copiloto-ia` | `features/copiloto_ia/` | Toda respuesta o sugerencia del Copiloto IA debe incluir cita expresa a la fuente oficial, artículo y versión. Si no hay fuente, declara incertidumbre ("No source / No answer"). |
| `INV_LOPDP_TENANT_BULKHEAD` | Aislamiento Criptográfico y Lógico Multi-Tenant | `¤seguridad-tenant` `¤adpa` | `¤¦seguridad-tenant`| `app_core/` | Pruebas de integración garantizan que ningún tenant puede leer o consultar datos, evidencias o embeddings vectoriales de otra organización. |
| `INV_LOPDP_UI_ANTIGRAVITY_CURSOR` | Ergonomía Frontend tipo IDE (Command Palette & Split Panes)| `¤frontend-ide` | `¤¦frontend-ide` | `frontend/` | Interfaz limpia, minimalista, soporte de temas Dark/Light, atajo global `Ctrl+K` para navegación instantánea y visualización de alta densidad sin recargas lentas. |
| `INV_LOPDP_REGULATION_AS_CODE_DIFF` | Versionado Inmutable de Corpus y Análisis de Impacto | `¤regulation-code` | `¤¦regulacion` | `features/regulacion/` | Las modificaciones de leyes o resoluciones generan un diff estructurado de impacto en clientes sin sobrescribir el historial de auditorías pasadas. |
| `INV_LOPDP_PRUNING_TREE_ANTECEDENCE` | Antecedencia Paramétrica y Poda Ontológica | `¤diagnostico-motor` `¤diagnostico` | `¤¦diagnostico` | `frontend/src/store/` | La Ficha Organizacional se parametriza y consolida en una pestaña antecedente independiente antes de instanciar el cuestionario diagnóstico ($\text{Root}(\mathcal{T}_{\text{poda}}) \prec \mathcal{Q}_{\text{diag}}$). |
| `INV_LOPDP_EVIDENCE_DOMAIN_PURGE` | Aislamiento Transaccional y Purga de Evidencias Multidominio | `¤evidencias` `¤diagnostico` | `¤¦evidencias` | `frontend/src/store/` | Al conmutar el selector normativo, se purga de forma atómica e irreversible el arreglo de evidencias y se activa la whitelist estricta por extensión de archivo. |
| `INV_LOPDP_UI_ACHROMATIC_INVERTED_HIERARCHY` | Jerarquía Tonal Invertida y Neutralidad Acromática | `¤frontend-ide` | `¤¦frontend-ide` | `frontend/src/components/` | Componentes estructurales en escala acromática neutra (`#0a0a0c`, `#141417`, `#26262b`), periferia con menor luminancia, y saturación cromática reservada para señales semánticas binarias (`#00c853`, `#ff1744`) y CTAs. |
| `INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10` | Validación Notarial Determinista Módulo 10 de Cédula | `¤seguridad-tenant` `¤copiloto-ia` | `¤¦seguridad-tenant`| `app_core/` | Detección y redacción preventiva obligatoria de números de cédula ecuatoriana que cumplan provincia, tercer dígito y checksum de coeficientes alternados antes de toda inferencia RAG. |

