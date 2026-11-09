# Metodologías de JUBYS Plataforma LOPDP 360
`¤metodologias`
`¤bbap` `¤diagnostico` `¤rat` `¤frontend-ide`

> **MARCO METODOLÓGICO INTEGRAL DE TRABAJO, CUMPLIMIENTO Y EXPERIENCIA:**
> Este documento define las metodologías de diagnóstico, diseño, gestión de riesgos, orquestación de tareas y experiencia de usuario que rigen la **Plataforma LOPDP 360**. Integra las mejores prácticas y ergonomías analizadas de referentes globales y herramientas líderes del mercado (**Antigravity / Cursor, Global Suite, Novoser, Pirani, Isotools y Odoo**), articuladas con el rigor normativo ecuatoriano de la SPDP.

---

## 1. Metodología de Diagnóstico Ágil: Sesión Timeboxed de 60 Minutos
`¤diagnostico` `¤diagnostico-motor`

Inspirada en el benchmark metodológico europeo **DMAT (Digital Maturity Assessment Tool)** y en la flexibilidad del Anexo de la Guía de Gestión de Riesgos de la SPDP:
*   **Timebox Estricto (60 minutos):** Diseñado para que una reunión ejecutiva de consultoría sea suficiente para trazar la línea base preliminar sin fatiga cognitiva.
*   **Estructura de la Sesión:**
    1. *Minuto 0 a 5:* Ficha Organizacional Inteligente (sector, tamaño, nube, sistemas críticos).
    2. *Minuto 5 a 45:* Núcleo Común (16 Dominios JUBYS $\times$ hasta 3 preguntas = 48 preguntas clave).
    3. *Minuto 45 a 55:* Preguntas Condicionales Críticas (solo si se activan por sector o tratamiento especial, máx. 12).
    4. *Minuto 55 a 60:* Validación de Hallazgos y Próximos Pasos.
*   **Poda Lógica Condicional:** La interfaz impone un **límite técnico infranqueable de 80 preguntas visibles por sesión**, con una ruta operativa promedio de **45 a 68 preguntas**.
*   **Regla de Cierre de Sesión:** Cualquier asunto que demande auditoría forense, muestreo de logs o análisis contractual profundo no detiene la entrevista: se etiqueta como `"Pendiente de Validación"` y se deriva a la fase de implementación.

---

## 2. Metodología de Evaluación y Madurez Multidimensional
`¤diagnostico-scoring`

Superación del paradigma del "porcentaje único ficticio". La plataforma evalúa mediante cuatro vectores ortogonales:
1.  **Madurez por dimensión (1 a 5):** Escala SMARTCIDI. Cada control recibe un nivel asignado de 1 a 5 y la evidencia lo limita; cada dimensión obtiene su nivel y ninguna cifra las combina. Valores, fórmulas y diferencias con el archivo fuente: `governance/ESCALA_MADUREZ.md`, cuya fuente única es `governance/contratos/escala_madurez.json`.
2.  **Estado de Conformidad Jurídica:** Clasificación booleana estricta: `Conforme`, `Parcial`, `No Conforme`, `No Verificado` o `No Aplicable`.
3.  **Calidad de Evidencia (0 a 4):** Verbal, informal, documental, operativa y revisada. Limita el nivel reconocido: `nivel efectivo = MIN(nivel asignado, evidencia + 1)`.
4.  **Vector de Riesgo Residual:** Identificación de brechas de impacto crítico sobre derechos y libertades que bloquean la conformidad independientemente del nivel de madurez alcanzado.

---

## 3. Metodología de "Compliance Graph" y Fuente Única de Verdad (Inspiración Odoo)
`¤rat` `¤implementacion`

Tomando como referencia la arquitectura modular y el modelo relacional unificado de **Odoo**:
*   **El RAT como Registro Maestro ("Master Record"):**
    *   En Odoo, el *Partner Record* es el eje sobre el cual giran compras, ventas y contabilidad sin duplicar entidades.
    *   En LOPDP 360, la **Actividad de Tratamiento del RAT** es el registro maestro. Un tratamiento se ingresa una sola vez y de él derivan:
        - La matriz de riesgos para derechos y libertades.
        - La evaluación de Tratamiento a Gran Escala (MTGE).
        - La necesidad de EIPD.
        - El inventario de terceros encargados y contratos asociados.
        - Las transferencias internacionales.
        - El aviso de privacidad y la asignación de controles.
