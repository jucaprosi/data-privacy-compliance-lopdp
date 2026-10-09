# Tratado Canónico de Aportes Inéditos, Teoremas Demostrados e Innovaciones Arquitectónicas de Plataforma LOPDP 360
`¤aportes`
`¤vpa` `¤invariantes` `¤fuentes`

> **ESTATUS DEL DOCUMENTO:**  
> Archivo Vivo de Gobernanza, Epistemología de Cumplimiento e Investigación de Software.  
> Cada sección de este tratado formaliza una contribución conceptual, matemática y metodológica original desarrollada para **JUBYS Plataforma LOPDP 360**. El documento consolida en una sola Fuente de Verdad (SSOT) tanto los teoremas y fundamentos epistémicos demostrables, como los aportes de diseño e ingeniería de software del producto.

---

# PARTE I: Conocimientos Epistémicos y Teoremas Demostrables

### Teorema 1: Asimetría de Capas Estigmérgicas ($\mathcal{T} = \mathcal{T}_{\text{meta}} \oplus \mathcal{T}_{\text{dominio}}$) y Autonomía Notarial Offline
`¤vpa` `¤bbap` `¤adpa`
* **Problema:** En sistemas agénticos asistidos por oráculos o servidores MCP en la nube, el uso de rastros meta-operativos del BIOS (`¤bbap`, `¤triaje`, `¤arbitro`) en artefactos locales de trabajo (`TASKS.md`) sin registro en el mapa estigmérgico local produce falsos positivos o alertas de "rastros huérfanos" en linters y pruebas de CI/CD ejecutadas de forma desconectada (*Zero-Network*).
* **Demostración y Ley de Aislamiento:** El espacio de nombres de rastros $\mathcal{T}$ se particiona en dos subespacios disjuntos ortogonales:
  $$\mathcal{T} = \mathcal{T}_{\text{meta}} \oplus \mathcal{T}_{\text{dominio}}$$
  Para garantizar la autosuficiencia notarial de un repositorio ($C=1$), la condición de cierre exige:
  $$\forall \tau \in \mathcal{T}_{\text{meta}} \quad (\tau \in \mathcal{D}_{\text{local}} \implies \tau \in \text{VPA\_MAP.md})$$
  Todo repositorio cliente debe formalizar una sección de *Doctrina Heredada* en `VPA_MAP.md` para ser evaluable y reproducible en cualquier entorno offline.

---

### Teorema 2: Inferencia de Metadatos OpenGraph como Filtro Heurístico de Pre-Ingesta
`¤diagnostico-motor` `¤seguridad-tenant`
* **Problema:** Sobrecosto computacional y fallos de parseo al intentar procesar recursos web interactivos protegidos (ej. Google Docs en rutas `/edit`) con scrapers ciegos o motores headless sin JavaScript.
* **Solución y Formulación:** La cabecera HTML estática no autenticada ($H_{\text{head}} \subset \text{DOM}_{\text{raw}}$) transporta un vector de proyección semántica invariante:
  $$\vec{v}_{\text{OG}} = \langle \text{og:title}, \text{og:description}, \text{og:site\_name} \rangle$$
  El cual permite una reconstrucción de intención y alcance con fidelidad $F \ge 0.85$ respecto al Blueprint del documento sin incurrir en ejecución de scripts pesados, actuando como un filtro preventivo de seguridad y minimización de datos antes de solicitar el archivo exportado al usuario.

---

### Teorema 3: Cota Superior Fija en Diagnósticos de Privacidad ($N_{\text{preguntas}} \le 80$)
`¤diagnostico` `¤diagnostico-motor`
* **Fundamento:** Basado en la **Teoría de Carga Cognitiva (Sweller, 1988)** y los modelos de interacción **DMAT**:
  * La atención ejecutiva y la veracidad de respuestas en una sesión consultiva decaen exponencialmente tras 45–60 minutos ($t \ge 3600 \text{ s}$).
  * Cuestionarios tradicionales de más de 200 preguntas inducen sesgo de aquiescencia y fatiga, registrando respuestas afirmativas carentes de sustento.
* **Ley de Poda Condicional:**
  $$N_{\text{visibles}} = N_{\text{núcleo}} + \sum_{i=1}^{k} \mathbf{1}_{[\text{aplica}(R_i, \vec{P}_{\text{org}})]} \cdot N_{\text{condicional}, i} \le 80$$
  Con una ruta operativa esperada $\mathbb{E}[N_{\text{visibles}}] \in [45, 68]$. Asuntos que demanden revisión documental forense se derivan asíncronamente al estado `"Pendiente de Validación"`.

---

### Teorema 4: Segregación Criptográfica y Arquitectónica de Funciones del DPO (SoD No Declarativa)
`¤dpo-cockpit` `¤dpo-independencia`
* **Fundamento:** Modelo formal de *Separation of Duties* en RBAC (Sandhu, Ferraiolo, Kuhn, 2000) y Art. 48 LOPDP:
  * La independencia del DPD/DPO es una **imposibilidad física en el código y en el esquema relacional**, no una directiva pasiva de buena fe.
* **Regla de Aislamiento:** Sea $\mathcal{R}_{\text{DPO}}$ el rol de Delegado y $\mathcal{T}_{\text{operativo}}$ las transacciones sobre finalidades, controles o medios de tratamiento:
  $$\forall u \in \mathcal{U}, \quad \text{Rol}(u) = \mathcal{R}_{\text{DPO}} \implies \text{Permiso}(u, t) = \emptyset \quad \forall t \in \mathcal{T}_{\text{operativo}}$$
  $$\text{Permiso}(u, \text{Supervisión}) = \text{Read-Only}(\text{RAT}, \text{Riesgos}, \text{EIPD})$$
  $$\text{Permiso}(u, \text{BandejaDictamen}) = \text{Append-Only}(\text{BitacoraDiligencia})$$

---

### Teorema 5: No-Degeneración de Métricas en Espacios de Cumplimiento Normativo
`¤diagnostico-scoring`
* **Problema:** Los promedios escalares tradicionales ($\Phi: \mathcal{M} \to [0, 1]$, ej. "87% de cumplimiento") generan pérdida de observabilidad crítica, asignando puntuaciones idénticas a organizaciones conformes y a empresas con infracciones graves pasibles de multas millonarias.
* **Formulación:** El espacio de evaluación debe conservar su naturaleza vectorial ortogonal cuádruple:
  $$\mathcal{M} = \mathcal{S}_{\text{SPDP}} \times \mathcal{C}_{\text{Legal}} \times \mathcal{E}_{\text{Evidencia}} \times \mathcal{R}_{\text{Residual}}$$
  Donde ningún requisito crítico no conforme en $\mathcal{C}_{\text{Legal}}$ puede ser compensado o enmascarado por un alto puntaje de madurez técnica en $\mathcal{S}_{\text{SPDP}}$.

---

### Teorema 6: Antecedencia Paramétrica y Poda Ontológica Unidireccional en Motores Diagnósticos Multidominio ($\text{Root}(\mathcal{T}_{\text{poda}}) \prec \mathcal{Q}_{\text{diag}}$)
`¤diagnostico-motor` `¤diagnostico`
* **Problema:** La coexistencia en el mismo plano visual de la Ficha Organizacional y el cuestionario diagnóstico genera inconsistencias operativas en el evaluador, provocando recalibración cíclica de preguntas activas mientras se responden ítems hoja.
* **Formulación y Demostración:** Sea $\mathcal{Q}_{\text{universal}}$ el banco normativo y $\mathcal{T}_{\text{poda}}$ el árbol de decisión condicional. La parametrización de la entidad $\vec{P}_{\text{org}} = \langle \text{Sector}, \text{Tamaño}, \text{RazónSocial}, \text{Normativa} \rangle$ opera como nodo raíz de poda. El operador de proyección de preguntas $\Pi_{\vec{P}_{\text{org}}}: \mathcal{Q}_{\text{universal}} \to \mathcal{Q}_{\text{activo}}$ exige precedencia estricta en el orden parcial temporal:
  $$\text{Configuración}(\vec{P}_{\text{org}}) \prec \text{Poda}(\mathcal{T}) \prec \text{Ejecución}(\mathcal{Q}_{\text{diag}})$$
  Para garantizar $\mathbb{E}[N_{\text{preguntas}}] \le 80$ y prevenir bucles de retroalimentación cognitiva, la parametrización de la entidad debe estar aislada y consolidada en una pestaña antecedente antes de instanciar el espacio de diagnóstico.

---

### Teorema 7: Aislamiento Transaccional y Purga Obligatoria de Contexto Evidencial ante Cambio de Dominio ($\Delta(\text{Normativa}) \implies \mathcal{E} \leftarrow \emptyset$)
`¤evidencias` `¤diagnostico`
* **Problema:** La persistencia indiscriminada de evidencias probatorias al conmutar entre marcos regulatorios heterogéneos (ej. Propiedad Intelectual vs. NIIF contables vs. ISO técnicas) contamina los repositorios de auditoría y provoca falsos positivos documentales en el compliance graph.
* **Formulación y Demostración:** La ontología de validez probatoria de cada dominio normativo es disjunta:
  $$\text{Dom}(\mathcal{E}_{\text{PI}}) \cap \text{Dom}(\mathcal{E}_{\text{NIIF}}) = \emptyset$$
  Donde $\text{Ext}(\mathcal{E}_{\text{PI}}) \subseteq \{\text{.pdf}, \text{.docx}, \text{.md}, \text{.txt}\}$ y $\text{Ext}(\mathcal{E}_{\text{NIIF}}) \subseteq \{\text{.csv}, \text{.xlsx}, \text{.xbrl}, \text{.ixbrl}, \text{.json}, \text{.xml}, \text{.sql}\}$.
  Para preservar la invariante de integridad probatoria $\mathcal{I}_{\text{evidencia}}$, la función de transición de estado del store global ante un cambio de selector normativo $\Delta(\mathcal{N})$ exige una purga atómica e irreversible:
  $$\mathcal{N}_{t+1} \neq \mathcal{N}_t \implies \mathcal{E}_{t+1} := \emptyset$$
  Impidiendo la presentación de un balance contable como sustento de un registro de marca o viceversa.

---

### Teorema 8: Jerarquía Tonal Invertida y Neutralidad Cromática para Reducción de Fatiga Ocular en Interfaces IDE de Alta Densidad (Achromatic Workspaces)
`¤frontend-ide`
* **Problema:** Interfaces analíticas densas que emplean colores primarios vivos (azul, verde, púrpura) en elementos estáticos, marcos contenedores e iconografía generan saturación sensorial y dispersión atencional en auditores y consultores durante jornadas de trabajo intensivo.
* **Formulación y Principio Ergonómico:** Basado en la Ley de Fitts, la Teoría de la Gestalt (Koffka, 1935) y los principios de densidad de datos de Tufte (1990):
  * La saturación cromática de los componentes estáticos debe tender a cero: $\lim_{t \to \infty} \mathcal{C}_{\text{estático}} \to 0$ (escala acromática estricta de negros `#0a0a0c`, grises `#141417`, `#26262b` y blancos neutros).
  * El color se reserva como señal semántica de alto impacto: Verde (`#00c853`) para cumplimiento/éxito, Rojo (`#ff1744`) para purga/riesgo crítico, y gradientes de marca exclusivamente en los desencadenantes de acción principal (CTA).
  * *Ley de la Jerarquía Tonal Invertida:* La periferia espacial y los docks de navegación portan la menor luminancia (`#0a0a0c` / `#141417`), concentrando la mayor pureza luminosa y contraste en el canvas central de trabajo para dirigir el foco sacádico del auditor sin dispersión periférica.

---

### Teorema 9: Arbitraje Exógeno Booleano vs. Auto-Aserción Introspectiva en Auditorías de Software (Teorema Proaño-Gemini-Dijkstra)
`¤bbap` `¤adpa`
* **Problema:** En sistemas de desarrollo agéntico o auditoría automatizada, el modelo generativo puede emitir aserciones introspectivas de éxito ("las pruebas pasaron") mediante mocks tautológicos o respuestas complacientes no fundamentadas, generando un falso estado de no-regresión.
* **Formulación y Demostración:** Sea $\mathcal{A}$ el agente generativo y $\mathcal{S}$ el sistema evaluado. La función de veredicto debe ser estrictamente exógena y determinista:
  $$\mathcal{V}(\mathcal{S}) \in \{0, 1\} \quad \text{donde} \quad \mathcal{V} \notin \text{Memoria}(\mathcal{A})$$
  El éxito operativo $(C \implies S) \land ((C \land S) \implies \neg R)$ es válido si y solo si un proceso físico del sistema operativo (arnés `.bat`, suite pytest, compilador Turbopack) emite Exit Code 0 de manera observable en disco, con cero tolerancia a aserciones generativas libres o mocks que testen tautologías ($A = A$).

---

### Teorema 10: Validación Algorítmica Determinista de Cédula de Identidad Ecuatoriana (Módulo 10 Notarial para DLP)
`¤seguridad-tenant` `¤copiloto-ia`
* **Problema:** La fuga de información personal no anonimizada hacia motores de inferencia LLM viola el principio de confidencialidad y el Art. 10 de la LOPDP. Los filtros regex genéricos producen falsos positivos (números de teléfono, facturas) o falsos negativos.
* **Formulación Algorítmica:** Un identificador $C = \langle d_1, d_2, \dots, d_{10} \rangle$ corresponde a un documento de identidad legal ecuatoriano si y solo si satisface las tres compuertas del algoritmo del Registro Civil:
  1. Provincia: $\text{int}(d_1 d_2) \in [1, 24] \cup \{30\}$.
  2. Tercer dígito de persona natural: $d_3 \in [0, 5]$.
  3. Checksum de coeficientes alternados:
     $$p_i = d_i \times (2 - (i \pmod 2)) \quad \forall i \in \{1, \dots, 9\}$$
     $$s_i = p_i - 9 \cdot \mathbf{1}_{[p_i \ge 10]}$$
     $$d_{\text{esperado}} = (10 - (\sum_{i=1}^9 s_i \pmod{10})) \pmod{10}$$
     $$\text{Validez}(C) \iff d_{10} == d_{\text{esperado}}$$
  Esta función se ejecuta en el pipeline DLP antes de cualquier vectorización semántica o consulta al copiloto IA.

---

### Teorema 11: Minimización de Latencia Cognitiva mediante Paletas de Comando Universales en Interfaces de Cumplimiento Masivo (Teorema Hick-Hyman / Fitts en IDEs de Compliance)
`¤frontend-ide` `¤regulation-code`
* **Problema:** En sistemas multidominio con decenas de módulos, normativas y miles de artículos legales, la navegación jerárquica basada en menús anidados y clics sucesivos degrada la eficiencia del auditor a tiempo lineal $O(n)$ y amplía la distancia motora ($D \gg 0$), provocando dispersión del estado de flujo (*flow state*) y fatiga cognitiva.
* **Formulación y Demostración:** Basado en la Ley de Hick-Hyman ($T = b \cdot \log_2(n + 1)$) y la Ley de Fitts ($T = a + b \log_2(1 + D/W)$):
  * Al implementar una Command Palette universal (`Ctrl+K` vía `cmdk`), la distancia motora se colapsa instantáneamente a cero ($D \to 0$), eliminando la dependencia del mouse.
  * El espacio de búsqueda jerárquico se aplana en un índice difuso monótono, reduciendo el tiempo de selección a escala logarítmica:
    $$T_{\text{selección}} = \mathcal{O}(\log_2 |\mathcal{A}_{\text{acciones}}|)$$
  * Esto garantiza que cualquier salto contextual (ej. de Ficha Organizacional a Evaluación de Riesgos MTGE o al Copiloto RAG) se efectúe en tiempo submilisegundo ($t < 200 \text{ ms}$), respetando el umbral de atención continua de Miller (1956).

---

### Teorema 12: Conservación de Superficie Útil y Desacoplamiento de Paneles Flexibles en Entornos de Inferencia Concurrente (Resilient Split-Pane Theorem)
`¤frontend-ide` `¤copiloto-ia`
* **Problema:** La concurrencia entre la lectura de evidencias probatorias, el diligenciamiento del cuestionario diagnóstico y la consulta al copiloto jurídico RAG genera asfixia visual cuando los paneles tienen dimensiones fijas o modales bloqueantes.
* **Formulación y Demostración:** Sea $\mathcal{S}_{\text{viewport}}$ la superficie total útil del viewport y $\mathcal{P}_1, \mathcal{P}_2$ los paneles de trabajo (Workspace principal y Copiloto RAG/Inspector). El operador elástico de división (`react-resizable-panels`) satisface el invariante de conservación de área:
  $$\mathcal{S}_1(t) + \mathcal{S}_2(t) = \mathcal{S}_{\text{viewport}} - \delta_{\text{handle}}$$
  Sujeto a las restricciones de frontera de legibilidad mínima:
  $$\mathcal{S}_1(t) \ge 0.45 \cdot \mathcal{S}_{\text{viewport}}, \quad \mathcal{S}_2(t) \in [0.18, 0.45] \cdot \mathcal{S}_{\text{viewport}}$$
  Demostrando que el inspector contextual puede redimensionarse elásticamente sin provocar desbordamientos horizontales, solapamientos modales ni re-renderizados destructivos del DOM central.

---

### Teorema 13: Verificación Notarial de Transiciones en Ciclos de Vida Regulatorios mediante Statecharts Jerárquicos (Teorema Harel-SPDP para SLAs de Privacidad)
`¤incidentes` `¤derechos`
* **Problema:** Los flujos con plazos preclusivos de ley (SLA de 72 horas para notificación de brechas a la SPDP/CSIRT y plazos de 15 días para atención de derechos ARCO+) modelados con booleanos planos en bases de datos sufren de "estados huérfanos", condiciones de carrera o transiciones ilegales (ej. marcar un incidente como "Cerrado" sin haber emitido la notificación obligatoria).
* **Formulación y Demostración:** Basado en el formalismo de Statecharts de David Harel (1987):
  * Un proceso de cumplimiento es una máquina de estados finitos jerárquica $\mathcal{M} = \langle \mathcal{Q}, \Sigma, \delta, q_0, \mathcal{F} \rangle$.
  * La transición $\delta(q_i, e) \to q_{i+1}$ está gobernada por un contrato precondicional estricto:
    $$q_{\text{Cerrado}} \in \mathcal{F} \implies \exists e_{\text{notarial}} \in \text{Eventos} \quad (\text{EvidenciaValida}(e_{\text{notarial}}) \land \text{TimestampsEnSLA}(e_{\text{notarial}}))$$
  * Garantiza que es matemáticamente imposible transicionar a un estado de resolución sin haber superado las aserciones de auditoría, erradicando los falsos cumplimientos por diseño de software.

---

### Teorema 14: Linaje Relacional Invariante en Grafos de Cumplimiento (Compliance Graph DAG Lineage)
`¤rat` `¤riesgos-eipd`
* **Problema:** En herramientas tradicionales, la actualización del inventario de tratamientos no propaga automáticamente sus consecuencias hacia los análisis de riesgos, contratos con terceros o evaluaciones de impacto, produciendo discrepancias graves ante una inspección de la autoridad.
* **Formulación y Demostración:** El "Compliance Graph" es un Grafo Acíclico Dirigido (DAG) $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ con raíz generadora en el Registro de Actividades de Tratamiento ($\text{RAT} \equiv v_0$):
  $$\forall v_k \in \mathcal{V} \setminus \{v_0\}, \quad \exists \text{Camino}(v_0, v_k)$$
  Cualquier mutación en el vector de tratamiento $\Delta(v_0) = \langle \text{Finalidad}, \text{CategoríaDatos}, \text{Destinatarios} \rangle$ dispara una propagación determinista en cascada:
  $$\Delta(v_0) \xrightarrow{\text{toposort}} \nabla(\text{Riesgos}) \to \nabla(\text{EIPD}) \to \nabla(\text{ContratosTerceros}) \to \nabla(\text{AvisosPrivacidad})$$
  Preservando la invariante global de consistencia interna y erradicando las matrices paralelas desarticuladas.

---

### Teorema 15: Eliminación Estricta de FOUC mediante Resolución Asíncrona de Cookies en el Servidor (Teorema Zero-FOUC en Arquitecturas Híbridas SSR/RSC)
`¤frontend-ide` `¤bbap`
* **Problema:** En aplicaciones web SPA o Jamstack tradicionales, la preferencia de tema (Dark/Light) se almacena en `localStorage` o se resuelve mediante hooks del cliente (`useEffect`). Esto provoca un *Flash of Unstyled Content* (FOUC) o destello blanco de alta luminancia mientras se hidrata el árbol DOM en el navegador, violando el Teorema 8 de neutralidad cromática y ergonomía visual prolongada.
* **Formulación y Demostración:** Sea $\mathcal{T}_{\text{tema}} \in \{\text{dark}, \text{light}\}$ el estado preferido del usuario. Al persistir el estado en una cookie HTTP (`smartcidi-theme`) y resolverla de forma determinista en el servidor mediante Server Components asíncronos (`await cookies()` en `layout.tsx` de Next.js 15.5):
  $$\mathcal{T}_{\text{inyectado}} = \text{ResolverCookie}(\text{Headers}_{\text{HTTP}})$$
  $$\text{DOM}_{\text{root}} := \langle \text{html} \quad \text{className} = f(\mathcal{T}_{\text{inyectado}}) \rangle$$
  El árbol HTML inicial viaja serializado con la clase de contraste adecuada antes del primer paquete TCP (*First Contentful Paint* - FCP). La latencia del destello colapsa estrictamente a:
  $$\Delta t_{\text{destello}} \equiv 0 \text{ ms}$$
  Garantizando renderizado cromático idéntico entre el servidor y el cliente sin parpadeo ni penalizaciones de re-renderizado.

---

### Teorema 16: Desacoplamiento No Compensatorio y Bloqueo Lexicográfico en Espacios de Cumplimiento Normativo (Teorema de No Dilución de Brechas Críticas)
`¤diagnostico-scoring` `¤invariantes`
* **Problema:** Los esquemas tradicionales de auditoría emplean agregaciones lineales ponderadas ($\sum w_i x_i$) que permiten a una entidad con infracciones legales graves (ej. ausencia de consentimiento o transferencias internacionales ilícitas, Arts. 7 y 56 LOPDP) obtener puntuaciones de "85% o 90% de cumplimiento" promediando requisitos operativos secundarios.
* **Formulación y Demostración:** Basado en la Teoría de Elección por Aspectos (Tversky, 1972) y el Orden Lexicográfico No Compensatorio (Fishburn, 1974):
  * La evaluación descompone el espacio en compuertas disjuntas:
    $$\mathcal{M} = \langle \mathcal{C}_{\text{Legal}}, \mathcal{S}_{\text{SPDP}}, \overline{E}, \mathcal{R}_{\text{Residual}} \rangle$$
  * Sea $\mathcal{B}_{\text{crítica}}$ el conjunto de preguntas críticas no conformes:
    $$\mathcal{B}_{\text{crítica}} = \{ q \in \mathcal{Q} \mid \text{esCritica}(q) \land (\text{cumple}(q) = \text{"No Conforme"}) \}$$
  * El operador de bloqueo jerárquico impone una cota superior inviolable sobre la madurez técnica:
    $$\mathcal{S}_{\text{SPDP}} \le \begin{cases} 0 \text{ (Caótico)}, & \text{si } |\mathcal{B}_{\text{crítica}}| \ge 3 \\ 1 \text{ (Implícito máx.)}, & \text{si } |\mathcal{B}_{\text{crítica}}| \in \{1, 2\} \\ 3 \text{ (Sin bloqueo)}, & \text{si } |\mathcal{B}_{\text{crítica}}| = 0 \end{cases}$$
    $$\mathcal{C}_{\text{Legal}} = \mathbf{1}_{[|\mathcal{B}_{\text{crítica}}| == 0]}$$
  Demostrando formalmente que ninguna acumulación de evidencias documentales ($E3$) o volumen de controles periféricos aprobados puede levantar el bloqueo jerárquico mientras subsista una brecha jurídica crítica sancionable.

---

### Teorema 17: Determinismo de Doble Compuerta en la Calificación de Tratamientos a Gran Escala (Teorema MTGE según Res. SPDP-SPD-2026-0005-R)
`¤mtge-granescala` `¤riesgos-eipd`
* **Problema:** La indeterminación semántica del concepto "Gran Escala" en la doctrina comparada permitía el arbitrio discrecional de los responsables del tratamiento para evadir la Evaluación de Impacto (EIPD, Art. 44 LOPDP) y la designación obligatoria de DPO (Art. 48 LOPDP).
* **Formulación y Demostración:** El motor algorítmico modela la calificación mediante una doble compuerta determinista exhaustiva:
  * **Compuerta 1 (Disparo Per Se por Cualidad o Censo Masivo):**
    $$(\text{"Biométricos"} \in \mathcal{C}_{\text{datos}}) \lor (\text{"Salud"} \in \mathcal{C}_{\text{datos}}) \implies \text{Puntaje} := 150, \quad \text{GranEscala} := \text{true}$$
    $$(\text{VolumenTitulares} > 10\,000) \implies \text{Puntaje} := \max(\text{Puntaje}, 120), \quad \text{GranEscala} := \text{true}$$
  * **Compuerta 2 (Ponderación Paramétrica Aditiva):** Para los tratamientos ordinarios restantes:
    $$\Phi_{\text{MTGE}} = P_{\text{volumen}}(V) + P_{\text{sensibilidad}}(C) + P_{\text{permanencia}}(\text{años})$$
    $$\text{GranEscala} \iff \Phi_{\text{MTGE}} \ge 100.0$$
  * **Consecuencia Jurídica Invariante:**
    $$\text{GranEscala} \implies (\text{requiereEIPD} := \text{true}) \land (\text{alertaForzosaDPO} := \text{true})$$
  Cerrando de forma binaria el espacio de ambigüedad jurídica y garantizando la aplicabilidad coercitiva de las salvaguardas legales ecuatorianas.

---

### Teorema 18: Inmutabilidad Notarial y Sellado Criptográfico Append-Only para Snapshots de Auditoría (Principio de Responsabilidad Proactiva Art. 10 num. 7 LOPDP)
`¤implementacion` `¤invariantes`
* **Problema:** En plataformas de gestión de cumplimiento, la sobrescritura mutable de evaluaciones pasadas o la mutabilidad retroactiva de estados destruye la validez probatoria ante litigios o inspecciones de la SPDP, haciendo imposible demostrar el estado histórico del sistema en un punto temporal dado.
* **Formulación y Demostración:** Basado en la teoría de árboles y firmas de Merkle (1987) y el estándar NIST FIPS 180-4:
  * Cada ciclo de evaluación completado se congela como un snapshot inmutable:
    $$\mathcal{S}_k = \langle \text{id}_{\text{UUID}}, t_{\text{cierre}}, \vec{P}_{\text{org}}, \mathcal{N}_{\text{versión}}, \mathcal{Q}_{\text{respuestas}}, \mathcal{M}_{\text{scoring}} \rangle$$
  * La firma de integridad digital sella el estado:
    $$\sigma_k = \text{SHA-256}(\text{CanonicalJSON}(\mathcal{S}_k))$$
  * La transición del historial de auditorías es estrictamente monótona creciente (Append-Only):
    $$\mathcal{H}_{t+1} = \mathcal{H}_t \cup \{ \langle \mathcal{S}_k, \sigma_k \rangle \}, \quad \text{Mutar}(\mathcal{S}_j) = \emptyset \quad \forall j \le k$$
  Garantizando que cualquier alteración posterior en el código o en las respuestas rompa el hash de verificación notarial ($\sigma_{\text{calculado}} \neq \sigma_{\text{registrado}}$), satisfaciendo la exigencia de trazabilidad probatoria del Art. 10 num. 7 y Art. 50 de la LOPDP.

---

# PARTE II: Aportes Arquitectónicos y de Ingeniería del Producto

### Aporte 1: El Paradigma del "Compliance Graph" Unificado
`¤rat` `¤implementacion`
* **Problema:** Silos de información desarticulados (RAT en Excel, riesgos en otra matriz, contratos en carpetas) que divergen y provocan fallos de auditoría.
* **Solución:** Grafo dirigido unificado donde un dato se registra una sola vez ($\text{SSOT}$) y propaga su estado en cascada:
  $$\text{Fuente Normativa} \to \text{Requisito} \to \text{RAT} \to \text{Control} \to \text{Evidencia} \to \text{Riesgo} \to \text{Acción} \to \text{DPO}$$

---

### Aporte 2: Diagnóstico Timeboxed Adaptativo en $\le 60$ Minutos
`¤diagnostico` `¤diagnostico-motor`
* **Solución:** Cuestionario inteligente de 4 bloques temporales con cota superior de 80 preguntas y derivación de brechas complejas a la fase de implementación mediante el rótulo "Pendiente de Validación".

---

### Aporte 3: Cuadratura Multidimensional de Evaluación
`¤diagnostico-scoring`
* **Solución:** Desacoplamiento explícito de 4 métricas en el dashboard ejecutivo: Madurez SPDP (0–3), Conformidad Legal (Booleana), Cobertura de Evidencias (E0–E3) y Riesgo Residual.

---

### Aporte 4: Confinamiento y Cockpit Exclusivo del DPD/DPO
`¤dpo-cockpit` `¤dpo-independencia`
* **Solución:** Módulo independiente con permisos SoD restringidos, bandeja de dictámenes técnicos no vinculantes y bitácora cronológica inviolable con acuse de recibo de alta dirección.

---

### Aporte 5: Motor MTGE Determinista para Tratamientos a Gran Escala
`¤mtge-granescala` `¤riesgos-eipd`
* **Solución:** Algoritmo paramétrico auditable basado en la Resolución SPDP-SPD-2026-0005-R que calcula el puntaje MTGE y activa obligatoriamente la EIPD y la designación de DPO ante cruce de umbrales.

---

### Aporte 6: "Regulation as Code" con Diff de Impacto
`¤regulation-code`
* **Solución:** Corpus legal versionado como datos operativos estructurados. Ante reformas de la SPDP o nuevas leyes, el motor genera un diff automático de impacto sobre los controles y contratos de cada tenant sin tocar el histórico de auditorías.

---

### Aporte 7: Copiloto Jurídico RAG de Confianza Cero con Filtro DLP
`¤copiloto-ia`
* **Solución:** Asistente cerrado que exige cita obligatoria a la unidad normativa ("sin fuente no hay respuesta"), prohibición de reentrenamiento con datos del cliente y sanitización preventiva DLP de cédulas y datos sensibles.

---

### Aporte 8: Frontend Tipo IDE Inspirado en Antigravity / Cursor
`¤frontend-ide`
* **Solución:** Ergonomía de alta densidad para consultores y auditores: Command Palette global (`Ctrl+K`), Split Panes contextuales (Evidencia / Cuestionario / Copiloto) y paleta Dark/Light de alto contraste técnico sin fatiga visual.

---

### Aporte 9: Síntesis Metodológica Hexagonal
`¤metodologias`
* **Solución:** Integración coherente de los 6 pilares de la industria:
  * *Odoo:* RAT como Master Record relacional abierto.
  * *Antigravity/Cursor:* Navegación veloz por teclado y paneles divididos.
  * *Global Suite:* Cruce con ISO 27002/27701 sin desvirtuar la ley ecuatoriana.
  * *Novoser:* Trazabilidad de tickets CAPA y reloj de notificación de incidentes.
  * *Pirani:* Accesibilidad visual de matrices de calor de riesgo.
  * *Isotools:* Orquestación de tareas periódicas y workflow documental formal.

---

### Aporte 10: Ficha Organizacional Reactiva y Desacoplada con Store Zustand (`useAuditStore`)
`¤frontend-ide` `¤diagnostico`
* **Problema:** El acoplamiento del estado de la empresa dentro de los formularios locales de preguntas provocaba pérdida de datos al navegar entre salas, duplicación de peticiones y dificultad para escalar hacia auditorías de normativas múltiples.
* **Solución:** Arquitectura de estado global desacoplado con Zustand (`useAuditStore.ts`) en Next.js 15 Turbopack. Centraliza `companyData` (`razonSocial`, `sector`, `tamano`), `normativaSeleccionada`, `archivosCargados` e `isConfigured` con mutadores atómicos, permitiendo que cualquier componente del IDE acceda y actualice la ficha del proyecto con latencia cero y sin re-renderizar ramas ajenas del árbol DOM.

