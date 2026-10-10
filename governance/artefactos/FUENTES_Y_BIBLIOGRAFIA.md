# Mapa de Linaje Epistémico, Fuentes y Bibliografía
`¤fuentes`
## Fuente Única de Verdad (SSOT) de Fundamentación Jurídica, Normativa y Tecnológica

> **HEAD DE ATENCIÓN DE GOBERNANZA AGÉNTICA (NIDO CENTRAL DE DESARROLLO):**
> Este documento es el **Catálogo Central de Trazabilidad Externa**. Registra y resguarda el linaje normativo del Ecuador, estándares internacionales y fuentes de ingeniería de software que fundamentan la **Plataforma LOPDP 360**. Cada fuente está vinculada a su respectivo rastro estigmérgico (`¤`).

---

## 1. ⚖️ Fuentes Normativas Primarias del Ecuador

### F01 · Constitución de la República del Ecuador
`¤legitimacion` `¤derechos`
* **Publicación:** Registro Oficial 449, 20-oct-2008 (con reformas vigentes).
* **Unidades clave:**
  * **Art. 66 numeral 19:** Derecho a la protección de datos de carácter personal (acceso, decisión, autorización y tutela).
  * **Art. 92:** Acción de Hábeas Data.
* **Aplicación en el sistema:** Base constitucional para el ejercicio de derechos y límites a la potestad estatal y privada.

### F02 · Ley Orgánica de Protección de Datos Personales (LOPDP)
`¤implementacion` `¤rat` `¤dpo-cockpit`
* **Publicación:** Registro Oficial, Quinto Suplemento 459, 26-may-2021.
* **Unidades clave:**
  * **Art. 10–12:** Principios de protección de datos (lealtad, transparencia, finalidad, minimización, conservación, seguridad, responsabilidad proactiva).
  * **Art. 7–9:** Bases de legitimación del tratamiento.
  * **Art. 21–33:** Derechos de los titulares (Acceso, Eliminación, Rectificación, Oposición, Portabilidad, etc.).
  * **Art. 41–46:** Medidas de seguridad y notificación de vulneraciones.
  * **Art. 47–50:** Delegado de Protección de Datos (designación, funciones, independencia).
* **Aplicación en el sistema:** Núcleo de requisitos legales mapeados al Compliance Graph.

### F03 · Reglamento General a la LOPDP (RGLOPDP)
`¤implementacion` `¤dpo-independencia`
* **Publicación:** Decreto Ejecutivo 904; Registro Oficial, Tercer Suplemento 435, 13-nov-2023.
* **Aplicación en el sistema:** Procedimientos operativos, condiciones de representación, plazos de respuesta a derechos e independencia del DPO.

### F04 · Guía de Gestión de Riesgos y EIPD (Versión 2 - 2026)
`¤riesgos-eipd`
* **Emisor:** Superintendencia de Protección de Datos Personales (SPDP).
* **Aplicación en el sistema:** Metodología oficial de análisis de riesgos orientada a derechos y libertades. Establece la no obligatoriedad de cuestionarios cerrados (Anexo p. 75), permitiendo que la plataforma defina su modelo ágil de diagnóstico.

### F05 · Guía de Protección de Datos desde el Diseño y por Defecto
`¤diagnostico-scoring` `¤privacy-gate`
* **Emisor:** SPDP, 21-oct-2025.
* **Unidades clave:** Capítulo 3, Tabla 1 (p. 17) y Tabla 4 (p. 20). Ejes `DevPrivOps`, `DevSecOps` y `DevRiskOps`.
* **Aplicación en el sistema:** Escala de madurez recomendada (0: Caótico, 1: Implícito, 2: Temprano explícito, 3: Maduro explícito).

### F06 · Resolución SPDP-SPD-2025-0028-R (Reglamento del DPD/DPO)
`¤dpo-cockpit` `¤dpo-independencia`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Delimitación formal de responsabilidades, casos de designación obligatoria, prohibición de conflicto de interés y régimen de independencia institucional.

### F07 · Resolución SPDP-SPD-2025-0006-R (Cláusulas Contractuales)
`¤transferencias`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Obligatoriedad de incorporar cláusulas específicas de protección de datos en contratos entre responsables y encargados de tratamiento en Ecuador.

### F08 · Resolución SPDP-SPD-2025-0030-R (Reglamento de Anonimización y Eliminación)
`¤conservacion`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Parámetros técnicos para la seudonimización, anonimización irreversible, bloqueo y disposición final de datos personales.

### F09 · Resolución SPDP-SPD-2025-0041-R (Interés Legítimo)
`¤legitimacion`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Parámetros para la prueba de ponderación de interés legítimo (test de idoneidad, necesidad y proporcionalidad).

### F10 · Resolución SPDP-SPD-2026-0004-R (Norma General de Transferencias)
`¤transferencias`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Requisitos de debida diligencia y archivo documental mínimo de 3 años para transferencias nacionales e internacionales de datos personales.

### F11 · Resolución SPDP-SPD-2026-0005-R (Tratamiento a Gran Escala - MTGE)
`¤mtge-granescala`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Algoritmo paramétrico de cálculo MTGE (número de titulares, volumen, datos sensibles, permanencia, alcance geográfico) y supuestos directos de calificación.

### F12 · Resolución SPDP-SPD-2026-0009-R (Garantía de Derechos en Sistemas de IA)
`¤copiloto-ia` `¤riesgos-eipd`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Obligaciones de transparencia algorítmica, EIPD para sistemas de IA y registro obligatorio en el RAT.

### F13 · Ley Orgánica para el Fortalecimiento de la Ciberseguridad
`¤incidentes`
* **Publicación:** Registro Oficial, Quinto Suplemento 290, 22-may-2026.
* **Unidades clave:** Art. 14 (reforma al artículo 43 de la LOPDP sobre notificación de incidentes).
* **Aplicación en el sistema:** Reloj normativo y sincronización de avisos a la SPDP y CSIRT nacional ante brechas de seguridad.

### F14 · Resoluciones y Doctrina Oficial SPDP (2024–2026)
`¤regulation-code`
* **Repositorio:** Portal oficial de resoluciones de la SPDP (`https://spdp.gob.ec/resoluciones2/`).
* **Aplicación en el sistema:** Base viva para el motor "Regulation as Code".

---

## 2. 🌍 Estándares Internacionales y Metodológicos

### F15 · ISO/IEC 27002:2022 & ISO/IEC 27701:2019
`¤evidencias` `¤adpa`
* **Controles:** Seguridad de la información, ciberseguridad y extensión de privacidad para PIMS.
* **Aplicación en el sistema:** Catálogo secundario de controles de referencia técnica (etiquetado como buena práctica, sin confundir con obligación legal directa).

### F16 · Modelos para Cálculo de Multas Administrativas SPDP
`¤riesgos-eipd`
* **Emisor:** SPDP.
* **Aplicación en el sistema:** Calibración de impacto económico y riesgo sancionatorio para priorización en el mapa de calor de riesgos.

### F17 · European Commission / EDIH — Digital Maturity Assessment Tool (DMAT)
`¤diagnostico`
* **Benchmark:** Evaluación asistida guiada en una sesión de 60 minutos para pymes.
* **Aplicación en el sistema:** Justificación metodológica para el límite de tiempo y el corte operativo de preguntas visibles.

### F18 · Reglamento (UE) 2016/679 (RGPD) — Referencia de Derecho Comparado
`¤diagnostico` `¤diagnostico-motor`
* **Publicación:** Diario Oficial de la Unión Europea L 119, 4-may-2016.
* **Unidades clave:** Art. 24(1) (medidas apropiadas según naturaleza, alcance, contexto, fines y riesgo del tratamiento); Art. 30(5) (exención condicionada del registro de actividades para organizaciones de menos de 250 personas); Considerando 13 (atención a la situación específica de micro, pequeñas y medianas empresas).
* **Aplicación en el sistema:** Evidencia de derecho comparado de que la protección de datos gradúa las obligaciones por escala y riesgo; sustenta la poda del cuestionario por talla (Aporte 53). Es una fuente comparada: no sustituye ni interpreta la LOPDP, cuya gradación por tamaño no se contrastó en la sesión.

### F19 · ISO 19011:2018 — Directrices para la Auditoría de Sistemas de Gestión
`¤evidencias` `¤diagnostico-scoring`
* **Emisor:** ISO (Organización Internacional de Normalización), 3.ª ed., 2018.
* **Aplicación en el sistema:** Criterio de que la evidencia de auditoría ha de ser verificable; fundamenta el modo de cálculo "verificado" y el sellado de solo lo demostrado (Aporte 49). Es una guía de auditoría, no un estándar de certificación.

---

## 3. 🛠️ Benchmarking de Herramientas de Mercado