*   **Cero Matrices Paralelas:** Erradicación de hojas de cálculo independientes que se desincronizan. Un cambio en una finalidad del RAT actualiza en cascada todos los módulos satélite.

---

## 4. Metodología de Ergonomía y Experiencia de Usuario: IDE / Command-Center (Inspiración Antigravity / Cursor)
`¤frontend-ide`

Dirigida a consultores, auditores, oficiales de seguridad y DPOs que requieren procesar grandes volúmenes de evidencia con máxima velocidad y precisión:
*   **Command Palette Universal (`Ctrl + K` / `Cmd + K`):**
    *   Permite saltar inmediatamente a cualquier artículo de la ley, actividad del RAT, cliente tenant, reporte o evidencia sin navegar por menús lentos.
*   **Layout de Paneles Divididos (Split Panes):**
    *   *Panel Izquierdo:* Árbol colapsable de módulos, dominios G01–G16 y tratamientos.
    *   *Panel Central:* Espacio de trabajo activo (cuestionario adaptativo, editor de control o tabla de RAT).
    *   *Panel Derecho Contextual:* Copiloto IA de cumplimiento y visor de evidencias/artículos vinculados.
*   **Estética Minimalista y Alta Densidad Técnica:**
    *   Soporte nativo Dark/Light mode con paletas de baja fatiga visual.
    *   Bordes ultra-finos de 1px, eliminación de sombras pesadas o animaciones innecesarias, tipografía dual: Inter/Geist para lectura y JetBrains Mono para códigos, metadatos, artículos y hashes de integridad.

---

## 5. Metodología de Integración Normativa y Continuidad (Inspiración Global Suite)
`¤regulation-code` `¤adpa`

Inspirada en la capacidad de **Global Suite** para articular marcos regulatorios locales con estándares internacionales:
*   **Cruce y Coexistencia Normativa:**
    *   El núcleo opera con la LOPDP, RGLOPDP y normativa de la SPDP de Ecuador.
    *   Permite incorporar catálogos de buenas prácticas internacionales como **ISO/IEC 27002:2022** e **ISO/IEC 27701:2019**, etiquetándolos con claridad como *estándares complementarios* sin confundirlos con obligaciones legales vinculantes.
*   **Módulos de Continuidad y Ciberseguridad Conexa:**
    *   Articulación con la Ley Orgánica para el Fortalecimiento de la Ciberseguridad (notificación ágil de brechas) y marcos de continuidad operativa.

---

## 6. Metodología de Auditoría, Tickets y CAPA (Inspiración Novoser)
`¤auditoria` `¤incidentes`

Inspirada en los flujos de gestión de tickets y aseguramiento de **Novoser**:
*   **Trazabilidad de Hallazgos a Acciones Correctivas (CAPA):**
    *   Cada no conformidad u observación genera un ticket con causa raíz, acción correctiva/preventiva, responsable asignado, fecha compromiso y evidencia de cierre.
*   **Verificación Independiente de Cierre:**
    *   Ningún ejecutor puede cerrar su propia no conformidad; la verificación de eficacia es realizada por un rol independiente o auditor.
*   **Gestión de Incidentes con Reloj Normativo:**
    *   Cronómetro de cuenta regresiva para cumplimiento de plazos legales de notificación a la SPDP y CSIRT nacional.

---

## 7. Metodología de Gestión Visual de Riesgos (Inspiración Pirani / Pirámid)
`¤riesgos-eipd` `¤mtge-granescala`

Inspirada en el enfoque de **Pirani** para democratizar la gestión de riesgos en América Latina:
*   **Matrices Intuitivas de Calor:**
    *   Visualización clara de Probabilidad $\times$ Impacto en cuadrículas interactivas 3x3 y 5x5.
    *   Desmitificación de la matemática de riesgo mediante racionalidades guiadas, permitiendo que jefes de área de negocio identifiquen amenazas sin requerir formación actuarial avanzada.
*   **Cálculo Asistido de Gran Escala (MTGE):**
    *   Parámetros sencillos de volumen, permanencia y sensibilidad que arrojan automáticamente si el tratamiento detona obligaciones reforzadas.

---

## 8. Metodología de Orquestación y Comités (Inspiración Isotools)
`¤implementacion` `¤dpo-cockpit`

Inspirada en los flujos de gobierno y automatización de comités de **Isotools**:
*   **Automatización de Notificaciones y Recordatorios:**
    *   Alertas automáticas por correo y notificación in-app ante vencimiento de controles, expiración de evidencias o solicitudes de derechos ARCO+.