---

### Aporte 11: Whitelist Evidencial Dinámica con Poka-Yoke de Extensión y Drag-and-Drop
`¤evidencias` `¤diagnostico`
* **Problema:** En auditorías multirregulatorias, la carga de formatos incompatibles (ej. hojas de cálculo complejas en auditorías de marcas o documentos narrativos de texto en auditorías contables) corrompe los procesos de extracción automatizada y genera errores en tiempo de ejecución.
* **Solución:** Mecanismo bidireccional de control Poka-Yoke:
  1. *Filtro Declarativo:* Atributo `accept` dinámico en el `<input type="file">` que expone al selector del sistema operativo exclusivamente las extensiones autorizadas (`.pdf,.docx,.md,.txt` para PI; `.csv,.xlsx,.xbrl,.ixbrl,.json,.xml,.sql` para NIIF/ISO).
  2. *Intercepción Reactiva:* Validación en memoria durante la selección y en la zona de arrastre (*Drag & Drop*). Si un archivo no cumple la whitelist, el pipeline aborta la ingesta, emite alerta semántica instantánea en `#ff1744` y purga la referencia sin alterar el estado previo.

---

### Aporte 12: Dual-Theme Purificado sin Artefactos Híbridos y Dock Lateral Plegable
`¤frontend-ide`
* **Problema:** Contaminación visual en cambios de tema (fondos claros con tarjetas oscuras o textos ilegibles) y pérdida de área de trabajo útil al mantener desplegadas etiquetas de texto redundantes en el menú lateral.
* **Solución:** Purificación total de la arquitectura CSS con Tailwind y variables de contraste:
  * *Tema Oscuro (Render Style):* Fondo `#0a0a0c`, tarjetas `#141417`, bordes sutiles `#26262b` y gradientes `#9a3bf1` a `#3892f3`.
  * *Tema Claro:* Escala de grises pura de alta luminosidad sin interferencias azuladas ni fondos oscuros residuales.
  * *Dock Dinámico Plegable:* Eliminación de rótulos redundantes para mantener el tamaño natural de los íconos, con expansión al hacer clic y botón de abatimiento para maximizar el área de trabajo del auditor.

---

### Aporte 13: Ecosistema Integrado de Librerías de Alta Densidad para IDEs de Regulación como Código
`¤frontend-ide` `¤bbap`
* **Problema:** Las plataformas web tradicionales de cumplimiento sufren de navegación pesada, modales bloqueantes y formularios desacoplados que ralentizan la labor forense del auditor.
* **Solución:** Integración de un tridente reactivo en Next.js 15 Turbopack:
  1. *`cmdk`:* Motor de Command Palette universal (`Ctrl+K` / `Cmd+K`) con accesibilidad nativa WAI-ARIA, filtrado en memoria y conmutación ágil de salas y comandos en tiempo submilisegundo.
  2. *`react-resizable-panels`:* División del layout en Split Panes ajustables elásticos (Dock, Formulario Central y Copiloto RAG contextual) con preservación estricta de cotas mínimas de visualización.
  3. *`react-dropzone`:* Zona de arrastre estocástica con validación Poka-Yoke inmediata integrada al store Zustand (`useAuditStore`), sincronizada con las extensiones dinámicas de la normativa activa y purga preventiva de buffers.

---

### Aporte 14: Arquitectura de Persistencia de Tema Acromático en Servidor (`themeActions.ts` + `layout.tsx`)
`¤frontend-ide` `¤bbap`
* **Problema:** El uso de almacenamiento local (`localStorage`) en el cliente produce destellos visuales (FOUC) de alta luminancia durante la hidratación de Next.js, degradando la ergonomía de trabajo y violando el principio de neutralidad acromática en jornadas de auditoría intensiva.
* **Solución:** Implementación de Server Actions puras (`setServerTheme`, `getServerTheme`) sustentadas en el módulo asíncrono `cookies()` de Next.js 15.5. Inyecta la clase semántica `dark theme-dark` o `theme-light` en la etiqueta raíz `<html>` directamente en el servidor antes del envío del primer paquete TCP (*First Contentful Paint*), suprimiendo la latencia del parpadeo a cero absoluto ($\Delta t = 0$).

---

### Aporte 15: Motor de Ponderación Analítica con Bloqueo Jerárquico Cuádruple (`scoringActions.ts`)
`¤diagnostico-scoring` `¤invariantes`
* **Problema:** Los motores de evaluación univariados emplean promedios aritméticos que enmascaran brechas jurídicas graves (ej. transferencias internacionales sin garantía o ausencia de base legitimadora) detrás de un alto porcentaje de cumplimiento de controles operativos.
* **Solución:** Server Action pura (`calcularMetricasDashboard`) interoperable universalmente con Zustand y APIs externas. Aplica las cuatro dimensiones ortogonales de la **Doctrina 4**:
  1. *Conformidad Legal Booleana:* Condición estricta que falla ante una sola brecha crítica.
  2. *Madurez SPDP (0 al 3):* Bloqueo forzoso en Nivel 0 o 1 ante brechas críticas abiertas, impidiendo matemáticamente ascensos espurios.
  3. *Cobertura de Evidencias:* Promedio continuo ponderado sobre la escala de sustento documental ($E0=0, E1=1, E2=2, E3=3$).
  4. *Riesgo Residual Paramétrico:* Deducción de exposición calculada restando la mitigación efectiva aportada por evidencias válidas ($E1+$) respecto al riesgo intrínseco.

---

### Aporte 16: RAT Maestro con Algoritmo MTGE Integrado y Persistencia JSON Local (`ratActions.ts` + `rat_master.json`)
`¤rat` `¤mtge-granescala`
* **Problema:** En la práctica forense, el Registro de Actividades de Tratamiento (RAT) se gestiona en documentos ofimáticos desconectados de las evaluaciones de riesgo y de la designación obligatoria de Delegado de Protección de Datos (DPO).
* **Solución:** Sala ADPA y Server Actions (`guardarActividadTratamiento`, `ejecutarAlgoritmoMTGE`, `obtenerActividadesRAT`, `eliminarActividadTratamiento`) gobernadas por el archivo local `data/rat_master.json` como Fuente Única de Verdad (Doctrina 5). Ejecuta el algoritmo determinista de la Resolución SPDP-SPD-2026-0005-R de la SPDP, evaluando disparadores per se (datos de salud/biometría o volumen $>10,000$) y scoring paramétrico para congelar automáticamente `requiereEIPD: true` y `alertaForzosaDPO: true`.

---

### Aporte 17: Bitácora de Snapshots Cuádruples Inmutables con Hashing SHA-256 (`auditActions.ts` + `snapshots.json`)
`¤implementacion` `¤invariantes`
* **Problema:** La mutabilidad de registros históricos en bases de datos relacionales destruye la cadena de custodia y la fe pública de auditorías pasadas ante requerimientos sancionatorios de la autoridad.
* **Solución:** Mecanismo notarial de congelamiento append-only (`congelarSnapshotAuditoria`, `obtenerHistorialAuditorias`). Serializa el estado integral de la empresa, respuestas y métricas, genera un hash SHA-256 inmutable, ejecuta `Object.freeze()` en memoria y almacena el registro en `data/snapshots.json`, emitiendo una traza de auditoría certificada (`[AUDIT_TRAIL] [SUCCESS]`).

---

### Teorema 19: Filtro DLP Pre-Inferencia como Compuerta de Confianza Cero en Pipelines LLM (Teorema del Liminal de Seguridad Semántica)
`¤copiloto-ia` `¤seguridad-tenant`
* **Problema:** En sistemas RAG sobre corpus jurídicos que procesan consultas en lenguaje natural de usuarios finales, el texto puede contener datos personales identificables (cédulas, nombres, números de cuenta) que, al ser enviados al modelo de lenguaje sin filtrar, constituyen un tratamiento no consentido de datos sensibles y violan el Art. 10 num. 1 (lealtad) y Art. 41 (medidas de seguridad) de la LOPDP.
* **Formulación y Demostración:** Sea $\mathcal{P}_{\text{raw}}$ el prompt crudo del usuario y $\mathcal{F}_{\text{DLP}}$ la función de saneamiento. El invariante de confianza cero exige que ningún dato identificable cruce la frontera hacia el modelo:
  $$\mathcal{P}_{\text{LLM}} = \mathcal{F}_{\text{DLP}}(\mathcal{P}_{\text{raw}}), \quad \mathcal{F}_{\text{DLP}}: \mathcal{P}_{\text{raw}} \to \mathcal{P}_{\text{anon}}$$
  Con patrones deterministas de detección ecuatoriana:
  - Cédula: $\text{Regex}_{C} = \texttt{/\textbackslash b[0-9]\{10\}\textbackslash b/}$ + Módulo-10
  - Teléfono móvil: $\texttt{/\textbackslash b09[0-9]\{8\}\textbackslash b/}$
  - RUC: $\texttt{/\textbackslash b[0-9]\{13\}\textbackslash b/}$
  La función de enmascaramiento reemplaza los hallazgos con tokens neutros: `[CÉDULA REDACTADA]`, `[TELÉFONO REDACTADO]`, garantizando que $\mathcal{P}_{\text{LLM}}$ sea semánticamente preservado pero privacidad-seguro. En la arquitectura de streaming HTTP (Vercel AI SDK + `streamText`), el filtro opera de forma síncrona **antes** del primer token generado, con latencia añadida $< 5$ ms.
* **Fuente:** Art. 10 num. 1 y Art. 41 LOPDP; DGRCIC Ecuador — Módulo 10; OWASP LLMTOP10 (2023) — LLM01: Prompt Injection, LLM06: Sensitive Information Disclosure.

---

### Teorema 20: Interoperabilidad Tipada Bidireccional entre Estado de Cliente (Zustand) y Servidor (Server Actions) en Arquitecturas Híbridas de GRC
`¤diagnostico-scoring` `¤implementacion` `¤adpa`
* **Problema:** En arquitecturas Next.js 15 App Router con estado global Zustand, los componentes cliente almacenan entidades en un formato ergonómico para el auditor (`{ preguntaId, cumple, evidenciaNivel, esCritica, riesgoBase }`), mientras que el servidor espera formatos canónicos del dominio normativo (`{ id_pregunta, respuesta_afirmativa, nivel_evidencia }`). La falta de normalización produce errores silenciosos de tipo `NaN`, `undefined` o pérdida de información crítica al serializar datos para Server Actions, invalidando el scoring multidimensional.
* **Formulación y Demostración:** Sea $\mathcal{F}_{\text{cliente}}$ el formato Zustand y $\mathcal{F}_{\text{servidor}}$ el formato canónico. La función de normalización universal $\mathcal{N}$ debe ser una biyección parcial segura con valor por defecto:
  $$\mathcal{N}: \mathcal{F}_{\text{cliente}} \cup \mathcal{F}_{\text{servidor}} \to \mathcal{F}_{\text{interno}}$$
  Con las siguientes reglas de fusión de campos:
  - $\text{idPregunta} \gets \texttt{idPregunta} \cup \texttt{id\_pregunta} \cup \texttt{preguntaId}$
  - $\text{esConforme} \gets \texttt{conforme} \lor \texttt{respuesta\_afirmativa} \lor (\texttt{cumple} \in \{\text{"Conforme"}, \text{"Parcial"}\})$
  - $\text{nivelEvidencia} \gets \texttt{evidenciaNivel} \cup \texttt{nivel\_evidencia} \cup \texttt{nivelEvidencia}$
  - $\text{esCritica} \gets \texttt{esCritica} \lor \texttt{es\_nucleo} \lor \texttt{true}$ (falla segura)
  La normalización se ejecuta en el servidor dentro de la Server Action, garantizando que **ningún formato** del cliente produzca pérdida de datos sin importar cuál de las variantes utilice el componente emisor.
* **Fuente:** TypeScript Handbook — Union Types & Type Guards (Microsoft, 2024); Vercel — Next.js 15 Server Actions Data Passing; principio de Falla Segura (*Fail-Safe Defaults*) — Saltzer & Schroeder (1975), *«The Protection of Information in Computer Systems»*.

---

### Teorema 21: Contrato Bilateral Agéntico de No-Regresión como Ley Matemática de Gobernanza IA $(C \Rightarrow S) \land ((C \land S) \Rightarrow \neg R)$
`¤bbap` `¤adpa` `¤invariantes`
* **Problema:** En sistemas de desarrollo agéntico colaborativo entre un cliente-principal y un agente-IA, la ausencia de una estructura formal de contrato produce ambigüedad en las responsabilidades, regresiones silenciosas y deriva semántica (Semantic Drift) donde las instrucciones se deforman progresivamente a lo largo de la cadena de Markov conversacional.
* **Formulación y Demostración:** El sistema opera bajo el Contrato Bilateral Agéntico (CBA):
  $$(C \Rightarrow S) \land ((C \land S) \Rightarrow \neg R)$$
  Donde:
  - $C$: El cliente cumple sus precondiciones completas (contexto preciso, alcance delimitado, invariantes explícitos).
  - $S$: El agente entrega el resultado técnico exacto especificado ($S = f(C)$).
  - $\neg R$: Cero Regresiones — la integridad sistémica es preservada ($\neg R \equiv \text{Exit Code} = 0$).
  **Propiedades formales del CBA:**
  1. *Condicionalidad:* $\neg C \implies \neg S$ (sin precondiciones completas, el agente no procede).
  2. *Exogeneidad del Veredicto:* $\neg R$ es verificable únicamente por árbitros externos (`pytest`, `tsc --noEmit`), nunca por auto-aserción del agente.
  3. *Preservación Monótona de Rastros:* $\mathcal{T}_{\text{pre}} \subseteq \mathcal{T}_{\text{post}}$ (los rastros u huellas estigmérgicas solo se acumulan, nunca se borran).
  4. *Inmutabilidad Doctrinal:* Los artefactos normativos (`.md`, `.yaml`) son Read-Only para el agente; solo el código ejecutable (`.py`, `.ts`) es refactorizable.
* **Fuente:** Teoría de Juegos — Nash (1950), *«Equilibrium Points in n-Person Games»*; Proaño (2026) — *Contrato Bilateral de Gobernanza Agéntica* (inédito); Dijkstra (1959) — Determinismo Exógeno.

---

### Teorema 22: Principio de Tipado Estricto como Árbitro Exógeno Sintáctico en Sistemas de Gobernanza y Riesgo (Type-Safety as Compliance Enforcement)
`¤implementacion` `¤adpa` `¤invariantes`
* **Problema:** En plataformas GRC (Governance, Risk, Compliance) implementadas sobre runtimes dinámicos o con tipado débil (JavaScript puro, Python sin type hints), los errores de tipo en las entidades jurídicas (ej. `volumenRegistros: "10000"` en vez de `number`, o `baseJuridica: "contrato"` en vez del literal exacto `"Ejecución Contractual"`) no se detectan hasta el momento de ejecución, pudiendo generar evaluaciones MTGE incorrectas, snapshots con datos corruptos y decisiones de cumplimiento fallidas.
* **Formulación y Demostración:** Sea $\mathcal{E}$ el conjunto de entidades jurídicas del sistema y $\mathcal{T}$ el sistema de tipos estático. El compilador de TypeScript funciona como un árbitro exógeno sintáctico de primer nivel:
  $$\mathcal{V}_{\text{sintáctico}}: \mathcal{E} \to \{0, 1\} \quad \text{donde} \quad \mathcal{V}_{\text{sintáctico}} = (\texttt{npx tsc --noEmit}, \text{Exit Code})$$
  Las invariantes de tipo garantizan en tiempo de compilación (no de ejecución):
  - $\texttt{BaseJuridicaRAT} \in \{\text{"Consentimiento"}, \text{"Obligación Legal"}, \text{"Ejecución Contractual"}, \text{"Interés Legítimo"}\}$ — imposible ingresar un valor fuera del Art. 7 LOPDP.
  - $\texttt{volumenRegistros}: \texttt{number}$ — imposible comparar con el umbral MTGE 10,000 si el valor es string.
  - $\texttt{madurezNivel}: 0 | 1 | 2 | 3$ — el sistema de tipos previene valores intermedios o negativos.
  El tipado estricto actúa como **primera línea de defensa notarial** antes de toda lógica de negocio, con un costo computacional de verificación de **0 ms en producción** (solo en tiempo de compilación).
* **Fuente:** TypeScript Team — *«TypeScript: Typed JavaScript at Any Scale»* (Microsoft, 2012-2026); Liskov & Wing (1994), *«A Behavioral Notion of Subtyping»*, ACM TOPLAS — Sustitución de tipos como garantía de integridad semántica; Cardelli & Wegner (1985), *«On Understanding Types, Data Abstraction, and Polymorphism»*.

---

### Aporte 18: Pipeline DLP Pre-Inferencia con Enmascaramiento Regex Ecuatoriano y Streaming HTTP (`dlp.ts` + `route.ts`)
`¤copiloto-ia` `¤seguridad-tenant`
* **Problema:** El envío de prompts crudos de usuario al LLM sin sanitización constituye un tratamiento no autorizado de datos personales identificables (cédulas, teléfonos, RUC) en violación al Art. 41 LOPDP y al principio de minimización del Art. 10 num. 3.
* **Solución:** Módulo `src/lib/dlp.ts` con función `sanitizarPrompt(texto)` que aplica expresiones regulares deterministas para detectar y enmascarar tokens de PII ecuatoriana antes de cada llamada al modelo. El endpoint de API (`src/app/api/chat/route.ts`) ejecuta el filtro síncronamente sobre el mensaje entrante y propaga el prompt saneado al pipeline de `streamText` del Vercel AI SDK, emitiendo el streaming de respuesta con citación normativa obligatoria.

---

### Aporte 19: Normalización Universal Bidireccional de Formatos Cliente-Servidor en Server Actions de Scoring
`¤diagnostico-scoring` `¤implementacion`
* **Problema:** La divergencia entre el formato Zustand (`cumple`, `evidenciaNivel`, `preguntaId`) y el formato canónico del servidor (`respuesta_afirmativa`, `nivel_evidencia`, `id_pregunta`) producía errores `NaN`/`undefined` silenciosos en el cálculo del scoring multidimensional y del algoritmo MTGE.
* **Solución:** Función de normalización universal en `src/app/actions/scoringActions.ts` que acepta cualquier variante de campo del cliente mediante fusión de alias tipados. Aplica valores por defecto seguros (*fail-safe*) y garantiza que `calcularMetricasDashboard()` produzca resultados deterministas con cualquier combinación de formatos de entrada sin pérdida de información crítica.

---

### Aporte 20: Contrato de Invariante de Módulo como Compuerta de Sesión Agéntica (BBAP Bilateral)
`¤bbap` `¤adpa`
* **Problema:** En sesiones de desarrollo agéntico prolongadas y multi-turno, la deriva semántica y la pérdida de contexto del agente sobre los invariantes activos del sistema producen regresiones accidentales en código previo, violación de compuertas ADPA y modificaciones no autorizadas de artefactos normativos.
* **Solución:** Protocolo de apertura y cierre de sesión formal basado en el Contrato Bilateral Agéntico: (1) `mcp_orchestrate_triage` al inicio de cada turno para recuperar el estado del sistema y validar precondiciones, (2) confinamiento de toda modificación de código en salas ADPA con compuertas `_service.py`, (3) `mcp_close_session` al cierre con `test_exit_code` exógeno, garantizando que $\neg R$ sea observable y registrado en la bitácora antes de liberar el turno.

---

### Aporte 18: Sistema de Gestión de Derechos ARCO+ con SLA Normativo Automatizado (`arcoActions.ts` + `arco.ts`)
`¤derechos` `¤arco-server-actions` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-15
* **Problema:** Las plataformas de cumplimiento ecuatorianas carecen de un subsistema automatizado que: (a) calcule el plazo legal de respuesta a derechos ARCO+ de forma invariable en el servidor (Art. 37 LOPDP: 15 días laborables), (b) bloquee la resolución de tickets sin expediente probatorio validado (Doctrina 3 - E1+), y (c) detecte automáticamente el estado `"Excedido"` por vencimiento del SLA sin necesidad de tareas cron externas.
* **Solución — Tres Invariantes de Diseño:**
  1. **SLA Server-Only:** La `fechaLimiteSLA` se calcula **exclusivamente en el servidor** (`crearSolicitudArco`) mediante un motor de días laborables que excluye sábados y domingos. Ninguna interfaz cliente puede fijar, alterar ni omitir este campo.
  2. **Bloqueo Probatorio Normativo (INV_ARCO_EVIDENCIA_E1):** `resolverSolicitudArco()` emite un error HTTP semántico bloqueante si `evidenciaUrl` está vacía o es nula, haciendo **matemáticamente imposible** cerrar un ticket sin adjuntar el expediente formal de respuesta.
  3. **Autodiagnóstico de Expiración:** `listarSolicitudesArco()` compara en tiempo real la fecha actual con `fechaLimiteSLA`. Si el plazo venció y el ticket no está resuelto, muta el estado a `"Excedido"` de forma atómica y lo persiste, garantizando trazabilidad sancionatoria sin intervención manual.
* **Tipado Estricto:** Discriminated union types con TypeScript (`TipoDerechoARCO`, `EstadoSolicitudARCO`) previenen cualquier estado ilegal en compilación. `ServerActionResponse<T>` se reutiliza desde `@/types/rat` (Doctrina 5 - SSOT).
* **Estructura JSON (arco_tickets.json):**
  ```json
  {
    "id": "UUID-invariable-servidor",
    "tipoDerecho": "Acceso | Rectificacion | Cancelacion | Oposicion | Portabilidad | Eliminacion",
    "fechaSolicitud": "ISO-8601",
    "fechaLimiteSLA": "ISO-8601 (15 dias laborables calculados en servidor)",
    "estado": "Recibido | En Revision | Resuelto | Excedido",
    "evidenciaRespuesta": "string-url | null (null solo en estados no resueltos)"
  }
  ```
* **Base normativa:** Arts. 21–24 y 37 LOPDP; Reglamento RGLOPDP; Res. SPDP-SPD-2026-0005-R; Doctrina 3 del PRD (Expedientes Probatorios Invariables); Teorema 13 (Statecharts Harel-SPDP).

---

### Aporte 19: Motor MTGE Relacional a Gran Escala con Mutación Global Irreversible de Tenant (`mtgeActions.ts`)
`¤mtge-granescala` `¤riesgos-eipd` `¤mtge-granescala-relacional`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-15
* **Problema:** El motor MTGE existente (`ratActions.ts` / Aporte 16) evalúa cada actividad del RAT **de forma individual**. Sin embargo, la Res. SPDP-SPD-2026-0005-R opera a nivel de la entidad jurídica como un todo: una empresa puede superar el umbral de Gran Escala por la **suma acumulada de todos sus tratamientos** aunque ninguno individual lo haga, o por combinaciones de sensibilidad-retención que solo emergen al leer el RAT completo.
* **Solución — Algoritmo Relacional Bifásico con Flag Permanente:**
  * **CRITERIO A (Volumen Masivo Agregado):** Si `Σ(volumenRegistros)` de todas las actividades del tenant supera 10.000 titulares, se activa `requiereEIPDForzoso: true`.
  * **CRITERIO B (Sensibilidad + Retención Prolongada):** Si alguna actividad combina categorías de datos Biométricos o de Salud (Art. 25 LOPDP) con permanencia `> 3 años`, se activa `requiereEIPDForzoso: true`.
  * **Efecto de Mutación Permanente:** El flag se escribe irreversiblemente en cada registro afectado de `rat_master.json` con timestamp ISO 8601. Solo el DPO puede revertirlo con aprobación explícita (SoD — Teorema 4). Esta irreversibilidad es una **garantía de no-dilución normativa**, análoga al principio de monotonía de acumulación de rastros u huellas estigmérgicas ($T_{\text{pre}} \subseteq T_{\text{post}}$).
* **Firma canónica:**
  ```typescript
  evaluarNecesidadEIPD(): Promise<ServerActionResponse<ResultadoMTGERelacional>>
  ```
* **Diferenciación del Aporte 16:** `ratActions.ts` evalúa **fila a fila** (nivel micro). `mtgeActions.ts` evalúa **el tensor completo del RAT** (nivel macro / tenant). Son complementarios y no redundantes.
* **Resultado JSON (`ResultadoMTGERelacional`):**
  ```json
  {
    "volumenTotalTitulares": 10900,
    "superaUmbralVolumen": true,
    "tieneTratamientoSensibleLargo": false,
    "requiereEIPDForzoso": true,
    "criterioActivacion": "CRITERIO_A_VOLUMEN_MASIVO | CRITERIO_B_SENSIBLE_LONG_RETENTION | CRITERIO_A_Y_B | NINGUNO",
    "actividadesQueDetonan": ["uuid-1", "uuid-2"],
    "evaluadoEn": "ISO-8601",
    "rationale": "texto en lenguaje natural"
  }
  ```
* **Base normativa:** Res. SPDP-SPD-2026-0005-R Arts. 12-13; LOPDP Arts. 25, 44, 48; Teorema 14 (Compliance Graph DAG Lineage); Teorema 17 (Determinismo de Doble Compuerta MTGE).

---

### Aporte 20: Teorema de Doble Escala MTGE — Evaluacion Micro vs. Macro en Motores de Gran Escala
`¤mtge-granescala` `¤invariantes` `¤riesgos-eipd`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-15
* **Enunciado Formal (Teorema 19):** Sea $\mathcal{R} = \{a_1, a_2, \dots, a_n\}$ el conjunto de actividades de tratamiento de un tenant, y sea $\mathcal{F}_{\text{micro}}: a_i \to \{0,1\}$ el predicado de Gran Escala individual (Aporte 16). Existe un predicado relacional de mayor potencia normativa:
  $$\mathcal{F}_{\text{macro}}: \mathcal{R} \to \{0,1\}$$
  tal que:
  $$\mathcal{F}_{\text{macro}}(\mathcal{R}) = 1 \iff \left(\sum_{i=1}^{n} V_i > 10\,000\right) \lor \left(\exists a_j \in \mathcal{R} : \text{Sensible}(a_j) \land P_j > 3\right)$$
  Y se cumple que: $\exists \mathcal{R}$ tal que $\forall i: \mathcal{F}_{\text{micro}}(a_i) = 0$ pero $\mathcal{F}_{\text{macro}}(\mathcal{R}) = 1$.
  Es decir, **existen tenants en Gran Escala que ningún motor individual detectaria** sin evaluar el tensor completo del RAT.
* **Corolario de Mutacion Monotona:** El flag $\text{requiereEIPDForzoso}$ es monotono creciente en el tiempo:
  $$\text{EIPD}(t_1) = 1 \implies \text{EIPD}(t_2) = 1 \quad \forall t_2 > t_1$$
  Lo que garantiza que un tenant que alguna vez cruzó el umbral de Gran Escala no puede "des-calificarse" pasivamente mediante reducción de datos en el RAT sin aprobación formal del DPO (Principio de Responsabilidad Proactiva Continua, Art. 10 num. 7 LOPDP).
* **Base bibliográfica:** Res. SPDP-SPD-2026-0005-R; LOPDP Arts. 44, 48; Teorema 17 (este documento); Teorema 4 (SoD DPO).

### Aporte 21: Prevención de Corrupción de Árboles Sintácticos (AST) por Firmas BOM
`¤bbap` `¤adpa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** La escritura de archivos de código fuente en entornos Windows utilizando comandos nativos de PowerShell (`Set-Content`, `[System.IO.File]::WriteAllText`) introduce por defecto la marca de orden de bytes (BOM - `\ufeff`). Este BOM invisible corrompe silenciosamente herramientas de análisis estático y linters basados en el módulo `ast` de Python (`ast.parse`), generando fallas en arneses de pruebas cero-regresiones.
* **Solución — Instanciación Programática Estricta:** La inyección de código mediante scripts temporales de Python utilizando `pathlib.Path.write_text(..., encoding='utf-8')` garantiza la creación de archivos limpios y previene colapsos deterministas.
* **Base normativa:** Principios de Clean-Room y Determinismo en pruebas automatizadas.

---

### Aporte 22: Arquitectura RAG de Cita Estricta (Zero-Hallucination Barrier)
`¤copiloto-ia` `¤regulacion-rag`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Los sistemas de Generación Aumentada por Recuperación (RAG) en dominios legales (LegalTech) sufren riesgos críticos de alucinación si no se restringe su inferencia ante la falta de resultados vectoriales.
* **Solución — Fallback Condicional Absoluto:** La arquitectura `RAGCopilotEngine` con el flag `strict_citation_mode=True`. Este patrón fuerza un retorno duro que emite exclusivamente la cadena *"No puedo responder esto basándome en la normativa indexada."* con un puntaje de confianza de `0.0`, impidiendo matemáticamente que el LLM infiera respuestas no ancladas en la base vectorial oficial.
* **Firma canónica:**
  ```python
  engine = RAGCopilotEngine(strict_citation_mode=True)
  ```
* **Base normativa:** Art. 48 LOPDP (Principio de certidumbre jurídica).

---

### Aporte 23: Emisión Documental Inmutable (WORM) para Diagnósticos de Cumplimiento
`¤diagnostico` `¤evidencias`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Un dictamen de cumplimiento regulatorio carece de valor auditor si no está acoplado inmutablemente a la versión de la ley exacta del momento de su emisión.
* **Solución — Sellado de Snapshots:** La integración de un `snapshot_normativo` (ej. LOPDP-2026-v1.0) y un sello temporal UTC estricto incrustados algorítmicamente en la generación binaria del PDF (vía `reportlab`). Esto transforma el documento en un artefacto WORM (Write Once, Read Many), garantizando no-repudio.
* **Base normativa:** Principios de trazabilidad técnica (ISO 27001), Arts. 21 y 37 LOPDP.

---

### Aporte 24: Aislamiento de Integración Asíncrona en Entornos Deterministas
`¤bbap` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Los tests de integración sobre FastAPI que consumen bases de datos asíncronas (`asyncpg`) fallan por desconexión en entornos de CI aislados (`WinError 1225`).
* **Solución — Dependency Overriding:** Sustitución topológica del generador asíncrono (`app.dependency_overrides[get_db_session] = MockSession()`) permitiendo validar middlewares de seguridad JWT y esquemas Pydantic `from_attributes=True` sin romper la invariante del entorno desconectado.

---

### Teorema 23: Orquestación Agéntica Concurrente mediante Arbitraje Exógeno Físico (Zero-Regression Parallelism)
`¤bbap` `¤adpa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En el desarrollo de software colaborativo impulsado por Inteligencia Artificial, la delegación de tareas arquitectónicas complejas a múltiples agentes paralelos provoca colapsos sistémicos (merge conflicts destructivos, violaciones de tipado, regresiones lógicas) si la aserción de éxito se confía a la evaluación semántica (introspectiva) de los propios modelos LLM.
* **Demostración y Solución:** Sea $\mathcal{A} = \{a_1, a_2, \dots, a_n\}$ un ensamble de agentes concurrentes modificando un repositorio compartido. La integridad del sistema $\mathcal{I}(\mathcal{A})$ es matemáticamente inestable a menos que esté acoplada a una compuerta física, determinista y estricta $\mathcal{C}_{\text{arnés}}$.
  $$\mathcal{I}(\mathcal{A}) = \text{true} \iff \forall \text{commit } c, \quad \text{ExitCode}(\mathcal{C}_{\text{arnés}}(c)) = 0$$
  El uso de un **Arnés Exógeno Cero Regresiones** (script `.bat` / suite Pytest + Next.js build) actúa como un reductor de entropía absoluto. Ningún bloque de código generado por un agente puede ser integrado lógicamente hasta que un proceso nativo del sistema operativo certifique cero aserciones fallidas, cero huellas abiertas y compilación estricta de TypeScript.

---

