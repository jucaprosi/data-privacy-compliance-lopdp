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
    *   `tarea/<persona>/<id>` → PR hacia `dev/<persona>` → desde las 19:00, PR de `dev/<persona>` hacia `main`. Producción se despliega de noche desde `produccion`.
    *   `main` exige que la rama esté al día; `dev/**` exige que todo cambio entre por PR. Consecuencia: el botón **«Update branch» no funciona en `dev/<persona>`**, porque es un push directo, y cada vez que `main` avanza hay que traerlo por PR.
    *   Pasos cuando `main` avanzó y el PR de `dev/<persona>` queda «out of date»:
        1. Abrir, o reutilizar, el PR de `main` hacia `dev/<persona>`.
        2. Si su última corrida es anterior a un arreglo ya fusionado en `dev/<persona>`, cerrarlo y reabrirlo: una corrida de PR no se repite sola cuando cambia la base, y «re-run» reutiliza la fusión vieja.
        3. Fusionarlo. Ese push deja `dev/<persona>` al día y actualiza el PR hacia `main`.
        4. Fusionar el PR hacia `main` cuando la compuerta pase.
    *   Alternativa que decide el propietario: añadir al administrador como excepción de la regla de PR de `dev/**`, con lo que «Update branch» vuelve a funcionar.
4.  **Un worktree por tarea, con `.env` propio:**
    *   Cada worktree lleva un `.env` con solo la `TEST_DATABASE_URL` de la rama Neon `test-<persona>`. Nunca se copia el `.env` principal, que apunta a producción; `tests/conftest.py` detiene la suite si falta el `.env` o si alguna URL apunta a producción.
5.  **Cierre honesto de cada proceso:**
    *   La corrida de cierre va en primer plano y como único comando; una suite en segundo plano no es evidencia.
    *   Cuando una investigación no encuentra la causa, se escribe «no se encontró el origen» y las salidas posibles, no una hipótesis disfrazada de hallazgo.
    *   Un commit cierra un proceso; las erratas y los paréntesis no abren uno.

---

## 14. Metodología de Reducción del Tiempo de Verificación: Arnés Local, Alcance por Salas y Una Corrida por Commit
`¤arbitro-arnes` `¤adpa`

Mediciones del 2026-10-30 y 2026-10-31 en este repositorio:

| Corrida | Antes | Después |
| :--- | ---: | ---: |
| Suite completa en el equipo del desarrollador | 48 min 21 s contra Neon | 1 min 40 s contra PostgreSQL local (1509 pruebas) |
| Arnés del CI, cambio confinado al frontend | 19 min 43 s (completo) | 6 min 21 s (por salas, 44 archivos de prueba) |
| Arnés del CI con tres corridas a la vez en la misma rama de Neon | 28 min 45 s | 8 a 11 min cada una, en cola |
| Commit de `dev/<persona>` que también es cabeza de un PR hacia `main` | Dos arneses completos | Uno: el PR adopta la corrida del push |

1.  **Arnés local sobre PostgreSQL local** (`verificadores/arnes_local.py`):
    *   Levanta un servidor local en `127.0.0.1:55432`, crea la base, migra y corre la misma suite. La diferencia de tiempo la pone Neon, con su latencia por consulta y su cómputo compartido, no la suite.
    *   El certificado declara `"base"` y `"alcance"`. No sustituye al CI: no ejercita el pooler ni la latencia real, y solo el certificado completo cierra una sesión.
    *   Instalación sin administrador documentada en `verificadores/README.md`.
2.  **Dos arneses en el CI según el alcance** (`scripts/seleccionar_pruebas.py`):
    *   El job «Alcance de la corrida» clasifica los archivos del PR. `features/<sala>/**`, `api/routers/<r>.py` y `tests/deuda_adpa/<sala>.txt` son de una sala; `frontend/`, `governance/`, `docs/`, `scripts/` y `verificadores/` son zonas; `app_core/`, `api/`, `alembic/`, `main.py`, `conftest.py` y `.github/` son compartidos y corren todo.
    *   «Arnés por salas» corre las pruebas de las salas tocadas, las de las salas que dependen de ellas (también a través de `app_core.pasillo.<sala>`) y el **núcleo**: las pruebas sin sala y las que recorren todo el repositorio (`git ls-files`, `rglob`, `os.walk`, árbitros de `scripts/verificar_*`). Una prueba pertenece a una sala si importa `features.<sala>` o nombra el prefijo HTTP de uno de sus routers.
    *   La mención de una zona en el texto de una prueba **suma** pruebas, nunca saca una del núcleo. Todo push a `dev/<persona>` o a `main` corre el completo.
    *   «Arnés Físico Determinista», el check obligatorio, es una compuerta que pasa solo si el arnés que corrió pasó; un arnés omitido no es un fallo.
3.  **Una corrida a la vez por rama de Neon** (`scripts/esperar_turno_neon.py`):
    *   Las corridas que comparten `test-<persona>` se reparten el cómputo de Neon. Cada arnés espera, por orden de llegada, a que terminen los de las corridas anteriores de la misma persona; la `concurrency` nativa de GitHub solo guarda una en espera y cancela la siguiente.
    *   Un push nuevo a la misma rama o al mismo PR cancela la corrida anterior, que ya no sirve. El ahorro neto viene de ahí; la cola reparte el tiempo, no lo reduce en total.
4.  **Un arnés por commit** (`scripts/corrida_cubierta.py`):
    *   El push a `dev/<persona>` y el PR de esa rama hacia `main` corren sobre el mismo commit. Si la rama está al día con `main`, la fusión de prueba del PR tiene el mismo árbol que la cabeza, así que el PR espera la corrida del push y adopta su resultado si pasó. Si no hubo push, falló, fue cancelado o la rama está detrás, el PR corre el suyo.
5.  **Lo que no se ganó todavía:**
    *   El núcleo son 45 de 118 archivos de prueba y corre siempre; `organizacion` tiene cinco salas dependientes y su arnés por salas se acerca al completo. Ambos mejoran conforme avance el retiro de dependencias laterales (ADR 0001).
    *   Playwright tarda de 6 a 9 min en paralelo: en los PR que no tocan el frontend es lo que marca el total.
    *   El mayor ahorro posible sigue pendiente de decisión: un PostgreSQL en contenedor dentro del CI corrió la suite completa en 46 s en un ensayo (PR #252, cerrado sin fusionar).

**Comandos:**

```powershell
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" verificadores\arnes_local.py --base origin/dev/juan-carlos
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" scripts\seleccionar_pruebas.py --mapa
```