*   **Gestión Documental con Flujo de Aprobación Formal:**
    *   Workflow estricto: `Borrador → En Revisión (Legal/DPO) → Aprobado (Responsable) → Publicado/Vigente`.
    *   Control estricto de próximas fechas de revisión y control de versiones con historial de cambios inmutable.

---

## 9. Metodología de Desarrollo del Software: BBAP y Confinamiento ADPA
`¤bbap` `¤adpa`

Rige la construcción del software bajo el canon Zero-Regression:
1.  **Metodología BBAP en 2 Pasos:**
    *   *Paso 1 (Boceto libre):* Prototipado rápido de componentes, pantallas y esquemas con máxima apertura creativa.
    *   *Paso 2 (Sellado):* Verificación física observable con pruebas automatizadas, linters AST y sellado de compuertas sin código propietario ajeno.
2.  **Confinamiento Modular en Salas ADPA:**
    *   Cada dominio (`rat`, `diagnostico`, `riesgos`, `dpo_cockpit`, etc.) se aísla en una sala hermética con compuerta pública `_service.py`. Cero acoplamiento circular.

---

## 10. Metodología de Poda Ontológica y Parametrización en 2 Fases
`¤diagnostico-motor` `¤diagnostico`

Rige la instanciación de diagnósticos multirregulatorios escalables:
1.  **Fase 1: Parametrización de la Ficha Organizacional (Raíz de Poda):**
    *   El usuario define Razón Social, Sector, Tamaño de empresa y la Normativa objetivo (`Propiedad Intelectual`, `NIIF`, `ISO`).
    *   Esta configuración se almacena en el store reactivo global (`useAuditStore`) de forma desacoplada antes de generar cualquier pregunta.
2.  **Fase 2: Instanciación del Cuestionario Podado ($\le 80$ preguntas):**
    *   El motor proyecta las reglas del sector y normativa elegida, ocultando o podando todas las ramas no aplicables.
    *   Se evita la sobrecarga cognitiva del auditor, asegurando un recorrido enfocado y determinista.

---

## 11. Metodología de Whitelist Evidencial y Validación Poka-Yoke
`¤evidencias` `¤diagnostico`

Garantiza la integridad probatoria y evita inyecciones de archivos incompatibles:
1.  **Barrera Declarativa de Sistema Operativo:**
    *   El selector de archivos implementa el atributo `accept` dinámico según la normativa seleccionada (`.pdf,.docx,.md,.txt` para PI; formatos tabulares/estructurados `.csv,.xlsx,.xbrl,.ixbrl,.json,.xml,.sql` para NIIF/ISO).
2.  **Intercepción Reactiva en Memoria y Drag-and-Drop:**
    *   Tanto en la selección por diálogo como en la zona de arrastre (*Dropzone*), un validador JavaScript inspecciona las extensiones en tiempo real.
    *   Cualquier archivo fuera de whitelist es rechazado instantáneamente con feedback semántico `#ff1744` sin contaminar el arreglo global.
3.  **Purga Transaccional Inmediata:**
    *   Si el usuario cambia el selector de normativa, el método mutador `setNormativa` vacía automáticamente el arreglo de evidencias previas para garantizar que no existan documentos huérfanos o fuera de contexto normativo.

---

## 12. Metodología de Ergonomía Visual Acromática y Jerarquía Tonal Invertida
`¤frontend-ide`

Fundamentada en la Ley de Fitts, la Psicología de la Gestalt (Koffka, 1935) y el *Data-Ink Ratio* de Edward Tufte (1990) para mitigar la fatiga visual en auditorías prolongadas:
1.  **Base Acromática Estricta (Achromatic Baseline):**
    *   Los componentes estructurales estáticos (tarjetas, divisores, inputs, contenedores) se mantienen en escalas neutras de negros (`#0a0a0c`), grises oscuros (`#141417`, `#26262b`) y grises claros/blancos en tema claro, suprimiendo azules o tintes saturados que distraen la fovea.
2.  **Señalética Semántica Reservada:**
    *   El color se utiliza exclusivamente para comunicar estados críticos: Verde (`#00c853`) para éxito/conformidad, Rojo (`#ff1744`) para purga/brecha crítica, y gradiente púrpura-azul (`#9a3bf1` a `#3892f3`) para el desencadenante de acción principal (CTA).