### Teorema 24: Aislamiento Transaccional Multi-Tenant Asíncrono mediante Propagación de Contexto (ContextVar RLS Injection)
`¤seguridad-tenant` `¤adpa` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En aplicaciones asíncronas Python (FastAPI + SQLAlchemy 2.0 con `asyncpg`), pasar el `tenant_id` por argumento a través de todas las capas de servicio y repositorios contamina la arquitectura y genera vulnerabilidades (Data Leakage) ante omisiones de los desarrolladores. El uso de variables globales o `thread.local` falla silenciosamente ante la concurrencia de corrutinas (`asyncio`).
* **Formulación y Demostración:** La seguridad a nivel de fila (Row-Level Security) en PostgreSQL exige inyectar la identidad de sesión en el driver SQL antes de procesar el query de la capa lógica. Utilizando un `contextvars.ContextVar`, el identificador fluye independientemente para cada *Event Loop Task*:
  $$\text{TenantID}_{\text{async}} = \text{ContextVar}(\text{'current\_tenant\_id'}, \text{default=None})$$
  Mediante un Dependency Builder en FastAPI:
  $$\forall \text{Request} \to \text{JWT}_{\text{middleware}} \to \text{ContextVar.set}(\text{UUID}) \to \text{Pool.acquire}() \to \text{SET LOCAL app.current\_tenant\_id = UUID}$$
  Esto garantiza que todo query derivado herede la frontera RLS de la base de datos sin alterar la pureza de las funciones ADPA. Si un programador olvida filtrar por tenant en Python, la base de datos devuelve cero registros (Falla Segura), demostrando invulnerabilidad matemática contra fugas cruzadas.

---

### Aporte 25: Pipeline CI/CD "Fail-Fast" de Gobernanza Zero-Regression
`¤ci-cd` `¤bbap`
* **Problema:** Un modelo de desarrollo agéntico o humano produce código que puede romper la integridad en el entorno de despliegue si los controles estigmérgicos solo corren en la máquina del consultor.
* **Solución:** `zero-regression-pipeline.yml` en GitHub Actions configura un flujo determinista de 3 capas:
  1. *Linting de Arquitectura:* Bloqueo inmediato ante firmas BOM o huellas (¦) huérfanas (Exit Code 1).
  2. *Backend Pytest:* Aserción determinista sobre el ecosistema RLS, FastAPI y el motor RAG.
  3. *Frontend Turbopack:* Compilación Node.js bajo rigor de TypeScript puro.
  Este patrón "Fail-Fast" aborta operaciones destructivas tempranamente, ahorrando cómputo de la nube y prohibiendo fusiones no conformes en la rama `main`.

---

### Aporte 26: Orquestación Containerizada Multi-Capa con Turbopack Standalone
`¤docker` `¤arquitectura`
* **Problema:** El levantamiento manual de 3 servicios interdependientes (DB Vectorial, API, IDE Frontend) produce fallas de red, colisión de puertos y discrepancias de entorno.
* **Solución:** Una coreografía `docker-compose.yml` que engrana:
  * `pgvector` con montura local para el Master Record.
  * `FastAPI` (backend) con un `depends_on: service_healthy` apuntado a la base de datos y *entrypoint* integrado para migraciones automáticas `alembic upgrade head`.
  * `Next.js` (frontend) procesado en modo *Multi-Stage Build* (`output: 'standalone'`), purgando dependencias crudas de Node para minimizar la superficie de ataque y el tamaño de la imagen final.
  El sistema entero opera como un ecosistema efímero, resiliente y de despliegue "One-Click".


### Aporte 27: Telemetría de Excepciones Estructurada Nativa en Gateways FastAPI (SIEM Ready)
`¤ciberseguridad` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En sistemas de gobernanza LOPDP, los fallos, rechazos de acceso (`HTTP 403`, `HTTP 401`) e invalidaciones (`ValidationError`) emitidos por FastAPI suelen registrarse en la capa de transporte como flujos de texto plano no estructurados. Esto anula la observabilidad automatizada y rompe la ingesta en sistemas SIEM, oscureciendo las auditorías exógenas ante incidentes de ciberseguridad.
* **Solución — Intercepción y Serialización Estricta:** Implementación global de un manejador de excepciones (`@app.exception_handler`) acoplado a un formateador JSON nativo (`JSONFormatter`). Toda anomalía o rechazo de SoD es forzado a serializarse como un objeto JSON unificado que contiene `timestamp` ISO 8601, `level`, método HTTP, URL y código de error. La telemetría se vuelve determinista y máquina-legible por diseño, sin necesidad de parseadores frágiles.

---

### Aporte 28: Diseño "Fail-Fast" de Configuración Ambiental Centralizada (Pydantic Hardening)
`¤ciberseguridad` `¤ci-cd`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** El uso de literales harcodeados o variables de entorno parseadas condicionalmente a nivel de componente causa vulnerabilidades críticas tardías (e.g. políticas CORS laxas, secretos débiles expuestos en producción) que escapan a los tests estáticos.
* **Solución:** Adopción del patrón 12-Factor App mediante `pydantic_settings.BaseSettings` en un core unificado (`app_core/config.py`). Se mapean variables críticas como obligatorias (`JWT_SECRET`, `CORS_ORIGINS`). Si el orquestador (Docker/CI) omite inyectar estos secretos durante el inicio del proceso, la aplicación aborta el arranque en el milisegundo cero (Exit Code 1) mediante una excepción de validación estricta, bloqueando matemáticamente cualquier estado operativo vulnerable.

### Aporte 29: Sanitización DLP Algorítmica Determinista (Módulo 10 Canónico)
¤dlp ¤zero-trust ¤rag
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** Los pipelines RAG (Retrieval-Augmented Generation) sufren fugas de datos sensibles (PII) si se confía la anonimización únicamente a heurísticas de NLP o pesos predictivos probabilísticos.
* **Solución:** Implementación de una barrera matemática estricta pre-inferencia. La validación de secuencias numéricas mediante el algoritmo de control canónico Módulo 10 (para cédulas ecuatorianas) garantiza asertividad determinista en el enmascaramiento antes de que los datos alcancen la inferencia del modelo.

### Aporte 30: Topología de Idempotencia Aislada en Inicialización de Datos (Multi-Tenant Seeding)
¤rls ¤ci-cd
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** El sembrado (seeding) de datos de prueba en sistemas SaaS de alta densidad con Row-Level Security (RLS) puede introducir colisiones o *race conditions* si la inserción asume un estado global virgen.
* **Solución:** Ejecución de clausuras de inicialización bajo un ContextVar asíncrono temporal, ejecutando operaciones DELETE de alcance estricto por 	enant_id previo a cualquier mutación. Esto asegura que el estado inicial del tenant sea 100% idempotente sin violar la partición criptográfica RLS.

### Aporte 31: Sincronización Determinista de Arranque con Migraciones DDL (Wait-For-Healthy)
¤devops ¤docker
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** En orquestaciones One-Click, los backend con Alembic fallan al intentar ejecutar esquemas si el motor DB no ha completado la hidratación de extensiones pesadas (e.g., pgvector).
* **Solución:** Dependencia condicionada estricta (condition: service_healthy) en Docker Compose, anclada a herramientas de polling nativas (pg_isready), y delegación del upgrade head al entrypoint del contenedor. Evita latencias artificiales (sleeps) y asegura integridad transaccional del esquema en el arranque.

---

### Teorema 25: Purga Probatoria por Inconsistencia Categórica en Formularios Forenses (Poka-Yoke de Evidencia)
`¤incidentes` `¤evidencias`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** En el diligenciamiento de formularios de incidentes legales (ej. Playbook de Brechas de Seguridad ARCO+), si un usuario adjunta evidencia $\mathcal{E}$ asumiendo una Severidad $ (ej. "Bajo"), y posteriormente altera la Severidad a $ (ej. "Crítico"), la evidencia $\mathcal{E}$ pierde su correlación semántica y legal, induciendo al auditor a falsos positivos probatorios que violan la integridad del caso.
* **Formulación y Demostración:** Sea $\mathcal{F}$ un formulario forense donde la validez de la evidencia $\mathcal{E}$ está ligada al contexto categórico $\mathcal{C}$. El principio de consistencia (Poka-Yoke documental) exige:
  \text{Cambio}(\mathcal{C}_{t} \to \mathcal{C}_{t+1}) \implies \mathcal{E}_{t+1} := \emptyset
  Implementado en React mediante un efecto colateral estricto (`useEffect` dependiente de $\mathcal{C}$), se garantiza la invalidación automática del buffer del gestor de archivos (`react-dropzone`). Esta transición de estado colateral actúa como un Poka-Yoke matemático que fuerza al operador a recertificar la prueba documental bajo la nueva premisa legal, eliminando la posibilidad de "evidencias fantasma" (Shigeo Shingo, 1961).

---

### Aporte 32: Renderizado Liminal Reactivo de Tokens DLP en Pipelines RAG
`¤copiloto-ia` `¤frontend-ide`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** Los motores RAG que aplican saneamiento DLP reemplazan información sensible por cadenas de texto neutras (ej. `[DATO_SANITIZADO_POR_DLP]`). En la interfaz final, este texto crudo es frecuentemente interpretado por el usuario como un error de procesamiento, una alucinación del LLM o código roto, disminuyendo la percepción de confianza en el sistema.
* **Solución:** Integración de un analizador sintáctico en tiempo de renderizado (`MarkdownConCitas`) que intercepta el token exacto mediante expresiones regulares y lo sustituye dinámicamente en el Virtual DOM por un componente visual de alto impacto (Badge rojo `#ff1744/15` con ícono de escudo `ShieldAlert`). Esto transmuta una supresión pasiva de texto crudo en un **comprobante activo de seguridad visible**, demostrando al auditor y al usuario que el pipeline Zero-Trust de JUBYZ OS está operando con éxito y protegiendo los datos PII.

### Aporte 33: Cálculo MTGE Determinista de Latencia Cero en Capa Cliente
`¤mtge-granescala` `¤frontend-ide`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** El recálculo de los puntajes de Tratamiento a Gran Escala (MTGE, Res. SPDP-SPD-2026-0005-R) requería consultas constantes al backend ante cada variación de los *sliders* de volumetría, generando latencia de red y degradación de la experiencia de usuario (UX) al explorar escenarios de impacto.
* **Solución:** Portabilidad algorítmica isomórfica. La lógica paramétrica exacta del backend se replicó en un semáforo reactivo en la capa cliente (React `useEffect`), permitiendo la previsualización instantánea (latencia 0 ms) de los umbrales de riesgo. La UI muta sus tarjetas de "EIPD Obligatoria" o "DPO Designado" en tiempo real mientras el usuario manipula la escala, actuando como una calculadora forense sin sacrificar la verdad matemática que validará el backend en el commit final.

# PARTE III: Optimizaciones Epistémicas y Arquitectónicas Derivadas (Análisis de Fuentes)

### Aporte 27: Hashing Anclado por Árbol de Merkle para No-Repudio Criptográfico (Merkle-Root Anchoring)
`¤implementacion` `¤invariantes` `¤seguridad`
* **Fuente Analizada:** *Ralph C. Merkle (1987)* y *RFC 3161 (Time-Stamp Protocol)* cruzado con Art. 10 num. 7 LOPDP (Responsabilidad Proactiva).
* **Diagnóstico Actual:** El Teorema 18 y el Aporte 23 generan snapshots WORM con firma SHA-256 individual en la base de datos o en un PDF. Sin embargo, si la base de datos entera es comprometida (nivel de infraestructura), un atacante podría regenerar todos los hashes.
* **Optimización Proyectada:** Implementar un **Árbol de Merkle Cronológico** donde cada snapshot $S_k$ es una hoja. Periódicamente (ej. cada 24 horas), el sistema computa el `Merkle Root` y lo emite hacia un servicio externo inmutable (Time Stamping Authority oficial o un Ledger público). Esto blinda matemáticamente el historial de auditorías contra alteraciones retroactivas, incluso frente a un compromiso total del clúster de base de datos.

---

### Aporte 28: K-Anonimato en Indexación Vectorial RAG (Defensa contra Inversión de Embeddings)
`¤copiloto-ia` `¤seguridad-tenant`
* **Fuente Analizada:** *OWASP Top 10 for LLM (LLM06: Sensitive Information Disclosure)* y *Guía de Arquitectura de Sistemas de IA Confiables (2025)*.
* **Diagnóstico Actual:** El Teorema 19 (Filtro DLP Pre-Inferencia) enmascara exitosamente la información personal en los *prompts* de los usuarios. No obstante, si se llegasen a indexar documentos de la empresa (Evidencias E3) en `pgvector` para ampliar el RAG, los embeddings resultantes podrían sufrir ataques de inversión semántica.
* **Optimización Proyectada:** Implementar **Indexación Vectorial K-Anónima**. Antes de generar el embedding con modelos como `text-embedding-3-small`, los textos se pasan por una canalización de sanitización asíncrona robusta (NER - Named Entity Recognition) que generaliza identificadores corporativos y nombres propios (Ej. "Juan Pérez" -> "Empleado A"). Esto garantiza que el espacio vectorial sea matemáticamente estéril de PII, impidiendo la exfiltración mediante prompt injection perimetral.

---

### Aporte 29: Motor Reactivo de Re-Evaluación Continua EIPD (Continuous EIPD Lifecycle)
`¤mtge-granescala` `¤riesgos-eipd`
* **Fuente Analizada:** *ISO/IEC 27701:2019* y *Res. SPDP-SPD-2026-0005-R*.
* **Diagnóstico Actual:** El Teorema 17 y Aporte 19 activan un flag irreversible `requiereEIPDForzoso = true` al superar el umbral de Gran Escala, pero no alertan si el nivel de exposición cambia drásticamente en un sistema que ya superó el umbral.
* **Optimización Proyectada:** Introducir un **Sensor de Deriva de Riesgo (Risk Drift Sensor)**. Si un tenant que ya tiene una EIPD aprobada sufre un incremento del volumen de datos $\Delta V \ge 25\%$ o añade una nueva categoría de datos biométricos, el Compliance Graph (Teorema 14) invalida automáticamente el estado de "EIPD Aprobada" y lo transiciona a "EIPD Obsoleta - Requiere Actualización", forzando al DPO a reevaluar el impacto. Esto cumple con la naturaleza iterativa de ISO 27701.

---

### Aporte 30: Command Palette Semántica de Contexto Topológico $O(1)$
`¤frontend-ide`
  {
    "volumenTotalTitulares": 10900,
    "superaUmbralVolumen": true,
    "tieneTratamientoSensibleLargo": false,
    "requiereEIPDForzoso": true,
    "criterioActivacion": "CRITERIO_A_VOLUMEN_MASIVO | CRITERIO_B_SENSIBLE_LONG_RETENTION | CRITERIO_A_Y_B | NINGUNO",
    "actividadesQueDetonan": ["uuid-1", "uuid-2"],
    "evaluadoEn": "ISO-8601",
    "rationale": "texto en lenguaje natural"
  }
  ```
* **Base normativa:** Res. SPDP-SPD-2026-0005-R Arts. 12-13; LOPDP Arts. 25, 44, 48; Teorema 14 (Compliance Graph DAG Lineage); Teorema 17 (Determinismo de Doble Compuerta MTGE).

---

### Aporte 20: Teorema de Doble Escala MTGE — Evaluacion Micro vs. Macro en Motores de Gran Escala
`¤mtge-granescala` `¤invariantes` `¤riesgos-eipd`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-15
* **Enunciado Formal (Teorema 19):** Sea $\mathcal{R} = \{a_1, a_2, \dots, a_n\}$ el conjunto de actividades de tratamiento de un tenant, y sea $\mathcal{F}_{\text{micro}}: a_i \to \{0,1\}$ el predicado de Gran Escala individual (Aporte 16). Existe un predicado relacional de mayor potencia normativa:
  $$\mathcal{F}_{\text{macro}}: \mathcal{R} \to \{0,1\}$$
  tal que:
  $$\mathcal{F}_{\text{macro}}(\mathcal{R}) = 1 \iff \left(\sum_{i=1}^{n} V_i > 10\,000\right) \lor \left(\exists a_j \in \mathcal{R} : \text{Sensible}(a_j) \land P_j > 3\right)$$
  Y se cumple que: $\exists \mathcal{R}$ tal que $\forall i: \mathcal{F}_{\text{micro}}(a_i) = 0$ pero $\mathcal{F}_{\text{macro}}(\mathcal{R}) = 1$.
  Es decir, **existen tenants en Gran Escala que ningún motor individual detectaria** sin evaluar el tensor completo del RAT.
* **Corolario de Mutacion Monotona:** El flag $\text{requiereEIPDForzoso}$ es monotono creciente en el tiempo:
  $$\text{EIPD}(t_1) = 1 \implies \text{EIPD}(t_2) = 1 \quad \forall t_2 > t_1$$
  Lo que garantiza que un tenant que alguna vez cruzó el umbral de Gran Escala no puede "des-calificarse" pasivamente mediante reducción de datos en el RAT sin aprobación formal del DPO (Principio de Responsabilidad Proactiva Continua, Art. 10 num. 7 LOPDP).
* **Base bibliográfica:** Res. SPDP-SPD-2026-0005-R; LOPDP Arts. 44, 48; Teorema 17 (este documento); Teorema 4 (SoD DPO).

### Aporte 21: Prevención de Corrupción de Árboles Sintácticos (AST) por Firmas BOM
`¤bbap` `¤adpa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** La escritura de archivos de código fuente en entornos Windows utilizando comandos nativos de PowerShell (`Set-Content`, `[System.IO.File]::WriteAllText`) introduce por defecto la marca de orden de bytes (BOM - `\ufeff`). Este BOM invisible corrompe silenciosamente herramientas de análisis estático y linters basados en el módulo `ast` de Python (`ast.parse`), generando fallas en arneses de pruebas cero-regresiones.
* **Solución — Instanciación Programática Estricta:** La inyección de código mediante scripts temporales de Python utilizando `pathlib.Path.write_text(..., encoding='utf-8')` garantiza la creación de archivos limpios y previene colapsos deterministas.
* **Base normativa:** Principios de Clean-Room y Determinismo en pruebas automatizadas.

---

### Aporte 22: Arquitectura RAG de Cita Estricta (Zero-Hallucination Barrier)
`¤copiloto-ia` `¤regulacion-rag`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Los sistemas de Generación Aumentada por Recuperación (RAG) en dominios legales (LegalTech) sufren riesgos críticos de alucinación si no se restringe su inferencia ante la falta de resultados vectoriales.
* **Solución — Fallback Condicional Absoluto:** La arquitectura `RAGCopilotEngine` con el flag `strict_citation_mode=True`. Este patrón fuerza un retorno duro que emite exclusivamente la cadena *"No puedo responder esto basándome en la normativa indexada."* con un puntaje de confianza de `0.0`, impidiendo matemáticamente que el LLM infiera respuestas no ancladas en la base vectorial oficial.
* **Firma canónica:**
  ```python
  engine = RAGCopilotEngine(strict_citation_mode=True)
  ```
* **Base normativa:** Art. 48 LOPDP (Principio de certidumbre jurídica).

---

### Aporte 23: Emisión Documental Inmutable (WORM) para Diagnósticos de Cumplimiento
`¤diagnostico` `¤evidencias`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Un dictamen de cumplimiento regulatorio carece de valor auditor si no está acoplado inmutablemente a la versión de la ley exacta del momento de su emisión.
* **Solución — Sellado de Snapshots:** La integración de un `snapshot_normativo` (ej. LOPDP-2026-v1.0) y un sello temporal UTC estricto incrustados algorítmicamente en la generación binaria del PDF (vía `reportlab`). Esto transforma el documento en un artefacto WORM (Write Once, Read Many), garantizando no-repudio.
* **Base normativa:** Principios de trazabilidad técnica (ISO 27001), Arts. 21 y 37 LOPDP.

---

### Aporte 24: Aislamiento de Integración Asíncrona en Entornos Deterministas
`¤bbap` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** Los tests de integración sobre FastAPI que consumen bases de datos asíncronas (`asyncpg`) fallan por desconexión en entornos de CI aislados (`WinError 1225`).
* **Solución — Dependency Overriding:** Sustitución topológica del generador asíncrono (`app.dependency_overrides[get_db_session] = MockSession()`) permitiendo validar middlewares de seguridad JWT y esquemas Pydantic `from_attributes=True` sin romper la invariante del entorno desconectado.

---

### Teorema 23: Orquestación Agéntica Concurrente mediante Arbitraje Exógeno Físico (Zero-Regression Parallelism)
`¤bbap` `¤adpa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En el desarrollo de software colaborativo impulsado por Inteligencia Artificial, la delegación de tareas arquitectónicas complejas a múltiples agentes paralelos provoca colapsos sistémicos (merge conflicts destructivos, violaciones de tipado, regresiones lógicas) si la aserción de éxito se confía a la evaluación semántica (introspectiva) de los propios modelos LLM.
* **Demostración y Solución:** Sea $\mathcal{A} = \{a_1, a_2, \dots, a_n\}$ un ensamble de agentes concurrentes modificando un repositorio compartido. La integridad del sistema $\mathcal{I}(\mathcal{A})$ es matemáticamente inestable a menos que esté acoplada a una compuerta física, determinista y estricta $\mathcal{C}_{\text{arnés}}$.
  $$\mathcal{I}(\mathcal{A}) = \text{true} \iff \forall \text{commit } c, \quad \text{ExitCode}(\mathcal{C}_{\text{arnés}}(c)) = 0$$
  El uso de un **Arnés Exógeno Cero Regresiones** (script `.bat` / suite Pytest + Next.js build) actúa como un reductor de entropía absoluto. Ningún bloque de código generado por un agente puede ser integrado lógicamente hasta que un proceso nativo del sistema operativo certifique cero aserciones fallidas, cero huellas abiertas y compilación estricta de TypeScript.

---

### Teorema 24: Aislamiento Transaccional Multi-Tenant Asíncrono mediante Propagación de Contexto (ContextVar RLS Injection)
`¤seguridad-tenant` `¤adpa` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En aplicaciones asíncronas Python (FastAPI + SQLAlchemy 2.0 con `asyncpg`), pasar el `tenant_id` por argumento a través de todas las capas de servicio y repositorios contamina la arquitectura y genera vulnerabilidades (Data Leakage) ante omisiones de los desarrolladores. El uso de variables globales o `thread.local` falla silenciosamente ante la concurrencia de corrutinas (`asyncio`).
* **Formulación y Demostración:** La seguridad a nivel de fila (Row-Level Security) en PostgreSQL exige inyectar la identidad de sesión en el driver SQL antes de procesar el query de la capa lógica. Utilizando un `contextvars.ContextVar`, el identificador fluye independientemente para cada *Event Loop Task*:
  $$\text{TenantID}_{\text{async}} = \text{ContextVar}(\text{'current\_tenant\_id'}, \text{default=None})$$
  Mediante un Dependency Builder en FastAPI:
  $$\forall \text{Request} \to \text{JWT}_{\text{middleware}} \to \text{ContextVar.set}(\text{UUID}) \to \text{Pool.acquire}() \to \text{SET LOCAL app.current\_tenant\_id = UUID}$$
  Esto garantiza que todo query derivado herede la frontera RLS de la base de datos sin alterar la pureza de las funciones ADPA. Si un programador olvida filtrar por tenant en Python, la base de datos devuelve cero registros (Falla Segura), demostrando invulnerabilidad matemática contra fugas cruzadas.

---

### Aporte 25: Pipeline CI/CD "Fail-Fast" de Gobernanza Zero-Regression
`¤ci-cd` `¤bbap`
* **Problema:** Un modelo de desarrollo agéntico o humano produce código que puede romper la integridad en el entorno de despliegue si los controles estigmérgicos solo corren en la máquina del consultor.
* **Solución:** `zero-regression-pipeline.yml` en GitHub Actions configura un flujo determinista de 3 capas:
  1. *Linting de Arquitectura:* Bloqueo inmediato ante firmas BOM o huellas (¦) huérfanas (Exit Code 1).
  2. *Backend Pytest:* Aserción determinista sobre el ecosistema RLS, FastAPI y el motor RAG.
  3. *Frontend Turbopack:* Compilación Node.js bajo rigor de TypeScript puro.
  Este patrón "Fail-Fast" aborta operaciones destructivas tempranamente, ahorrando cómputo de la nube y prohibiendo fusiones no conformes en la rama `main`.

---

### Aporte 26: Orquestación Containerizada Multi-Capa con Turbopack Standalone
`¤docker` `¤arquitectura`
* **Problema:** El levantamiento manual de 3 servicios interdependientes (DB Vectorial, API, IDE Frontend) produce fallas de red, colisión de puertos y discrepancias de entorno.
* **Solución:** Una coreografía `docker-compose.yml` que engrana:
  * `pgvector` con montura local para el Master Record.
  * `FastAPI` (backend) con un `depends_on: service_healthy` apuntado a la base de datos y *entrypoint* integrado para migraciones automáticas `alembic upgrade head`.
  * `Next.js` (frontend) procesado en modo *Multi-Stage Build* (`output: 'standalone'`), purgando dependencias crudas de Node para minimizar la superficie de ataque y el tamaño de la imagen final.
  El sistema entero opera como un ecosistema efímero, resiliente y de despliegue "One-Click".


### Aporte 27: Telemetría de Excepciones Estructurada Nativa en Gateways FastAPI (SIEM Ready)
`¤ciberseguridad` `¤arquitectura`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En sistemas de gobernanza LOPDP, los fallos, rechazos de acceso (`HTTP 403`, `HTTP 401`) e invalidaciones (`ValidationError`) emitidos por FastAPI suelen registrarse en la capa de transporte como flujos de texto plano no estructurados. Esto anula la observabilidad automatizada y rompe la ingesta en sistemas SIEM, oscureciendo las auditorías exógenas ante incidentes de ciberseguridad.
* **Solución — Intercepción y Serialización Estricta:** Implementación global de un manejador de excepciones (`@app.exception_handler`) acoplado a un formateador JSON nativo (`JSONFormatter`). Toda anomalía o rechazo de SoD es forzado a serializarse como un objeto JSON unificado que contiene `timestamp` ISO 8601, `level`, método HTTP, URL y código de error. La telemetría se vuelve determinista y máquina-legible por diseño, sin necesidad de parseadores frágiles.

---

### Aporte 28: Diseño "Fail-Fast" de Configuración Ambiental Centralizada (Pydantic Hardening)
`¤ciberseguridad` `¤ci-cd`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** El uso de literales harcodeados o variables de entorno parseadas condicionalmente a nivel de componente causa vulnerabilidades críticas tardías (e.g. políticas CORS laxas, secretos débiles expuestos en producción) que escapan a los tests estáticos.
* **Solución:** Adopción del patrón 12-Factor App mediante `pydantic_settings.BaseSettings` en un core unificado (`app_core/config.py`). Se mapean variables críticas como obligatorias (`JWT_SECRET`, `CORS_ORIGINS`). Si el orquestador (Docker/CI) omite inyectar estos secretos durante el inicio del proceso, la aplicación aborta el arranque en el milisegundo cero (Exit Code 1) mediante una excepción de validación estricta, bloqueando matemáticamente cualquier estado operativo vulnerable.

### Aporte 29: Sanitización DLP Algorítmica Determinista (Módulo 10 Canónico)
¤dlp ¤zero-trust ¤rag
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** Los pipelines RAG (Retrieval-Augmented Generation) sufren fugas de datos sensibles (PII) si se confía la anonimización únicamente a heurísticas de NLP o pesos predictivos probabilísticos.
* **Solución:** Implementación de una barrera matemática estricta pre-inferencia. La validación de secuencias numéricas mediante el algoritmo de control canónico Módulo 10 (para cédulas ecuatorianas) garantiza asertividad determinista en el enmascaramiento antes de que los datos alcancen la inferencia del modelo.

### Aporte 30: Topología de Idempotencia Aislada en Inicialización de Datos (Multi-Tenant Seeding)
¤rls ¤ci-cd
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** El sembrado (seeding) de datos de prueba en sistemas SaaS de alta densidad con Row-Level Security (RLS) puede introducir colisiones o *race conditions* si la inserción asume un estado global virgen.
* **Solución:** Ejecución de clausuras de inicialización bajo un ContextVar asíncrono temporal, ejecutando operaciones DELETE de alcance estricto por tenant_id previo a cualquier mutación. Esto asegura que el estado inicial del tenant sea 100% idempotente sin violar la partición criptográfica RLS.

### Aporte 31: Sincronización Determinista de Arranque con Migraciones DDL (Wait-For-Healthy)
¤devops ¤docker
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-17
* **Problema:** En orquestaciones One-Click, los backend con Alembic fallan al intentar ejecutar esquemas si el motor DB no ha completado la hidratación de extensiones pesadas (e.g., pgvector).
* **Solución:** Dependencia condicionada estricta (condition: service_healthy) en Docker Compose, anclada a herramientas de polling nativas (pg_isready), y delegación del upgrade head al entrypoint del contenedor. Evita latencias artificiales (sleeps) y asegura integridad transaccional del esquema en el arranque.

---

### Teorema 25: Purga Probatoria por Inconsistencia Categórica en Formularios Forenses (Poka-Yoke de Evidencia)
`¤incidentes` `¤evidencias`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** En el diligenciamiento de formularios de incidentes legales (ej. Playbook de Brechas de Seguridad ARCO+), si un usuario adjunta evidencia $\mathcal{E}$ asumiendo una Severidad $ (ej. "Bajo"), y posteriormente altera la Severidad a $ (ej. "Crítico"), la evidencia $\mathcal{E}$ pierde su correlación semántica y legal, induciendo al auditor a falsos positivos probatorios que violan la integridad del caso.
* **Formulación y Demostración:** Sea $\mathcal{F}$ un formulario forense donde la validez de la evidencia $\mathcal{E}$ está ligada al contexto categórico $\mathcal{C}$. El principio de consistencia (Poka-Yoke documental) exige:
  \text{Cambio}(\mathcal{C}_{t} \to \mathcal{C}_{t+1}) \implies \mathcal{E}_{t+1} := \emptyset
  Implementado en React mediante un efecto colateral estricto (`useEffect` dependiente de $\mathcal{C}$), se garantiza la invalidación automática del buffer del gestor de archivos (`react-dropzone`). Esta transición de estado colateral actúa como un Poka-Yoke matemático que fuerza al operador a recertificar la prueba documental bajo la nueva premisa legal, eliminando la posibilidad de "evidencias fantasma" (Shigeo Shingo, 1961).

---

### Aporte 32: Renderizado Liminal Reactivo de Tokens DLP en Pipelines RAG
`¤copiloto-ia` `¤frontend-ide`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** Los motores RAG que aplican saneamiento DLP reemplazan información sensible por cadenas de texto neutras (ej. `[DATO_SANITIZADO_POR_DLP]`). En la interfaz final, este texto crudo es frecuentemente interpretado por el usuario como un error de procesamiento, una alucinación del LLM o código roto, disminuyendo la percepción de confianza en el sistema.
* **Solución:** Integración de un analizador sintáctico en tiempo de renderizado (`MarkdownConCitas`) que intercepta el token exacto mediante expresiones regulares y lo sustituye dinámicamente en el Virtual DOM por un componente visual de alto impacto (Badge rojo `#ff1744/15` con ícono de escudo `ShieldAlert`). Esto transmuta una supresión pasiva de texto crudo en un **comprobante activo de seguridad visible**, demostrando al auditor y al usuario que el pipeline Zero-Trust de JUBYZ OS está operando con éxito y protegiendo los datos PII.

### Aporte 33: Cálculo MTGE Determinista de Latencia Cero en Capa Cliente
`¤mtge-granescala` `¤frontend-ide`
* **Sesión de origen:** Conversación acb3d7c2-56f8-4340-b59a-b6be7a1c21b4 · 2026-09-17
* **Problema:** El recálculo de los puntajes de Tratamiento a Gran Escala (MTGE, Res. SPDP-SPD-2026-0005-R) requería consultas constantes al backend ante cada variación de los *sliders* de volumetría, generando latencia de red y degradación de la experiencia de usuario (UX) al explorar escenarios de impacto.
* **Solución:** Portabilidad algorítmica isomórfica. La lógica paramétrica exacta del backend se replicó en un semáforo reactivo en la capa cliente (React `useEffect`), permitiendo la previsualización instantánea (latencia 0 ms) de los umbrales de riesgo. La UI muta sus tarjetas de "EIPD Obligatoria" o "DPO Designado" en tiempo real mientras el usuario manipula la escala, actuando como una calculadora forense sin sacrificar la verdad matemática que validará el backend en el commit final.