* **Global Suite:** Referente en cruce de matrices normativas ISO vs locales y gestión de continuidad de negocio.
* **Novoser:** Referente en trazabilidad de tickets, workflows de auditoría y gestión de incidentes con SLA.
* **Pirani (Pirámid):** Referente en UX minimalista y ergonomía de matrices de riesgo accesibles para no expertos en LATAM.
* **Isotools:** Referente en automatización de tareas periódicas, gestión documental y seguimiento de comités CAPA.
* **Odoo (OCA - Odoo Community Association):** Referente en arquitectura de datos relacional abierta, donde una entidad maestra (*Master Record / Partner Record*) centraliza y propaga el estado hacia todos los módulos satélite sin duplicación.
* **SMARTCIDI (2026):** *Matriz de Madurez del SGPDP* (`Assessment_Madurez_SGPDP_COAC_SMARTCIDI (2).xlsx`) y *Reporte Assessment SGPDP COAC* (15-sep-2026). Referente metodológico de las 10 dimensiones ponderadas, del nivel efectivo `MIN(Nivel asignado, Evidencia+1)`, del riesgo `(5-Nivel efectivo)×Criticidad` y del ajuste de nivel por controles estructurales (Aporte 48). Fuente interna: el mecanismo de sus fórmulas no se auditó celda a celda.

---

## 4. 💻 Fundamentación Científica de Arquitectura, Cognición y Seguridad