3.  **Jerarquía Tonal Invertida:**
    *   La periferia de control (dock lateral de navegación y barra superior) posee la menor luminancia para estabilizar el horizonte visual, proyectando el mayor contraste y pureza lumínica sobre el lienzo central de trabajo.
4.  **Dock Dinámico Plegable:**
    *   El menú lateral mantiene sus íconos en tamaño natural y prescinde de títulos estáticos comprimidos ("Salas de cumplimiento"). Permite expansión suave y botón de abatimiento para ceder el 100% del espacio al análisis documental cuando sea requerido.

---

## 13. Metodología de Trabajo en Equipo por Archivos Disjuntos y Fusión por PR
`¤coordinacion` `¤adpa`

Probada en este repositorio entre el 2026-10-30 y el 2026-10-31 (PR #253 a #278) y, según reporta el propietario, en seis tandas de otro proyecto sin una sola colisión:
1.  **Reparto por archivos disjuntos:**
    *   Cada tarea declara en su ficha (`governance/tareas/<ID>.md`, campo `propiedad`) los archivos que escribe. Dos tareas de una misma tanda no comparten ningún archivo; si lo comparten, van en tandas distintas o una absorbe a la otra.
    *   Antes de lanzar una tanda, sus archivos se cruzan con **todas las ramas abiertas del equipo**, no solo entre sus tareas. Así se detectó que DIAG-08 reescribía los archivos que la tanda 3 del ADR 0001 iba a tocar.
    *   El árbitro `scripts/verificar_alcance_pr.py` compara en el CI el diff del PR con la propiedad de la ficha que nombra la rama (`tarea/<persona>/<id>-...`): rechaza en las tareas `ADPA-*` y avisa en las demás.
    *   Se agrupa por **sala consumidora**, no por dependencia: tres dependencias que tocaban el mismo motor cabían en una sola tarea.
2.  **Lo que garantiza y lo que no:**
    *   Archivos disjuntos garantizan cero conflictos de Git. **No garantizan cero regresiones**: dos PR en verde pueden romper la base juntos, y un PR puede romper un árbitro que vigila archivos de otra zona (el #265 borró un archivo del frontend y rompió el contrato de la escala de madurez).
    *   Por eso los PR se fusionan de uno en uno, cada uno se actualiza con la base y repite la suite antes de fusionar, y la fusión corre siempre la suite completa.
3.  **Ramas, reglas y fusión (regla 10):**
    > **Decisión del propietario (2026-11-05):** se retiran las ramas `dev/<persona>`. Cada `tarea/<persona>/<id>` nace de `origin/main` y abre su PR directo hacia `main`; el PR corre humo, contenedor y arnés por salas, y el push a `main` corre el arnés completo contra Neon. Lo que sigue describe el flujo con `dev/<persona>` tal como rigió del 2026-10-29 al 2026-11-05 y se conserva como historia; donde dice `origin/dev/<persona>` léase `origin/main`, y el PR de tarea va hacia `main`.
    *   **Directriz del propietario (2026-11-01):** cada rama parte de la punta, en el remoto autoritativo, de la rama de la que deriva, no de su copia local; el coordinador comprueba el punto de unión de cada rama al integrar. En LOPDP eso es `git fetch origin` y partir de `origin/dev/<persona>`. Una rama que no salga de esa punta se devuelve antes de integrarla.
    *   `dev/<persona>` fue el punto de integración de cada colaborador y de sus chats hasta el 2026-11-05 (PR #401 llevó a `main` todo lo que tenían; véase la decisión de arriba).
    *   **Ciclo diario:** (1) cada persona abre su PR de `dev/<persona>` hacia `main` al cierre de la jornada; (2) cada PR entra con el CI en verde; (3) cuando todos hayan entrado, `main` se fusiona en cada `dev/<persona>`, por PR; (4) toda tarea nueva parte de esa base actualizada.
    *   `tarea/<persona>/<id>` → PR hacia `dev/<persona>` → desde las 19:00, PR de `dev/<persona>` hacia `main`. Producción se despliega de noche desde `produccion`.
    *   `main` exige que la rama esté al día; `dev/**` exige que todo cambio entre por PR. Consecuencia: el botón **«Update branch» no funciona en `dev/<persona>`**, porque es un push directo, y cada vez que `main` avanza hay que traerlo por PR.
    *   Pasos cuando `main` avanzó y el PR de `dev/<persona>` queda «out of date»:
        1. Abrir, o reutilizar, el PR de `main` hacia `dev/<persona>`.
        2. Si su última corrida es anterior a un arreglo ya fusionado en `dev/<persona>`, cerrarlo y reabrirlo: una corrida de PR no se repite sola cuando cambia la base, y «re-run» reutiliza la fusión vieja.
        3. Fusionarlo. Ese push deja `dev/<persona>` al día y actualiza el PR hacia `main`.
        4. Fusionar el PR hacia `main` cuando la compuerta pase.
    *   Alternativa que decide el propietario: añadir al administrador como excepción de la regla de PR de `dev/**`, con lo que «Update branch» vuelve a funcionar.
4.  **Un worktree por tarea, con `.env` propio:**
    *   Hay dos carpetas de worktrees y las dos valen: `.worktrees/<tarea>`, creada a mano, y `.claude/worktrees/<tarea>-<hash>`, creada por la aplicación de Claude. Las dos están fuera de git: la primera por `.gitignore`; la segunda, hasta esta decisión, solo por el `.git/info/exclude` local de cada máquina, por lo que se añade también a `.gitignore`.
    *   Al fusionar el PR de una tarea, su worktree se retira en el mismo cierre (`git worktree remove`), igual que se borra su rama Neon temporal. Las ramas de git se conservan.
    *   **La carpeta principal es solo para operar**, no se edita ni se corren pruebas ahí: su `.env` apunta a producción, y los árbitros que recorren el disco desde esa carpeta (`tests/test_adpa_bulkhead.py`, `tests/test_sin_sql_interpolado.py`) analizarían las copias de los worktrees; el 2026-11-01 el recorrido de `test_adpa_bulkhead.py` alcanzaba 398 archivos `.py` dentro de `.claude/worktrees/`.
    *   Cada worktree lleva un `.env` con solo la `TEST_DATABASE_URL` de la rama Neon `test-<persona>`. Nunca se copia el `.env` principal, que apunta a producción; `tests/conftest.py` detiene la suite si falta el `.env` o si alguna URL apunta a producción.
5.  **Cierre honesto de cada proceso:**
    *   La corrida de cierre va en primer plano y como único comando; una suite en segundo plano no es evidencia.
    *   Cuando una investigación no encuentra la causa, se escribe «no se encontró el origen» y las salidas posibles, no una hipótesis disfrazada de hallazgo.
    *   Un commit cierra un proceso; las erratas y los paréntesis no abren uno.
6.  **Archivos de gobernanza compartidos, un solo escritor:**
    *   `governance/artefactos/TASKS.md` y `governance/apoyo/BRIEFS_POR_BLOQUE.md` los tocan varias ramas y chocan a diario. La fuente de verdad son las fichas de `governance/tareas/`, un archivo por tarea; el índice de `TASKS.md` se regenera con `scripts/generar_indice_tareas.py --escribir`.
    *   Regla: los PR de tarea no editan ninguno de los dos. Los edita una sola persona por día, el coordinador, en un PR de gobernanza que cierra la tanda y regenera el índice; los demás cambian solo su ficha. Dos ediciones de gobernanza el mismo día se encadenan, no se cruzan.
7.  **Delegar una tarea a un agente: se hace con un brief:**
    *   Toda tarea que se entrega a un agente (un chat nuevo o un subagente) se encarga con un **brief**, no con una instrucción libre. Un brief es un prompt estructurado de cinco líneas:
        - **Objetivo:** qué se quiere lograr, en una frase.
        - **Alcance:** los archivos que puede tocar, tomados de la `propiedad` de la ficha, y lo que queda fuera.
        - **Hecho es cuando:** el criterio comprobable, es decir, el árbitro de la ficha y el CI.
        - **Límites:** sin commit, push ni PR sin autorización de la propietaria; solo su rama y su worktree; sin credenciales; las bases solo con la rama Neon de pruebas propia.
        - **Informe:** qué hizo, qué comprobó (con SHA y «X de Y terminados, N en curso»), qué supuso, qué no pudo verificar y qué necesita de una persona.
    *   La ficha manda: el brief resume `governance/tareas/<ID>.md` y su bloque de `BRIEFS_POR_BLOQUE.md` y nunca los contradice. Si el agente necesita tocar un archivo fuera de su lista, se detiene y pregunta.
    *   La plantilla está en `governance/Metodología de trabajo en equipo.md`, Parte 8, plantilla 1.

---

## 14. Metodología de Reducción del Tiempo de Verificación: Arnés Local, Alcance por Salas y Una Corrida por Commit
`¤arbitro-arnes` `¤adpa`

Mediciones del 2026-10-30 y 2026-10-31 en este repositorio:

| Corrida | Antes | Después |
| :--- | ---: | ---: |
| Suite completa en el equipo del desarrollador | 48 min 21 s contra Neon | 1 min 40 s contra PostgreSQL local (1509 pruebas) |
| Arnés del CI, cambio confinado al frontend | 19 min 43 s (completo) | 6 min 21 s (por salas, 44 archivos de prueba) |
| Arnés del CI con tres corridas a la vez en la misma rama de Neon | 28 min 45 s | 8 a 11 min cada una, en cola |
| Commit de `dev/<persona>` que también es cabeza de un PR hacia otra rama `dev/` | Dos arneses completos | Uno: el PR adopta la corrida del push |

1.  **Arnés local sobre PostgreSQL local** (`verificadores/arnes_local.py`):
    *   Levanta un servidor local en `127.0.0.1:55432`, crea la base, migra y corre la misma suite. La diferencia de tiempo la pone Neon, con su latencia por consulta y su cómputo compartido, no la suite.
    *   El certificado declara `"base"` y `"alcance"`. No sustituye al CI: no ejercita el pooler ni la latencia real, y solo el certificado completo cierra una sesión.
    *   Instalación sin administrador documentada en `verificadores/README.md`.
2.  **Dos arneses en el CI según el alcance** (`scripts/seleccionar_pruebas.py`):
    *   El job «Alcance de la corrida» clasifica los archivos del PR. `features/<sala>/**`, `api/routers/<r>.py` y `tests/deuda_adpa/<sala>.txt` son de una sala; `frontend/`, `governance/`, `docs/`, `scripts/` y `verificadores/` son zonas; `app_core/`, `api/`, `alembic/`, `main.py`, `conftest.py` y `.github/` son compartidos y corren todo.
    *   «Arnés por salas» corre las pruebas de las salas tocadas, las de las salas que dependen de ellas (también a través de `app_core.pasillo.<sala>`) y el **núcleo**: las pruebas sin sala y las que recorren todo el repositorio (`git ls-files`, `rglob`, `os.walk`, árbitros de `scripts/verificar_*`). Una prueba pertenece a una sala si importa `features.<sala>` o nombra el prefijo HTTP de uno de sus routers.
    *   La mención de una zona en el texto de una prueba **suma** pruebas, nunca saca una del núcleo. Todo push a `dev/<persona>` o a `main` corre el completo.
    *   «Arnés Físico Determinista», el check obligatorio, es una compuerta que pasa solo si el arnés que corrió pasó; un arnés omitido no es un fallo.
3.  **Sin fila ni espera de turno en el CI (CI-17):**
    *   Tanto los PR como el push a `main` usan su propio contenedor PostgreSQL 16 temporal dentro del job, sin compartir base de Neon ni esperar turno.
    *   Un push nuevo al mismo PR cancela la corrida anterior, que ya no sirve.
4.  **Un arnés por commit** (`scripts/corrida_cubierta.py`):
    *   Solo aplica a un PR con cabeza `dev/<persona>`: `on.push` no cubre `tarea/**`, así que un PR de tarea no tiene push que adoptar, corre su arnés y Playwright una sola vez, y aquí no ahorra tiempo. `tarea/**` no se añade a `on.push`: crearía una corrida para luego adoptarla y gastaría otra por cada rama sin PR.
    *   El push a una rama y el PR de esa rama corren sobre el mismo commit. Si la rama está al día con su base, la fusión de prueba del PR tiene el mismo árbol que la cabeza, así que el PR espera la corrida del push y adopta su resultado si pasaron el arnés y Playwright, y omite su Playwright. Si no hubo push, si uno de los dos falló o fue cancelado o si la rama está detrás, el PR corre los suyos.
    *   Un PR hacia `main` nunca adopta: el push de su rama corrió contra el contenedor, y el pooler y la latencia reales solo se comprueban en su corrida propia contra Neon.
5.  **Lo que no se ganó todavía:**
    *   El núcleo son 45 de 118 archivos de prueba y corre siempre; `organizacion` tiene cinco salas dependientes y su arnés por salas se acerca al completo. Ambos mejoran conforme avance el retiro de dependencias laterales (ADR 0001).
    *   Playwright tarda de 6 a 9 min en paralelo: en los PR que no tocan el frontend es lo que marca el total.
6.  **PostgreSQL 16 en contenedor para todo el CI, incluido `main` (CI-17)** (`zero-regression-pipeline.yml`):
    *   El humo y los dos arneses (tanto en PR como en el push a `main`) corren contra un servicio `pgvector/pgvector:pg16` sin secretos, que nace vacío y se migra en un único paso cuya URL es literal y solo puede apuntar al runner (`tests/test_ci_migrar_contenedor.py`, que desde CI-18 reemplaza a `tests/test_verificar_revision_alembic.py`).
    *   Limitación: en el contenedor el rol dueño es superusuario y no le aplica `FORCE ROW LEVEL SECURITY`; RLS lo prueba explícitamente `lopdp_app` en `tests/test_rls_app_role.py`.
7.  **Pytest en paralelo en todo el CI (CI-17)** (`zero-regression-pipeline.yml`):
    *   Tanto los PR como el push a `main` instalan `pytest-xdist` y corren con `-n auto` contra el contenedor; cada trabajador clona su base de la ya migrada (`tests/conftest.py`).
    *   Medición del 2026-11-02 en el arnés completo del CI: en serie, 75,66 s de Pytest y 1775 aprobadas + 25 omitidas (1800); con 4 trabajadores, 46,52 s y 1776 aprobadas + 25 omitidas (1801, una más por la prueba de esta condición). El paso completo baja de 79 s a 48 s.

**Comandos:**

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py --base origin/dev/juan-carlos
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" scripts\seleccionar_pruebas.py --mapa
```

---

## 15. Procedimiento por Colaborador y por Chat: Worktree, Rama, `.env` y PR
`¤coordinacion` `¤arbitro-arnes`

Vale para Juan Carlos, Aleczandra, José y para todo chat que trabaje en nombre de uno de ellos. Un chat lo sigue en su propio worktree y no se salta ningún paso; donde dice `<persona>` va `juan-carlos`, `aleczandra` o `jose`, y donde dice `<id>` va el identificador de la ficha en minúsculas (`rat-07`, `bib-402`). Los comandos se pegan tal cual desde la **carpeta principal del clon**; en Windows van en PowerShell, en Mac o Linux en la terminal.

1.  **Una sola vez por máquina:**
    *   Tener el clon actualizado y, con el PR de GOB-04, `.gitignore` con `.worktrees/` y `.claude/worktrees/`. Antes de eso, la carpeta de la aplicación de Claude solo estaba ignorada en la máquina de Juan Carlos.
    *   Tener la rama Neon `test-<persona>` y su cadena de conexión (`governance/operaciones/RAMAS_NEON_DE_DESARROLLO.md`). Para el arnés rápido, PostgreSQL local según `verificadores/README.md`; es opcional, el CI sigue siendo el árbitro.
    *   **La carpeta principal del clon no se edita y no corre pruebas.** Sirve para `git fetch`, `git worktree` y, en quien migra producción, para migrar. Su `.env` puede apuntar a producción, y los árbitros que recorren el disco verían ahí las copias de los worktrees.
2.  **Al empezar una tarea, persona o chat:**
    *   La tarea tiene ficha en `governance/tareas/<ID>.md` con su `propiedad`; el chat escribe solo dentro de ella y no toca `TASKS.md` ni `BRIEFS_POR_BLOQUE.md`.
    *   La rama parte de la punta remota de `main`, nunca de la copia local (hasta el 2026-11-05 partía de `origin/dev/<persona>`):

        ```powershell
        git fetch origin; git worktree add ".worktrees\<id>" -b "tarea/<persona>/<id>" "origin/main"
        ```

        ```bash
        git fetch origin && git worktree add ".worktrees/<id>" -b "tarea/<persona>/<id>" "origin/main"
        ```

        Si el worktree lo crea la aplicación de Claude, queda en `.claude/worktrees/<id>-<hash>`; vale igual, con la misma rama de origen.
    *   En el worktree se crea un `.env` a mano con solo las variables de pruebas de `test-<persona>`. Nunca se copia ni se enlaza el `.env` principal. Antes de correr nada, la comprobación de `RAMAS_NEON_DE_DESARROLLO.md` §5: si falta el `.env` o contiene el host de producción, se detiene.
3.  **Mientras se trabaja, desde el worktree:**
    *   Verificación corta: `python verificadores/arnes_local.py --base origin/main` (con PostgreSQL local) o `ejecutar_arnes_tres_pilares.bat` (contra Neon). En Mac o Linux, `python verificadores/arnes_local.py` con la ruta de PostgreSQL en `LOPDP_PG_DIR`.
    *   Un commit por proceso cerrado; sin `--no-verify`; sin `git stash`, porque el stash es común a todos los worktrees; sin datos reales ni credenciales en ningún archivo; `.agents/` no se versiona.
4.  **Al cerrar la tarea:**
    *   Suite completa en primer plano y como único comando: `python verificadores/arnes_local.py`. Con salida distinta de 0 no se abre el PR.
    *   `git push -u origin tarea/<persona>/<id>` y PR hacia `main` (hasta el 2026-11-05, hacia `dev/<persona>`). El nombre de la rama lleva el `<id>` para que `scripts/verificar_alcance_pr.py` encuentre la ficha. Entra con la compuerta «Arnés Físico Determinista» en verde.
    *   Si la tarea trae migración, antes de fusionar se trae `main` y se corre `alembic heads`; con más de una cabeza se reencadena o se añade una migración de fusión según `governance/operaciones/FUSION_ALEMBIC.md`, y se avisa en el PR.
    *   Fusionado el PR, el worktree se retira en el mismo cierre, desde la carpeta principal: `git worktree remove ".worktrees\<id>"` en Windows, `git worktree remove ".worktrees/<id>"` en Mac o Linux. La rama de git se conserva; la rama Neon temporal, si la hubo, se borra.
5.  **Al cerrar la jornada, cada persona:**
    *   Desde el 2026-11-05 no hay PR nocturno: cada tarea ya entró a `main` por su PR. Si `main` avanzó mientras el PR estaba abierto, «Update branch» sí funciona en `tarea/**` y repite solo la corrida corta del PR.
    *   Toda tarea nueva del día siguiente parte de `origin/main`.
    *   *(Hasta el 2026-11-05:)* PR de `dev/<persona>` hacia `main`, con el CI en verde; cuando los tres habían entrado, PR de `main` hacia cada `dev/<persona>`; «Update branch» no servía en `dev/**`.
6.  **Comprobación de que un worktree cumple el procedimiento**, desde el worktree; las tres líneas deben imprimir `ok`:

    ```powershell
    git fetch origin; if ((git branch --show-current) -like "tarea/*") { "ok rama" } else { "NO: la rama no es tarea/<persona>/<id>" }; git merge-base --is-ancestor "origin/main" HEAD; if ($LASTEXITCODE -eq 0) { "ok punta remota" } else { "NO: la rama no parte de la punta de origin/dev/<persona>" }; if ((Test-Path .env) -and -not (Select-String -Path .env -Pattern 'ep-late-hall' -Quiet)) { "ok .env" } else { "NO: falta el .env propio o apunta a produccion" }
    ```

    ```bash
    git fetch origin; r=$(git branch --show-current); case "$r" in tarea/*) echo "ok rama";; *) echo "NO: la rama no es tarea/<persona>/<id>";; esac; if git merge-base --is-ancestor "origin/main" HEAD; then echo "ok punta remota"; else echo "NO: la rama no parte de la punta de origin/dev/<persona>"; fi; if [ -f .env ] && ! grep -q 'ep-late-hall' .env; then echo "ok .env"; else echo "NO: falta el .env propio o apunta a produccion"; fi
    ```

    La segunda línea es el «punto de unión» de la directriz: la rama contiene la punta remota actual de `dev/<persona>`. Si imprime `NO` es porque esa punta avanzó desde que se abrió la rama, lo normal cuando otros chats fusionan durante el día; el remedio es traerla y repetir el arnés, no abrir otra rama:

    ```powershell
    git fetch origin; git merge --no-edit origin/main
    ```

    ```bash
    git fetch origin && git merge --no-edit origin/main
    ```

    El coordinador repite la comprobación al integrar cada PR. Se devuelve la rama que, tras traer la punta, no pasa el arnés, trae conflictos que su autor no resolvió o contiene commits que no son suyos ni de `dev/<persona>`. El 2026-11-01 la propia rama de GOB-04 imprimió `NO` al terminar su redacción, porque `dev/juan-carlos` había recibido dos PR entre tanto; se trajo la punta y se repitió la suite.