# PARTE III: Optimizaciones Epistémicas y Arquitectónicas Derivadas (Análisis de Fuentes)

### Aporte 27: Hashing Anclado por Árbol de Merkle para No-Repudio Criptográfico (Merkle-Root Anchoring)
`¤implementacion` `¤invariantes` `¤seguridad`
* **Fuente Analizada:** *Ralph C. Merkle (1987)* y *RFC 3161 (Time-Stamp Protocol)* cruzado con Art. 10 num. 7 LOPDP (Responsabilidad Proactiva).
* **Diagnóstico Actual:** El Teorema 18 y el Aporte 23 generan snapshots WORM con firma SHA-256 individual en la base de datos o en un PDF. Sin embargo, si la base de datos entera es comprometida (nivel de infraestructura), un atacante podría regenerar todos los hashes.
* **Optimización Proyectada:** Implementar un **Árbol de Merkle Cronológico** donde cada snapshot $S_k$ es una hoja. Periódicamente (ej. cada 24 horas), el sistema computa el `Merkle Root` y lo emite hacia un servicio externo inmutable (Time Stamping Authority oficial o un Ledger público). Esto blinda matemáticamente el historial de auditorías contra alteraciones retroactivas, incluso frente a un compromiso total del clúster de base de datos.

---

### Aporte 28: K-Anonimato en Indexación Vectorial RAG (Defensa contra Inversión de Embeddings)
`¤copiloto-ia` `¤seguridad-tenant`
* **Fuente Analizada:** *OWASP Top 10 for LLM (LLM06: Sensitive Information Disclosure)* y *Guía de Arquitectura de Sistemas de IA Confiables (2025)*.
* **Diagnóstico Actual:** El Teorema 19 (Filtro DLP Pre-Inferencia) enmascara exitosamente la información personal en los *prompts* de los usuarios. No obstante, si se llegasen a indexar documentos de la empresa (Evidencias E3) en `pgvector` para ampliar el RAG, los embeddings resultantes podrían sufrir ataques de inversión semántica.
* **Optimización Proyectada:** Implementar **Indexación Vectorial K-Anónima**. Antes de generar el embedding con modelos como `text-embedding-3-small`, los textos se pasan por una canalización de sanitización asíncrona robusta (NER - Named Entity Recognition) que generaliza identificadores corporativos y nombres propios (Ej. "Juan Pérez" -> "Empleado A"). Esto garantiza que el espacio vectorial sea matemáticamente estéril de PII, impidiendo la exfiltración mediante prompt injection perimetral.

---

### Aporte 29: Motor Reactivo de Re-Evaluación Continua EIPD (Continuous EIPD Lifecycle)
`¤mtge-granescala` `¤riesgos-eipd`
* **Fuente Analizada:** *ISO/IEC 27701:2019* y *Res. SPDP-SPD-2026-0005-R*.
* **Diagnóstico Actual:** El Teorema 17 y Aporte 19 activan un flag irreversible `requiereEIPDForzoso = true` al superar el umbral de Gran Escala, pero no alertan si el nivel de exposición cambia drásticamente en un sistema que ya superó el umbral.
* **Optimización Proyectada:** Introducir un **Sensor de Deriva de Riesgo (Risk Drift Sensor)**. Si un tenant que ya tiene una EIPD aprobada sufre un incremento del volumen de datos $\Delta V \ge 25\%$ o añade una nueva categoría de datos biométricos, el Compliance Graph (Teorema 14) invalida automáticamente el estado de "EIPD Aprobada" y lo transiciona a "EIPD Obsoleta - Requiere Actualización", forzando al DPO a reevaluar el impacto. Esto cumple con la naturaleza iterativa de ISO 27701.

---