* **David L. Parnas (1972):** *«On the Criteria to Be Used in Decomposing Systems into Modules»*, CACM. Criterios de descomposición y ocultamiento de información para salas ADPA.
* **Michael T. Nygard (2007/2018):** *«Release It!»*. Patrón Bulkhead (Mamparos Estancos) para contención de fallas entre subsistemas.
* **Martin Kleppmann et al. (2019):** *«Local-First Software: You Own Your Data, in Spite of the Cloud»*. Persistencia y soberanía de datos del tenant.
* **John Sweller (1988):** *«Cognitive Load During Problem Solving: Effects on Learning»*, Cognitive Science, 12(2), pp. 257–285. Teoría de la Carga Cognitiva que fundamenta el timebox de 60 minutos y la cota superior estricta de $N \le 80$ preguntas visibles en diagnóstico.
* **Ravi Sandhu, David Ferraiolo, Richard Kuhn (2000):** *«The NIST Model for Role-Based Access Control: Toward a Unified Standard»*, ACM Workshop on RBAC. Formalización matemática de Separación de Obligaciones (Separation of Duties - SoD) estática y dinámica para la independencia del DPO.
* **The Open Graph Protocol (2010 / W3C & RFC 5988):** Especificación de metadatos estructurados web para inferencia semántica y pre-clasificación de recursos en clientes sin motor JavaScript.
* **Antigravity / Cursor / Linear Ergonomics (2023–2026):** Paradigma de interfaces de alta densidad, interacción por teclado vía Command Palette (`Ctrl+K`), Split Panes contextuales y latencia submilisegundo sin sobrecarga visual.
* **Edward R. Tufte (1990):** *«Envisioning Information»*, Graphics Press. Principios de *Data-Ink Ratio* y reducción de ruido cromático en sistemas visuales de alta densidad de datos.
* **Kurt Koffka (1935):** *«Principles of Gestalt Psychology»*, Harcourt, Brace. Leyes de segregación perceptiva, contraste figura-fondo y jerarquía visual en interfaces de usuario.
* **Stuart Russell & Peter Norvig (2020):** *«Artificial Intelligence: A Modern Approach»* (4th ed.), Pearson. Teoría de poda en árboles de decisión y optimización de espacios de búsqueda condicionales.
* **Edsger W. Dijkstra (1959):** *«A Note on Two Problems in Connexion with Graphs»*, Numerische Mathematik, 1, pp. 269–271. Precedencia topológica y ordenación causal en grafos dirigidos.
* **Dirección General de Registro Civil, Identificación y Cedulación del Ecuador:** Norma Técnica Notarial de Validación de Cédula de Identidad Ciudadana mediante Algoritmo Módulo 10 Canónico.
* **W3C Web Content Accessibility Guidelines (WCAG 2.2 - 2023):** Criterios de contraste no textual (1.4.11) y contraste mínimo (1.4.3) para entornos analíticos prolongados.
* **William E. Hick (1952) & Ray Hyman (1953):** *«On the rate of gain of information»* (Quarterly Journal of Experimental Psychology) / *«Stimulus information as a determinant of reaction time»* (Journal of Experimental Psychology). Ley de Hick-Hyman sobre tiempo logarítmico de toma de decisiones ante alternativas múltiples, fundamento de la Command Palette universal (`Ctrl+K` vía `cmdk`).
* **Paul M. Fitts (1954):** *«The information capacity of the human motor system in controlling the amplitude of movement»*, Journal of Experimental Psychology. Ley de Fitts sobre reducción de distancia y latencia motora ($D \to 0$) mediante interfaces por teclado y paneles elásticos contextuales (`react-resizable-panels`).
* **David Harel (1987):** *«Statecharts: A visual formalism for complex systems»*, Science of Computer Programming, 8(3), pp. 231–274. Formalismo matemático de máquinas de estados concurrentes y jerárquicas que fundamenta la modelación estricta de SLAs en derechos ARCO+ y relojes de incidentes (XState); también fundamenta que regiones concurrentes reaccionen por difusión a una transición de estado compartido con independencia de cuál las provocó (Aporte 74).
* **Jakob Nielsen (1993):** *«Usability Engineering»*, Morgan Kaufmann. Heurísticas de visibilidad del estado del sistema, diseño preventivo de errores (Poka-Yoke) y aceleradores de teclado en interfaces analíticas.
* **Peter C. Fishburn (1974) & Amos Tversky (1972):** *«Lexicographic Orders, Utilities and Decision Rules»* (Management Science) / *«Elimination by Aspects: A Theory of Choice»* (Psychological Review). Formalización de órdenes no compensatorios y bloqueo jerárquico lexicográfico, base matemática de la Cuadratura Multidimensional (Doctrina 4) donde una brecha crítica invalida promedios aritméticos.
* **Ralph C. Merkle (1987) & NIST FIPS PUB 180-4 (2015):** *«A Digital Signature Based on a Conventional Encryption Function»* / *«Secure Hash Standard (SHS) - SHA-256»*. Teoría de libros mayores inmutables y sellado criptográfico determinista para bitácoras y snapshots de auditoría legal (Doctrina 10).
* **Guillermo Rauch et al. / Vercel Core Team (2024–2026):** *«React Server Components & Next.js App Router Architecture: Asynchronous Cookies and Streaming HTTP Boundaries»*. Fundamentación del renderizado híbrido sin destello (Zero-FOUC) mediante inyección server-side de preferencias antes del primer paquete TCP.
* **OWASP Foundation (2023):** *«OWASP Top 10 for Large Language Model Applications — LLM01: Prompt Injection, LLM06: Sensitive Information Disclosure»*, versión 1.1. Marco canónico de seguridad para pipelines de inferencia LLM; base del Teorema del Liminal DLP Pre-Inferencia y del filtrado obligatorio de PII antes de cruzar la frontera de inferencia.
* **Jerome H. Saltzer & Michael D. Schroeder (1975):** *«The Protection of Information in Computer Systems»*, Proceedings of the IEEE, vol. 63, no. 9. Principios clásicos de seguridad informática — en especial *Fail-Safe Defaults* (valores por defecto seguros) — fundamento de la normalización bidireccional con falla segura en Server Actions de GRC.
* **Barbara Liskov & Jeannette M. Wing (1994):** *«A Behavioral Notion of Subtyping»*, ACM Transactions on Programming Languages and Systems (TOPLAS), vol. 16, no. 6. Principio de Sustitución de Liskov como garantía formal de integridad semántica en jerarquías de tipos para entidades jurídicas tipadas (Teorema 22).
* **Luca Cardelli & Peter Wegner (1985):** *«On Understanding Types, Data Abstraction, and Polymorphism»*, ACM Computing Surveys, vol. 17, no. 4. Fundamentos de la teoría de tipos estáticos aplicados a la verificación de conformidad legal en sistemas GRC con TypeScript.
* **John Forbes Nash Jr. (1950):** *«Equilibrium Points in n-Person Games»*, Proceedings of the National Academy of Sciences, vol. 36, no. 1, pp. 48–49. Fundamento de la Teoría de Juegos y contratos de equilibrio cooperativo, base formal del Contrato Bilateral Agéntico (CBA) entre cliente-principal y agente-IA (Teorema 21).
* **TypeScript Team — Microsoft (2012–2026):** *«TypeScript: Typed JavaScript at Any Scale»* (Documentación oficial y GitHub — github.com/microsoft/TypeScript). Fundamento del tipado estricto como árbitro exógeno sintáctico en plataformas GRC y sistemas de cumplimiento normativo (Teorema 22, Aporte 19).
* **Node.js Core Team (2022–2026):** *«node:crypto — randomUUID()»*, Documentación oficial Node.js (nodejs.org/api/crypto.html). UUID v4 criptográfico como identificador inmutable de tickets ARCO+ generado exclusivamente en el servidor (Aporte 18 — invariante de no-suplantación de identidad de solicitudes).
* **ECMAScript 2022 / ECMA-262, 13th ed.:** *«Temporal Proposal / Date API»*. Fundamento del motor de cómputo de días laborables (excluyendo sábados y domingos) para el cálculo del SLA de 15 días laborables del Art. 37 LOPDP (Aporte 18 — calcularFechaLimiteSLA).
* **Python Software Foundation (2026):** *«ast — Abstract Syntax Trees»*. Documentación de la fragilidad del parser frente a codificaciones híbridas y marcas BOM en análisis estático. (Aporte 21).
* **Guía de Arquitectura de Sistemas de IA Confiables (2025):** *«Zero-Hallucination Patterns in RAG»*. Patrones de limitación heurística y fallback estricto en motores de inferencia. (Aporte 22).
* **Especificación PDF WORM (Write Once, Read Many):** Fundamentos criptográficos y de formato para inmutabilidad documental en expedientes legales y notariado digital. (Aporte 23).
* **Tiangolo / FastAPI (2026):** *«Testing FastAPI with Async Databases»*. Metodologías canónicas de Dependency Injection y mocking asíncrono. (Aporte 24).
* **PEP 567 (Python Software Foundation):** *«Context Variables»*. Fundamento nativo para el aislamiento de variables de entorno por corrutina, base del Teorema 24 (Async RLS ContextVar).
* **GitHub Actions Architecture:** *«Fail-Fast CI/CD Patterns»*. Enforzamiento del Contrato Bilateral Agéntico en la nube (Aporte 25).
- [IFRS-18] IASB (International Accounting Standards Board). *NIIF 18: Presentación e Información a Revelar en los Estados Financieros*.
* **IETF RFC 3161 (2001):** *«Internet X.509 Public Key Infrastructure Time-Stamp Protocol (TSP)»*. Sellado de tiempo criptográfico de raíces de Merkle para no-repudio legal ante autoridades de control (Teorema 27, Aporte 40).
* **Bertrand Meyer (1992):** *«Applying 'Design by Contract'»*, Computer, vol. 25, no. 10, pp. 40–51. Fundamentación formal del endurecimiento contractual (*Contract Tightening*) y la sincronización causal de asertos de integración en arquitecturas con arbitraje exógeno físico (Teorema 28, Aporte 41).
* **Patrick Lewis et al. (2020):** *«Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks»*, NeurIPS 2020. Fundamento de la intercepción de incerteza y delimitación de corpus cerrado para la erradicación de alucinaciones en RAG legal (Aporte 41).
* **ISO/IEC 19005-1:2005 (PDF/A-1):** *«Document management — Electronic document file format for long-term preservation»*. Principios de inmutabilidad documental, sellado WORM de metadatos normativos UTC y streaming en memoria volátil (Aporte 23, Aporte 36).
* **Carl Hewitt, Peter Bishop, Richard Steiger (1973):** *«A Universal Modular ACTOR Formalism for Artificial Intelligence»*, IJCAI. Fundamentación matemática del Modelo de Actores y comunicación por paso de mensajes asíncronos. Base teórica del Desacoplamiento de Subsistemas Algorítmicos mediante Enjambres Agénticos (ADPA-Swarm Pattern, Aporte 34), permitiendo aislamiento riguroso y concurrencia sin estado compartido.
* **Dan Abramov, React Core Team (2015-2026):** *«Flux Architecture / Redux / Zustand»*. Teoría del flujo unidireccional de datos y mutaciones inmutables de estado global. Fundamenta el Aporte 35 (Reactividad Contable en Vivo), eliminando inconsistencias en el DOM mediante proyecciones directas de una Fuente Única de Verdad (SSOT) reactiva.
* **NIST Special Publication 800-88 Revision 1 (2014):** *«Guidelines for Media Sanitization»*. Directrices federales sobre la retención y purgado seguro de datos. Inspira la arquitectura Zero-Trace (Aporte 36) al evitar por completo la escritura en disco (Clear/Purge) de artefactos WORM, mitigando el riesgo intrínseco de recuperación de datos (Data Remanence) en la generación de reportes financieros.
* **Vercel / Guillermo Rauch (2020+):** *«SWR: React Hooks for Data Fetching (RFC 5861)»*. Fundamento del patrón Stale-While-Revalidate implementado en el AI Copilot Tracker para garantizar reactividad en vivo en los flujos de remediación GRC (Aporte 37).
* **React Core Team (2022+):** *«React 18 Architecture: Hydration and Server Components»*. Base teórica que exige la disociación estricta del estado de cliente persistido frente a pasadas de servidor (SSR), validando formalmente el mecanismo de *Skeleton-mounted* del Teorema 26.
* **Ralph C. Merkle (1987):** *«A Digital Signature Based on a Conventional Encryption Function»*, Advances in Cryptology — CRYPTO '87, Springer LNCS 293, pp. 369–378. Árboles de Merkle para agregación logarítmica y no-repudio de secuencias temporales inmutables de snapshots normativos (Teorema 27, Aporte 40).
* **John E. Hopcroft, Rajeev Motwani, Jeffrey D. Ullman (2001):** *«Introduction to Automata Theory, Languages, and Computation»* (2nd ed.), Addison-Wesley. Teoría de autómatas, gramáticas libres de contexto (CFG) y análisis sintáctico determinista. Base matemática de la decodificación restringida por gramática (Grammar-Constrained Decoding) para forzar salidas de modelos generativos a esquemas Pydantic exactos (Teorema 29).
* **Brandon T. Willard & Rémi Louf (2023):** *«Efficient Guided Generation for Large Language Models»*, arXiv:2307.09702. Formalización del guiado por autómatas finitos y gramáticas en la distribución de logits para garantizar que $P(t \notin \mathcal{L}(\mathcal{G})) = 0$, base de Structured Outputs en APIs de inferencia moderna (Teorema 29).
* **OpenAI API Architecture Team (2024):** *«Introducing Structured Outputs in the API»* (Technical Report & Documentation, openai.com). Especificación técnica del soporte nativo de JSON Schema estricto y parsing tipado Pydantic (`beta.chat.completions.parse`), eliminando alucinaciones estructurales en pipelines de producción (Teorema 29, Aporte 42).
* **Michael T. Nygard (2018):** *«Release It! Design and Deploy Production-Ready Software»* (2nd ed.), Pragmatic Bookshelf. Patrones de estabilidad, *Fail-Safe Defaults* y *Graceful Degradation* para subsistemas de inferencia con fallbacks heurísticos locales en ausencia de servicios externos o credenciales (Aporte 42).
* **IASB (International Accounting Standards Board - 2024):** *«IFRS 18: Presentation and Disclosure in Financial Statements»*. Requisitos de presentación y revelación contable, fundamento del polimorfismo de prompts de auditoría GRC (Aporte 43) y de la reactividad contable en vivo (Aporte 35).
* **Latanya Sweeney (2002):** *«k-anonymity: A model for protecting privacy»*, International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), pp. 557-570. Formalismo matemático de k-anonimato y generalización de identificadores cuasi-identificadores, base del pipeline pre-vectorización en pgvector (Aporte 38).
* **John X. Morris, Volodymyr Kuleshov, Vitaly Shmatikov, Alexander M. Rush (2023):** *«Text Embeddings Reveal (Almost) As Much As Text»*, Cornell University / arXiv:2310.06816. Demostración formal de la reversibilidad de embeddings densos mediante ataques de inversión semántica, justificando el filtrado homomórfico obligatorio previo al cálculo vectorial (Aporte 38).
* **Congzheng Song & Anshumali Shrivastava (2020):** *«Information Leakage in Embedding Models»*, ACM CCS. Análisis riguroso de fuga de privacidad y atributos en espacios vectoriales latentes.
* **MITRE Corporation (2024):** *«CWE-532: Insertion of Sensitive Information into Log File»*. Marco de vulnerabilidades y mitigaciones en observabilidad estructurada, fundamento de la redacción activa en memoria de credenciales (`APILoggerFilter`, Aporte 39).
* **Mark C. Paulk, Bill Curtis, Mary Beth Chrissis & Charles V. Weber (1993):** *«Capability Maturity Model for Software, Version 1.1»*, CMU/SEI-93-TR-024, Software Engineering Institute; y **CMMI Product Team (2010):** *«CMMI for Development, Version 1.3»*, CMU/SEI-2010-TR-033. Representación por etapas: un nivel de madurez solo se alcanza cuando se satisfacen las áreas de proceso de ese nivel y de los inferiores; antecedente de la cota estructural de madurez (Aporte 48).
* **Michael Power (1997):** *«The Audit Society: Rituals of Verification»*, Oxford University Press. Riesgo de que la verificación documental sustituya a la verificación de eficacia; fundamenta que el vínculo documental sea condición necesaria pero no suficiente (Aporte 49).
* **W3C (2017):** *«Web Cryptography API»*, W3C Recommendation, 26-ene-2017 (`SubtleCrypto.digest`). Cálculo del SHA-256 en el navegador sin transmitir el documento (Aporte 50).
* **NIST Special Publication 800-107 Revision 1 (2012):** *«Recommendation for Applications Using Approved Hash Algorithms»*. Uso apropiado de funciones hash aprobadas para integridad de datos (Aportes 50 y 51).
* **Sean Quinlan & Sean Dorward (2002):** *«Venti: a new approach to archival storage»*, USENIX Conference on File and Storage Technologies (FAST '02). Almacenamiento direccionado por contenido mediante huella criptográfica; base del registro idempotente por huella (Aporte 50). El diseño original emplea SHA-1; el principio es independiente de la función hash.
* **Leslie Lamport (1978):** *«Time, Clocks, and the Ordering of Events in a Distributed System»*, Communications of the ACM, 21(7), pp. 558–565. Contadores lógicos estrictamente crecientes como mecanismo de ordenación; antecedente de los correlativos por marca de agua (Aporte 52).
* **PostgreSQL Global Development Group (documentación oficial vigente):** *«Sequence Manipulation Functions»*. Un valor de secuencia consumido no se revierte ni se reutiliza y se aceptan huecos; precedente de identificadores no reutilizables (Aporte 52).
* **Martin Kleppmann (2017):** *«Designing Data-Intensive Applications»*, O'Reilly Media, cap. 4 «Encoding and Evolution». Compatibilidad hacia atrás y hacia adelante de los esquemas de datos persistidos (Aporte 54).
* **Zustand (pmndrs) — documentación oficial:** *«Persisting store data»* (middleware `persist`, opciones `version` y `migrate`). Mecanismo de migración del estado persistido en el navegador (Aporte 54).
* **OWASP Foundation:** *«Input Validation Cheat Sheet»* y *«File Upload Cheat Sheet»*. Los datos que cruzan una frontera no confiable se validan como entrada externa; la validación por extensión es una lista blanca de conveniencia y no una verificación de contenido (Aportes 54 y 58).
* **Peter Buneman, Sanjeev Khanna & Wang-Chiew Tan (2001):** *«Why and Where: A Characterization of Data Provenance»*, International Conference on Database Theory (ICDT 2001), LNCS 1973, pp. 316–330. Formalización de la procedencia de los datos; base del marcado de datos de referencia (Aporte 55).
* **NASA Mars Climate Orbiter Mishap Investigation Board (1999):** *«Phase I Report»*, 10-nov-1999. Caso canónico de pérdida de una misión por discrepancia de unidades en la frontera entre dos sistemas (Aporte 56).
* **Matt Bishop & Michael Dilger (1996):** *«Checking for Race Conditions in File Accesses»*, Computing Systems, 9(2), pp. 131–152. Caracterización del intervalo entre comprobación y uso (TOCTOU) (Aporte 57).
* **React Team — documentación oficial (react.dev):** *«useMemo»* y *«You Might Not Need an Effect»* (sección de obtención de datos y condiciones de carrera). Recálculo solo ante cambio de dependencias y patrón de descarte de resultados asíncronos obsoletos (Aporte 57).
* **Melvin E. Conway (1968):** *«How Do Committees Invent?»*, Datamation, 14(4), pp. 28–31. La estructura de un sistema refleja la de comunicación de quienes lo construyen; fundamenta asignar a cada agente un conjunto de archivos exclusivo (Aporte 59).
* **Frederick P. Brooks Jr. (1975):** *«The Mythical Man-Month»*, Addison-Wesley. Coste de comunicación de $n(n-1)/2$ canales entre $n$ participantes; justifica reducir el acoplamiento entre agentes paralelos mediante contratos cerrados (Aporte 59).
* **Michael E. Fagan (1976):** *«Design and code inspections to reduce errors in program development»*, IBM Systems Journal, 15(3), pp. 182–211. Inspección formal por personas distintas del autor como detección temprana de defectos (Aporte 59).
* **Edsger W. Dijkstra (1970):** *«Notes on Structured Programming»* (EWD249). Las pruebas pueden mostrar la presencia de defectos pero no su ausencia; fundamenta que un arnés exógeno en verde es condición necesaria y no suficiente (Aporte 59).
* **Elaine J. Weyuker (1982):** *«On Testing Non-testable Programs»*, The Computer Journal, 25(4), pp. 465–470. Estrategias de oráculo cuando no existe salida esperada conocida, incluido el contraste contra una implementación independiente (pseudo-oráculo); base metodológica de la comparación diferencial contra la matriz canónica (Aporte 60).
* **John C. Knight & Nancy G. Leveson (1986):** *«An Experimental Evaluation of the Assumption of Independence in Multiversion Programming»*, IEEE Transactions on Software Engineering, SE-12(1), pp. 96–109. Dos implementaciones independientes de una misma especificación fallan de forma correlacionada; justifica validar primero la transcripción antes de usarla como oráculo (Aporte 60).
* **Ronald A. Fisher (1935):** *«The Design of Experiments»*, Oliver & Boyd. Aislamiento del efecto de un factor mediante su variación controlada; fundamento de la atribución por conmutación de reglas de a una (Aporte 60).
* **Ralph L. Keeney & Howard Raiffa (1976):** *«Decisions with Multiple Objectives: Preferences and Value Tradeoffs»*, John Wiley & Sons. Condiciones de validez de la agregación aditiva ponderada de criterios; base de la ponderación por criticidad sobre base completa (Aporte 61).
* **ISO/IEC 33020:2019:** *«Information technology — Process assessment — Process measurement framework for assessment of process capability»*. Escalas de medición de capacidad de proceso y reglas de agregación de atributos; marco normativo del score por dimensión (Aporte 61).
* **W. Edwards Deming (1986):** *«Out of the Crisis»*, MIT Center for Advanced Engineering Study. Una medida que puede mejorarse alterando su denominador deja de medir el proceso; fundamenta eliminar la renormalización sobre las dimensiones evaluadas (Aporte 61).
* **Garrett Birkhoff (1940):** *«Lattice Theory»*, American Mathematical Society Colloquium Publications, vol. 25. Propiedades del ínfimo sobre un orden total (asociatividad, conmutatividad e idempotencia); fundamenta que los topes de nivel sean independientes del orden de evaluación (Aporte 62).
* **Edsger W. Dijkstra (1975):** *«Guarded Commands, Nondeterminacy and Formal Derivation of Programs»*, Communications of the ACM, 18(8), pp. 453–457. El resultado de un conjunto de comandos guardados no depende del orden de evaluación de las guardas; antecedente formal de los topes conmutativos (Aporte 62).
* **IEEE Std 754-2019:** *«IEEE Standard for Floating-Point Arithmetic»*, IEEE Computer Society. Representación binaria, redondeo y no asociatividad de la suma en coma flotante; base de la cota de reproducibilidad entre implementaciones (Aporte 63).
* **David Goldberg (1991):** *«What Every Computer Scientist Should Know About Floating-Point Arithmetic»*, ACM Computing Surveys, 23(1), pp. 5–48. Propagación del error de redondeo y dependencia del resultado respecto del orden de las operaciones (Aporte 63).
* **Nicholas J. Higham (2002):** *«Accuracy and Stability of Numerical Algorithms»* (2ª ed.), SIAM. Análisis del error de sumación y de su dependencia del orden de agregación (Aporte 63).
* **Richard A. DeMillo, Richard J. Lipton & Frederick G. Sayward (1978):** *«Hints on Test Data Selection: Help for the Practicing Programmer»*, IEEE Computer, 11(4), pp. 34–41. Análisis de mutantes: introducir un defecto conocido para comprobar que la batería de pruebas es capaz de detectarlo; base de la verificación del árbitro por mutación dirigida (Teorema 32).
* **Charles A. E. Goodhart (1975):** *«Problems of Monetary Management: The U.K. Experience»*, Papers in Monetary Economics, Reserve Bank of Australia. Una medida que se convierte en objetivo deja de ser buena medida; fundamenta que el estado «en verde» sea señal y no meta (Teorema 32).
* **W3C (2023):** *«Accessible Rich Internet Applications (WAI-ARIA) 1.2»* y *«Accessible Name and Description Computation 1.2»*, W3C Recommendations. Cómputo del nombre accesible y exposición de rol y estado; base del anclaje de localizadores del arnés de interfaz en el árbol de accesibilidad (Aporte 64).
* **W3C (2023):** *«Web Content Accessibility Guidelines (WCAG) 2.2»*, criterio 4.1.2 *Name, Role, Value*. Todo componente de interfaz expone nombre, rol y estado por medios programáticos; precondición del arnés y origen de los cuatro defectos de accesibilidad detectados (Aporte 64).
* **Kent C. Dodds (2018):** *«Testing Library — Guiding Principles»* (testing-library.com). Cuanto más se parezcan las pruebas a la forma real de uso del software, más confianza aportan; fundamenta localizar por rol y nombre accesible en lugar de por clases de presentación (Aporte 64).
* **Gerard Meszaros (2007):** *«xUnit Test Patterns: Refactoring Test Code»*, Addison-Wesley. Patrones *Fresh Fixture* (cada prueba parte de un estado conocido) y *Obscure Test* (las premisas se declaran, no se heredan); base del arranque limpio y explícito de cada escenario (Aporte 64).
* **Kent Beck (2002):** *«Test-Driven Development by Example»*, Addison-Wesley. Independencia del orden de ejecución entre pruebas; fundamenta la limpieza del estado persistido antes de cada escenario (Aporte 64).
* **Microsoft — Playwright, documentación oficial vigente (playwright.dev):** *«Test configuration»* (opciones `webServer`, `reuseExistingServer`, `workers`, `expect.timeout`), *«Locators»* (prioridad de `getByRole` sobre selectores de presentación) y *«Page.addInitScript»* (ejecución de un script antes de cualquier script de la página). Especificación de las opciones que hacen reproducible el arranque del arnés de interfaz y de la limpieza previa a la hidratación (Aporte 64).
* **React — documentación oficial (react.dev):** *«Synchronizing with Effects»* y *«You Might Not Need an Effect»*. Una suscripción declarada en un efecto se registra una vez por instancia montada y se cancela con ella; fundamenta la no idempotencia de una acción conmutante registrada globalmente bajo montaje múltiple (Aporte 65).
* **Leslie Lamport (1977):** *«Proving the Correctness of Multiprocess Programs»*, IEEE Transactions on Software Engineering, SE-3(2), pp. 125–143. Propiedades de seguridad (*safety*) sobre estado compartido frente a acciones concurrentes; marco del análisis de la conmutación múltiple (Aporte 65).
* **Seda Gürses, Carmela Troncoso & Claudia Diaz (2011):** *«Engineering Privacy by Design»*, Computers, Privacy & Data Protection (CPDP), KU Leuven. Presenta la minimización de datos como punto de partida de ingeniería, dependiente de la finalidad, y aclara que minimizar no equivale necesariamente a anonimizar. Base del Aporte 72. Fuente primaria: https://software.imdea.org/~carmela.troncoso/papers/Gurses-CPDP11.pdf
* **Chloe Autio et al. / NIST (2024; ficha actualizada 8-abr-2026):** *«Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile»*, NIST AI 600-1, DOI 10.6028/NIST.AI.600-1. Documenta la confabulación de contenido, razonamientos y citas y propone gestión del riesgo durante todo el ciclo de vida. Base de los Aportes 72 y 73. Fuente oficial: https://doi.org/10.6028/NIST.AI.600-1
* **OWASP GenAI Security Project (2025):** *«LLM05:2025 Improper Output Handling»*. Establece que la salida del LLM debe tratarse con enfoque de confianza cero y validarse antes de pasar a componentes posteriores. Base de la fusión acotada y validación por lista positiva del Aporte 73. Fuente oficial: https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/
* **DeepSeek (documentación oficial vigente consultada el 20-sep-2026):** *«JSON Output»*. Define `response_format: {"type":"json_object"}`, el requisito de instruir la salida JSON y advierte sobre truncamiento o contenido ocasionalmente vacío. Sustenta únicamente el contrato del proveedor empleado en A73; no constituye evidencia independiente de exactitud jurídica. https://api-docs.deepseek.com/guides/json_mode/

---

## 5. 📐 Teoremas Inéditos Producidos en esta Plataforma (Referencias Cruzadas)

| Teorema / Aporte | Título Canónico | Primer Registro |
|---|---|---|
| **T1** | **Asimetría de Capas Estigmérgicas ($\mathcal{T} = \mathcal{T}_{\text{meta}} \oplus \mathcal{T}_{\text{dominio}}$)** | **APORTES_INEDITOS.md §T1** |
| **T2** | **Inferencia de Metadatos OpenGraph como Filtro Heurístico** | **APORTES_INEDITOS.md §T2** |
| **T3** | **Cota Superior Fija en Diagnósticos de Privacidad ($N \le 80$)** | **APORTES_INEDITOS.md §T3** |
| **T4** | **Segregación Criptográfica y Arquitectónica de Funciones del DPO** | **APORTES_INEDITOS.md §T4** |
| **T5** | **No-Degeneración de Métricas en Espacios de Cumplimiento Normativo** | **APORTES_INEDITOS.md §T5** |
| **T6** | **Antecedencia Paramétrica y Poda Ontológica Unidireccional** | **APORTES_INEDITOS.md §T6** |
| **T7** | **Aislamiento Transaccional y Purga Obligatoria de Contexto Evidencial** | **APORTES_INEDITOS.md §T7** |
| **T8** | **Jerarquía Tonal Invertida y Neutralidad Cromática (Achromatic Workspaces)** | **APORTES_INEDITOS.md §T8** |
| **T9** | **Arbitraje Exógeno Booleano vs. Auto-Aserción Introspectiva (Proaño-Gemini-Dijkstra)** | **APORTES_INEDITOS.md §T9** |
| **T10** | **Validación Algorítmica Determinista de Cédula Ecuatoriana (Módulo 10 DLP)** | **APORTES_INEDITOS.md §T10** |
| **T11** | **Minimización de Latencia Cognitiva mediante Command Palette Universal** | **APORTES_INEDITOS.md §T11** |
| **T12** | **Conservación de Superficie Útil y Desacoplamiento de Paneles Flexibles** | **APORTES_INEDITOS.md §T12** |
| **T13** | **Verificación Notarial de Transiciones Regulatorias mediante Statecharts** | **APORTES_INEDITOS.md §T13** |
| **T14** | **Compliance Graph DAG Lineage** | **APORTES_INEDITOS.md §T14** |
| **T15** | **Invariante Estigmérgico de No Regresión en Agentes Autónomos** | **APORTES_INEDITOS.md §T15** |
| **T16** | **Desacoplamiento No Compensatorio y Bloqueo Lexicográfico (No Dilución)** | **APORTES_INEDITOS.md §T16** |
| **T17** | **Determinismo de Doble Compuerta en Calificación MTGE (Res. 2026-0005-R)** | **APORTES_INEDITOS.md §T17** |
| **T18** | **Inmutabilidad Notarial y Sellado Criptográfico Append-Only para Snapshots** | **APORTES_INEDITOS.md §T18** |
| **T19** | **Doble Escala MTGE: Evaluación Micro vs. Macro en Motores de Gran Escala** | **APORTES_INEDITOS.md §A20 · 2026-09-15** |
| **T20** | **Interoperabilidad Tipada Bidireccional Zustand-ServerActions en GRC** | **APORTES_INEDITOS.md §T20** |
| **T21** | **Contrato Bilateral Agéntico de No-Regresión como Ley Matemática ($(C \implies S) \land ((C \land S) \implies \neg R)$)** | **APORTES_INEDITOS.md §T21** |
| **T22** | **Principio de Tipado Estricto como Árbitro Exógeno Sintáctico** | **APORTES_INEDITOS.md §T22** |
| **T23** | **Orquestación Agéntica Concurrente mediante Arbitraje Exógeno Físico** | **APORTES_INEDITOS.md §T23 · 2026-09-17** |
| **T24** | **Aislamiento Transaccional Multi-Tenant Asíncrono mediante ContextVar RLS** | **APORTES_INEDITOS.md §T24 · 2026-09-17** |
| **T25** | **Purga Probatoria por Inconsistencia Categórica en Formularios Forenses** | **APORTES_INEDITOS.md §T25 · 2026-09-17** |
| **T26** | **Principio de Hidratación Asíncrona Aislada en Renderizado Híbrido (Next.js 15+)** | **APORTES_INEDITOS.md §T26 · 2026-09-19** |
| **T27** | **Inmutabilidad Criptográfica de Snapshots de Auditoría por Anclaje en Árbol de Merkle** | **APORTES_INEDITOS.md §T27 · 2026-09-17** |
| **T28** | **Sincronización Causal de Asertos ante Endurecimiento Contractual** | **APORTES_INEDITOS.md §T28 · 2026-09-17** |
| **T31** | **Auditoría Financiera Cruzada (Teorema de GRC Unificado)** | **APORTES_INEDITOS.md §T31 · 2026-09-18** |
| **A32** | **Renderizado Liminal Reactivo de Tokens DLP en Pipelines RAG** | **APORTES_INEDITOS.md §A32 · 2026-09-17** |
| **A33** | **Cálculo MTGE Determinista de Latencia Cero en Capa Cliente** | **APORTES_INEDITOS.md §A33 · 2026-09-17** |
| **A34** | **Desacoplamiento de Subsistemas Algorítmicos mediante Enjambres Agénticos** | **APORTES_INEDITOS.md §A34 · 2026-09-18** |
| **A35** | **Reactividad Contable en Vivo en Capa Cliente (Live IFRS Reactivity)** | **APORTES_INEDITOS.md §A35 · 2026-09-18** |
| **A36** | **Emisión Inmutable de Archivos de Cálculo WORM en Memoria (Zero-Trace)** | **APORTES_INEDITOS.md §A36 · 2026-09-18** |
| **A37** | **Ciclo de Vida Reactivo de Remediación mediante Polling SWR (AI Copilot Tracker)** | **APORTES_INEDITOS.md §A37 · 2026-09-19** |
| **A38** | **Pipeline de K-Anonimato Determinista con Mapeo Homomórfico Intradocumental** | **APORTES_INEDITOS.md §A38 · 2026-09-17** |
| **A39** | **Arquitectura Liminal de Zero Data Leakage en LLM Copilot y APILoggerFilter** | **APORTES_INEDITOS.md §A39 · 2026-09-17** |
| **A40** | **Motor Criptográfico de Árbol de Merkle y Anclaje Temporal Asíncrono (`merkle_tree.py`)** | **APORTES_INEDITOS.md §A40 · 2026-09-17** |
| **A41** | **Pasarela RAG con Modo Estricto de Cero Alucinación y Convalidación Gateway** | **APORTES_INEDITOS.md §A41 · 2026-09-17** |
| **T29** | **Restricción Gramatical Sintáctica por Decodificación Guiada en Motores GRC** | **APORTES_INEDITOS.md §T29 · 2026-09-17** |
| **A42** | **Motor de Inferencia Isomórfico Resiliente con Doble Compuerta y Fallback Heurístico** | **APORTES_INEDITOS.md §A42 · 2026-09-17** |
| **A43** | **Polimorfismo Semántico en Prompts de Auditoría GRC Multi-Normativa** | **APORTES_INEDITOS.md §A43 · 2026-09-17** |
| **A48** | **Cota Estructural de Madurez por Controles Habilitadores (Nivel Ajustado ≤ 2)** | **APORTES_INEDITOS.md §A48 · 2026-09-19** |
| **A49** | **Modo de Cálculo "Verificado": Evidencia Vinculada como Condición del Nivel Sellado** | **APORTES_INEDITOS.md §A49 · 2026-09-19** |
| **A50** | **Custodia de Huella sin Custodia de Contenido con Verificación por Re-presentación** | **APORTES_INEDITOS.md §A50 · 2026-09-19** |
| **A51** | **Contrato de Digest No Ambiguo (Corrección del Doble Hash)** | **APORTES_INEDITOS.md §A51 · 2026-09-19** |
| **A52** | **Correlativos Monótonos por Marca de Agua (No Reutilización de Códigos Citados)** | **APORTES_INEDITOS.md §A52 · 2026-09-19** |
| **A53** | **Poda del Cuestionario por Talla en Dos Ejes con Habilitadores Invariantes** | **APORTES_INEDITOS.md §A53 · 2026-09-19** |
| **A54** | **Estado Persistido Versionado y Lectura Tolerante de Proyectos Guardados** | **APORTES_INEDITOS.md §A54 · 2026-09-19** |
| **A55** | **Datos de Referencia con Procedencia Marcada e Inhabilitados como Prueba** | **APORTES_INEDITOS.md §A55 · 2026-09-19** |
| **A56** | **Invariante de Unidad en las Fronteras de Serialización** | **APORTES_INEDITOS.md §A56 · 2026-09-19** |
| **A57** | **Coherencia Temporal del Estado Derivado (Contexto Capturado y Memoización Obsoleta)** | **APORTES_INEDITOS.md §A57 · 2026-09-19** |
| **A58** | **Catálogo Canónico como Único Punto de Decisión por Normativa y Mediación Completa** | **APORTES_INEDITOS.md §A58 · 2026-09-19** |
| **A59** | **Paralelismo de Agentes con Partición Previa de Archivos y Revisión Independiente (Extensión de T23)** | **APORTES_INEDITOS.md §A59 · 2026-09-19** |
| **T30** | **Invariante de Deriva Paramétrica de Riesgo en Ciclos de Vida EIPD (Continuous EIPD State Machine)** | **APORTES_INEDITOS.md §T30 · 2026-09-17** |
| **A44** | **Motor Reactivo de Re-Evaluación Continua EIPD (`mtge_engine.py` + `models.py`)** | **APORTES_INEDITOS.md §A44 · 2026-09-17** |
| **A45** | **Motor de Cálculo de Impacto de Reformas SPDP con Invariante Histórico (`diff_engine.py`)** | **APORTES_INEDITOS.md §A45 · 2026-09-17** |
| **A46** | **Poka-Yoke Estructural de Garantías en Transferencias Internacionales de Datos** | **APORTES_INEDITOS.md §A46 · 2026-09-17** |
| **A47** | **Refactorización Orgánica mediante Bus de Memoria Estigmérgica (Trans-Conversational Context Injection)** | **APORTES_INEDITOS.md §A47 · 2026-09-18** |
| **A60** | **Reconstrucción Ejecutable de una Matriz de Cálculo Externa y Comparación Diferencial por Escenarios** | **APORTES_INEDITOS.md §A60 · 2026-09-19** |
| **A61** | **Score Ponderado por Criticidad sobre Base Completa y Compuerta de Cobertura (sustituye la agregación de A48)** | **APORTES_INEDITOS.md §A61 · 2026-09-19** |
| **A62** | **Topes de Nivel Independientes y Conmutativos, con Conjunto Bloqueante Derivado del Catálogo** | **APORTES_INEDITOS.md §A62 · 2026-09-19** |
| **A63** | **Cota de Reproducibilidad entre Implementaciones por Asociatividad en Coma Flotante** | **APORTES_INEDITOS.md §A63 · 2026-09-19** |
| **T32** | **Verificación del Árbitro por Mutación Dirigida (un arnés en verde no se acredita a sí mismo)** | **APORTES_INEDITOS.md §T32 · 2026-09-19** |
| **A64** | **Arnés de Interfaz Anclado en Rol y Nombre Accesible (acoplamiento verificabilidad–accesibilidad)** | **APORTES_INEDITOS.md §A64 · 2026-09-19** |
| **A65** | **No Idempotencia de Componentes con Escucha Global bajo Montaje Múltiple (Conmutación Par Silenciosa)** | **APORTES_INEDITOS.md §A65 · 2026-09-19** |
| **A74** | **Retrasar el Estado Compartido, no la Llamada Local, para Sincronizar un Aviso con un Desmontaje Ajeno** | **APORTES_INEDITOS.md §A74 · 2026-09-27** |
| **A75** | **Envolver el Filtro Exportado por una Librería para Normalizar Entrada, en vez de Reimplementar su Algoritmo** | **APORTES_INEDITOS.md §A75 · 2026-09-27** |
| **A76** | **El `<dialog>` Nativo con `showModal()` Bloquea Realmente el Resto del Documento, a Diferencia de una Superposición Decorativa** | **APORTES_INEDITOS.md §A76 · 2026-09-27** |
| **A77** | **Descomponer un Flag Booleano Sobrecargado en Dos Flags con Semántica Distinta** | **APORTES_INEDITOS.md §A77 · 2026-09-28** |
| **A78** | **Orden de Precedencia en Clasificación por Coincidencia de Subcadena de Texto Libre** | **APORTES_INEDITOS.md §A78 · 2026-09-28** |
| **A79** | **Invariante Estructural Independiente (Suma de una Balanza = Cero) como Validador de Datos Heredados** | **APORTES_INEDITOS.md §A79 · 2026-09-28** |
| **A80** | **Verificar Importaciones Activas antes de Editar un Componente de Layout "Huérfano"** | **APORTES_INEDITOS.md §A80 · 2026-09-28** |
| **A81** | **Dos Uniones de Tipo Literal Paralelas para "Vista Activa", sin Fuente Única de Verdad** | **APORTES_INEDITOS.md §A81 · 2026-09-28** |
| **A82** | **Reporte "Imprimible a PDF" como HTML Autocontenido — Nomenclatura que Puede Inducir a Error** | **APORTES_INEDITOS.md §A82 · 2026-09-28** |
| **A83** | **Verificador de "Listo para E2E" que Solo Reconoce Python Aprueba por Vacuidad Otros Lenguajes** | **APORTES_INEDITOS.md §A83 · 2026-09-28** |
| **A84** | **Políticas RLS Habilitadas pero Inertes cuando la Aplicación se Conecta como Dueña con `BYPASSRLS`** | **APORTES_INEDITOS.md §A84 · 2026-10-08** |
| **A85** | **`UNIQUE` con Columna Anulable no Impide Duplicados y con Revocación Lógica Bloquea la Re-Asignación** | **APORTES_INEDITOS.md §A85 · 2026-10-08** |
| **A86** | **Una Falla que Solo Aparece en el Arnés no Prueba una Diferencia de Entorno** | **APORTES_INEDITOS.md §A86 · 2026-10-08** |
| **A87** | **Probar RLS como el Rol de Aplicación sin su Contraseña: `INHERIT FALSE, SET TRUE` y `SET LOCAL ROLE`** | **APORTES_INEDITOS.md §A87 · 2026-10-08** |
| **A88** | **Un Parámetro sin `Header()` en una Dependencia FastAPI se Lee de la Query String** | **APORTES_INEDITOS.md §A88 · 2026-10-08** |
| **A89** | **Un `SET ROLE` de Sesión a Través del Pooler de Neon (PgBouncer, Modo Transacción) se Filtra a Otros Clientes** | **APORTES_INEDITOS.md §A89 · 2026-10-09** |
| **A90** | **Una Carpeta de Trabajo Compartida entre Sesiones Concurrentes Cambia de Rama y Revierte Ediciones sin Confirmar** | **APORTES_INEDITOS.md §A90 · 2026-10-09** |
| **A91** | **El Mamparo ADPA que Degrada un Router sin Fallar Convierte un Error de Arranque en un 404 con `/health` en Verde** | **APORTES_INEDITOS.md §A91 · 2026-10-09** |
| **A92** | **`git checkout` sobre una Carpeta con una Junction de Windows Modifica el Árbol de Destino** | **APORTES_INEDITOS.md §A92 · 2026-10-09** |
| **A93** | **Dos Carpetas de Artefactos Vivos con Escritores Distintos Divergen en Silencio** | **APORTES_INEDITOS.md §A93 · 2026-10-09** |
| **A94** | **Un Prompt que Exige «el Esquema X» sin Incluirlo, y un Tope de Tokens por Debajo de la Salida, Producen JSON Inválido o Cortado** | **APORTES_INEDITOS.md §A94 · 2026-10-10** |
| **A95** | **Dos Trampas de Python al Cargar y Leer Archivos: `dataclass` con el Módulo sin Registrar y `Path.read_text(newline=)` Anterior a 3.13** | **APORTES_INEDITOS.md §A95 · 2026-10-10** |
| **A96** | **`git rm --cached` Deja el Archivo en Disco Solo a Quien lo Ejecuta; Quien Actualiza `main` lo Pierde** | **APORTES_INEDITOS.md §A96 · 2026-10-10** |
| **A97** | **Hacer Comprobable el Reparto de Archivos entre Tareas Paralelas con Propiedad Exclusiva y Secciones Reservadas (Extensión de A59)** | **APORTES_INEDITOS.md §A97 · 2026-10-10** |
| **A98** | **`SET LOCAL` no Admite Parámetros de Enlace; `set_config(nombre, valor, true)` es el Equivalente Parametrizable** | **APORTES_INEDITOS.md §A98 · 2026-10-10** |
| **A99** | **Las APIs `System.IO` de .NET Resuelven Rutas Relativas contra el Directorio del Proceso, no contra la Ubicación de PowerShell** | **APORTES_INEDITOS.md §A99 · 2026-10-10** |
| **A100** | **`psycopg` Asíncrono Falla en Windows con el Bucle por Defecto; `uvicorn` solo Elige el Bucle Compatible con `--reload` o Varios Trabajadores** | **APORTES_INEDITOS.md §A100 · 2026-10-10** |
| **A101** | **Un Mismo Parámetro en Dos Contextos de Tipo Distinto Produce `AmbiguousParameter`** | **APORTES_INEDITOS.md §A101 · 2026-10-10** |
| **A102** | **Corrección y Extensión del Aporte 21: `WriteAllText` sin Codificación no Escribe BOM** | **APORTES_INEDITOS.md §A102 · 2026-10-10** |
| **A103** | **El Certificado que Emite el Arnés de este Proyecto no Puede ser Validado por ZERAG: Ruta, Pruebas Contadas, Firma y Commit Difieren de su Validador** | **APORTES_INEDITOS.md §A103 · 2026-10-10** |
| **A104** | **Un Certificado de Pruebas Versionado en Git no Certifica Nada: no está Atado al Commit y se Reescribe en Cada Corrida** | **APORTES_INEDITOS.md §A104 · 2026-10-10** |
| **A105** | **Una Prueba que Lanza un Subproceso Hereda las Credenciales del `.env` y Pasa en Local pero Falla en la CI (Extensión del Aporte 86)** | **APORTES_INEDITOS.md §A105 · 2026-10-10** |
| **A106** | **Lanzar un `.bat` con `cmd /c` desde Git Bash Devuelve Código 0 sin Ejecutarlo; el Código de Salida del Arnés no Basta como Prueba** | **APORTES_INEDITOS.md §A106 · 2026-10-10** |
* **Pierre-Paul Grassé (1959):** *«La reconstruction du nid et les coordinations inter-individuelles chez Bellicositermes natalensis et Cubitermes sp. La théorie de la Stigmergie: Essai d'interprétation du comportement des termites constructeurs»*, Insectes Sociaux. Fundamentación biológica y matemática de la Estimergia (coordinación indirecta a través de la modificación del entorno), que constituye la base científica del **Bus de Memoria Estigmérgica** para ensambles de agentes LLM aislados (Aporte 47).
* **Vercel / Microsoft Playwright Team (2024–2026):** *«Playwright: Reliable End-to-End Testing for Modern Web Apps»* (documentación oficial, playwright.dev). Especificación de configuración moderna: `fullyParallel`, `reuseExistingServer`, `trace: "retain-on-failure"`, Workers adaptativos, Fresh Fixture guarantee. Base técnica de Aporte 66.
* **Kent C. Dodds (2018):** *«Testing Library — Guiding Principles»* (testing-library.com). Máxima: cuanto más se parezcan las pruebas al uso real, más confianza aportan. Prioridad de `getByRole` sobre selectores de presentación. Fundamenta Aporte 68 (LocatorResolver Jerarquía PCP).
* **Gerard Meszaros (2007):** *«xUnit Test Patterns: Refactoring Test Code»*, Addison-Wesley. Patrones Fresh Fixture (cada prueba parte de estado conocido) y Object Mother (constructores de datos). Base de Aporte 67 (Data Builders y Fixtures Reales).
* **Ralph Merkle (1987):** *«A Digital Signature Based on a Conventional Encryption Function»*, Advances in Cryptology — CRYPTO '87, Springer LNCS 293, pp. 369–378. Fundamentación teórica de árboles de Merkle y hashing criptográfico determinista. Aplicación: Aporte 70 (AuditTrail con certificación SHA-256 para snapshots).
* **NIST FIPS PUB 180-4 (2015):** *«Secure Hash Standard (SHS) - SHA-256»*. Estándar federal de hashing criptográfico. Aplicación: Aporte 70 (certificación notarial de screenshots).
* **Sean Quinlan & Sean Dorward (2002):** *«Venti: A New Approach to Archival Storage»*, USENIX FAST '02. Almacenamiento direccionado por contenido mediante huella criptográfica. Principio de integridad verificable: Aporte 70.
* **The Unicode Consortium:** *«Unicode Standard Annex #15 — Unicode Normalization Forms»* (UAX #15, revisión vigente). Especifica las formas de normalización NFC/NFD y el mecanismo de descomposición de un carácter con diacrítico en carácter base más marca combinante. Fundamento técnico de la búsqueda insensible a tildes en la paleta de comandos (Aporte 75).
* **WHATWG:** *«HTML Living Standard — The dialog element»* (§4.11.4, revisión vigente). Especifica que `showModal()` añade el diálogo al *top layer* del documento y que el resto de los elementos deja de recibir eventos de puntero mientras permanece abierto. Fundamento del diagnóstico del bloqueo real de interacción en el arnés de interfaz (Aporte 76).
* **Martin Fowler (2018):** *«Refactoring: Improving the Design of Existing Code»* (2ª ed.), Addison-Wesley. El catálogo de *code smells* documenta el parámetro/flag booleano que en realidad codifica más de una decisión como señal concreta para descomponerlo. Fundamento de la separación de `disponible` en `bancoDisponible` (Aporte 77).
* **Luca Pacioli (1494):** *«Summa de Arithmetica, Geometria, Proportioni et Proportionalita»*. Origen documentado de la partida doble; su propiedad estructural fundamental es que toda balanza de comprobación correctamente registrada suma cero. Fundamento del invariante de cuadre contable como validador independiente de la lógica de clasificación (Aporte 79).
* **PostgreSQL Global Development Group (documentación oficial, v16):** *«Row Security Policies»* (§5.8). Los superusuarios y los roles con `BYPASSRLS` siempre omiten la seguridad por filas, y el dueño de la tabla normalmente también salvo `ALTER TABLE … FORCE ROW LEVEL SECURITY`. Fundamento del diagnóstico de RLS inerte (Aporte 84).
* **PostgreSQL Global Development Group (documentación oficial, v16):** *«Unique Constraints»* (§5.4.3). Los valores nulos no se consideran iguales en una restricción única salvo que se declare `NULLS NOT DISTINCT` (PostgreSQL ≥ 15). Fundamento del Aporte 85.
* **Qingzhou Luo, Farah Hariri, Lamyaa Eloussi & Darko Marinov (2014):** *«An Empirical Analysis of Flaky Tests»*, Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE 2014). Clasificación empírica de las causas raíz de tests intermitentes, entre ellas la dependencia de recursos de red; respalda descartar primero la dependencia externa antes de atribuir una falla al runner (Aporte 86).
* **PostgreSQL Global Development Group (documentación oficial, v16):** *«GRANT»* y *«SET ROLE»*. Opciones `INHERIT` y `SET` de la membresía de roles (nuevas en v16) y cambio de identidad efectiva de la sesión; fundamento de la prueba de RLS como rol restringido (Aporte 87).
* **Tiangolo / FastAPI (documentación oficial vigente):** *«Query Parameters»* y *«Header Parameters»*. Los parámetros de función que no son de ruta se interpretan como query; las cabeceras requieren `Header`. Fundamento del Aporte 88.
* **PgBouncer (documentación oficial vigente):** *«Features»*, tabla de compatibilidad de funciones de PostgreSQL por modo de pooling. En modo transacción el estado de sesión (`SET`, `LISTEN`, advisory locks de sesión) no es seguro porque la conexión del servidor se comparte entre clientes. Fundamento del Aporte 89, junto con la documentación de *SET* de PostgreSQL v16 (`SET LOCAL`).
* **Documentación oficial de Git:** *«git-worktree(1)»* (git-scm.com). Un repositorio admite varios árboles de trabajo vinculados, cada uno con su propio `HEAD` e índice; es el mecanismo para trabajar en varias ramas a la vez sin pisarse. Fundamento del Aporte 90.
* **Kubernetes (documentación oficial vigente):** *«Configure Liveness, Readiness and Startup Probes»* (kubernetes.io). La sonda de disponibilidad (*readiness*) indica si la aplicación puede atender peticiones, distinta de que el proceso esté vivo. Fundamento del Aporte 91, junto con Nygard, *Release It!* (ya registrado arriba por el patrón Bulkhead; el patrón *Fail Fast* es del mismo libro).
* **Microsoft (documentación de Win32):** *«Hard Links and Junctions»* (learn.microsoft.com). Una *junction* es un punto de reanálisis que redirige el acceso a una ruta hacia otro directorio y es transparente para las aplicaciones. Fundamento del Aporte 92.
* **Andrew Hunt & David Thomas (2019):** *«The Pragmatic Programmer»* (ed. 20.º aniversario), Addison-Wesley. Principio DRY: cada pieza de conocimiento debe tener una representación única, inequívoca y autorizada. Fundamento del Aporte 93.
* **DeepSeek (documentación oficial vigente):** *«JSON Output»* (api-docs.deepseek.com). Pide incluir en el prompt un ejemplo del formato JSON deseado, fijar `max_tokens` con criterio para que la cadena no se trunque y presenta el modo como garantía de JSON válido, no de un esquema. Fundamento del Aporte 94 (rastro `¤roadmap` `¤copiloto-ia`).
* **Python Software Foundation (documentación oficial, Python 3.13):** *«importlib»*, receta «Importing a source file directly» (asigna `sys.modules[module_name]` antes de `exec_module`), y *«pathlib»* (`Path.read_text`: parámetro `newline` añadido en 3.13; `Path.write_text`: en 3.10). Fundamento del Aporte 95 (rastro `¤arbitro` `¤ci-cd`).
* **Git (documentación oficial):** *«git-rm(1)»* (git-scm.com), opción `--cached`: elimina las rutas solo del índice y deja intactos los archivos del árbol de trabajo de quien lo ejecuta; no describe el efecto en quienes integran el commit, que procede del experimento del Aporte 96 (rastro `¤invariantes`).
* **Psycopg (documentación oficial, psycopg 3):** *«Differences from psycopg2 → Server-side binding»* (psycopg.org). La vinculación de parámetros en el servidor no funciona con `SET`, `NOTIFY` ni sentencias de definición de datos; nombra `set_config()` y `pg_notify()` como sustitutos. Fundamento del Aporte 98 (rastro `¤seguridad` `¤invariantes`).
* **PostgreSQL Global Development Group (documentación oficial, v16):** *«Configuration Settings Functions»* (§9.27.1, Tabla 9.89). `set_config(setting_name, new_value, is_local)` corresponde al comando `SET` y con `is_local` verdadero el valor solo rige en la transacción actual; no trata la parametrización. Soporte parcial del Aporte 98.
* **Microsoft (documentación de .NET):** *«Environment.CurrentDirectory Property»* (learn.microsoft.com). Obtiene o establece la ruta completa del directorio de trabajo actual; por definición, el directorio donde el proceso se inició. No trata la resolución de rutas relativas ni PowerShell. Soporte parcial del Aporte 99 (rastro `¤arbitro` `¤invariantes`).
* **Microsoft (documentación de .NET):** *«File.WriteAllText Method»* (learn.microsoft.com). Sin codificación explícita usa UTF-8 sin BOM; para incluirlo hay que usar la sobrecarga con codificación. Fundamento del Aporte 102 (rastro `¤arbitro` `¤invariantes`).
* **Microsoft (documentación de PowerShell):** *«about_Character_Encoding»* (learn.microsoft.com). En Windows PowerShell 5.1 el valor `UTF8` del parámetro `-Encoding` usa UTF-8 con BOM, y cualquier codificación Unicode salvo `UTF7` siempre crea BOM. Fundamento del Aporte 102.
* **Psycopg (documentación oficial, psycopg 3):** *«Asynchronous support»* (psycopg.org). En Windows, Psycopg no es compatible con el `ProactorEventLoop` por defecto; sugiere usar otro bucle, por ejemplo `SelectorEventLoop`. Fundamento del Aporte 100 (rastro `¤arbitro` `¤seguridad`).
* **Python Software Foundation (documentación oficial, Python 3.13):** *«asyncio → Platform support»* (docs.python.org). En Windows, `ProactorEventLoop` es el bucle por defecto desde Python 3.8; `SelectorEventLoop` no soporta subprocesos. Soporte del Aporte 100.
* **PostgreSQL Global Development Group (documentación oficial, v16):** *«PREPARE»* (postgresql.org/docs/16/sql-prepare.html). Si no se especifica el tipo de un parámetro, se infiere del contexto en que se referencia por primera vez. Soporte del Aporte 101 (rastro `¤roadmap` `¤invariantes`).
* **OpenSSF — SLSA (especificación v1.0):** *«Provenance»* (slsa.dev/spec/v1.0/provenance). La procedencia es una atestación de que una plataforma produjo unos artefactos y registra la revisión de origen (`resolvedDependencies` con el `digest` `gitCommit`). Trata de compilaciones, no de pruebas: su aplicación a certificados de pruebas es una analogía del Aporte 104 (rastro `¤arbitro` `¤ci-cd`).
* **Python Software Foundation (documentación oficial, Python 3.13):** *«subprocess»* (docs.python.org/3/library/subprocess.html). Si `env` es `None`, el proceso hijo hereda el entorno del actual; un mapeo lo sustituye y, para añadir variables conservando el resto, se copia `os.environ`. Fundamento del Aporte 105 (rastro `¤arbitro` `¤ci-cd`).
* **Microsoft (documentación de Win32):** *«NeedCurrentDirectoryForExePathW function (processenv.h)»* (learn.microsoft.com). Un nombre de ejecutable con barra invertida siempre incluye el directorio actual en la búsqueda; sin ella solo se comprueba la existencia de `NoDefaultCurrentDirectoryInExePath`, y `cmd.exe` lo usa para elegir entre `.;%PATH%` y `%PATH%`. Fundamento del Aporte 106 (rastro `¤arbitro` `¤ci-cd` `¤seguridad`).
* **MSYS2 (documentación oficial):** *«Filesystem Paths»* (msys2.org/docs/filesystem-paths). Los argumentos que parecen rutas Unix se convierten automáticamente a Windows y se pueden excluir con `MSYS2_ARG_CONV_EXCL`; no trata el argumento `/c` ni `MSYS_NO_PATHCONV`. Soporte parcial del Aporte 106.