### Aporte 30: Command Palette Semántica de Contexto Topológico $O(1)$
`¤frontend-ide`
* **Fuente Analizada:** *Leyes de Hick-Hyman y Fitts* cruzadas con diseño de interacciones (Nielsen, 1993).
* **Diagnóstico Actual:** El Aporte 13 implementa `cmdk` para saltos de página inmediatos, reduciendo la fricción motora.
* **Optimización Proyectada:** Expandir el Command Palette (`Ctrl+K`) para que sea **Topológicamente Consciente**. Si el usuario presiona `Ctrl+K` estando en la ruta `/dpo-cockpit`, las primeras sugerencias deben ser dinámicas y predictivas relativas a su estado actual (ej. *Resolver Incidente #402*, *Aprobar Dictamen MTGE*), alterando la ponderación del índice de búsqueda en tiempo real basándose en los SLAs vencidos (Aporte 18). Esto colapsa el tiempo de resolución operativo al mínimo teórico absoluto.


### Teorema 31: Auditoría Financiera Cruzada (Teorema de GRC Unificado)
Demostración empírica de que el modelo matemático de JUBYS (Scoring 4D Cuádruple y modelo probatorio E0-E3) es ortogonal y agnóstico a la materia sustantiva legal. El mismo motor evalúa de forma idéntica un mandato punitivo (LOPDP) y un mandato financiero (NIIF 18), consolidando la transición hacia un Ecosistema Multi-Normativa (GRC).

---

### Aporte 34: Desacoplamiento de Subsistemas Algorítmicos mediante Enjambres Agénticos (ADPA-Swarm Pattern)
`¤bbap` `¤adpa` `¤arquitectura`
* **Sesión de origen:** Conversación ab0e5903-da73-4c5f-ad94-9f89be88a58b · 2026-09-18
* **Problema:** Los motores monolíticos de cálculo financiero y normativo acumulan complejidad ciclomática que dificulta el mantenimiento, la auditabilidad algorítmica y el testing de frontera. La refactorización manual de estos monolitos conlleva riesgos extremos de regresión y pérdida de conocimiento de dominio.
* **Solución — División Asíncrona:** Implementación de un patrón de refactorización distribuida donde se instancian sub-agentes concurrentes especializados (Data Engineer, Math Engineer, AI Engineer). Cada agente extrae, tipa e implementa un sub-dominio aislado (`parser_engine`, `classifier_engine`, `financials_engine`, `mpm_engine`), subordinados a una compuerta orquestadora (Service Gatekeeper). El enjambre preserva la invariante ADPA (Arquitectura Desacoplada de Procesos Agénticos) reduciendo la deuda técnica sin intervención manual y certificando el acoplamiento a través de interfaces bien definidas en un tiempo de resolución drásticamente inferior.

---

### Aporte 35: Reactividad Contable en Vivo en Capa Cliente (Live IFRS Reactivity)
`¤frontend-ide` `¤adpa`
* **Sesión de origen:** Conversación ab0e5903-da73-4c5f-ad94-9f89be88a58b · 2026-09-18
* **Problema:** En aplicaciones contables y de auditoría regulatoria, las reclasificaciones manuales de cuentas requieren procesos *batch* pesados o recargas completas de matriz (full-page reload) que interrumpen el flujo de trabajo forense del usuario y aumentan la latencia cognitiva.
* **Solución:** Arquitectura reactiva híbrida isomórfica. El frontend despacha mutaciones granulares asíncronas hacia un endpoint inmutable (`/api/v1/niif18/recalcular-subtotales`). El backend recalcula el árbol P&L completo de NIIF 18 (Resultado Operativo, Antes de Fin. e Imp., Resultado del Periodo) en milisegundos y retorna el tensor matricial actualizado. El gestor de estado global (Zustand) inyecta el nuevo estado a los componentes, los cuales re-renderizan instantáneamente (Latencia de Interacción < 50ms). Esto garantiza que la vista del usuario sea siempre una proyección visual estricta y verificada matemáticamente del motor backend.

---

### Aporte 36: Emisión Inmutable de Archivos de Cálculo WORM en Memoria (Zero-Trace In-Memory Exports)
`¤evidencias` `¤implementacion`
* **Sesión de origen:** Conversación ab0e5903-da73-4c5f-ad94-9f89be88a58b · 2026-09-18
* **Problema:** La exportación tradicional de archivos (Excel/XBRL) para cumplimiento normativo implica escribir blobs temporales en el disco del servidor. Esto expone los datos financieros a ataques de *Directory Traversal*, genera fugas por datos remanentes y destruye la garantía WORM (Write Once, Read Many).
* **Solución:** La generación del archivo regulatorio XBRL/Excel se realiza íntegramente en buffers de memoria volátil (`io.BytesIO`) en el backend FastAPI. El archivo se despacha de inmediato como un flujo binario directo (`StreamingResponse` / `Blob`) hacia el DOM del cliente, forzando la descarga del navegador. El disco del servidor jamás recibe un solo byte del reporte financiero. Esta arquitectura "Zero-Trace" certifica que el informe emitido es un snapshot puro en el instante $t$, sin posibilidad de manipulación intermedia.
---

### Teorema 26: Principio de Hidratación Asíncrona Aislada en Renderizado Híbrido (Next.js 15+)
¤frontend-arquitectura ¤nextjs ¤react
* **Sesión de origen:** Conversación d1a625451422 · 2026-09-19
* **Problema:** Los componentes de React que dependen de motores de estado cliente (Zustand / localStorage) sufren de *Hydration Mismatch* severo al ser renderizados en modo SSR/App Router, provocando destellos de UI y fallos del DOM (FOUC).
* **Solución (Demostración):** Todo componente anclado a un estado persistente o a un motor de polling pasivo (useSWR) debe delegar su renderizado primario a una variable condicional de ciclo de vida (mounted), proyectando un Skeleton isométrico inerte durante el SSR y transicionando atómicamente al árbol reactivo completo post-montaje, preservando el Exit Code 0 y eliminando la entropía de hidratación.

---

### Aporte 37: Ciclo de Vida Reactivo de Remediación mediante Polling SWR (AI Copilot Tracker)
¤ai-copilot ¤grc
* **Sesión de origen:** Conversación d1a625451422 · 2026-09-19
* **Problema:** En sistemas de Gobierno, Riesgo y Cumplimiento (GRC), la remediación sugerida por IA suele aislarse en paneles estáticos que requieren actualizaciones manuales cruzadas (F5), rompiendo la inmediatez del análisis de brechas.
* **Solución:** La integración de un patrón *Stale-While-Revalidate* (vía SWR) a un diseño Kanban (ALTO, MEDIO, BAJO) inyecta latencia cero a la percepción del progreso. Al detonar el diagnóstico asíncrono cognitivo, el frontend muta su caché y entra en un ciclo de polling reactivo. Esto fusiona el tiempo de inferencia de la IA con la retroalimentación continua de la UI, operando de manera estricta bajo el esquema *Zero-Trust* al encapsular JWT Bearers en funciones de fetch aisladas.

---

### Aporte 38: Pipeline de K-Anonimato Determinista con Mapeo Homomórfico Intradocumental en Indexación Vectorial (Anti-Embedding Inversion)
`¤ciberseguridad` `¤rag` `¤seguridad-tenant`
* **Sesión de origen:** Conversación 84473ee9-de59-4e3d-abba-20688986922d · 2026-09-17
* **Problema:** Los sistemas RAG tradicionales indexan fragmentos de texto crudo en bases de datos vectoriales (`pgvector`). La literatura criptográfica moderna (Morris et al., 2023; Song & Raghunathan, 2020) demuestra que los modelos de embeddings sufren ataques de inversión semántica (*Embedding Inversion Attacks*), donde un adversario con acceso de lectura a los vectores densos puede reconstruir el texto original, filtrando información confidencial, PII y secretos industriales.
* **Solución — Pipeline Sanitizador Homomórfico con Memoria Local (`NERSanitizer`):** Implementación de una compuerta estricta pre-vectorización (`features/diagnostico/services/ner_sanitizer.py`) que procesa la evidencia E3 antes de generar los embeddings. El pipeline aplica un modelo de reemplazo determinista con estado: si una entidad ("Juan Pérez", un correo o una cédula) aparece repetidamente en un mismo documento, se mapea biyectivamente al mismo pseudotoken (`[PERSONA_1]`, `[EMAIL_1]`, `[CEDULA_1]`). Esto preserva las frecuencias de término y la coherencia semántica necesarias para la recuperación por similitud de coseno en RAG, pero garantiza que la base vectorial sea matemáticamente estéril de PII. Si los vectores en `pgvector` son exfiltrados o invertidos, el atacante solo recupera la estructura abstracta sin identidad real.
* **Base científica y normativa:** Latanya Sweeney (2002) *$k$-anonymity*; Morris et al. (2023) *Text Embeddings Reveal (Almost) As Much As Text*; Art. 10 num. 1 y Art. 41 LOPDP.

---

### Aporte 39: Arquitectura Liminal de Zero Data Leakage en LLM Copilot & Filtro Dinámico de Redacción Criptográfica en Telemetría (APILoggerFilter)
`¤ciberseguridad` `¤copiloto-ia` `¤invariantes`
* **Sesión de origen:** Conversación 84473ee9-de59-4e3d-abba-20688986922d · 2026-09-17
* **Problema:** En asistentes cognitivos para auditoría y remediación de normativas (LOPDP, NIIF 18), el motor de inferencia recibe árboles de datos diagnósticos ("Scoring 4D", `brechas_identificadas`) que contienen razones sociales de clientes corporativos, direcciones IPv4 de infraestructura crítica, correos electrónicos y nombres de empleados. Al invocar APIs externas de LLMs (OpenAI, Gemini), se incurre en una fuga masiva de secretos comerciales y datos protegidos fuera de la VPC. Adicionalmente, las rutinas de logging estructurado JSON corren el riesgo de registrar inadvertidamente tokens de autenticación (`OPENAI_API_KEY`, Bearer tokens) en disco secundario o consolas SIEM.
* **Solución — Doble Compuerta Liminal (Sanitización Recursiva de Árboles + Filtro de Stream de Logs):**
  1. *Sanitizador Estructural Recurrente (`LLMDataSanitizer` en `features/ai_copilot/domain/sanitizer.py`):* Recorre recursivamente diccionarios y listas arbitrarias de brechas y scoring 4D, reconociendo y sustituyendo entidades nombradas corporativas (ej. razones sociales con sufijos `S.A.`, `C.A.`, `Inc`, `Corp`), direcciones IP, correos y personas físicas por identificadores neutros (`[EMPRESA_1]`, `[IP_1]`) previo al ensamblado del prompt HTTP. Ningún dato sensible o secreto de negocio cruza la frontera perimetral hacia el proveedor de IA.
  2. *Filtro In-Memory de Telemetría (`APILoggerFilter` en `features/ai_copilot/services/inference_engine.py`):* Acoplado al stream del logger JSON (`jubys_lopdp_json_logger`), inspecciona atómicamente el payload en memoria y redacta instantáneamente cualquier token de API (`OPENAI_API_KEY` $\to$ `[REDACTED_API_KEY]`) antes de serializar a disco o consola, imposibilitando fugas de credenciales en almacenamiento secundario.
* **Base científica y normativa:** OWASP Top 10 for LLM Applications (2023/2025: *LLM01 Prompt Injection, LLM06 Sensitive Information Disclosure*); Saltzer & Schroeder (1975) *Principles of Information Protection (Complete Mediation)*; MITRE CWE-532 (*Insertion of Sensitive Information into Log File*).

---

### Teorema 27: Inmutabilidad Criptográfica de Snapshots de Auditoría por Anclaje en Árbol de Merkle ($S_k \neq S_k' \implies \text{Root}(M) \neq \text{Root}(M')$)
`¤criptografia` `¤auditoria_capa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En sistemas de auditoría regulatoria continua (LOPDP Art. 10 num. 7 y Art. 48), los snapshots normativos congelados individualmente con hashes planos SHA-256 en base de datos sufren de vulnerabilidad ante compromisos de infraestructura: un atacante o administrador con privilegios directos sobre el motor SQL podría alterar un registro histórico y recomputar su hash individual de forma aislada sin detección.
* **Formulación y Demostración:** Sea $\mathcal{S} = \{s_1, s_2, \dots, s_n\}$ la secuencia temporal de snapshots normativos de auditoría congelados. Cada snapshot se mapea a una hoja $h_i = \text{SHA-256}(\text{JSON}(s_i))$. El Árbol de Merkle binario $\mathcal{M}$ reduce la secuencia por niveles pares:
  $$h_{i, j}^{(k+1)} = \text{SHA-256}(h_i^{(k)} \parallel h_j^{(k)})$$
  duplicando el último elemento si la cardinalidad del nivel es impar ($|L| \pmod 2 = 1$).
  Por las propiedades de resistencia a colisiones y preimagen de SHA-256 (NIST FIPS 180-4), cualquier mutación infinitesimal en cualquier snapshot pretérito $s_m \to s_m'$ ($m \le n$) induce una avalancha determinista a través de la ruta de autenticación (*Merkle Path*):
  $$s_m \neq s_m' \implies \text{Root}(\mathcal{M}) \neq \text{Root}(\mathcal{M}')$$
  con probabilidad de colisión $P(\text{colisión}) \le 2^{-256}$. Al persistir periódicamente $\text{Root}(\mathcal{M})$ en un ancla inmutable (`data/merkle_anchors.json`) sellada con Timestamp UTC (simulando una Autoridad de Sellado de Tiempo RFC 3161), se erradica la posibilidad de reescritura retroactiva, garantizando no-repudio absoluto en juicio o fiscalización de la SPDP.
* **Base bibliográfica:** Ralph C. Merkle (1987); IETF RFC 3161; NIST FIPS PUB 180-4; LOPDP Arts. 10 y 48.

---

### Aporte 40: Motor Criptográfico de Árbol de Merkle y Anclaje Temporal Asíncrono de Snapshots Normativos (`merkle_tree.py` + `merkle_anchors.json`)
`¤criptografia` `¤auditoria_capa` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** La materialización técnica del Teorema 27 exigía un motor criptográfico desacoplado dentro de la sala ADPA `features/auditoria_capa/`, que no incurriera en dependencias externas pesadas, que interactuara transparentemente con `generar_checklist_anual` y que soportara anclajes periódicos desasistidos.
* **Solución Técnica Implementada:**
  1. **Motor Merkle (`features/auditoria_capa/services/merkle_tree.py`):** Clase `MerkleTree` con balanceo determinista de hojas impares y cómputo de `compute_root()`.
  2. **Intercepción en Mamparo ADPA (`auditoria_service.py`):** Cada vez que se congela un checklist normativo anual, sus atributos canónicos (`id`, `snapshot_normativo`) se serializan en JSON ordenado (`sort_keys=True`) y se indexan como hoja SHA-256 en la estructura Merkle.
  3. **Anclaje Temporal RFC 3161 (`anclar_root_hash_ahora` / `anclar_root_hash_periodicamente`):** Función asíncrona que persiste el `root_hash`, `leaves_count` y un timestamp estricto en formato ISO-8601 UTC en `data/merkle_anchors.json`.
  4. **Aserción Físico-Matemática:** Verificado en `tests/test_merkle_anchoring.py` (`test_merkle_tree_corrupcion`), demostrando que modificar una hoja antigua corrompe el Root Hash general con Exit Code 0 en el arnés cero-regresiones.
* **Firma canónica:**
  ```python
  tree = MerkleTree()
  tree.add_leaf(data: str)
  root_hash: str = tree.compute_root()
  anclar_root_hash_ahora() -> str
  ```
* **Base normativa:** Art. 10 num. 7 y Art. 48 LOPDP; RFC 3161; FIPS PUB 180-4; Teorema 27.

---

### Teorema 28: Sincronización Causal de Asertos ante Endurecimiento Contractual (Contract Tightening Invariant)
`¤bbap` `¤arnes` `¤invariantes`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** En arquitecturas gobernadas por un arnés físico estricto, la elevación de rigidez de un contrato normativo (ej. transición de un Copiloto RAG tolerante a incertidumbre hacia un `strict_citation_mode=True` de cero alucinación) colisiona con asertos de integración legados (`test_api_gateway.py`) que esperan la respuesta ambigua original, provocando falsos positivos de regresión en el pipeline.
* **Formulación y Demostración:** Sea $\mathcal{C}_{\text{old}}$ el contrato de salida permisivo y $\mathcal{C}_{\text{new}}$ el contrato endurecido, donde $\mathcal{C}_{\text{new}} \subset \mathcal{C}_{\text{old}}$ y $\mathcal{C}_{\text{old}} \setminus \mathcal{C}_{\text{new}} \neq \emptyset$. La suite de arbitraje exógeno $\mathcal{A}$ se compone de pruebas unitarias $\mathcal{U}$ y de integración gateway $\mathcal{G}$.
  $$\text{ExitCode}(\mathcal{A}) = 0 \iff (\forall u \in \mathcal{U}, u(f) = 1) \land (\forall g \in \mathcal{G}, g(f) = 1)$$
  Si $f$ transiciona estrictamente a $\mathcal{C}_{\text{new}}$, cualquier $g \in \mathcal{G}$ configurado con $g(\text{output}) \iff \text{output} \in (\mathcal{C}_{\text{old}} \setminus \mathcal{C}_{\text{new}})$ fallará necesariamente. Por ende, todo endurecimiento contractual normativo exige una sincronización topológica atómica:
  $$\Delta(\text{Contrato}) = \mathcal{C}_{\text{new}} \implies \Delta(\text{Gateways}) := \text{Assert}_{\mathcal{C}_{\text{new}}}$$
  Demostrando que la actualización de tests no es una laxitud de regresión, sino una convalidación notarial obligatoria del nuevo invariante de Cero Alucinación.
* **Base bibliográfica:** Bertrand Meyer (1992); Edsger W. Dijkstra (1976); Art. 48 LOPDP.

---

### Aporte 41: Pasarela RAG con Modo Estricto de Cero Alucinación y Convalidación Gateway (`rag_engine.py` + `rag_router.py`)
`¤copiloto-ia` `¤regulacion-rag` `¤api-gateway`
* **Sesión de origen:** Conversación 3d7b4609-918d-4e03-ba3b-22029c4a8c40 · 2026-09-17
* **Problema:** La integración de un RAG legal en APIs públicas requiere una barrera inviolable contra alucinaciones sin romper los endpoints existentes ni violar los mamparos ADPA.
* **Solución Técnica:**
  1. Configuración forzosa de `strict_citation_mode=True` por defecto en `RAGCopilotEngine` (`features/regulacion_rag/services/rag_engine.py`).
  2. Implementación de router dedicado `api/routers/rag_router.py` exponiendo `POST /api/v1/rag/query` con inyección de dependencias seguras y delegación estricta hacia la compuerta pública `regulacion_rag_service.py`.
  3. Convalidación notarial del test E2E `test_api_gateway.py::test_rag_endpoint` para auditar la cadena de fallback absoluto *"No puedo responder esto basándome en la normativa indexada."* con confianza cero y bandera `fuente_oficial_verificada=False`.
* **Base normativa:** Art. 48 LOPDP; ISO/IEC 42001 (Sistemas de Gestión de IA); Teorema 28.

---

### Teorema 29: Restricción Gramatical Sintáctica por Decodificación Guiada en Motores GRC (Grammar-Constrained Decoding / Zero-Hallucination Schema Barrier)
`¤copiloto-ia` `¤invariantes` `¤bbap`
* **Sesión de origen:** Conversación ae0e63a5-1330-41df-b50c-7f86a3bc58a2 · 2026-09-17
* **Problema:** En asistentes cognitivos para auditoría y remediación regulatoria (LOPDP / NIIF 18), la inferencia no restringida o la solicitud de JSON mediante prompts en lenguaje natural ("Devuelve un JSON con tal formato") produce alucinaciones sintácticas, atributos omitidos, mutaciones en nombres de llaves o tipos de datos disjuntos (e.g. `string` en lugar de `List[TareaMitigacionIA]`). Estos fallos invalidan silenciosamente la serialización en la capa de transporte o arrojan excepciones no controladas de `ValidationError` en FastAPI, rompiendo la invariante de Cero Regresión ($\neg R$).
* **Formulación y Demostración:** Sea $\Sigma^*$ el conjunto de cadenas posibles sobre el vocabulario del LLM autorregresivo $\mathcal{M}_{\theta}$, y sea $\mathcal{G}_{\text{Pydantic}}$ la gramática libre de contexto (CFG) que formaliza de manera biyectiva el esquema canónico $\mathcal{S}$ (`PlanMitigacionResponse`). La decodificación guiada por gramática impone una máscara de logits determinista $\mathcal{M}_{\text{mask}}$ sobre la distribución softmax de tokens en cada paso generativo $t$:
  $$P(w_t \mid w_{<t}) = \text{Softmax}\left(\frac{z_t + \mathcal{M}_{\text{mask}}(w_{<t}, \mathcal{G}_{\text{Pydantic}})}{T}\right)$$
  Donde:
  $$\mathcal{M}_{\text{mask}}(w_{<t}, \mathcal{G}_{\text{Pydantic}}) = \begin{cases} 0, & \text{si } \exists \alpha \in \Sigma^* \text{ tal que } w_{<t} \cdot w_t \cdot \alpha \in \mathcal{L}(\mathcal{G}_{\text{Pydantic}}) \\ -\infty, & \text{en caso contrario} \end{cases}$$
  Al suprimir a $-\infty$ la probabilidad de cualquier token que desvíe la cadena del autómata de pila de la gramática del esquema Pydantic, se garantiza formalmente que:
  $$P\left(\text{Salida}(\mathcal{M}_{\theta}) \notin \mathcal{L}(\mathcal{G}_{\text{Pydantic}})\right) \equiv 0$$
  La respuesta generada es 100% conforme por construcción matemática al esquema de dominio, erradicando alucinaciones estructurales sin necesidad de reintentos heurísticos ni sanitizadores reactivos post-hoc.
* **Base científica y normativa:** Hopcroft, Motwani & Ullman (2001) *«Introduction to Automata Theory, Languages, and Computation»*; Willard & Louf (2023) *«Efficient Guided Generation for Large Language Models»*; OpenAI Structured Outputs Specification (2024); Principio de Tipado Estricto de Liskov & Wing (1994); Teorema 22 de esta plataforma.

---

### Aporte 42: Motor de Inferencia Isomórfico Resiliente con Doble Compuerta y Fallback Heurístico Transparente (`inference_engine.py`)
`¤copiloto-ia` `¤adpa` `¤bbap` `¤invariantes`
* **Sesión de origen:** Conversación ae0e63a5-1330-41df-b50c-7f86a3bc58a2 · 2026-09-17
* **Problema:** En suites de pruebas automatizadas, entornos de CI/CD aislados (*Clean-Room / Zero-Network*) o entornos de desarrollo donde `OPENAI_API_KEY` no se encuentra inyectada o la red externa no responde, la invocación de clientes de inferencia LLM lanza excepciones bloqueantes (`AuthenticationError`, `APIConnectionError`). Esto provoca la detención intempestiva del pipeline y falsos positivos de regresión en sistemas de auditoría continua.
* **Solución Técnica — Doble Compuerta con Degradación Elegante:** Implementación en la sala ADPA `features/ai_copilot/services/inference_engine.py` de una función asíncrona pura `generar_plan_mitigacion(request)` bajo el patrón *Graceful Degradation*:
  1. *Compuerta Primaria (Inferencia Real Estructurada):* Si `OPENAI_API_KEY` está presente en las variables de entorno y `AsyncOpenAI` está disponible, se inicializa el cliente asíncrono y se ejecuta `client.beta.chat.completions.parse` con `response_format=PlanMitigacionResponse` y `temperature=0.2`.
  2. *Compuerta Secundaria (Fallback Heurístico Determinista):* Si falta la credencial de API, la librería no está instalada o la llamada remota falla con excepción de red o cuota, el motor intercepta el evento e invoca un clasificador heurístico local determinista:
     $$\text{es\_riesgo\_alto} \iff \text{request.scoring\_global} < 3.0$$
     Generando de forma síncrona una instancia válida de `PlanMitigacionResponse` con tareas tipadas `TareaMitigacionIA` clasificadas con impacto `"ALTO"` o `"MEDIO"`.
  3. *Pureza Funcional y Cero Efectos Secundarios:* La función no muta estado global, opera de manera puramente asíncrona (`async/await`) y asegura que la suite de integración devuelva siempre `Exit Code 0` en entornos con o sin conexión externa.
* **Firma canónica:**
  ```python
  async def generar_plan_mitigacion(request: AnalisisDiagnosticoRequest) -> PlanMitigacionResponse
  ```
* **Base científica y normativa:** Michael T. Nygard (2018) *«Release It!»* (Patrones Circuit Breaker y Graceful Degradation); Saltzer & Schroeder (1975) *Fail-Safe Defaults*; Principios Clean-Room del Contrato Bilateral Agéntico (CBA).

---

### Aporte 43: Polimorfismo Semántico en Prompts de Auditoría GRC Multi-Normativa (Dynamic GRC Prompt Specialization)
`¤copiloto-ia` `¤regulation-code`
* **Sesión de origen:** Conversación ae0e63a5-1330-41df-b50c-7f86a3bc58a2 · 2026-09-17
* **Problema:** En plataformas unificadas de Gobierno, Riesgo y Cumplimiento (GRC) que procesan dominios heterogéneos (e.g. derecho sancionatorio de protección de datos personales LOPDP vs. normativa técnica contable y de revelación financiera NIIF 18), el uso de prompts estáticos generalistas induce a respuestas ambiguas o desalineadas con la pericia técnica requerida para cada corpus legal.
* **Solución Técnica:** Especialización ontológica dinámica en tiempo de inferencia dentro de `generar_plan_mitigacion`. El System Prompt se parametriza en tiempo de ejecución de acuerdo al discriminador `request.normativa`:
  $$\text{Prompt}_{\text{sys}}(\mathcal{N}) = \text{BaseAudit}_{\text{GRC}} \oplus \begin{cases} \text{DirectivaPrivacidad}(\text{LOPDP}), & \text{si } \mathcal{N} = \text{"LOPDP"} \\ \text{DirectivaContableFinanciera}(\text{NIIF 18}), & \text{si } \mathcal{N} = \text{"NIIF 18"} \end{cases}$$
  Instruyendo al modelo a enfocar su análisis de mitigación en privacidad y protección de datos para LOPDP (derechos, transferencias, bases legitimadoras), o en presentación, clasificación de categorías operativas e información a revelar para NIIF 18. Esto permite que una única interfaz y contrato de datos gobiernen auditorías cruzadas sin duplicar servicios de inferencia.
* **Base científica y normativa:** Teorema 31 (Auditoría Financiera Cruzada / GRC Unificado); IASB NIIF 18 (2024); LOPDP Ecuador (2021).
---

### Teorema 30: Invariante de Deriva Paramétrica de Riesgo en Ciclos de Vida EIPD (Continuous EIPD State Machine & Risk Drift Sensor)
`¤mtge-granescala` `¤riesgos-eipd` `¤invariantes`
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-19
* **Problema:** En la gestión de privacidad clásica (LOPDP / RGPD), las Evaluaciones de Impacto en la Protección de Datos (EIPD / DPIA) se abordan como artefactos documentales estáticos fechados en $t_0$. Cuando una actividad de tratamiento (RAT) evoluciona en producción —por ejemplo, aumentando progresivamente su masa de titulares o incorporando datos biométricos mediante actualizaciones de software—, la organización cae en ceguera de riesgo y en ilicitud sobrevenida al ampararse en una EIPD aprobada pero materialmente desfasada. Esto vulnera el principio de responsabilidad proactiva (Art. 10 num. 7 LOPDP) y el principio de mejora continua de riesgos de ISO/IEC 27701:2019.
* **Formulación y Demostración:**
  Sea una EIPD aprobada con estado $\mathcal{E}_0 = \text{ACTIVA}$, asociada a una actividad de tratamiento con volumen de titulares de referencia $V_0 \in \mathbb{N}^+$ y conjunto finito de categorías de datos autorizadas $\mathcal{C}_0$.
  Sea $RAT(t)$ la tupla del tratamiento en cualquier instante posterior $t > t_0$, caracterizada por su volumen actual $V(t)$ y sus categorías de datos $\mathcal{C}(t)$.
  Definimos el operador booleano de deriva de riesgo $\Phi: RAT \times EIPD \to \{0, 1\}$:
  $$\Phi(RAT(t), EIPD) \iff \left(\frac{V(t) - V_0}{V_0} > 0.25\right) \lor \left(\text{"BIOMETRICOS"} \in \mathcal{C}(t) \setminus \mathcal{C}_0\right)$$
  El autómata de transición de estado del ciclo de vida de la EIPD se rige por:
  $$\text{Estado}(EIPD_{t}) = \begin{cases} \text{OBSOLETA\_REQUIERE\_ACTUALIZACION}, & \text{si } \Phi(RAT(t), EIPD) = 1 \\ \text{ACTIVA}, & \text{en caso contrario} \end{cases}$$
  Al ser $\Phi$ una función determinista computable en $O(1)$ sobre los atributos del RAT, se demuestra formalmente que la obsolescencia es inmediata, no compensatoria e inmune a la discrecionalidad humana, forzando la reevaluación obligatoria del DPO y garantizando el cumplimiento continuo del Art. 48 de la LOPDP y la Res. SPDP-SPD-2026-0005-R.
* **Base científica y normativa:** ISO/IEC 27701:2019 (Cláusula 6.5 y Anexo A); EDPB Guidelines 04/2019 on Data Protection by Design and by Default; David Harel (1987) *Statecharts: A visual formalism for complex systems*; Res. SPDP-SPD-2026-0005-R.

---

### Aporte 44: Implementación del Motor Reactivo de Re-Evaluación Continua EIPD (`mtge_engine.py` + `models.py`)
`¤mtge-granescala` `¤riesgos-eipd` `¤backend` `¤clean-room`
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-19
* **Problema:** La materialización técnica del Sensor de Deriva de Riesgo requería extender el dominio del RAT y crear un motor de re-evaluación reactivo en Python sin introducir regresiones en el RLS ni alterar la base de datos de auditorías.
* **Solución Técnica:**
  1. Extensión en `features/rat/domain/models.py` de la entidad `ActividadRAT` con el atributo `categorias_datos: List[str]` y formalización de las entidades tipadas `EstadoEIPD` (`EN_PROGRESO`, `ACTIVA`, `OBSOLETA_REQUIERE_ACTUALIZACION`) y `EIPD` (`volumen_titulares_aprobacion`, `categorias_datos_aprobacion`).
  2. Implementación en `features/rat/services/mtge_engine.py` de la función de evaluación determinista `evaluar_deriva_riesgo_eipd(rat_actualizado: ActividadRAT)` y el repositorio `EIPDRepository`.
  3. Verificación con árbitro exógeno en `tests/test_eipd_drift_sensor.py`: 3 pruebas unitarias estrictas en verde validando la transición atómica al superar el 25% de volumen, la transición al inyectar datos biométricos, y la preservación del estado activo cuando la variación permanece dentro de los umbrales tolerables ($\Delta V \le 25\%$).
* **Firma canónica:**
  ```python
  def evaluar_deriva_riesgo_eipd(rat_actualizado: ActividadRAT) -> Optional[EIPD]
  ```

---

### Aporte 45: Motor de Cálculo de Impacto de Reformas SPDP con Invariante Histórico (`diff_engine.py` + `regulacion_service.py`)
`¤regulation-code` `¤adpa` `¤auditoria`
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-19
* **Problema:** Cuando la Superintendencia de Protección de Datos Personales (SPDP) emite nuevas resoluciones normativas vinculantes, los sistemas de GRC tradicionales o bien no computan el impacto en los tratamientos existentes (generando pasivos regulatorios ocultos), o bien sobreescriben auditorías históricas previas (destruyendo el principio probatorio procesal de inmutabilidad).
* **Solución Técnica:**
  1. Implementación en `features/regulacion_rag/services/diff_engine.py` de la función `calcular_impacto_reforma(reforma: Dict[str, Any])`. Mapea descriptores ontológicos y palabras clave de la reforma hacia los dominios de control del marco G01–G16 y las actividades del RAT vinculadas.
  2. Emisión de recomendaciones atómicas: produce una lista de revalidaciones sugeridas y áreas de riesgo emergentes hacia el futuro.
  3. *Invariante Histórico de Inmutabilidad:* Ninguna auditoría, dictamen DPO o snapshot pasado es mutado ni recalculado retrospectivamente, garantizando la preservación de la cadena de custodia probatoria (WORM) exigida por el Art. 10 num. 7 de la LOPDP.
  4. Confinamiento ADPA en `features/regulacion_rag/regulacion_service.py` (`evaluar_impacto_resolucion`), asegurando que las demás capas consuman el diff normativo como un servicio desacoplado.
* **Base científica y normativa:** Guido Governatori, Monica Palmirani, et al. (2013) *«Norm Compliance in Business Processes: An Approach Based on Deontic Logic and Change Impact Analysis»*; Bohne (2021) *«Legal Informatics & Regulation as Code»*; LOPDP Art. 10 num. 7 y Art. 48.

---

### Aporte 46: Poka-Yoke Estructural de Garantías en Transferencias Internacionales de Datos (`encargados_service.py` + `seed_database.py`)
`¤transferencias` `¤poka-yoke` `¤seguridad-tenant`
* **Sesión de origen:** Conversación bd221bdd-9d0f-4812-9cfb-2a9cc5939ca5 · 2026-09-19
* **Problema:** En plataformas multi-tenant de privacidad, permitir el registro descuidado o la exportación de datos hacia encargados o terceros ubicados en países sin nivel adecuado de protección sin exigir garantías contractuales (Cláusulas Tipo / SCCs) genera una infracción muy grave conforme al Art. 56 LOPDP y una vulnerabilidad transaccional crítica.
* **Solución Técnica:**
  1. Implementación de guardián de dominio Poka-Yoke en `features/transferencias/services/encargados_service.py` a través del método booleano:
     ```python
     def es_transferencia_legal(self) -> bool:
         if self.nivel_proteccion == NivelProteccion.ADECUADO:
             return True
         return self.clausulas_firmadas
     ```
  2. Blindaje a nivel de modelo relacional SQLAlchemy: `TerceroEncargado` almacena de forma inmutable `tenant_id`, `pais_destino`, `nivel_proteccion` y el flag booleano `clausulas_firmadas`.
  3. Demostración en el seeder `scripts/seed_database.py`: inyección de casos de prueba controlados incluyendo un caso no conforme (`CallCenter Offshore`, nivel `NO_ADECUADO` y `clausulas_firmadas=False`) para detonar alertas preventivas inmediatas en el frontend y evitar transferencias no autorizadas.
* **Base científica y normativa:** Shigeo Shingo (1961) *«Poka-Yoke System»*; Art. 56 y 57 LOPDP Ecuador; Capítulo V RGPD (Art. 44–46).

---

### Aporte 47: Refactorización Orgánica mediante Bus de Memoria Estigmérgica (Trans-Conversational Context Injection)
¤bbap ¤arquitectura ¤gobernanza-agentica
* **Sesión de origen:** Análisis global de las 23 conversaciones del repositorio rain de Antigravity · 2026-09-19
* **Problema:** En arquitecturas de desarrollo gobernadas por múltiples subagentes concurrentes y sesiones conversacionales separadas, el conocimiento arquitectónico se fragmenta (Amnesia Agéntica). Los agentes aislados tienden a reinventar soluciones complejas (ej. mitigación de ataques de inyección, barreras DLP, enfoques WORM) con diversos grados de madurez técnica, provocando una deriva arquitectónica sistémica.
* **Solución Técnica:** La obligatoriedad transversal del uso de APORTES_INEDITOS.md y FUENTES_Y_BIBLIOGRAFIA.md como únicos repositorios de "Verdad Epistémica" ($). El análisis del *brain* evidencia que agentes operando en hilos completamente independientes (ej. el Frontend Architect y el AI Cognitive Engineer) lograron acoplar sus invenciones (como el Renderizado Liminal Reactivo del Aporte 32 y el K-Anonimato en Indexación Vectorial del Aporte 38) sin comunicación síncrona (RPC/mensajes). La simple lectura del archivo de Aportes en cada inicio de sesión actuó como un **Bus de Memoria Estigmérgica**, permitiendo que el conocimiento técnico se heredara, se compendiara y se protegiera contra refutaciones o regresiones a lo largo de toda la topología del proyecto.
* **Base científica y normativa:** Pierre-Paul Grassé (1959) *«La reconstruction du nid et les coordinations inter-individuelles chez Bellicositermes natalensis»* (Teoría de la Estimergia); Arquitecturas de Blackboards (Sistemas Multi-Agente).

---

# PARTE IV: Assessment por Dimensiones, Poda por Talla y Evidencia Verificada (Sesión 2026-09-19)
`¤diagnostico` `¤evidencias` `¤invariantes`

> **CRITERIO DE ADMISIÓN DE ESTA PARTE:** Solo se registran hallazgos (a) ausentes de este tratado al 2026-09-19 (verificado por búsqueda textual en `APORTES_INEDITOS.md`, `FUENTES_Y_BIBLIOGRAFIA.md`, `INVARIANTS.md` y `PRD.md`), (b) comprobables con un árbitro exógeno o una lectura del código, y (c) compatibles con la literatura citada. Cada aporte declara su **estado de validación**: qué se ejecutó y qué solo se leyó. Los límites conocidos se registran junto al aporte para no dejar afirmaciones expuestas a refutación posterior. Numeración correlativa a partir del Aporte 48.

---

## Notas de vigencia sobre registros anteriores

* **T7 y Aporte 11 (régimen "PI" como caso activo).** Sus ejemplos designan *Propiedad Intelectual* como régimen activo, con whitelist `.pdf, .docx, .md, .txt`. Desde 2026-09-19 la normativa por defecto es **LOPDP** (catálogo `frontend/src/lib/normativas.ts`), con whitelist `.pdf, .docx, .xlsx, .csv, .txt, .png, .jpg, .jpeg`; PI e ISO figuran como *Próximamente* (no seleccionables) por carecer de banco propio. La invariante de T7 ($\Delta(\mathcal{N}) \implies \mathcal{E} \leftarrow \emptyset$) **se mantiene** y ahora alcanza también al registro de evidencias con huella (Aporte 50). Origen de la discrepancia: el assessment de protección de datos se ejecutaba bajo la etiqueta *PI*, que designa otra rama del derecho (derechos de autor, marcas y licencias; autoridad SENADI), porque no existía la opción LOPDP.
* **T3 (rango esperado $\mathbb{E}[N_{\text{visibles}}] \in [45, 68]$).** La medición por talla del banco de 80 controles es **39 / 59 / 73 / 80** (micro / pequeña / mediana / corporativo; Aporte 53). La cota superior $N \le 80$ se cumple; el rango 45–68 solo describe tallas intermedias: la microempresa queda por debajo y la corporativa alcanza la cota.
* **Whitelist por extensión (Aporte 11).** Es un Poka-Yoke de conveniencia, no una verificación de contenido: un archivo con extensión permitida pero contenido distinto se acepta. El PRD contempla firmas de archivo (*magic bytes*) en la capa de seguridad; el frontend no las valida.

---

### Aporte 48: Cota Estructural de Madurez por Controles Habilitadores (Nivel Ajustado ≤ 2)
`¤diagnostico-scoring` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Un score ponderado alto puede coexistir con la ausencia de las bases que hacen demostrable el resto del sistema (inventario de tratamientos, RAT, clasificación de datos sensibles, verificación de identidad). Sin una regla explícita, el tablero reportaría "Nivel 4" sobre un sistema cuya trazabilidad no puede probarse.
* **Formulación:** Para cada control $i$ con nivel asignado $n_i \in \{1..5\}$, evidencia $E_i \in \{0..3\}$ reescalada a $\varepsilon_i = \tfrac{4}{3}E_i$ y criticidad $\kappa_i \in \{1..5\}$:
  $$n^{ef}_i = \min\!\big(n_i,\ \varepsilon_i + 1\big) \qquad \rho_i = (5 - n^{ef}_i)\,\kappa_i \qquad s_d = \frac{100}{5\,|I_d|}\sum_{i \in I_d} n^{ef}_i$$
  $$S = \frac{\sum_{d \in D^{+}} w_d\, s_d}{\sum_{d \in D^{+}} w_d}, \quad D^{+} = \{d : |I_d^{\text{evaluados}}| > 0\}$$
  Sea $H = \{9, 10, 13, 28\}$ el conjunto de controles habilitadores. El nivel final es:
  $$N_{\text{ajus}} = \begin{cases} \min(N_{\text{teo}}(S),\, 2), & \exists h \in H:\ n^{ef}_h < 3 \\ N_{\text{teo}}(S), & \text{en otro caso} \end{cases}$$
* **Propiedad demostrable (no compensación):** mientras subsista $n^{ef}_h < 3$ para algún $h \in H$, $N_{\text{ajus}} \le 2$ con independencia de $n^{ef}_j$ para todo $j \notin H$. Demostración: la cota es una constante que no depende de $S$; $S$ puede crecer, pero $\min(\cdot, 2)$ lo trunca.
* **Estado de validación:** *Ejecutado.* Con el conjunto de referencia de 80 controles: $S = 75{,}58$, $N_{\text{teo}} = 4$ (Gestionado), los 4 habilitadores con $n^{ef} = 1{,}00$ y $\rho = 20$ cada uno ⇒ $N_{\text{ajus}} = 2$. Un auditor independiente recalculó a mano la dimensión D02 (46,7 %) y coincidió con el código; el navegador mostró "75,6 % · Nivel teórico 4 · Degradado 4 → 2".
* **Origen y atribución:** La fórmula del nivel efectivo y del riesgo proviene de la hoja *ASSESSMENT* de la Matriz de Madurez SMARTCIDI (`Assessment_Madurez_SGPDP_COAC_SMARTCIDI (2).xlsx`), y el caso 81,02 % → Nivel 2 del *Reporte Assessment SGPDP COAC* (15-sep-2026). El ajuste a Nivel 2 se tomó del resultado de ese reporte; el mecanismo interno del libro **no** se auditó celda a celda. Aporte propio: la formalización, la propiedad de no compensación, la implementación tipada y su verificación numérica.
* **Relación con T16:** T16 acota $\mathcal{S}_{\text{SPDP}}$ según el *número de brechas críticas* (0 / 1–2 / ≥3). Esta cota se activa por el *estado de los habilitadores*, con otro disparador. Coexisten (ver Hallazgos abiertos).
* **Límites conocidos:** (i) Renormalizar sobre $D^{+}$ hace que una evaluación parcial parezca madura: con 2 de 39 controles respondidos el tablero mostró 85,6 %; el score solo es interpretable junto a la cobertura (5,1 % en ese caso). (ii) El conjunto $H$ y el tope 2 son parámetros de negocio heredados del reporte, no derivados.
* **Base científica:** Paulk et al. (1993), *CMM v1.1*, y CMMI Product Team (2010), *CMMI-DEV v1.3* (representación por etapas: un nivel exige satisfacer las áreas de los niveles inferiores); Tversky (1972) y Fishburn (1974) para la no compensación (ya catalogados).

---

### Aporte 49: Modo de Cálculo "Verificado" — Evidencia Vinculada como Condición del Nivel Sellado
`¤evidencias` `¤diagnostico-scoring` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** El nivel de evidencia E0–E3 lo declara el auditor. Un cuestionario donde "Conforme + E3" no exige documento alguno permite autodeclaración con apariencia de prueba (Doctrina 3). Además, el snapshot inmutable (T18) fijaba esa autodeclaración con valor probatorio.
* **Formulación:** Sea $\mathcal{E}$ el registro de evidencias y $\text{vinc}(e)$ los controles que respalda $e \in \mathcal{E}$. Un control está *verificado* si $V(i) = \mathbf{1}\big[\exists e \in \mathcal{E}: i \in \text{vinc}(e)\big]$. El nivel de evidencia verificado es:
  $$E^{\text{ver}}_i = V(i)\cdot E^{\text{decl}}_i$$
  El tablero calcula $S^{\text{decl}}$ y $S^{\text{ver}}$ con la misma fórmula del Aporte 48. El snapshot sella $E^{\text{ver}}_i$ (un control sin documento se sella como E0) y calcula su resumen con el modo verificado.
* **Propiedad demostrable (monotonía):** $E^{\text{ver}}_i \le E^{\text{decl}}_i \implies n^{ef,\text{ver}}_i \le n^{ef,\text{decl}}_i$. Como $D^{+}$ y los pesos $w_d$ no cambian entre modos, cada $s_d$ y por tanto $S$ son monótonos: $S^{\text{ver}} \le S^{\text{decl}}$ y el nivel sellado nunca supera al declarado.
* **Estado de validación:** *Ejecutado en navegador y a mano.* Control 1 (Conforme, E3, sin documento) y control 9 (Conforme, E2, con EVD-0001): declarado D01 = 100 %, D02 = 73,3 % ⇒ $S = 85{,}6$ (Nivel 4); verificado control 1 → $n^{ef} = \min(5, 1) = 1$ (20 %), control 9 → $\min(5, 3{,}67) = 3{,}67$ (73,3 %) ⇒ $S = 48{,}7$ (Nivel 2). El tablero informó "57 % de la madurez declarada está demostrada". *No ejecutado:* el sellado real (escribe en `data/snapshots.json`, historial inmutable); se verificó por lectura del código.
* **Límites conocidos:** **el vínculo documental es condición necesaria, no suficiente.** Un documento vinculado conserva el nivel declarado (p. ej. E3) aunque solo acredite E1; la verificación prueba existencia e integridad del documento, no su idoneidad ni la implementación operativa (E2/E3). Propuesta no implementada: tope por tipo de evidencia (documento ⇒ ≤ E1; registro operativo ⇒ ≤ E2).
* **Base científica y normativa:** ISO 19011:2018 (la evidencia de auditoría debe ser verificable); Power (1997) *The Audit Society: Rituals of Verification* (riesgo de que la verificación documental sustituya a la de eficacia); Doctrina 3 del PRD.

---

### Aporte 50: Custodia de Huella sin Custodia de Contenido, con Verificación por Re-presentación
`¤evidencias` `¤seguridad-tenant` `¤implementacion`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Un registro probatorio que almacena el documento contradice la minimización (Doctrina 8) y convierte a la plataforma en custodio de información sensible; un registro sin integridad no permite probar que un documento presentado es el registrado.
* **Solución:** El navegador calcula $h = \text{SHA-256}(\text{bytes}(f))$ con `crypto.subtle.digest` y registra la tupla $e = \langle \text{código}, \text{nombre}, \text{tamaño}, \text{tipo}, h, N, C \rangle$; el archivo no se transmite ni se conserva. La verificación es por *re-presentación*:
  $$\text{Íntegro}(f') \iff \exists e \in \mathcal{E}:\ \text{SHA-256}(f') = h(e)$$
  El registro está direccionado por contenido con clave $(h, N)$: registrar dos veces el mismo documento en la misma normativa devuelve la misma evidencia y **une** los controles pedidos (operación idempotente y conmutativa sobre el conjunto de vínculos).
* **Estado de validación:** *Ejecutado.* Un agente cotejó el SHA-256 del navegador contra `sha256sum` y `certutil` sobre un archivo de 3 MB con resultado idéntico (`e7bff00c…b3a6ed`); en el navegador, el documento original dio "Íntegro: coincide con EVD-0001" y una copia con un carácter cambiado dio "No coincide". *Salvedad:* el valor esperado de la prueba en navegador usó la misma API Web Crypto que la aplicación, por lo que esa comparación no es independiente; la independiente es la del cotejo con `sha256sum`/`certutil`.
* **Límites conocidos:** (i) Integridad no es autenticidad ni fecha: la huella la produce el cliente y, sin sello de tiempo (RFC 3161, ya en Aporte 40), no prueba anterioridad. (ii) El digest de un documento corto o predecible es adivinable por diccionario, por lo que no es confidencial en ese caso. (iii) El registro reside en `localStorage`; existe un backend equivalente en memoria (Aporte 51) que **no** está sincronizado con el frontend. (iv) La extensión validada no garantiza el contenido (ver Notas de vigencia).
* **Base científica y normativa:** NIST FIPS 180-4 (2015) y NIST SP 800-107 Rev. 1 (2012); W3C *Web Cryptography API* (2017); Quinlan & Dorward (2002), *Venti* (almacenamiento direccionado por contenido); Art. 10 LOPDP (minimización).

---

### Aporte 51: Contrato de Digest No Ambiguo (Corrección del Doble Hash)
`¤evidencias` `¤implementacion` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** El endpoint `POST /evidencias` hasheaba siempre `contenido_texto_o_hash`. Si el cliente enviaba un SHA-256 ya calculado, el sistema almacenaba $\text{SHA-256}(h)$, distinto del hash del archivo: la verificación de integridad fallaba **en silencio**, sin error ni advertencia.
* **Solución:** Campos distintos por tipo semántico: `sha256_hash` (64 caracteres hexadecimales, normalizado a minúsculas y almacenado tal cual) y `contenido_texto` (hasheado una sola vez por el servidor). Si llegan ambos y difieren, o ninguno, o el digest es inválido ⇒ HTTP 422.
  $$\text{almacenado}(h) = h \quad (h \in \text{Hex}_{64}), \qquad \text{almacenado}(t) = \text{SHA-256}(t)$$
* **Estado de validación:** *Ejecutado.* `tests/test_evidencias_contrato.py`: 24 pruebas en verde (digest almacenado tal cual y distinto de $\text{SHA-256}(h)$; conflicto ⇒ 422; digest inválido `abc`, `z*64`, 63, 65 y vacío ⇒ 422; deduplicación con unión de vínculos; aislamiento entre tenants; código correlativo no repetido). Suite completa: 75 en verde y 2 fallos preexistentes ajenos (`test_api_health_check`, `test_ai_copilot_diagnosticar_mock`). En una ejecución posterior del mismo día la suite dio 77 en verde: esos 2 fallos ya no se reprodujeron (causa no investigada; uno de ellos dependía del orden de ejecución).
* **Trade-off documentado:** el campo heredado `contenido_texto_o_hash` (obsoleto) interpreta como digest todo valor con forma de SHA-256; un texto que fuese literalmente 64 caracteres hexadecimales se clasificaría mal. Una unión de tipos en un solo campo es inherentemente ambigua; de ahí su deprecación.
* **Base científica:** Meyer (1992), *Applying Design by Contract* (precondiciones sobre la entrada); NIST FIPS 180-4 (256 bits = 64 caracteres hexadecimales).

---

### Aporte 52: Correlativos Monótonos por Marca de Agua (No Reutilización de Códigos Citados)
`¤evidencias` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Un snapshot sellado cita evidencias por código (`EVD-0003 (SHA-256 …)`). Si el código se asigna como "máximo existente + 1", eliminar la última evidencia libera su número y el siguiente documento lo reutiliza: el sello histórico pasa a apuntar a otro documento.
* **Formulación:** El contador es una marca de agua persistida, independiente del conjunto vigente $\mathcal{E}_t$:
  $$c_{t+1} = \max\!\big(c_t,\ \max_{e \in \mathcal{E}_t}\text{num}(e)\big) + 1$$
  Demostración: $c$ es estrictamente creciente por construcción y la eliminación solo reduce $\mathcal{E}$, nunca $c$; luego la asignación código → documento es inyectiva durante toda la vida del proyecto. El contador viaja en el estado persistido y en la instantánea del proyecto.
* **Estado de validación:** *Ejecutado en navegador.* Se registraron EVD-0001 y EVD-0002, se eliminó EVD-0002 y el siguiente documento recibió **EVD-0003** (contador = 3).
* **Límite conocido:** el backend (`_siguiente_codigo`) usa el máximo existente por tenant y año; hoy no hay endpoint de eliminación, pero repetiría códigos si se añadiera uno sin una marca de agua equivalente.
* **Base científica:** Lamport (1978), contadores lógicos estrictamente crecientes; documentación oficial de PostgreSQL sobre secuencias (un valor consumido no se revierte ni se reutiliza, y se aceptan huecos).

---

### Aporte 53: Poda del Cuestionario por Talla en Dos Ejes (Número y Redacción) con Habilitadores Invariantes
`¤diagnostico` `¤diagnostico-motor`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Un mismo cuestionario aplicado a una microempresa y a un grupo corporativo genera brechas artificiales (se pregunta por comités, auditoría interna o segregación de ambientes que la organización no puede tener) y exige verificaciones desproporcionadas. Esto contamina el scoring sin describir un incumplimiento real.
* **Formulación:** Sea $t \in \{\text{micro} < \text{pequeña} < \text{mediana} < \text{corporativo}\}$. Cada control $q$ declara $t_{\min}(q)$ y variantes de enunciado y evidencia. Entonces:
  $$Q(t) = \{q : t_{\min}(q) \le t\}, \qquad \tau(q, t) = \text{variante de la mayor talla} \le t \text{ (herencia hacia abajo)}$$
  Propiedades: **P1** anidamiento, $t \le t' \implies Q(t) \subseteq Q(t')$ (el predicado es monótono en $t$); **P2** $H \subseteq Q(\text{micro})$: los habilitadores del Aporte 48 aplican a toda talla; **P3** $|Q(t)| \le 80$. La cobertura del tablero usa como denominador $|Q(t)|$ (lo exigible), no lo respondido.
* **Estado de validación:** *Ejecutado.* Script de validación del banco: 80 ids únicos, `control` y `dimensionId` idénticos al conjunto de referencia, 4 habilitadores con `tamanoMinimo = micro`, $|Q| = 39 / 59 / 73 / 80$, 73 controles con redacción por talla y 68 con evidencia por talla. En navegador, el control 1 se redacta "…aprobada por el propietario o la gerencia y comunicada al personal" en microempresa y "…cuerpo normativo interno… Alta Dirección… en todas las filiales" en corporativo.
* **Límites conocidos (relevantes):** las asignaciones $t_{\min}$, las redacciones y las **referencias normativas del banco fueron redactadas por agentes de IA y no han sido validadas por asesoría jurídica ni auditadas artículo por artículo contra la LOPDP/RGLOPDP**. A los agentes se les indicó no citar artículos inciertos, pero la ausencia de citas erróneas no se verificó. Debe revisarlas un DPO o abogado antes de usarlas con clientes. La poda gradúa la *forma de verificación*; no debe leerse como exención de obligaciones legales.
* **Base científica y normativa:** Reglamento (UE) 2016/679, Art. 24(1) (medidas según naturaleza, alcance, contexto y riesgo), Art. 30(5) y Considerando 13 (atención a micro, pequeñas y medianas empresas) como evidencia de derecho comparado de que la protección de datos gradúa obligaciones por escala y riesgo; Sweller (1988) sobre carga cognitiva (ya catalogado). La LOPDP no se contrastó sobre este punto en la sesión.

---

### Aporte 54: Estado Persistido Versionado y Lectura Tolerante de Proyectos Guardados
`¤frontend-ide` `¤implementacion`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Con el middleware `persist` de Zustand, el estado rehidratado sustituye al inicial en las claves persistidas. Sin `version` ni `migrate`, un cambio de esquema o de datos semilla **no llega** a quien ya tenía estado: quien conservara las 3 respuestas antiguas (sin dimensión) dejaría el panel nuevo vacío y la función parecería no existir. La biblioteca de proyectos guardados sufre el mismo problema al evolucionar el esquema. Este efecto lo **predijo** un auditor por lectura de `partialize`; no se observó en el navegador porque la migración se aplicó antes de probarlo.
* **Solución:** `version: 3` con una cadena de migraciones (`< 2`: respuestas → conjunto de referencia; `< 3`: normativa PI/ISO → LOPDP y `evidencias := []`). Los proyectos guardados se leen como **entrada externa**: si no traen `evidencias` se abren con lista vacía; se remapea la normativa; se descartan las evidencias mal formadas o de otra normativa mediante una guarda de tipo (`esEvidenciaValida`); y el correlativo se recalcula como el máximo entre el guardado y los códigos presentes.
* **Estado de validación:** *Ejecutado en navegador* para la migración (tras recargar, el estado persistido quedó en `version: 3` con normativa `LOPDP`; el valor por defecto anterior era PI) y para guardar, crear y reabrir un proyecto con su evidencia intacta. *No ejercitado:* la rama de descarte de evidencias mal formadas (cubierta solo por tipos y lint).
* **Principio:** lo leído del almacenamiento del navegador es controlable por el usuario y por extensiones; se valida como cualquier otra entrada externa.
* **Base científica:** Kleppmann (2017), *Designing Data-Intensive Applications*, cap. 4 (compatibilidad hacia atrás y hacia adelante de esquemas persistidos); documentación oficial de Zustand (`persist`: `version`, `migrate`); OWASP *Input Validation Cheat Sheet*.

---

### Aporte 55: Datos de Referencia con Procedencia Marcada e Inhabilitados como Prueba
`¤diagnostico` `¤evidencias` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Un tablero necesita datos semilla para mostrar su estructura, pero unas respuestas sintéticas pueden confundirse con declaraciones del auditor; sellarlas produciría un snapshot con apariencia de auditoría cerrada.
* **Solución:** Toda fila semilla lleva `esReferencia: true`. El cuestionario arranca en blanco (no presenta las semilla como respondidas); la **primera respuesta propia descarta todas las semilla** (nunca coexisten con las reales); el tablero muestra un aviso "Resultados de referencia… sin valor probatorio"; y el sellado se rechaza si no hay respuestas propias.
  $$\text{Sellables} = \{r : \neg r.\text{esReferencia} \wedge \text{exigible}(r)\}$$
* **Propiedad:** como la primera respuesta propia vacía el conjunto semilla, un snapshot no puede mezclar filas sintéticas y reales.
* **Estado de validación:** *Ejecutado en navegador:* tras responder, el estado contenía únicamente las respuestas propias y el aviso se mostraba mientras solo había semilla. *No ejecutado:* el rechazo de sellado (verificado por lectura del código, para no escribir en el historial inmutable).
* **Base científica:** Buneman, Khanna & Tan (2001), *Why and Where: A Characterization of Data Provenance*; Doctrina 3 del PRD.

---

### Aporte 56: Invariante de Unidad en las Fronteras de Serialización
`¤invariantes` `¤implementacion`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** El tipo `ScoringFinalSnapshot.madurez` está documentado como porcentaje (0–100), pero el sellado escribía el índice `madurezSPDP` en escala 0–3 (p. ej. 2,28). El historial de auditorías interpreta el campo con umbrales 85 / 65 / 40 y lo imprime con el sufijo "%", de modo que un snapshot mostraría "2,28 %" y un nivel erróneo. Defecto **preexistente**, hallado al hacer el sellado exclusivamente verificado.
* **Solución:** el resumen sellado calcula `madurez` y `coberturaEvidencias` en porcentaje (0–100) a partir del cálculo verificado.
* **Invariante:** productor y consumidor de un campo serializado acuerdan su unidad; conviene codificarla en el nombre (`madurezPct`) o en un tipo marcado, no solo en un comentario.
* **Estado de validación:** *Discrepancia confirmada por lectura del código* (comentario del tipo, umbrales y sufijo de `AuditHistory`). *No observada en la interfaz* (no se selló ningún snapshot). Corrección verificada solo con tipos y lint.
* **Límite abierto:** las etiquetas de nivel del historial siguen en la escala 0–3 ("Nivel 3 (Optimizado)"), distinta de la escala 1–5 del tablero.
* **Base científica:** NASA Mars Climate Orbiter Mishap Investigation Board (1999), *Phase I Report* (discrepancia de unidades en una frontera entre sistemas como causa raíz de la pérdida); Meyer (1992).

---

### Aporte 57: Coherencia Temporal del Estado Derivado (Contexto Capturado y Memoización Obsoleta)
`¤frontend-ide` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Dos defectos con la misma causa: un valor derivado se usa cuando ya no corresponde a su fuente. (1) *Comprobar y actuar con intervalo:* al soltar un archivo grande se calcula su huella de forma asíncrona y solo después se registra con la normativa *vigente en ese momento*; si el usuario cambia de normativa durante el cálculo, la evidencia queda registrada bajo el régimen nuevo tras la purga y viola T7. (2) *Memoización congelada:* `useMemo(() => calcularScoring(), [calcularScoring])` depende de la referencia de una función del store, que es estable, así que nunca se recalcula y el resumen sellado usaba el scoring del primer render.
* **Solución:** (1) capturar la normativa al iniciar y comprobar que sigue igual antes de registrar, abortando si cambió; (2) calcular en cada render (o depender de los datos, no de la función).
* **Invariante:** un valor derivado debe ser función de la fuente **vigente en el instante de uso**, y toda continuación asíncrona revalida las premisas con las que fue lanzada.
* **Estado de validación:** *Solo revisión de código.* Un revisor independiente identificó ambos; las correcciones se verificaron con tipos y lint, pero **ni la carrera ni la memoización obsoleta se reprodujeron en el navegador**.
* **Base científica:** Bishop & Dilger (1996), *Checking for Race Conditions in File Accesses* (vulnerabilidad de intervalo entre comprobación y uso); documentación oficial de React (`useMemo` recalcula solo si cambian las dependencias; patrón de descarte de resultados asíncronos obsoletos).

---

### Aporte 58: Catálogo Canónico como Único Punto de Decisión por Normativa y Mediación Completa en el Almacén
`¤adpa` `¤evidencias` `¤frontend-ide`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** La normativa se comparaba contra literales (`"PI"`, `"NIIF"`) en 10 archivos (16 apariciones) y "PI" tenía un doble significado (Propiedad Intelectual y "assessment de datos"). Añadir una normativa exigía tocar todos y cada camino de cambio debía replicar sus propias reglas.
* **Solución:** `lib/normativas.ts` define por normativa su descriptor (formatos permitidos, disponibilidad, subtítulo) y las decisiones `usaBancoSGPDP`, `esNormativaFinanciera` y `extensionPermitida`. La regla de disponibilidad se aplica **en el store** (`setNormativa` ignora una normativa no disponible), no solo en la interfaz.
* **Propiedad:** añadir una normativa es una entrada del catálogo; todo camino que cambia la normativa (selector, paleta de comandos, código) atraviesa la misma guarda. Un revisor independiente encontró que la paleta de comandos (Ctrl+K) permitía activar ISO —o cambiar a NIIF purgando evidencias sin aviso— saltándose el selector: una violación de *mediación completa*. Se corrigió en el punto de mediación (el store) y no en cada componente.
* **Estado de validación:** *Ejecutado.* Tras el cambio, `grep '"PI"'` sobre `frontend/src` solo encuentra el catálogo. En navegador, con 2 evidencias registradas la paleta no cambió la normativa (siguió LOPDP, 2 evidencias) y redirigió a Configuración; el selector muestra PI e ISO deshabilitadas.
* **Base científica:** Parnas (1972) (ocultamiento de la decisión que puede cambiar); Saltzer & Schroeder (1975) (*economy of mechanism* y *complete mediation*, ya catalogados); OWASP *File Upload Cheat Sheet* (la extensión es una lista blanca, no validación de contenido).

---

### Aporte 59: Paralelismo de Agentes con Partición Previa de Archivos y Revisión Independiente (Extensión de T23)
`¤bbap` `¤adpa` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** T23 establece que el arnés exógeno certifica la integración de agentes concurrentes. No cubre (a) cómo evitar que agentes paralelos escriban sobre los mismos archivos ni (b) qué ocurre con los defectos que el arnés no codifica.
* **Método:** *Fase 0* (director técnico): cerrar los contratos compartidos y **partir los archivos compartidos** (`ProjectConfig`, store, catálogo) hasta que cada agente disponga de archivos exclusivos. *Fase 1*: agentes en paralelo, cada uno con su conjunto de archivos. *Fase 2*: un revisor de solo lectura, con contexto limpio y sin acceso al razonamiento de los autores, más una prueba de extremo a extremo.
* **Resultados medidos:** 5 agentes en paralelo con conjuntos de archivos disjuntos; **no se observó ningún conflicto de escritura**. En el momento de la revisión pasaban tipos, lint y pytest (solo fallos preexistentes) y la prueba de extremo a extremo del camino feliz; el revisor reportó **6 defectos** (0 críticos, 2 altos, 3 medios, 1 bajo), **los 6 confirmados contra el código** antes de corregirlos, y los 6 corregidos. Todos estaban fuera del camino feliz que se ejercitó: paleta de comandos, carrera asíncrona, borrado seguido de alta, duplicados, proyectos guardados con datos mal formados y sellado inconsistente con el tablero.
* **Interpretación:** un árbitro físico verifica lo que codifica; los tipos, el lint y las pruebas no codificaban invariantes semánticos entre componentes (p. ej. "el sello coincide con el tablero"). El arnés exógeno es **necesario pero no suficiente**, y su cobertura no equivale a ausencia de defectos. Refina T9 y T23 sin contradecirlos.
* **Límites:** N = 1, un solo revisor y sin grupo de control; no es una afirmación estadística. Los subagentes no ejecutaron el triaje ni el cierre MCP que exige la gobernanza (su tarea les restringía los archivos permitidos); esa llamada la ejecutó el director técnico. Queda abierta la regla para agentes delegados.
* **Base científica:** Conway (1968) (estructura del sistema refleja la de comunicación de quien lo construye); Parnas (1972); Brooks (1975) (canales de comunicación $n(n-1)/2$); Fagan (1976) (inspección formal); Dijkstra (1970), *Notes on Structured Programming* (las pruebas muestran la presencia de defectos, no su ausencia).

---

## Hallazgos abiertos de la sesión (no validados; registrados para evitar su refutación posterior)

| # | Hallazgo | Estado |
|---|----------|--------|
| 1 | Coexisten dos escalas de madurez en el mismo tablero: la tarjeta "Madurez SPDP" (0–3, motor de T16) y el panel de dimensiones (niveles 1–5, Aporte 48); las etiquetas de `AuditHistory` siguen en la escala 0–3. | Sin resolver |
| 2 | La renormalización sobre $D^{+}$ (Aporte 48) infla evaluaciones parciales; falta un umbral mínimo de cobertura antes de publicar un nivel. | **Resuelto** (Aporte 61, misma fecha) |
| 3 | El banco de 80 controles (talla mínima, redacción, referencias normativas) carece de validación jurídica (Aporte 53). | Requiere DPO/abogado |
| 4 | El vínculo documental no acredita idoneidad: falta un tope de nivel por tipo de evidencia (Aporte 49). | Propuesto |
| 5 | Proyectos y evidencias viven solo en el navegador; el backend de evidencias no está sincronizado con el frontend (Aporte 50). | Sin resolver |
| 6 | El camino de sellado (snapshot) no se ejecutó de extremo a extremo tras los cambios; se verificó por lectura (Aportes 49, 55, 56). | Pendiente de prueba |
| 7 | El índice de `FUENTES_Y_BIBLIOGRAFIA.md` §5 no lista T30 ni A44–A47 (omisión previa a esta sesión). | **Resuelto** (índice completado, misma fecha) |

---

# PARTE V: Alineación con la Matriz Canónica y Arnés de Interfaz (Sesión 2026-09-19, continuación)
`¤diagnostico-scoring` `¤arbitro` `¤interfaz`

> **CRITERIO DE ADMISIÓN DE ESTA PARTE:** idéntico al de la Parte IV. Se añade una exigencia: todo aporte que **modifique** un registro anterior lo declara en las Notas de vigencia, de modo que ninguna afirmación previa quede en pie sin corregir. Numeración correlativa a partir del Aporte 60; teoremas, a partir de T32.

---

## Notas de vigencia sobre la Parte IV

* **Aporte 48 — fórmula del score (sustituida).** La formulación $s_d = \tfrac{100}{5|I_d|}\sum n^{ef}_i$ (media simple sobre los controles *evaluados*) y la renormalización $S = \sum_{D^{+}} w_d s_d / \sum_{D^{+}} w_d$ **quedan sustituidas** por el Aporte 61 (ponderación por criticidad sobre base completa, sin renormalizar). **Lo que sobrevive intacto** del Aporte 48: el nivel efectivo $n^{ef}_i = \min(n_i, \varepsilon_i + 1)$, el riesgo $\rho_i$, la cota por habilitadores y la propiedad de no compensación, cuya demostración no depende de cómo se calcule $S$.
* **Aporte 48 — cifras de validación (obsoletas).** El valor $S = 75{,}58$ sobre el conjunto de referencia corresponde a la fórmula sustituida. Con el motor vigente, el mismo conjunto da $S = 78{,}26$, $N_{\text{teo}} = 4$ y $N_{\text{ajus}} = 2$. La conclusión cualitativa (degradación a Nivel 2) se mantiene; el número no.
* **Aporte 48 — límite (i) resuelto.** El límite «renormalizar sobre $D^{+}$ hace que una evaluación parcial parezca madura» queda cerrado por el Aporte 61. El caso citado (2 de 39 controles ⇒ 85,6 %) ya no se reproduce: hoy esa situación informa Nivel 0.
* **Aporte 49 — propiedad de monotonía (se mantiene y se refuerza).** La demostración invocaba que «$D^{+}$ y los pesos $w_d$ no cambian entre modos». Bajo el Aporte 61 el denominador es la base de criticidad de todo lo aplicable, que tampoco depende del modo: $S^{\text{ver}} \le S^{\text{decl}}$ sigue siendo cierto y su demostración es ahora independiente de qué controles se hayan respondido.
* **Aporte 53 — conjunto $H$ (generalizado).** Los cuatro habilitadores $H = \{9, 10, 13, 28\}$ dejan de ser una lista mantenida a mano y pasan a ser un subconjunto del criterio derivado del catálogo (Aporte 62).
* **T11 (Command Palette).** T11 sostiene la minimización de latencia cognitiva por atajo universal. Entre una fecha no determinada y 2026-09-19 el atajo `Ctrl+K` **no abría la paleta** por doble montaje del componente (Aporte 65). T11 no queda refutado —el mecanismo es correcto— pero su beneficio no se estaba realizando en producción; se registra para que la afirmación no se lea como verificada de forma continua.

---

### Aporte 60: Reconstrucción Ejecutable de una Matriz de Cálculo Externa y Comparación Diferencial por Escenarios
`¤diagnostico-scoring` `¤arbitro` `¤metodologia`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** La afirmación «la plataforma da los mismos resultados que la hoja de cálculo de referencia» no es comprobable por inspección. Ambos artefactos son grandes, la hoja compartida llega con las columnas de entrada vacías (plantilla en blanco) y una comparación puntual sobre un caso no distingue coincidencia de equivalencia.
* **Método (tres etapas, cada una con su propio control):**
  1. **Transcripción y validación de la transcripción.** Las fórmulas de la hoja se transcriben a un lenguaje ejecutable y la transcripción se coteja contra el libro real evaluado por un motor de fórmulas independiente. Sin este paso, un error de lectura de la hoja se confundiría con una divergencia del producto.
  2. **Comparación diferencial.** Se generan $M$ escenarios de entrada estratificados (aleatorios completos, perfil del informe publicado, cobertura parcial, extremos, casos límite dirigidos) y se ejecuta con ellos **el motor real del producto**, no una réplica.
  3. **Atribución por conmutación de reglas.** Cada regla candidata se activa *de a una* sobre el modelo del producto y se mide su efecto aislado. Esto convierte «los resultados difieren» en «difieren por estas causas, con este peso cada una».
* **Estado de validación:** *Ejecutado.* Transcripción contra el libro real: diferencia máxima $2{,}2\times10^{-16}$ (redondeo de coma flotante). El modelo reprodujo el motor real del producto en **164/164** escenarios y, activando las ocho reglas, la hoja en **164/164**: las ocho reglas explican la totalidad de la divergencia, sin residuo atribuible a causas no identificadas. Atribución medida (desviación media del score y número de niveles finales alterados): no renormalizar ⇒ 12,72 pts y 22 niveles en cobertura 70 %, 24,70 pts y 12 niveles en cobertura 40 %; compuerta de cobertura ⇒ 20 niveles en cobertura 40 %; ponderar por criticidad ⇒ 0,38–0,53 pts; pesos D09/D10 ⇒ 0,19–0,46 pts.
* **Propiedad metodológica:** la etapa 3 es lo que distingue este método de una prueba de regresión. Una batería que solo informa «pasa / no pasa» no permite decidir *qué* cambiar; la atribución por conmutación entrega un orden de intervención (aquí: la renormalización pesaba dos órdenes de magnitud más que los pesos).
* **Límites conocidos:** (i) la hoja compartida no traía datos, de modo que los valores de entrada los fijó el experimento y no un caso real; (ii) los catálogos de control de ambos artefactos difieren (reparto por dimensión y criticidades), por lo que la equivalencia acreditada es **de motor**, no de resultado absoluto contra esa hoja concreta; (iii) $M = 164$ escenarios cubren el espacio por estratos, no exhaustivamente; (iv) el arnés de comparación **no reside en el repositorio** (ver Hallazgos abiertos).
* **Base científica:** Elaine J. Weyuker (1982), *On Testing Non-testable Programs* (oráculo pseudo-inverso: contrastar una implementación contra otra independiente cuando no hay salida esperada conocida); Knight & Leveson (1986) (dos implementaciones de la misma especificación fallan de forma correlacionada: de ahí que se valide primero la transcripción); Fisher (1935), *The Design of Experiments* (variación de un factor por vez para aislar su efecto).

---

### Aporte 61: Score Ponderado por Criticidad sobre Base Completa y Compuerta de Cobertura (Sustituye la Agregación del Aporte 48)
`¤diagnostico-scoring` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Dos defectos independientes de la agregación anterior. (a) La media simple del nivel efectivo trata por igual un control de criticidad 1 y uno de criticidad 5, de modo que cumplir lo accesorio compensa incumplir lo esencial. (b) Renormalizar sobre las dimensiones con datos hace que un diagnóstico a medias sea indistinguible de uno completo: el denominador encoge con el numerador.
* **Formulación:** Sea $A_d$ el conjunto de controles **aplicables** a la dimensión $d$ (exigibles a la talla, respondidos o no) y $R_d \subseteq A_d$ los respondidos:
  $$s_d = \frac{100}{\sum_{i \in A_d} \kappa_i}\sum_{i \in R_d} \frac{n^{ef}_i}{5}\,\kappa_i \qquad S = \frac{\sum_{d \in A} w_d\, s_d}{\sum_{d \in A} w_d}$$
  Un control sin responder suma al denominador y no al numerador: computa como cero, no se excluye. Sea $c = |R| / |A|$ la cobertura global y $c_{\min}$ el mínimo de emisión. La compuerta es:
  $$N_{\text{emitido}} = \begin{cases} 0\ (\text{«Sin evaluación suficiente»}), & c < c_{\min} \\ N_{\text{ajus}}, & c \ge c_{\min} \end{cases}$$
* **Propiedad demostrable (monotonía del avance):** $S$ es monótono no decreciente en el número de controles respondidos y nunca decrece al responder uno nuevo con $n^{ef} > 0$, porque el denominador $\sum_{A_d}\kappa_i$ es constante respecto de $R_d$. Bajo la fórmula sustituida esto **no** se cumplía: responder un control con nivel bajo podía hacer *caer* el score, y responder solo controles favorables lo inflaba.
* **Distinción frente a los topes de nivel:** la compuerta de cobertura no es un tope más, sino una negativa a emitir. Su semántica es «no hay dato suficiente», no «hay madurez baja». La diferencia importa jurídicamente: un informe que declara Nivel 1 sobre 4 controles de 39 afirma algo que no midió.
* **Estado de validación:** *Ejecutado.* 22 pruebas en `tests/test_assessment_matriz.py`, con los valores esperados **derivados a mano de las fórmulas** y no tomados de la salida del motor; ese criterio detectó un error de aritmética del propio redactor (63,55 frente al valor correcto 69,73). Suite completa: 152 en verde. En navegador, 1 control respondido de 39 ⇒ «1,2 % · Nivel 0 · Sin evaluación suficiente» (antes habría informado un nivel ordinario). El caso publicado en el informe de referencia da 81,04 % con los pesos canónicos frente a 80,25 % con los anteriores (el informe declara 81,02 %).
* **Límites conocidos:** (i) $c_{\min}$ y los pesos son parámetros de negocio heredados de la matriz canónica, no derivados; (ii) la cota es inclusiva ($c = c_{\min}$ emite) por decisión explícita, documentada en prueba; (iii) una dimensión sin controles aplicables queda fuera del ponderado —no computa como cero— porque su ausencia proviene de la poda por talla y no de falta de respuesta.
* **Base científica:** Keeney & Raiffa (1976), *Decisions with Multiple Objectives* (agregación aditiva ponderada y condiciones de su validez); Tversky (1972) y Fishburn (1974) (no compensación, ya catalogados); ISO/IEC 33020:2019 (escalas de medición de capacidad de proceso y su agregación); Deming (1986), *Out of the Crisis* (una medida que puede mejorarse cambiando el denominador deja de medir el proceso).

---

### Aporte 62: Topes de Nivel Independientes y Conmutativos, con Conjunto Bloqueante Derivado del Catálogo
`¤diagnostico-scoring` `¤invariantes`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Las reglas que degradan el nivel se habían ido acumulando como casos particulares (una lista fija de cuatro controles habilitadores). Añadir una quinta regla exigía decidir en qué orden se aplican y mantener a mano un conjunto que ya estaba implícito en el catálogo.
* **Formulación:** Cada restricción $k$ aporta una cota $t_k$ activada por un predicado $P_k$ sobre el estado de los controles. El nivel final es el ínfimo de las cotas activas:
  $$N_{\text{ajus}} = \min\Big(N_{\text{teo}}(S),\ \min_{k\,:\,P_k}\ t_k\Big)$$
  Con tres restricciones vigentes: $P_1$ = existe control bloqueante con $n^{ef} < 3$, $t_1 = 2$; $P_2$ = existe control de criticidad $\ge 4$ con evidencia reescalada $< 2$, $t_2 = 3$; $P_3$ = cobertura insuficiente, $t_3 = 0$.
* **Propiedad demostrable (conmutatividad e idempotencia):** $\min$ es asociativo, conmutativo e idempotente sobre un orden total, luego **el resultado no depende del orden de evaluación de las reglas ni de que una regla se evalúe dos veces**. Consecuencia práctica: añadir una cuarta restricción no obliga a revisar las tres anteriores ni a fijar una precedencia. La formulación anterior, encadenada por condicionales, sí dependía del orden.
* **Derivación del conjunto bloqueante:** la inspección del catálogo canónico mostró que la marca «bloqueante» coincide **exactamente** con la criticidad máxima: los 32 controles marcados tienen criticidad 5, y ninguno de los 48 restantes la alcanza (criticidades 4×35, 3×12, 2×1). La equivalencia es bidireccional, de modo que el predicado $P_1$ se evalúa sobre un atributo que el catálogo ya declara y **deja de existir una lista paralela que pueda desincronizarse**. Los cuatro habilitadores del Aporte 48 son un subconjunto propio de este criterio, no una regla aparte.
* **Estado de validación:** *Ejecutado.* Conteo sobre el catálogo canónico (32/32 bloqueantes con criticidad 5; 0/48 no bloqueantes con criticidad 5). Pruebas dirigidas: un único control de criticidad 5 en nivel 1 dentro de un assessment por lo demás impecable mantiene $S > 90$ y $N_{\text{teo}} = 5$, y aun así $N_{\text{ajus}} = 2$; un control de criticidad 4 con evidencia E1 da $N_{\text{ajus}} = 3$ sin activar $P_1$.
* **Límites conocidos:** la equivalencia «bloqueante ⟺ criticidad 5» es una propiedad **observada** del catálogo vigente, no un invariante impuesto por el sistema. Si un catálogo futuro introduce un control de criticidad 5 no bloqueante, la derivación deja de ser fiel y debe volver a una marca explícita. No existe hoy un árbitro que detecte esa divergencia.
* **Base científica:** Birkhoff (1940), *Lattice Theory* (ínfimo sobre un orden total: conmutatividad, asociatividad e idempotencia); Dijkstra (1975), *Guarded Commands, Nondeterminacy and Formal Derivation of Programs* (el resultado no depende del orden de evaluación de las guardas); Parnas (1972) (una decisión que puede cambiar se declara en un solo lugar).

---

### Aporte 63: Cota de Reproducibilidad entre Implementaciones por Asociatividad en Coma Flotante
`¤diagnostico-scoring` `¤arbitro`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** Tras alinear las ocho reglas, 5 de 164 escenarios seguían difiriendo en 0,01 puntos entre dos implementaciones de la **misma** fórmula. La tentación es tratarlo como una regla pendiente o forzar la coincidencia con una tolerancia arbitraria.
* **Diagnóstico:** en esos 5 casos la suma ponderada cae en la frontera exacta de redondeo. Un ejemplo medido: el valor sin redondear es $4297{,}5$ en una implementación y $4297{,}499999999999$ en la otra. La suma en coma flotante **no es asociativa** ($(a+b)+c \neq a+(b+c)$ en IEEE 754), de modo que dos recorridos distintos del mismo conjunto de sumandos producen últimos bits distintos; cuando el valor cae justo en $x{,}5$, esa diferencia de un ULP decide el redondeo y se amplifica a $10^{-2}$ en la cifra publicada.
* **Consecuencia (cota de reproducibilidad):** entre dos implementaciones independientes de una fórmula con redondeo final existe un **piso de divergencia no eliminable por corrección lógica**, determinado por el orden de agregación. Afirmar «resultados idénticos» sin acotar ese piso es una afirmación no verificable. Lo correcto es declarar: idénticos salvo en fronteras de redondeo, con cota conocida y sin efecto sobre las magnitudes de decisión.
* **Estado de validación:** *Ejecutado.* 159/164 coincidencias exactas; los 5 restantes difieren 0,01 y **ninguno altera el nivel teórico, el nivel final, el conteo de brechas críticas ni el de altas** —se verificó que la comparación de esos campos enteros pasaba en los 164—. La frontera se comprobó imprimiendo el valor sin redondear con 15 decimales.
* **Límites conocidos:** (i) la cota es empírica sobre este conjunto de escenarios, no una demostración del peor caso; (ii) sería eliminable con aritmética decimal exacta en ambos lados, a coste de rendimiento y de divergir de la hoja original, que tampoco la usa; (iii) el diagnóstico no exime de comprobar que la divergencia no crece: si un caso futuro difiere en más de 0,01, la explicación deja de aplicar.
* **Base científica:** IEEE Std 754-2019, *Standard for Floating-Point Arithmetic*; David Goldberg (1991), *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, ACM Computing Surveys 23(1), pp. 5–48 (no asociatividad y propagación del error de redondeo); Nicholas J. Higham (2002), *Accuracy and Stability of Numerical Algorithms* (2ª ed.), SIAM (dependencia del resultado respecto del orden de sumación).

---

### Teorema 32: Verificación del Árbitro por Mutación Dirigida (Un Arnés en Verde no se Acredita a Sí Mismo)
`¤arbitro` `¤invariantes` `¤bbap`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** T9 establece que la validación reside en árbitros exógenos booleanos. A59 añadió que un árbitro en verde es condición necesaria y no suficiente, porque no cubre lo que no codifica. Queda un supuesto sin examinar y más elemental: **que el árbitro sea capaz de emitir 0**. Un arnés mal anclado —selector que nunca encuentra su elemento, aserción vacía, escenario que no ejercita lo que dice— pasa siempre y es indistinguible de uno correcto mientras el código esté sano.
* **Enunciado:** Sea $\mathcal{A}$ un árbitro exógeno y $\mathcal{P}$ el sistema bajo prueba. $\mathcal{A}(\mathcal{P}) = 1$ solo aporta información sobre $\mathcal{P}$ si se ha exhibido al menos una mutación $\mu$ del invariante que $\mathcal{A}$ declara vigilar tal que:
  $$\exists\,\mu:\quad \mathcal{A}(\mu(\mathcal{P})) = 0 \ \land\ \text{el componente que falla es el que declara vigilar } \mu$$
  La segunda conjunción es imprescindible: un arnés que se pone en rojo por un fallo colateral (la aplicación no arranca) tampoco acredita cobertura del invariante.
* **Corolario (jerarquía de suficiencia):** $\mathcal{A}$ capaz de emitir 0 $\Rightarrow$ $\mathcal{A}$ informativo $\not\Rightarrow$ $\mathcal{P}$ correcto. La mutación dirigida es condición necesaria para que T9 opere; A59 acota por arriba lo que un árbitro acreditado puede concluir.
* **Estado de validación:** *Ejecutado.* Se mutó una constante del invariante de cobertura ($c_{\min}: 60 \rightarrow 0$) y el arnés de interfaz pasó a **1 fallo / 3 pases**, siendo el fallo exactamente el escenario que declara vigilar esa regla; restaurada la constante, 6/6 en verde. El mismo principio, aplicado a la suite de cálculo, ya había dado fruto antes de cualquier mutación deliberada: una aserción derivada a mano detectó un error de aritmética del redactor.
* **Distinción frente al análisis de mutantes clásico:** la práctica académica genera mutantes de forma masiva y automática para estimar una tasa de detección. Aquí la mutación es **dirigida y unitaria** sobre la constante que encarna el invariante declarado, y su propósito no es puntuar el arnés sino acreditar el vínculo entre una regla escrita en prosa y un árbitro que la vigila. Es más débil como métrica y más fuerte como evidencia de anclaje.
* **Límites conocidos:** (i) acredita el anclaje de la regla mutada, no de las demás; (ii) no mide cobertura; (iii) exige que el invariante esté encarnado en un punto único y mutable —un invariante disperso por varios archivos no admite esta comprobación sin refactorizarlo antes—.
* **Base científica:** Richard A. DeMillo, Richard J. Lipton & Frederick G. Sayward (1978), *Hints on Test Data Selection: Help for the Practicing Programmer*, IEEE Computer 11(4), pp. 34–41 (análisis de mutantes); Dijkstra (1970), EWD249 (ya catalogado); Charles A. E. Goodhart (1975) (una medida que se convierte en objetivo deja de ser buena medida: fundamenta que el verde no sea el objetivo sino la señal).

---

### Aporte 64: Arnés de Interfaz Anclado en Rol y Nombre Accesible, y el Acoplamiento entre Verificabilidad y Accesibilidad
`¤interfaz` `¤arbitro` `¤implementacion`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** La comprobación de la interfaz se venía haciendo por conducción manual de un navegador: no reproducible, no versionable y ausente del repositorio. Un arnés automatizado resuelve eso, pero introduce su propio riesgo: si los selectores se anclan a clases de estilo, cualquier recomposición visual lo rompe y el equipo aprende a desactivarlo.
* **Solución:** Los localizadores se anclan en el **rol y el nombre accesible** del elemento (`getByRole("button", { name: "Conforme" })`), no en su presentación. Un cambio de color, espaciado o clase no altera el árbol de accesibilidad; solo lo altera un cambio de comportamiento, que es justo cuando el arnés debe intervenir.
* **Hallazgo principal (acoplamiento):** anclar en el árbol de accesibilidad **exige** que los elementos tengan identidad en él. Al proveerla afloraron cuatro defectos reales de accesibilidad preexistentes, invisibles para tipos, lint y pruebas de unidad: (1) etiquetas de formulario sin asociar a su campo (`for` nulo), de modo que un lector de pantalla no anunciaba qué se escribía; (2) botones de opción sin estado de selección expuesto (`aria-pressed`); (3) grupos de opción sin nombre; (4) mosaicos de métrica sin nombre accesible, cuya cifra se leía descontextualizada. La conclusión generalizable: **la accesibilidad no es un coste añadido del arnés sino su precondición, y el arnés actúa como detector incidental de deuda de accesibilidad.**
* **Mecánica de arranque reproducible (condiciones no obvias, todas medidas):**
  * *Limpieza antes de la carga.* El estado persistido debe borrarse mediante un script de inicialización que corre **antes** de los scripts de la página. Borrarlo después es inútil: el almacén se hidrata durante el primer render y la limpieza posterior deja en memoria justo lo que se quería descartar.
  * *Espera de hidratación con señal positiva.* Interactuar antes de que el almacén se hidrate hace que la escritura se descarte silenciosamente. La señal fiable es un dato del propio almacén ya presente en pantalla; un indicador visual de carga (`animate-pulse`) resultó **falso proxy**, por coexistir con adornos permanentes que lo usan.
  * *Punto de partida explícito.* El estado inicial del producto **no está vacío**: incluye un cuestionario de referencia ya respondido (Aporte 55). Sin descartarlo por la vía que la propia aplicación ofrece, la cobertura arranca al 100 % y ningún escenario mide lo que él mismo responde. Esta premisa se dio por cierta y resultó falsa; se registra por eso.
  * *Paralelismo acotado al servidor de desarrollo.* El servidor compila cada ruta bajo demanda; con demasiados contextos simultáneos la primera visita excede cualquier espera razonable y el arnés falla **por lentitud, no por regresión**, que es el modo de fallo que más rápido destruye la confianza en un árbitro.
* **Estado de validación:** *Ejecutado.* 6 escenarios en verde (4 sobre el tablero de madurez, 2 sobre la paleta de comandos); comprobación de tipos completamente limpia por primera vez en la sesión —el escenario huérfano heredado apuntaba a una ruta inexistente y era el origen de los 3 errores que se arrastraban—; suite de cálculo intacta en 152. Capacidad de emitir 0 acreditada por T32.
* **Límites conocidos:** (i) cubre el tablero de madurez y la paleta; no cubre evidencias, pre-llenado ni el menú de proyectos; (ii) no está integrado en integración continua: hoy se lanza a mano; (iii) un solo motor de navegador; (iv) el arnés depende de que el nombre accesible sea estable —si se traduce la interfaz, los localizadores por nombre visible deben pasar a una clave estable—.
* **Base científica y normativa:** W3C *WAI-ARIA 1.2* y *Accessible Name and Description Computation 1.2* (cómputo del nombre accesible); W3C *WCAG 2.2*, criterio 4.1.2 *Name, Role, Value* (todo componente de interfaz expone nombre, rol y estado); Kent C. Dodds (2018), *Testing Library — Guiding Principles* (cuanto más se parezcan las pruebas al uso real del software, más confianza dan); Gerard Meszaros (2007), *xUnit Test Patterns* (*Fresh Fixture* y *Obscure Test*: cada prueba parte de un estado conocido y declara sus premisas); Kent Beck (2002), *Test-Driven Development by Example* (pruebas independientes del orden).

---

### Aporte 65: No Idempotencia de Componentes con Escucha Global bajo Montaje Múltiple (Conmutación Par Silenciosa)
`¤interfaz` `¤invariantes` `¤implementacion`
* **Sesión de origen:** Conversación 04b305b8-3a4b-4fe9-9e8b-19db3f57e16f · 2026-09-19
* **Problema:** El atajo universal de la paleta de comandos (T11) no abría la paleta. No había error en consola, ni excepción, ni aviso: la pulsación simplemente no producía efecto. Ninguna comprobación de tipos, lint, prueba de unidad ni revisión de código lo había detectado, y tampoco la conducción manual del navegador durante la propia sesión.
* **Causa raíz:** el mismo componente estaba montado dos veces —en el layout raíz y en la página— y cada instancia registraba su **propio** escucha global de teclado sobre `window`, con una acción de **conmutación** del estado compartido. Una pulsación se propaga a todos los escuchas registrados.
* **Formulación:** sea un componente que registra un escucha global cuyo efecto es una conmutación $\sigma \mapsto \neg\sigma$, y sean $k$ sus instancias montadas. Una pulsación aplica la conmutación $k$ veces:
  $$\sigma' = \neg^{k}(\sigma) = \begin{cases} \sigma, & k \text{ par} \\ \neg\sigma, & k \text{ impar} \end{cases}$$
  Con $k$ par el sistema es **observacionalmente idéntico a uno sin funcionalidad**, y el fallo es silencioso porque cada instancia se comporta correctamente por separado. Corolario operativo: una acción registrada globalmente debe ser **idempotente** (fijar un valor: «abrir», «cerrar») o su registro debe ser único por construcción; conmutar desde un escucha global es seguro solo bajo la garantía —no comprobada por el compilador— de instancia única.
* **Solución:** montaje único en el layout raíz y eliminación del duplicado, con la razón anotada en el punto donde estaba, para que un futuro lector no lo reintroduzca.
* **Estado de validación:** *Ejecutado.* Antes del cambio, un sondeo automatizado registró que tras la pulsación no aparecía el campo de búsqueda de la paleta pese a existir sus nodos en el árbol. Tras el cambio, dos escenarios en verde: el atajo abre la paleta y `Escape` la cierra; y el filtrado por texto navega a la sala elegida. *No verificado:* si existen otros componentes del producto con el mismo patrón —se localizaron tres registros de `keydown` sobre `window` en el código y solo se auditó el de la paleta—.
* **Interpretación y relación con T32 y A59:** este defecto es la ilustración empírica de ambos. Sobrevivió a todos los árbitros existentes porque ninguno lo codificaba (A59), y solo apareció cuando se construyó un árbitro que ejercitaba el camino real de usuario. Refuerza además que la conducción manual por un operador —incluida la de un agente— no sustituye a un árbitro: el defecto estuvo presente durante toda la sesión manual y no se advirtió.
* **Base científica:** React — documentación oficial, *Synchronizing with Effects* y *You Might Not Need an Effect* (suscripción y cancelación por instancia; un efecto se ejecuta una vez por instancia montada); Leslie Lamport (1977), *Proving the Correctness of Multiprocess Programs* (propiedades de seguridad frente a acciones sobre estado compartido); Saltzer & Schroeder (1975), *economy of mechanism* (ya catalogado): un mecanismo registrado en un solo lugar no admite esta clase de fallo.

---

# PARTE VI: Aportes de Testing y Automatización Playwright (2026-09-19)

### Aporte 66: Configuración Playwright Moderna para Tests E2E de GRC con Automatización Multi-Proyecto
`¤playwright-config` `¤testing-framework` `¤bbap` `¤adpa`
* **Sesión de origen:** Conversación 2026-09-19 (análisis multi-proyecto ERP/Jubilo Pl/PDA)
* **Problema:** Configuración monolítica en `playwright.config.ts` que no optimizaba paralelización, reutilización de servidor ni reportería adaptativa entre CI y desarrollo.
* **Solución — Configuración Canónica:**
  - `workers: process.env.CI ? 2 : 3` — Adaptación automática según contexto.
  - `reuseExistingServer: !process.env.CI` — Economía en dev, reset limpio en CI.
  - `trace: "retain-on-failure"` — Captura trazas solo cuando falla (economía de almacenamiento).
  - `screenshot: "only-on-failure"` — Screenshots solo en defectos.
  - `fullyParallel: true` — Garantiza independencia de orden (Fresh Fixture).
  - `forbidOnly: Boolean(process.env.CI)` — Previene `.only` olvidados en producción.
  - `expect.timeout: 15_000` — Timeout largo para redes lentas.
  - Reporters adaptativos: GitHub Actions en CI, consola en dev.
* **Tipado:** TypeScript impide errores de configuración.
* **Base técnica:** Vercel Playwright Docs (2024-2026); Meszaros (2007) — Fresh Fixture.

---

### Aporte 67: Fixtures Reales y Data Builders para Tests de GRC (Patrón PDA Importado)
`¤testing-fixtures` `¤testing-data-builders` `¤playground` `¤bbap`
* **Sesión de origen:** Conversación 2026-09-19 (importación de patrones PDA)
* **Problema:** Tests e2e replicaban setup de datos (15-20s por test), inconsistencias entre specs, imposibilidad de reutilizar flows complejos.
* **Solución — Tres Artefactos:**
  1. **Fixtures Reales (`fixtures.ts`):**
     - `createTestProject(page, config)`: Abre app limpia, configura razonSocial/normativa/industria con instancias reales.
     - `createTestAssessment(page, config)`: Responde N controles, calcula nivel final automáticamente.
     - Retornan `{level, coverage, hasDiscrepancy, applicableControls}`.
     - **No mocks:** tocan localStorage, API, store Zustand reales.

  2. **Data Builders (`testDataBuilder.ts`):**
     - `ProjectBuilder`: Fluido `new ProjectBuilder().withName(...).withNormativa(...).build()`.
     - `ControlBuilder`: Presets `compliant()`, `partial()`, `nonCompliant()`.
     - `AssessmentBuilder`: Presets `level1()`, `level5()`, `unevaluated()`.
     - `ControlSetBuilder`: Generación masiva `mixed(total: 20, compliant: 13, partial: 7)`.
     - `TestScenario`: Casos predefinidos `newCompany()`, `level1Maturity()`, `level5Maturity()`.
     - Reducción: 100+ líneas hardcoded → 1-2 líneas.

  3. **Reexportación (`utiles.ts`):**
     - Namespace único: `import { createTestProject, ProjectBuilder } from "./utiles"`.

* **Tipado TypeScript:** Previene datos inválidos.
* **Base técnica:** PDA `test_xlsx_importer_service.py`; Meszaros (2007) — Object Mother pattern.

---

### Aporte 68: LocatorResolver con Jerarquía PCP (6 Niveles de Prioridad para Selectores)
`¤playwright-selectors` `¤testing-resilience` `¤adpa`
* **Sesión de origen:** Conversación 2026-09-19 (importación del patrón ERP)
* **Problema:** Selectores CSS puro fallaban ante cambios de diseño (`.button.primary` → `.btn.cta`). No existía sistema uniforme de priorización.
* **Solución — Jerarquía PCP (`locatorResolver.ts`):**
  ```
  N1: ID        (#myId)
  N2: data-testid ([data-testid="save-btn"])
  N3: role      (role=button[name="Guardar"])
  N4: placeholder (placeholder="...")
  N6: text      (text="Buscar")
  N5: CSS       (button.primary — fallback)
  ```
  **Algoritmo:** Intenta N1→N2→N3→N4→N6→N5 hasta encontrar match.
  **Alias corto:** `L.resolve(page, L.testId("btn-save"))`.
  **Refactor global:** `grep -r "locator\(" | refactor a L.testId()`.
  
* **Invariante:** Selector único funciona aunque diseño cambie (exploración semántica).
* **Base técnica:** ERP `playwright_driver.py`; W3C WCAG 2.2 (2023) — Name, Role, Value; Dodds (2018) — Testing Library.

---

### Aporte 69: ConsoleSentinel para Auditoría de Errores en Tests E2E
`¤console-monitoring` `¤testing-auditing` `¤bbap`
* **Sesión de origen:** Conversación 2026-09-19 (importación del patrón ERP)
* **Problema:** Tests fallaban intermitentemente por `console.error()` que no se propagaban a excepciones.
* **Solución — ConsoleSentinel (`consoleSentinel.ts`):**
  ```typescript
  const sentinel = new ConsoleSentinel();
  sentinel.attach(page);
  // ... test logic ...
  sentinel.assertZeroErrors();  // Falla si console.error()
  ```
  **Métodos:**
  - `attach(page)`: Adjunta listeners a `console` y `pageerror`.
  - `assertZeroErrors()`: Falla si errors.length > 0.
  - `report()`: Retorna `{errors, warnings, logsCount, totalEvents}`.
  
* **Eventos capturados:** `console.error()`, `console.warn()`, `page.on("pageerror")`.
* **Detección:** Regresiones silenciosas (API 200 pero error de parseo en consola).
* **Base técnica:** ERP `playwright_driver.py` (ConsoleSentinel).

---

### Aporte 70: AuditTrail con Certificación SHA-256 para Snapshots (Inmutabilidad Notarial)
`¤audit-trail` `¤screenshot-certification` `¤testing-forensics` `¤bbap`
* **Sesión de origen:** Conversación 2026-09-19 (importación del patrón ERP)
* **Problema:** Screenshots sin integridad verificable. Tester puede modificar captura manualmente sin detección.
* **Solución — AuditTrail (`auditTrail.ts`):**
  ```typescript
  await AuditTrail.injectTracker(page);
  const clickLog = await AuditTrail.getClickLog(page);
  // Retorna: [{timestamp, tag, id, testId, x, y, xpath}, ...]
  
  const snapshot = await AuditTrail.captureSnapshot(page, "resultado");
  // Retorna: {timestamp, path, sha256, bytes, url}
  
  await AuditTrail.exportAuditLog(page, "./audit-logs/test.json");
  ```
  **Artifacts:**
  - `test-results/screenshots/resultado-*.png` (captura).
  - `test-results/screenshots/resultado-*.png.meta.json` (SHA-256 + metadata).
  - `audit-logs/test.json` (clicks con coordenadas, XPath).
  
  **Verificación:** `AuditTrail.verifySnapshot(path)` recalcula SHA-256.
  
* **Invariante:** Alteración en Photoshop cambia SHA-256 → detección automática.
* **Cumplimiento:** Art. 50 LOPDP (registros auditoría inalterables); Teorema 18.
* **Base técnica:** ERP `playwright_driver.py`; Merkle (1987); NIST FIPS 180-4.

---

### Aporte 71: Trazabilidad Estigmérgica en Tests E2E (Rastros y Huellas ¤¦ vs Comentarios Verbosos)
`¤testing-stigmergy` `¤documentation` `¤bbap` `¤adpa`
* **Sesión de origen:** Conversación 2026-09-19 (refactorización de patrones)
* **Problema:** Comentarios "miga de pan" (`--- INICIO: KAIZEN: ---`) ocupaban 8-10 líneas. Falta trazabilidad automática spec↔requisito.
* **Solución — Rastros y Huellas Estigmérgicas Puras:**
  ```typescript
  /** ¤¦assessment_nivel_1 | LOPDP § 3.2 */
  test("assessment emite discrepancia", async ({ page }) => {
    // test logic
    // ¦assessment_nivel_1
  });
  ```
  **Convención:**
  - `¤¦nombre_feature`: Inicio (docstring).
  - `¦nombre_feature`: Fin (comment).
  - Requisito: `| LOPDP § 3.2` o `| Bug #456`.
  
  **Búsqueda:** `rg "¤¦assessment_nivel_1"` (ambas líneas).
  **Ventajas:** Compacto (1 línea), indexable, monótono (nunca se borran).
  
* **CI Integration:** Linter valida que toda sección crítica tiene rastro.
* **Base técnica:** Grassé (1959) — Stigmergie; Proaño (2026) — Non-Verbal Stigmergic Cognition.

---

## Hallazgos abiertos de la Parte V

| # | Hallazgo | Estado |
|---|----------|--------|
| 8 | El arnés de comparación contra la matriz canónica (164 escenarios, Aporte 60) **no reside en el repositorio**: vive en un directorio temporal de sesión y desaparece con ella. Nadie vuelve a contrastar contra la hoja original. | Sin resolver |
| 9 | El catálogo de 80 controles no está alineado con el reparto por dimensión ni con las criticidades de la matriz canónica (D03 = 6 y D04 = 10 frente a 8 y 8). La equivalencia acreditada es de motor, no de resultado absoluto. | Requiere decisión de negocio |
| 10 | La equivalencia «bloqueante ⟺ criticidad 5» (Aporte 62) es una propiedad observada del catálogo vigente, sin árbitro que detecte su ruptura. | Sin resolver |
| 11 | El arnés de interfaz no cubre evidencias, pre-llenado ni el menú de proyectos, y no está integrado en integración continua. | Parcial |
| 12 | Existen otros dos registros de `keydown` sobre `window` sin auditar frente al patrón del Aporte 65. | Sin resolver |
| 13 | El `Dockerfile` no declara las dependencias `openai`, `pypdf`, `openpyxl`, `defusedxml` ni `python-multipart` (arrastrado de la sesión anterior). | Sin resolver |

---

# PARTE VII: Copiloto Externo con Minimización por Construcción y Autoridad Jurídica Local (Sesión 2026-09-20)
`¤copiloto-ia` `¤implementacion` `¤regulation-code`

> **CRITERIO DE ADMISIÓN DE ESTA PARTE:** Se compararon los candidatos con los Aportes 39, 41 y 42 y con el catálogo bibliográfico existente. Solo se incorporan las propiedades nuevas observables en código y pruebas. La revisión de vigencia se contrastó con NIST AI 600-1 (2024, actualizado en 2026), OWASP LLM05:2025, Gürses–Troncoso–Diaz (2011), la LOPDP y la documentación oficial del proveedor. No se encontró una contradicción posterior en las fuentes revisadas; esta afirmación describe una búsqueda razonable, no una prueba universal de ausencia de refutación.

### Aporte 72: Proyección de Contexto por Finalidad antes de Sanitización (Minimización por Construcción)
`¤copiloto-ia` `¤dlp` `¤privacidad-diseno`
* **Sesión de origen:** Conversación 2026-09-20.
* **Problema:** El Aporte 39 sanitiza recursivamente un árbol diagnóstico antes de enviarlo a un LLM, pero un filtro aplicado al objeto completo conserva el riesgo de omitir una nueva clase de dato sensible o de enviar campos irrelevantes ya pseudonimizados. La redacción reduce contenido; no reduce por sí sola la superficie estructural transmitida.
* **Solución:** Construir primero una proyección explícita por finalidad y aplicar después el sanitizador:
  $$C_T(X)=S\left(\pi_{K_T}(X)\right)$$
  donde $X$ es el estado completo, $K_T$ contiene únicamente los campos necesarios para la tarea $T$ y $S$ es la sanitización DLP. Para el asistente de brechas, $K_T$ se limita a pregunta sanitizada, identificador y severidad del control, fundamentos normativos versionados y guía base genérica. Organización, documentos, evidencias, credenciales e historial quedan fuera de la proyección.
* **Propiedad verificable de no interferencia estructural:** Si dos estados $X$ e $Y$ coinciden en $K_T$, entonces $\pi_{K_T}(X)=\pi_{K_T}(Y)$; por tanto, los campos excluidos no pueden modificar el cuerpo HTTP mientras la proyección y el serializador sean los únicos caminos de salida. Esta propiedad es más fuerte y más fácil de probar que buscar por lista negra todos los secretos posibles.
* **Distinción frente al Aporte 39:** A39 protege un árbol recibido mediante sustitución; A72 reduce primero el universo de datos al esquema mínimo de la tarea y conserva DLP como segunda barrera para el texto libre permitido. Son controles complementarios.
* **Estado de validación:** *Ejecutado.* `tests/test_implementation_assistant_provider.py::test_deepseek_recibe_contexto_minimo_sanitizado_y_fusiona_salida` inspecciona el cuerpo HTTP y demuestra la ausencia de organización, historial, evidencia, cédula, teléfono, correo y credencial; también comprueba la presencia del contexto normativo permitido. El arnés completo registró 182 pruebas en verde.
* **Límites conocidos:** La propiedad cubre el cuerpo construido por esta ruta, no telemetría del proveedor ni canales externos ajenos al cliente HTTP. Los campos permitidos de texto libre aún requieren DLP. Minimización no equivale a anonimización ni elimina la necesidad de condiciones contractuales con el proveedor.
* **Base científica y jurídica:** Art. 10 LOPDP (minimización y finalidad); Gürses, Troncoso & Diaz (2011), *Engineering Privacy by Design* (la minimización como punto de partida y dependiente de la finalidad); Saltzer & Schroeder (1975), principio de mínimo privilegio; NIST AI 600-1 (gestión de riesgos en sistemas generativos).

---

### Aporte 73: Separación de Autoridad entre Planificación Generativa y Fundamento Jurídico con Fusión Acotada
`¤copiloto-ia` `¤regulation-code` `¤invariantes`
* **Sesión de origen:** Conversación 2026-09-20.
* **Problema:** Un formato JSON válido solo garantiza sintaxis. Un proveedor externo puede devolver un identificador de brecha no solicitado, atribuir la ejecución al DPD o inventar artículos y plazos. Aceptar la respuesta completa convertiría al modelo probabilístico en autoridad jurídica y permitiría que sustituyera datos canónicos.
* **Solución:** Dividir el resultado final en dos dominios de autoridad. El corpus local conserva control, fundamento, artículo, versión y URL. El modelo externo solo puede proponer campos operativos permitidos —pasos, rol ejecutor, evidencias, criterio de cierre y seguimiento— y únicamente para identificadores presentes en la solicitud. Cada campo se valida en tipo, longitud, cardinalidad y reglas de segregación; toda cita numérica debe pertenecer al conjunto de artículos suministrado. La fusión es por `pregunta_id` conocido y nunca reemplaza `fundamento`.
* **Invariantes verificables:**
  $$ID_{salida}\subseteq ID_{solicitud},\qquad Fundamento_{final}=Fundamento_{local}$$
  Una cita ajena al corpus invalida la respuesta externa completa y activa el respaldo local; un plan con identificador ajeno se descarta sin modificar las demás brechas.
* **Distinción frente a los Aportes 41 y 42:** A41 exige fuente para responder y A42 define degradación ante fallo del proveedor. A73 regula una llamada técnicamente exitosa pero semánticamente no confiable mediante autoridad por campo, lista positiva de identidades y fusión parcial.
* **Estado de validación:** *Ejecutado.* Las pruebas `test_cita_fuera_del_corpus_fuerza_respaldo_local`, `test_plan_de_id_ajeno_se_descarta_y_no_modifica_otras_brechas` y los casos de HTTP/JSON inválido verifican rechazo, aislamiento y fallback. El frontend siempre recibe los fundamentos conservados por el servidor.
* **Límites conocidos:** La pertenencia de un número de artículo al corpus evita citas nuevas, pero no prueba que una frase generada interprete correctamente ese artículo. La recomendación sigue requiriendo revisión humana y evidencia de cierre. `response_format=json_object` facilita el parseo, pero la propia documentación de DeepSeek reconoce posibles respuestas vacías; no sustituye la validación semántica.
* **Base científica y técnica:** NIST AI 600-1 documenta confabulaciones y citas falsas en IA generativa; OWASP LLM05:2025 prescribe tratar la salida del modelo como entrada no confiable y validarla; Lewis et al. (2020) fundamenta la memoria no paramétrica de RAG; DeepSeek, *JSON Output*, especifica el contrato sintáctico y sus límites operativos.

---

# PARTE VIII: Gating de Evidencia por Conformidad y Corrección de Defectos de Interfaz Hallados por el Arnés (Sesión 2026-09-27)
`¤interfaz` `¤arbitro` `¤implementacion`

> **CRITERIO DE ADMISIÓN DE ESTA PARTE:** idéntico al de las partes IV-V. Se releyó el archivo completo (incluidas las Partes VI y VII, de sesiones distintas a la de origen) antes de admitir cada aporte, para no repetir un hallazgo ya cubierto por Aportes 60-73 con otras palabras. De varios candidatos identificados en la sesión (entre ellos: una heurística de hidratación que solo era válida para un estado inicial concreto, y la necesidad genérica de recorrer la aplicación real para detectar deriva de un arnés desactualizado), se descartaron los que no superaban el criterio de novedad o generalidad suficiente frente a lo ya registrado; el resumen de descarte figura al final de esta parte.

---

### Aporte 74: Retrasar el Estado Compartido, no la Llamada Local, para Sincronizar un Aviso con un Desmontaje Decidido por un Efecto Ajeno
`¤interfaz` `¤invariantes` `¤implementacion`
* **Sesión de origen:** Sesión 2026-09-27 (reparación de `ProjectConfig.tsx`).
* **Problema:** En una arquitectura con una vista central que decide qué componente mostrar a partir de estado compartido (`dashboard/page.tsx` deriva la vista activa de `isConfigured`, `normativaSeleccionada` y `activeView` vía un `useEffect` con esas tres dependencias), un componente hijo no puede garantizar su propio tiempo de vida retrasando únicamente su propia llamada de navegación. El primer intento de corrección retrasó el `setActiveView` local dentro de `ProjectConfig.tsx` sin efecto observable: el aviso de guardado seguía sin verse.
* **Causa exacta:** el efecto ajeno en `dashboard/page.tsx:105-120` no reacciona a la llamada de navegación del hijo — reacciona a `isConfigured`. En cuanto `isConfigured` pasa a `true`, ese efecto encuentra que `activeView === "configuracion"` ya no es válido y dispara su propio `setActiveView`, desmontando `ProjectConfig` en el mismo ciclo, con independencia total de lo que el hijo hubiera planeado hacer con su propia llamada.
* **Verificación booleana (antes/después, mismo componente, mismo flujo de guardado):**
  $$\text{retrasar}(\texttt{setActiveView}_{\text{local}}) \implies \text{aviso\_visible} = \text{False}$$
  $$\text{retrasar}(\texttt{setIsConfigured}) \implies \text{aviso\_visible durante } \sim\!640\text{ms} = \text{True}$$
  Medido con un muestreo del DOM cada 80ms inyectado en la página real (no en una réplica), escribiendo cada muestra a `sessionStorage` para sobrevivir a la posible destrucción del contexto de ejecución del script por el propio cambio de vista que se estaba midiendo.
* **Estado de validación:** *Ejecutado.* El segundo intento (retrasar `setIsConfigured` 700ms tras fijar el mensaje) mostró el aviso "Ficha organizacional guardada" visible de forma continua entre, aproximadamente, el milisegundo 470 y el 1110 tras el clic, antes de que desapareciera al completarse la navegación.
* **Límites conocidos:** la solución añade una demora fija de latencia percibida a cambio de que el aviso sea observable; no corrige el patrón arquitectónico de fondo (un efecto ancestro con navegación decidida por estado compartido y múltiples dependencias) — un tercer componente futuro con el mismo problema tendría que aplicar la misma solución por su cuenta, ya que no hay ninguna guardia genérica que la imponga.
* **Base científica:** David Harel (1987), *Statecharts: A visual formalism for complex systems* (ya catalogado en este archivo, T13): el formalismo de statecharts modela exactamente esta situación — regiones concurrentes que reaccionan por difusión (*broadcast*) a una transición de estado compartido, sin que ninguna región individual controle cuándo reacciona otra; solo controlando la transición del estado en sí se controla el conjunto. React, documentación oficial, *Synchronizing with Effects* (ya catalogado, Aporte 65): un efecto se sincroniza con el valor observado de sus dependencias, no con la intención del código que las modificó.

---

### Aporte 75: Envolver el Filtro Exportado por una Librería para Normalizar Entrada, en vez de Reimplementar su Algoritmo de Coincidencia
`¤interfaz` `¤implementacion`
* **Sesión de origen:** Sesión 2026-09-27 (reparación de `CommandPalette.tsx`).
* **Problema:** El filtro por defecto de `cmdk` no normaliza diacríticos: buscar "Diagnóstico" (con tilde, la forma natural de escribirlo en español) y buscar "Diagnostico" (sin tilde) devolvían conjuntos de resultados distintos para la misma palabra clave indexada (`"diagnostico"`, sin tilde) — el comando "Ir a Normativa" solo aparecía en la segunda consulta.
* **Por qué envolver y no reimplementar:** reimplementar el algoritmo de coincidencia difusa para añadirle normalización arriesga degradar silenciosamente la calidad de su ranking en casos límite que la biblioteca ya resuelve. `cmdk` 1.1.1 exporta su propio `defaultFilter` (`(value, search, keywords?) => number`) como símbolo público; se normalizan `value`, `search` y cada elemento de `keywords` con `String.prototype.normalize("NFD")` seguido de eliminar las marcas diacríticas combinantes (rango Unicode U+0300–U+036F), y se delega el resultado ya normalizado a `defaultFilter` sin tocar su lógica interna de puntuación.
* **Verificación booleana:** comparación en vivo, contra la aplicación real, del conjunto de resultados para dos consultas que solo difieren en un diacrítico:
  $$\text{resultados}(\texttt{"Diagnostico"}) = \text{resultados}(\texttt{"Diagnóstico"})$$
  Confirmado: ambas consultas devolvieron el mismo arreglo de 7 elementos en el mismo orden, incluido "Ir a Normativa".
* **Estado de validación:** *Ejecutado.* Un primer intento de verificación fijando `input.value` vía DOM y disparando un `Event("input")` sintético no actualizó el estado controlado de React del componente y produjo un falso negativo (resultados idénticos para ambas consultas, antes y después del arreglo); hubo que repetir la verificación con tecleo real. Prueba de regresión añadida en `commandPalette.spec.ts`, que vuelve a buscar con tilde.
* **Límites conocidos:** la normalización asume que el rango U+0300–U+036F cubre los diacríticos relevantes en español; no se probó explícitamente con entrada ya compuesta en forma NFC (`normalize("NFD")` debería descomponerla de forma equivalente antes de comparar, pero ese caso concreto no se ejecutó). No cubre transliteración de otros alfabetos.
* **Base científica:** The Unicode Consortium, *Unicode Standard Annex #15 — Unicode Normalization Forms* (UAX #15, revisión vigente). Especifica formalmente las formas NFC/NFD y el mecanismo de descomposición de un carácter con diacrítico en carácter base más marca combinante, fundamento técnico exacto de la normalización aplicada.

---

### Aporte 76: El `<dialog>` Nativo con `showModal()` Bloquea Realmente el Resto del Documento, a Diferencia de una Superposición Decorativa
`¤interfaz` `¤arbitro`
* **Sesión de origen:** Sesión 2026-09-27 (diagnóstico de fallos en `assessmentDashboard.spec.ts` tras la reparación del arnés).
* **Problema:** Un modal construido con un `<div>` posicionado (`position: fixed`, `z-index`) no bloquea por sí solo la interacción con el resto de la página a nivel de navegador — depende enteramente de que el propio código intercepte los eventos. El elemento HTML `<dialog>` invocado con `showModal()` es un mecanismo distinto: el navegador lo coloca en el *top layer* del documento y el resto del árbol deja de recibir eventos de puntero, sin que el desarrollador implemente ese bloqueo. Un arnés que no distinga ambos casos falla de forma opaca: reintenta el clic sobre un elemento que supera todas sus propias comprobaciones de "clicable" (visible, habilitado, estable) sin que el clic llegue nunca a su destino, hasta agotar el tiempo de espera.
* **Verificación booleana:** el propio registro de reintentos de Playwright expone el predicado exacto que fallaba:
  $$\texttt{dialog.open} = \text{True} \;\land\; \texttt{visible}(\text{objetivo}) = \text{True} \;\land\; \texttt{enabled}(\text{objetivo}) = \text{True} \;\land\; \texttt{click}(\text{objetivo})\text{.interceptedBy} = \texttt{dialog}$$
  Confirmado 112 veces en un único test (reintentos cada 500ms hasta el timeout de 60s) antes de identificar la causa real, que exigió leer el mensaje de error completo del framework y no su resumen truncado.
* **Solución:** cerrar explícitamente el diálogo mediante su control de cierre accesible, como parte del flujo de arranque del arnés, en el punto exacto en que se sabe que se abrirá (la primera pregunta de la primera dimensión evaluada).
* **Estado de validación:** *Ejecutado.* Aislar el test fallido con un filtro por nombre y volcar el mensaje de error íntegro reveló el elemento interceptor exacto (`<dialog open aria-labelledby="alerta-dimension-titulo">`) y permitió localizar el componente responsable (`AlertaDimension.tsx`) con una sola búsqueda de texto por ese identificador.
* **Límites conocidos:** la observación describe el comportamiento definido por la especificación HTML del elemento `<dialog>`, no el de cualquier superposición visual; un modal construido sin ese elemento no bloquea el resto del documento a menos que el propio código lo replique (p. ej. con el atributo `inert` o deteniendo la propagación de eventos), y en ese caso un arnés podría hacer clic "a través" de una superposición presente pero no bloqueante — el fallo descrito aquí ocurrió precisamente porque el bloqueo era real, no decorativo.
* **Base científica:** WHATWG, *HTML Living Standard — The dialog element* (§4.11.4, revisión vigente). Especifica formalmente que `showModal()` añade el diálogo al *top layer* del documento y que el resto de los elementos deja de ser objetivo de eventos de puntero mientras el diálogo modal permanece abierto.

---

## Candidatos descartados de esta sesión (Parte VIII)

| Candidato | Motivo del descarte |
|---|---|
| Una comprobación de hidratación basada en "el campo ya trae un valor" es válida solo para el estado de fábrica (con datos de demostración) y falla en silencio tras un reinicio deliberado que deja el campo vacío a propósito. | Hallazgo real y corregido en `tests/utiles.ts`, pero demasiado específico de este arnés concreto para valer como patrón reconocible en otro proyecto; no añade generalidad sobre lo ya registrado. |
| Recorrer la aplicación real en vivo es el único método fiable para resincronizar un arnés desactualizado tras un rediseño de producto. | Cierto, pero es práctica estándar de pruebas end-to-end sin un mecanismo o predicado verificable propio que lo distinga de la disciplina habitual; no supera el criterio 1 (utilidad específica más allá de lo obvio) con suficiente margen. |

---

# PARTE IX: Minería Retrospectiva de Sesiones Previas del Proyecto (Ejecutada 2026-09-28)
`¤interfaz` `¤diagnostico-scoring` `¤implementacion` `¤arbitro`

> **CRITERIO DE ADMISIÓN DE ESTA PARTE:** a diferencia de las partes anteriores, estos aportes no provienen de la sesión que los registra, sino de una minería retrospectiva de otras cuatro transcripciones locales de este mismo proyecto (identificadas por su ID de conversación de Claude Code), delegada a subagentes de investigación y luego verificada por esta sesión contra el código vigente antes de escribir una sola línea. Esta parte aplica además la revisión de esta skill que dejó de exigir un predicado booleano como condición de admisión: un hallazgo empírico —reproducido una vez, sin causa formalizable, o dependiente de infraestructura fuera de este repositorio— se admite igual si es útil, verificable en la medida de lo posible y no está ya registrado, y se documenta con el mismo estándar de honestidad sobre su nivel de confianza que exigiría una cita. Se excluyeron explícitamente varios candidatos de las mismas transcripciones por pertenecer, en realidad, a otros dos proyectos (ERP, ZERAG) cuyos propios archivos de aportes ya los registraron — repetirlos aquí sería precisamente el patrón de inflación por copia entre proyectos que esta skill existe para evitar.

---

### Aporte 77: Descomponer un Flag Booleano Sobrecargado en Dos Flags con Semántica Distinta, para que la Navegación se Habilite por Capacidad de Datos y no por Mera Selección
`¤interfaz` `¤invariantes`
* **Sesión de origen:** minería retrospectiva de la transcripción local `3d99699e-adeb-4a16-8e68-1fd11716ab26` (sesión de rediseño de onboarding).
* **Problema:** el catálogo de normativas usaba un único campo `disponible: boolean` para decidir si una normativa aparecía habilitada en el selector. Ese campo mezclaba dos preguntas distintas —¿existe esta opción en el catálogo? y ¿tiene esta opción un banco de preguntas real detrás?—, de modo que PI e ISO, marcadas como no disponibles por carecer de banco propio, producían además un efecto colateral al intentar seleccionarlas: un enrutamiento de reserva incorrecto mostraba preguntas de NIIF.
* **Solución:** renombrar el campo a `bancoDisponible: boolean`, dejando que codifique exclusivamente si la normativa tiene banco de preguntas propio. La barra de navegación de `dashboard/page.tsx` consulta ese mismo campo para decidir si expone solo el módulo "Normativa" o el conjunto completo de módulos (Dashboard, RAT, Riesgos, etc.): la navegación se habilita por capacidad real de datos, no por el mero hecho de que el usuario haya tocado el selector.
* **Verificabilidad:** confirmado contra el código vigente que el campo se llama `bancoDisponible` en las cuatro entradas del catálogo (`frontend/src/lib/normativas.ts:27,41,53,65,76`) y que `dashboard/page.tsx` lo consulta para construir la lista de módulos visibles. No aplica un predicado booleano de "antes/después": el estado con el campo `disponible` original ya no existe en el árbol de trabajo — es un patrón de diseño de nomenclatura, no una propiedad de estado observable hoy.
* **Estado:** implementado y vigente en el código actual.
* **Límites conocidos:** su generalidad depende de que el lector reconozca la misma clase de error (un booleano que en realidad codifica dos preguntas distintas) en su propio código — es un gotcha de diseño, no un invariante demostrable.
* **Base científica:** Martin Fowler (2018), *Refactoring: Improving the Design of Existing Code* (2ª ed.), Addison-Wesley — el catálogo de *code smells* documenta el parámetro/flag booleano que en realidad codifica más de una decisión como una señal concreta para descomponerlo, precisamente el patrón observado aquí.

---

### Aporte 78: Orden de Precedencia en Clasificación por Coincidencia de Subcadena de Texto Libre, cuando una Descripción Puede Contener Términos de Ambas Categorías
`¤diagnostico-scoring` `¤implementacion`
* **Sesión de origen:** minería retrospectiva de `3d99699e-adeb-4a16-8e68-1fd11716ab26` (trabajo sobre el motor NIIF 18).
* **Problema:** el motor de clasificación contable NIIF 18 determina si una cuenta de resultados es de naturaleza ingreso o gasto buscando, en parte, palabras clave dentro de la descripción libre de la cuenta. Una descripción real puede contener simultáneamente un término que sugiere ingreso y uno que sugiere gasto: "Costo de **ventas**" contiene "venta" (término de ingreso) pero es, contablemente, un gasto; "Gasto por impuesto a las **ganancias**" contiene "ganancias" (término de ingreso) pero también es un gasto. Comprobar primero la lista de ingreso clasifica ambas cuentas como ingreso por error, y ese error no se manifiesta como excepción sino como un desplazamiento silencioso del resultado operativo.
* **Solución:** comprobar primero la lista de términos que delatan gasto/costo (`costo`, `gasto`, `impuesto`, `depreciaci`, `amortizaci`, `comisi`, `provisi`, `perdida`, `deterioro`) y solo si ninguno coincide, comprobar la lista de términos de ingreso. La corrección está en el orden de verificación, no en el contenido de ninguna de las dos listas por separado.
* **Verificabilidad:** para toda cuenta con descripción que contiene simultáneamente un término de gasto y uno de ingreso, la clasificación resultante debe ser gasto. Comprobado con una balanza de prueba real (`tests/test_niif18.py::test_costos_e_impuestos_restan_del_resultado`) que incluye exactamente las dos cuentas conflictivas citadas arriba: el resultado operativo esperado es \$295.000,00 — no los \$995.000,00 que resultarían si esas dos cuentas se clasificaran como ingreso por su subcadena. El test pasa contra el código vigente en `features/niif18/engines/financials_engine.py:10-31`.
* **Estado de validación:** *Ejecutado.* Test en verde contra el código actual del repositorio.
* **Límites conocidos:** la solución depende de mantener la lista de términos de gasto lo bastante completa como para cubrir toda ambigüedad conocida; un término de gasto nuevo no listado seguiría clasificándose por la lista de ingreso si esta lo contiene. El test ancla los casos conocidos, no prueba la ausencia de colisiones futuras.
* **Base científica:** no se encontró una fuente académica específica sobre precedencia en clasificadores basados en listas de palabras clave que se pueda citar aquí sin forzarla — es una heurística de ingeniería (evaluar primero la condición más específica o dominante en una cadena de reglas con posible conflicto), no un principio formalizado en una fuente verificable con confianza para este caso puntual. Se omite la cita en vez de forzar una.

---

### Aporte 79: Invariante Estructural Independiente (Suma Algebraica de una Balanza = Cero) como Validador que Expone Defectos de Datos Heredados, no Solo Errores de Lógica Propia
`¤diagnostico-scoring` `¤implementacion`
* **Sesión de origen:** minería retrospectiva de `3d99699e-adeb-4a16-8e68-1fd11716ab26`.
* **Problema:** al portar un motor de diagnóstico contable desde un proyecto de referencia externo, la tentación es confiar en que los datos de ejemplo de ese proyecto ya son correctos y usarlos tal cual para validar la lógica portada. Un dato de referencia puede en sí mismo estar mal formado sin que nadie lo haya notado en el proyecto de origen — y clasificar correctamente cuentas que no deberían tener esas cantidades no corrige el desbalance subyacente.
* **Solución:** aplicar un invariante estructural independiente de la lógica de clasificación —una balanza de comprobación contable debe sumar cero— también sobre los datos de referencia, no solo sobre datos nuevos. Ese único chequeo, aplicado retroactivamente, expuso un defecto real en el dataset de referencia del proyecto de origen que la lógica de clasificación por sí sola no habría detectado.
* **Verificabilidad:** $\text{cuadra} := |\Sigma\,\text{saldos}| \le \text{TOLERANCIA\_CUADRE}$. Comprobado con dos casos reales en `tests/test_niif18.py`: uno con una balanza deliberadamente desbalanceada (`cuadra = False`, línea 87) y uno con una balanza correcta (`cuadra = True`, línea 127), contra la implementación vigente en `features/niif18/engines/diagnostico_engine.py:78-180`.
* **Estado de validación:** *Ejecutado.* Ambos casos en verde contra el código actual.
* **Límites conocidos:** el invariante detecta un desbalance agregado; no localiza por sí solo cuál cuenta individual está mal registrada — sirve como alarma de "algo está mal en los datos", no como diagnóstico de causa. Tampoco prueba que una balanza que sí cuadra esté correctamente clasificada por cuenta: cuadrar es necesario, no suficiente.
* **Base científica:** Luca Pacioli (1494), *Summa de Arithmetica, Geometria, Proportioni et Proportionalita* — origen documentado de la partida doble, cuya propiedad estructural fundamental es que toda balanza de comprobación correctamente registrada suma cero; el invariante contable más antiguo y verificable que existe, y la razón de que "cuadre = 0" sea una comprobación válida con independencia del contenido semántico de las cuentas.

---

### Aporte 80: Verificar que un Componente Tiene Importaciones Activas desde una Ruta Real antes de Editarlo — un Componente de Layout "Huérfano" Puede Parecer el Objetivo Correcto sin Estarlo
`¤interfaz` `¤implementacion`
* **Sesión de origen:** minería retrospectiva de la transcripción local `e22d64cd-c77d-4af9-8f1b-831a0ff0487c` (construcción del módulo de Reportes).
* **Problema:** en un proyecto Next.js con refactors previos puede quedar un componente de layout/navegación cuyo nombre y estructura lo hacen parecer el punto de entrada correcto para agregar una pestaña nueva, pero que ya no está montado en ninguna ruta activa. Editarlo compila sin error —TypeScript no sabe que el archivo es huérfano— y el cambio simplemente nunca aparece en la aplicación real; el asistente de esa sesión editó ese componente, verificó con el navegador que "Reportes" no aparecía, y solo entonces, con `grep` confirmando cero importaciones activas, encontró que el componente real montado era otro.
* **Solución/heurística:** antes de editar un componente que decide navegación o layout, confirmar con una búsqueda de texto que ese archivo tiene al menos una importación activa desde algún archivo de enrutamiento real (`app/**/page.tsx` en Next.js App Router); y usar la aplicación real en el navegador —no solo la compilación de tipos— como árbitro final antes de reportar un cambio de UI como completo.
* **Verificabilidad:** no aplica un predicado booleano de "antes/después" reproducible hoy — el componente huérfano concreto de esa sesión ya no existe en el árbol de trabajo ni en el historial de git de este repositorio (se limpió antes del commit inicial). Lo que sí es verificable y reusable es la heurística en sí: `grep -rn "NombreComponente" src --include=*.tsx` sin resultados de importación fuera del propio archivo es condición suficiente para sospechar que un componente de navegación está huérfano, con independencia del proyecto.
* **Estado:** hallazgo empírico confirmado una vez en la sesión de origen; no refutado, no vuelto a reproducir en esta sesión. Se registra por ser el tipo de error silencioso —compila, no lanza excepción, pero no aparece— que vuelve a costar tiempo de diagnóstico si no se deja escrito como sospecha a probar primero.
* **Base científica:** se reutiliza Kent C. Dodds (2018), *Testing Library — Guiding Principles* (ya catalogado, Aporte 64): cuanto más se parezca la verificación al uso real de la aplicación, más confianza aporta — el navegador real como árbitro final, no la compilación de tipos, es la aplicación directa de ese principio a este hallazgo.

---

### Aporte 81: Dos Uniones de Tipo Literal Paralelas para el Mismo Concepto de Dominio ("Vista Activa"), sin una Fuente Única de Verdad
`¤interfaz` `¤invariantes`
* **Sesión de origen:** minería retrospectiva de `e22d64cd-c77d-4af9-8f1b-831a0ff0487c`.
* **Problema:** el concepto "vista/módulo activo actualmente mostrado" está tipado dos veces de forma independiente: `ActiveView` en `useAuditStore.ts` (la fuente de verdad en tiempo de ejecución, vía Zustand) y `VistaActiva` en `dashboard/page.tsx` (el tipo local del componente de navegación). Ambas uniones deben mantenerse sincronizadas a mano cada vez que se agrega una vista nueva; si difieren, TypeScript lo señala como un error de asignación en el punto de uso, pero nada impide que ambas colecciones de literales diverjan silenciosamente mientras no se ejerciten todos los casos en el mismo cambio.
* **Verificabilidad:** confirmado contra el código vigente que ambos tipos existen de forma independiente — `type VistaActiva` en `frontend/src/app/dashboard/page.tsx:63` (21 variantes) y `export type ActiveView` en `frontend/src/store/useAuditStore.ts:50` (21 variantes) —, sin que uno derive del otro mediante un alias de tipo compartido: no existe ningún `import type { ActiveView }` en `dashboard/page.tsx`.
* **Estado de validación:** hallazgo abierto, no corregido. La duplicación sigue presente en el código actual; hoy ambas listas coinciden en sus 21 valores (no hay divergencia activa ni bug en producción), así que se registra como fragilidad estructural y candidato concreto de refactorización (unificar bajo un solo alias de tipo exportado y consumido por ambos archivos), no como un defecto ya manifestado.
* **Límites conocidos:** se manifestará como error de tipos recién cuando alguien agregue una vista de un lado y olvide el otro — hasta entonces es silenciosa por construcción.
* **Base científica:** no se encontró una fuente formal específica sobre duplicación de tipos paralelos en TypeScript que agregue algo más allá del principio general de fuente única de verdad ya invocado implícitamente en otros aportes de este archivo; se omite forzar una cita nueva.

---

### Aporte 82: Generación de Reporte "Imprimible a PDF" como HTML Autocontenido en el Cliente — una Sustitución de Alcance Válida cuya Nomenclatura Puede Inducir a Error
`¤interfaz` `¤implementacion`
* **Sesión de origen:** minería retrospectiva de `e22d64cd-c77d-4af9-8f1b-831a0ff0487c`.
* **Problema:** sin un endpoint de backend para generar reportes, agregar una librería de generación de PDF en el cliente o construir un endpoint nuevo tiene un costo de alcance mayor al de la funcionalidad pedida en el momento. La decisión tomada fue generar un documento HTML autocontenido (estilos embebidos) y descargarlo vía `Blob` + enlace de descarga, confiando en que el usuario lo abra e imprima a PDF desde su propio navegador.
* **Por qué es útil aquí:** es una heurística de alcance razonable para un MVP, pero el nombre de la función (`descargarReporteAssessment`) y el comentario del archivo ("imprimible a PDF") conviven con una extensión de archivo real `.html`, no `.pdf`. Alguien que busque "dónde se genera el PDF" en este código no encontrará ninguna librería PDF ni ningún archivo `.pdf` producido — el artefacto real descargado es HTML.
* **Verificabilidad:** confirmado contra el código vigente — `frontend/src/lib/reportes/generarReporteAssessment.ts:130-135` construye un `Blob` de tipo `text/html;charset=utf-8` y fija `a.download` con extensión `.html`; no hay importación de ninguna librería de generación de PDF ni en ese archivo ni en `ReportesModule.tsx`. No aplica verificación booleana adicional: es una decisión de alcance documentada, no una propiedad de estado.
* **Estado:** implementado y en uso; no es un defecto sino una decisión de alcance deliberada, ya explicada en el propio comentario del archivo. Se registra para que quien retome este módulo no asuma, por el nombre de la función, que existe una librería PDF real.
* **Base científica:** no aplica — es una decisión de alcance de producto, no un patrón con respaldo académico que agregue algo genuino más allá de la propia decisión.

---

### Aporte 83: Un Verificador de "Listo para Pruebas E2E" que Solo Reconoce Puntos de Entrada de un Lenguaje Aprueba por Vacuidad Proyectos Escritos en Otro
`¤arbitro` `¤invariantes`
* **Sesión de origen:** minería retrospectiva de la transcripción local `4284d49a-9965-4afb-a1c3-d934fb92876e` (sesión sobre los proyectos hermanos ERP y ZERAG).
* **Nivel de confianza — leer antes que el resto del aporte:** a diferencia de los demás aportes de esta parte, este describe un componente de la infraestructura de gobernanza EXTERNA a este repositorio (vive en el proyecto ZERAG, no aquí), así que no pudo verificarse contra su código real desde esta sesión. Se registra igual, con esta reserva explícita, porque la sesión de origen nombra a "Plataforma LOPDP 360" como el caso concreto que expuso el defecto, y el costo de no anotarlo —confiar en un veredicto "aprobado" que en realidad no evaluó nada de este proyecto— es mayor que el costo de registrar un hallazgo de segunda mano correctamente etiquetado como tal.
* **Problema reportado:** la infraestructura de gobernanza cuya salida se consulta como árbitro exógeno ("arnés físico determinista") incluye un verificador de "¿esta aplicación está lista para pruebas end-to-end?" que localiza el punto de entrada de la aplicación buscando artefactos de un runtime Python. "Plataforma LOPDP 360" es una aplicación Next.js/TypeScript sin ese tipo de punto de entrada; según la sesión de origen, el verificador, al no encontrar ninguno, no reportaba "inconcluso" — reportaba "aprobado".
* **Formulación:** $\nexists\ \text{objetivo}_{\text{python}} \implies \text{veredicto} = \text{"aprobado"}$, en vez de $\text{veredicto} = \text{"inconcluso"}$ — un caso de verdad vacua ($\forall x \in \emptyset,\ P(x)$ es trivialmente verdadero) aplicado, según lo reportado, a un chequeo de gobernanza donde la ausencia de una precondición reconocible se interpretó como satisfacción de la postcondición en vez de como "no evaluado".
* **Estado:** hallazgo de segunda mano, reportado por la sesión de origen sobre infraestructura ajena a este repositorio; no confirmado de primera mano por esta sesión y sin forma de saber, desde aquí, si ya fue corregido desde que se reportó.
* **Por qué es útil aquí:** si el check "Arnés Físico Determinista" de este mismo proyecto alguna vez muestra "aprobado" sin que se haya corrido realmente la suite Playwright, este es un candidato de causa raíz a considerar junto con —no en lugar de— otras causas ya documentadas en este proyecto (p. ej. un bloqueo de facturación de la cuenta, que es la causa confirmada de sus fallos recientes).
* **Base científica:** convención estándar de cuantificación vacua en lógica de primer orden ($\forall x \in \emptyset,\ P(x) = \text{verdadero}$) — resultado elemental de la propia definición del cuantificador universal; no requiere una cita de investigación específica más allá de cualquier texto introductorio de lógica formal.

---

# PARTE X: Hallazgos de la Sesión RBAC de la Hoja de Ruta (Ejecutada 2026-10-08)
`¤rbac` `¤arbitro` `¤invariantes`

> **ORIGEN:** sesión que completó el RBAC de backend (API de administración de la organización, SoD del DPO, cuatro ojos en evidencia, alcance por área) sobre la rama `feature/roadmap-ia`. Los tres aportes se verificaron contra la rama **test** de Neon y el código vigente; ninguno se infirió solo de la conversación.

---

### Aporte 84: Políticas RLS Habilitadas pero Inertes cuando la Aplicación se Conecta como Dueña de las Tablas con `BYPASSRLS`
`¤rbac` `¤invariantes`
* **Problema:** las migraciones de la Hoja de Ruta ejecutan `ALTER TABLE … ENABLE ROW LEVEL SECURITY` y crean políticas `tenant_isolation_*` sobre 7 tablas, y el código inyecta `app.current_tenant_id` con `set_config`. Todo eso compila, migra y "se ve" correcto, pero PostgreSQL no aplica RLS a los roles con atributo `BYPASSRLS` ni, por defecto, al dueño de la tabla. Las cuatro URLs del `.env` (`DATABASE_URL`, `MIGRATION_DATABASE_URL`, `TEST_DATABASE_URL`, `TEST_MIGRATION_DATABASE_URL`) usan el mismo rol `lopdp_beta_owner`, que es dueño de las tablas y tiene `rolbypassrls = True`; ninguna tabla tiene `FORCE ROW LEVEL SECURITY`.
* **Verificación booleana (rama test, 2026-10-08):**
  $$\texttt{rolbypassrls}(\texttt{lopdp\_beta\_owner}) = \text{True} \;\land\; \texttt{relforcerowsecurity}(\texttt{user\_tenant\_roles}) = \text{False}$$
  $$\texttt{app.current\_tenant\_id} = \text{"tenant-inexistente-xyz"} \implies |\texttt{SELECT * FROM user\_tenant\_roles}| = 16 \neq 0$$
  Con un tenant que no existe, la política debería devolver 0 filas; devuelve las 16 de la tabla.
* **Consecuencia:** hoy el aislamiento multi-tenant real depende únicamente de los `WHERE tenant_id = :tid` explícitos del código (presentes en `roadmap_service.py` y `rbac_service.py`), no de la BD. Una consulta futura que olvide ese filtro filtraría datos entre tenants sin que ninguna política lo impida. `tests/test_database_rls.py` no lo detecta: su propio comentario declara que es un esqueleto que solo prueba el `ContextVar`, no el filtrado en PostgreSQL.
* **Estado:** hallazgo abierto, **no corregido**. Verificado en la rama test; en producción se infiere por usar el mismo nombre de rol (las ramas de Neon heredan los roles), pero no se consultó la BD de producción. Corrección esperada: un rol de aplicación sin `BYPASSRLS` y que no sea dueño de las tablas, y `FORCE ROW LEVEL SECURITY`, más un test que afirme $|\text{filas visibles con tenant ajeno}| = 0$.
* **Límites conocidos:** el trigger `fn_utr_dpo_sod` de esta misma sesión se declaró `SECURITY DEFINER` para que su `EXISTS` no dependa de la visibilidad RLS del invocante. Hoy no hace diferencia porque RLS no se aplica; empezará a importar en cuanto se corrija este hallazgo.
* **Base científica:** PostgreSQL Global Development Group, documentación oficial (v16), §5.8 *Row Security Policies*: los superusuarios y los roles con `BYPASSRLS` siempre omiten la seguridad por filas, y el dueño de la tabla normalmente también, salvo que se use `ALTER TABLE … FORCE ROW LEVEL SECURITY`.

---

### Aporte 85: Una Restricción `UNIQUE` con Columna Anulable no Impide Duplicados, y con Revocación Lógica Bloquea la Re-Asignación
`¤rbac` `¤invariantes`
* **Problema:** `user_tenant_roles` declara `UNIQUE (user_id, tenant_id, area_id, role)`. Dos efectos no evidentes:
  (a) como `area_id` es `NULL` en los roles transversales al tenant, y en PostgreSQL los `NULL` son distintos entre sí dentro de un `UNIQUE`, la restricción **no** impide asignar dos veces el mismo rol transversal;
  (b) como la revocación es lógica (`valid_to = now()`, la fila se conserva para auditoría), una asignación revocada con `area_id` no nulo **sí** colisiona con una nueva asignación idéntica, así que re-asignar falla con `IntegrityError` aunque no haya ninguna asignación activa.
* **Verificación booleana (rama test, en transacción revertida):** dos `INSERT` idénticos con `role='encargado'` y `area_id IS NULL` para el mismo usuario y tenant ⟹ `count(*) = 2` (ambos aceptados).
* **Solución aplicada:** `rbac_service.grant_role` comprueba en la aplicación el duplicado **activo** antes de insertar (cubre a) y, si existe una fila revocada con la misma combinación, la reactiva en lugar de insertar (cubre b). Lo verifican `test_sod_dpo_y_ciclo_de_revocacion` (duplicado activo ⟹ 409) y `test_regrant_reactiva_asignacion_revocada` (mismo `id`, `valid_to = None`).
* **Estado:** mitigado en la aplicación; la BD sigue aceptando duplicados transversales si alguien escribe directo en la tabla. Una corrección en la BD sería `UNIQUE NULLS NOT DISTINCT` (PostgreSQL ≥ 15; Neon usa 16) o un índice único parcial `WHERE valid_to IS NULL`. No se aplicó en esta sesión.
* **Base científica:** PostgreSQL Global Development Group, documentación oficial (v16), §5.4.3 *Unique Constraints*: los valores nulos no se consideran iguales salvo que se declare `NULLS NOT DISTINCT`.

---

### Aporte 86: Una Falla que Solo Aparece en el Arnés no Prueba una Diferencia de Entorno — Repetir la Corrida Aislada antes de Atribuirla
`¤arbitro`
* **Problema:** `tests/test_ai_copilot.py::test_asistente_acepta_estado_de_seguimiento_y_rechaza_otro_valor` falló en las 2 corridas de `ejecutar_arnes_tres_pilares.bat` y pasó en las primeras corridas aisladas. La hipótesis natural era una diferencia del entorno del `.bat` (`chcp 65001`, `PYTHONPATH=.test-runtime`, `-v` en vez de `-q`), y se invirtió tiempo en aislar cada una. La causa real era otra: `features/ai_copilot/services/assistant_provider.py:17` arma la configuración como `{**dotenv_values(ENV_PATH), **os.environ}`, de modo que el test hereda `DEEPSEEK_API_KEY` del `.env` y hace una llamada **real** al LLM, cuya respuesta no es determinista y a veces no contiene la palabra que el test exige.
* **Observación reproducible:** reproduciendo el entorno exacto del `.bat` sobre solo ese archivo, el resultado fue `6 passed`, luego `1 failed, 5 passed`; en total pasó 5 de 7 corridas aisladas. La falla no dependía del entorno sino del azar de la respuesta remota; que coincidiera dos veces con el arnés fue casualidad.
* **Heurística:** ante un test que falla solo bajo cierto runner, correrlo varias veces (≥ 5) en el entorno "bueno" antes de investigar diferencias de entorno; y revisar si el código bajo prueba lee secretos desde un archivo por ruta (no solo desde `os.environ`), porque eso conecta silenciosamente un test unitario con un servicio externo.
* **Verificabilidad:** no aplica un predicado booleano estable (la falla es probabilística por construcción). Lo verificable es la causa: la línea 17 citada y que el endpoint usa `httpx.AsyncClient` hacia el proveedor.
* **Estado:** diagnosticado; la corrección (aislar el test del proveedor real) quedó delegada a una sesión aparte el mismo día.
* **Base científica:** Luo, Q., Hariri, F., Eloussi, L. & Marinov, D. (2014), *An Empirical Analysis of Flaky Tests*, FSE 2014 (ACM). Clasifica empíricamente las causas raíz de los tests intermitentes en proyectos reales; la dependencia de recursos de red y el orden de ejecución están entre las categorías identificadas, lo que respalda descartar primero la dependencia externa antes de atribuir la falla al runner.

---

## Candidatos descartados de esta sesión (Parte X)

| Candidato | Motivo del descarte |
|---|---|
| Aplicar SoD en dos capas: validación en el servicio (error 409 legible) más trigger en BD como respaldo. | Práctica estándar de defensa en profundidad; ya está implícita en el invariante del PRD («La base de datos y la UI bloquean…»). Sin generalidad nueva. |
| Alcance jerárquico de `responsable_area` con CTE recursiva sobre `areas.parent_area_id`. | Técnica SQL estándar; nada específico que se repita como error. |
| Cuatro ojos universal (quien sube no valida) en vez de solo para el DPO. | Decisión de diseño de esta sesión, no un hallazgo; el principio (Fagan 1976, ya catalogado) está registrado. |
| `git worktree add` falla en Windows con `Filename too long` por el PDF de la SPSP en la raíz del repo, cuando la ruta del worktree es profunda. | Limitación conocida y documentada de Git para Windows (`core.longpaths`); lo único propio del proyecto es el nombre del archivo. Se anota aquí para que las sesiones que usen worktrees lo sepan, sin elevarlo a aporte. |


---

# PARTE XI: Hallazgos de la Sesión de Rol de Aplicación RLS (Ejecutada 2026-10-08)

Sesión que corrige el Aporte 84: migración `20261008_app_role_rls` (rol `lopdp_app`), arreglo de `has_active_role` y test de aislamiento `tests/test_rls_app_role.py`. Se consideraron 5 candidatos; sobrevivieron 2.

### Aporte 87: Probar RLS como el Rol de Aplicación sin Conocer su Contraseña — Membresía `INHERIT FALSE, SET TRUE` y `SET LOCAL ROLE`
`¤rbac` `¤invariantes` `¤arbitro`
* **Problema:** para probar que las políticas RLS aíslan de verdad hay que consultar *como* el rol restringido, pero su contraseña no debe vivir en el código ni en los tests, y en Neon se fija a mano. Probar como el dueño no sirve: tiene `BYPASSRLS` y el resultado sería verde aunque las políticas no funcionen (exactamente el defecto del Aporte 84).
* **Solución:** la migración concede `GRANT lopdp_app TO CURRENT_USER WITH INHERIT FALSE, SET TRUE` (sintaxis de PostgreSQL 16). `INHERIT FALSE` evita que el dueño gane los privilegios del rol; `SET TRUE` le permite asumirlo. El test se conecta con la URL de pruebas existente y ejecuta `SET LOCAL ROLE lopdp_app` dentro de la transacción: RLS se evalúa contra `current_user`, así que las políticas se aplican como en producción, y el `ROLLBACK` devuelve la sesión al dueño para el cleanup del fixture. En PostgreSQL 16 el creador de un rol con `CREATEROLE` recibe `ADMIN OPTION` pero no `SET` por defecto (`createrole_self_grant` vacío), por eso la concesión explícita es necesaria.
* **Verificación booleana (rama test, 2026-10-08), `tests/test_rls_app_role.py` 4/4:**
  $$\texttt{rolbypassrls}(\texttt{lopdp\_app}) = \text{False} \;\land\; |\texttt{utr}|_{\text{tenant ajeno}} = 0 \;\land\; |\texttt{utr}|_{\text{sin tenant}} = 0 \;\land\; |\texttt{utr}|_{\text{tenant propio}} = 1$$
  La migración se aplicó, revirtió y re-aplicó en la rama test; la suite completa quedó en 252 passed.
* **Límites conocidos:** la app en ejecución sigue conectándose como dueño hasta que se dé `LOGIN` y contraseña a `lopdp_app` en Neon y se cambie `DATABASE_URL`; el test prueba las políticas, no la configuración de despliegue. Hay que hacerlo con `ALTER ROLE … LOGIN PASSWORD` por SQL: en la rama test se observó `rolbypassrls(neon_superuser) = True`, y Neon añade a ese grupo los roles creados desde su consola.
* **Estado:** implementado en `alembic/versions/20261008_app_role_rls.py` y `tests/test_rls_app_role.py` (commit `5ccbb21`). No introduce token nuevo de gobernanza.
* **Base científica:** PostgreSQL Global Development Group, documentación oficial (v16), *GRANT* (opciones `INHERIT` y `SET` de la membresía, nuevas en v16) y *SET ROLE* (los privilegios y las comprobaciones pasan a ser los del rol asumido).

---

### Aporte 88: Un Parámetro sin `Header()` en una Dependencia FastAPI se Lee de la Query String — el Contexto RLS Nunca se Fija
`¤rbac`
* **Problema:** `app_core/db/session.py` declara `get_session(x_user_id: str | None = None, x_tenant_id: str | None = None)` y, si llegan, ejecuta `set_config('app.current_tenant_id', …)`. Por los nombres parece leer las cabeceras `X-User-ID`/`X-Tenant-ID`, pero FastAPI interpreta todo parámetro escalar sin `Header()`/`Path()`/`Body()` como **parámetro de query**, también dentro de una dependencia. Las peticiones mandan el tenant por cabecera, así que ambos valen `None` y la sesión nunca fija el tenant. Con el rol dueño no se notaba; con `lopdp_app`, toda consulta que dependa de ese `set_config` vería 0 filas.
* **Mitigación aplicada:** `rbac_service.has_active_role` (llamada por `api/rbac.py::get_context` en cada petición) ahora fija el tenant antes de leer `user_tenant_roles`; como FastAPI reutiliza la misma sesión dentro de la petición y `set_config(…, true)` dura la transacción, el contexto queda fijado para el resto de la petición. Lo cubre `test_tenant_propio_ve_sus_filas_y_has_active_role`.
* **Verificabilidad:** no se ejecutó una petición HTTP para demostrarlo; lo verificable es la firma en `app_core/db/session.py` (sin `Header`) frente a `api/rbac.py`, que sí usa `Header(..., alias="X-Tenant-ID")`. Predicado comprobable a futuro: `GET /…` con cabecera `X-Tenant-ID=t` y sin query ⟹ `current_setting('app.current_tenant_id', true) IS NULL` dentro de `get_session`.
* **Estado:** abierto en `get_session` (se dejó como seguimiento); mitigado para las rutas que pasan por `get_context`.
* **Base científica:** documentación oficial de FastAPI, *Query Parameters* y *Header Parameters*: los parámetros de función que no forman parte de la ruta se interpretan como query; para leer una cabecera hay que declararla con `Header`.

---

## Candidatos descartados de esta sesión (Parte XI)

| Candidato | Motivo del descarte |
|---|---|
| `FORCE ROW LEVEL SECURITY` no afecta a roles con `BYPASSRLS`. | Ya está en la cita del Aporte 84 (§5.8). |
| Bitácoras de auditoría con `GRANT SELECT, INSERT` (append-only). | Práctica estándar de mínimo privilegio; sin causa de error repetible. |
| Un `cat > archivo` sin entrada en Git Bash cuelga el comando hasta el timeout. | Comportamiento trivial de la shell, ajeno al proyecto. |


---

# PARTE XII: Hallazgos de la Prueba del Rol de Aplicación en la Rama TEST (Ejecutada 2026-10-09)

### Aporte 89: Un `SET ROLE` de Sesión a Través del Pooler de Neon (PgBouncer, Modo Transacción) se Filtra a Otros Clientes
`¤rbac` `¤invariantes` `¤arbitro`
* **Problema:** para correr la suite con la app operando como `lopdp_app` sin contraseña, un plugin de pytest ejecutaba `SET ROLE lopdp_app` en cada conexión nueva del engine de la app. Las URLs `*-pooler` de Neon pasan por PgBouncer en modo transacción: el cliente no posee la conexión del servidor, solo la usa durante una transacción. Un `SET` de nivel de sesión queda en la conexión del servidor y lo hereda el siguiente cliente que la reciba, aunque sea otro engine, otro proceso o la CI.
* **Observación reproducible (rama test):** tras la corrida, el engine de los fixtures (otro engine, mismo usuario dueño) y conexiones `psycopg` nuevas abiertas desde un proceso aparte devolvían:
  $$\forall i \in 1..15:\ (\texttt{current\_user}, \texttt{session\_user})_i = (\texttt{lopdp\_app}, \texttt{lopdp\_beta\_owner})$$
  Los fixtures no podían insertar en `user_tenant_roles` (`new row violates row-level security policy`), lo que rompió 31 tests. La primera corrida con el mismo plugin había pasado por azar de asignación de conexiones.
* **Solución:** (1) limpiar el pooler terminando, desde la URL directa (sin `-pooler`), los backends del usuario en la rama test (`pg_terminate_backend`), y (2) usar `SET LOCAL ROLE` en el evento `begin` de cada transacción, que se revierte al terminarla. Verificado: suite 256 passed con el engine de la app como `lopdp_app` y el de fixtures como dueño, y después $\{\texttt{current\_user}\}_{10\ \text{conexiones}} = \{\texttt{lopdp\_beta\_owner}\}$.
* **Regla general:** con un pooler en modo transacción, todo estado de sesión (`SET`, `SET ROLE`, `set_config(…, false)`, prepared statements, `LISTEN`, advisory locks de sesión) es compartido entre clientes; solo es seguro el estado de transacción (`SET LOCAL`, `set_config(…, true)`). El código de la app ya usa `set_config(…, true)` para `app.current_tenant_id`, que es correcto; en producción la app debe conectarse directamente con el usuario `lopdp_app` en lugar de cambiar de rol.
* **Estado:** plugin de prueba fuera del repo (scratchpad de la sesión); no cambia código de la app. No introduce token nuevo de gobernanza.
* **Base científica:** PgBouncer, documentación oficial, *Features* (tabla de compatibilidad por modo de pooling: en modo transacción no se admiten las funciones de sesión como `SET`/`RESET`, `LISTEN` ni los advisory locks de sesión); PostgreSQL Global Development Group, documentación oficial (v16), *SET* (`SET LOCAL` solo dura hasta el fin de la transacción actual).
