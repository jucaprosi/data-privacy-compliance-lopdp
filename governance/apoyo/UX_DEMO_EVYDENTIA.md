# Demo comercial EVYDENTIA — cambios de UX/UI frente a la demo del PMV (DEMO-04)

UX/UI de EVYDENTIA · 2026-11-07 · Fuentes: PRD_EVYDENTIA_REVENTA_NUBE.md §5.5 y §5.6 (PR #435, rama `tarea/juan-carlos/prd-evydentia-demo`); FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1 (Arquitecto ADPA). Antecedente: `governance/apoyo/UX_DEMO_COMERCIAL.md`. **Todo lo que no se cita aquí sigue igual que en el antecedente.**

Nota: en `origin/main` todavía no existe el aviso de EP-02 ni `GET /api/v1/entorno` en el frontend. Esta especificación define el componente común; la tarea que lo construya primero (EP-02 o DEMO-04) lo crea y la otra lo reutiliza.

## 1. Aviso de entorno común (EP-02) y su variante «demo»

Un solo componente `AvisoEntorno`, montado en `app/layout.tsx` encima del `DashboardHeader`.

**Cuándo se pinta.** Se llama a `GET /api/v1/entorno` al montar.
- `entorno = production`, o la llamada falla: no se pinta nada. Ante la duda no se muestra el aviso, porque un aviso de "datos ficticios" en producción sería grave.
- `entorno = pruebas`: variante «pruebas».
- `entorno = demo`: variante «demo». Además se llama a `GET /api/v1/demo/estado`; si responde 404 o 401, la franja se pinta sin las piezas de demo.
- `NEXT_PUBLIC_APP_ENV` solo sirve para la primera pintura, sin parpadeo. Manda siempre la respuesta del servidor.

| Variante | Texto | Color | Piezas a la derecha |
|---|---|---|---|
| pruebas | «Entorno de pruebas · datos ficticios» | Azul pizarra (fondo `#E8EEF7` / oscuro `#16233A`, texto `#1F3A64` / `#A9C2E8`), icono `FlaskConical` | Ninguna |
| demo | «Demostración · datos ficticios» · «Cooperativa Demo» | Ámbar (fondo `#FFF4D6` / oscuro `#3A2E10`, texto `#7A5A00` / `#F5D27A`), icono `Presentation` | Selector «Ver como» y botón texto «Terminar demo» |

- Colores distintos a propósito: quien prueba y quien vende no deben confundir los dos entornos en una captura.
- Los dos tonos son suaves; el rojo queda solo para errores.
- Alto de 32 px, fija, no se puede cerrar, con `role="status"`.

**Espacio previsto para la cuenta profesional (§5.6.6).** El hueco del cambio de organización queda entre el nombre de la organización y el selector: `[Organización ▾]`. En esta entrega no se pinta. El nombre de la organización se muestra como texto plano dentro de un contenedor `data-slot="organizacion"`, que en la fase siguiente se convertirá en un desplegable de cartera (dos organizaciones) sin mover nada más. El `SelectorOrganizacion` actual del encabezado no se toca.

**Pantallas estrechas**

| Ancho | Franja demo |
|---|---|
| ≥ 1024 px | Texto completo · organización · «Ver como: Nombre · Rol» · «Terminar demo» |
| 640–1023 px | «Demostración · datos ficticios» · avatar con iniciales y rol corto («DPO») · icono `LogOut` con la etiqueta accesible «Terminar demo» |
| < 640 px | Icono y «Demo · ficticio» · avatar. «Terminar demo» pasa al final del panel «Ver como» |

- La regla en pantallas estrechas: primero se acorta el texto del aviso, después se oculta la organización. El texto de datos ficticios y el selector nunca desaparecen.

## 2. «Ver como» con seis personas

Orden fijo, de acuerdo con el ciclo que se enseña: Administrador de la organización, DPO, Coordinador, Implementador, Responsable de área, Auditor. El primero es la persona de arranque; los demás siguen el ciclo.

| Rol (`rol_etiqueta` del servidor) | Línea que muestra el panel |
|---|---|
| Administrador de la organización | Configura la organización y sus unidades, designa al DPO y al coordinador y asigna los dominios. |
| DPO | Supervisa con independencia: reúne el soporte del diagnóstico, lo sella y valida la evidencia. |
| Coordinador | Reparte las tareas a las áreas y hace la primera validación de la evidencia. |
| Implementador | Acompaña el RAT, la Biblioteca y el plan de acción. |
| Responsable de área · *Unidad* | Responde los dominios de su unidad, ejecuta sus tareas y carga la evidencia. |
| Auditor | Audita por dominio, levanta actas por área y verifica las acciones correctivas. |

Textos propuestos por el CTO, alineados con el §3 del PRD EVYDENTIA y con el art. 48 de la LOPDP (independencia del DPO). **Validados por el propietario el 2026-11-07, incluida la versión del DPO que dice «reúne el soporte».** Los cuatro ojos son el coordinador y el DPO; el responsable de área no aprueba el cierre de sus propias tareas.

- Si el servidor envía la unidad, se añade después del rol con un punto medio («Responsable de área · Talento Humano»).
- La línea descriptiva vive en un diccionario del frontend, indexado por `rol`. Textos validados (ver tabla).
- Pie del panel, como enlace clicable: «Recorrido sugerido: Responsable de área → Coordinador → DPO → Auditor», que sigue los cuatro ojos. Al pulsarlo cambia a la persona Responsable de área.
- El panel mide 360 px. Con seis filas sigue sin scroll (unos 420 px de alto); por debajo de 640 px se abre como hoja inferior.
- Los estados (cambiando, error 403 DEMO_PERSONA_AJENA, otros errores) no cambian frente al antecedente.

## 3. «Terminar demo»

Igual que en el antecedente. El aviso posterior, en la entrada, es literal: «La demo se cerró y sus datos se eliminan esta noche».

## 4. Errores: se añade el 503

| Código | Dónde | Título | Acción |
|---|---|---|---|
| 503 DEMO_NO_DISPONIBLE | Entrada, en línea, en el lugar del panel de progreso | «No pudimos preparar la demo; intenta de nuevo» (literal) | «Intentar de nuevo», activo de inmediato, que repite `POST /demo/entrar` |

- Los otros cuatro (403 DEMO_NO_AUTORIZADO, 409 DEMO_OCUPADA, 401 DEMO_VENCIDA y 403 DEMO_PERSONA_AJENA) siguen igual, con el texto literal del PRD.
- Si el 503 se repite tres veces seguidas, se añade una línea: «Si el problema sigue, avisa al equipo de EVYDENTIA».

## 5. Entrada: carga más larga

La copia ahora incluye diagnóstico, hoja de ruta, biblioteca, evidencias y clips. El panel de progreso es cualitativo, sin porcentajes ni barra con fin:

1. «Creando la Cooperativa Demo y sus dos unidades»
2. «Preparando a las seis personas»
3. «Copiando el diagnóstico y la hoja de ruta»
4. «Cargando documentos y evidencias»
5. «Abriendo la plataforma como Administrador»

- Lista de pasos con su icono: el paso en curso gira y los anteriores muestran un check.
- El backend responde una sola vez, al final, así que el avance es por tiempo: un paso cada ~3 s. El último se queda en curso hasta el 201.
- El orden copia la secuencia real del Arquitecto (§1.1) para no prometer algo falso.
- Con más de 20 s: «Está tardando un poco más de lo habitual».
- Con más de 60 s: se corta la espera y se muestra el 503 (DEMO_NO_DISPONIBLE).
- Con 201: toast «Estás viendo la plataforma como Administrador de la organización. Cambia de persona en “Ver como”.»

## 6. Criterios de aceptación nuevos o cambiados (Playwright)

1. Con `entorno=production` no existe `[data-testid=aviso-entorno]`; si `/api/v1/entorno` falla, tampoco.
2. Con `entorno=pruebas`: texto «Entorno de pruebas · datos ficticios», sin selector ni «Terminar demo».
3. Con `entorno=demo`: texto «Demostración · datos ficticios», selector con 6 personas en el orden del §2 y la unidad visible en Responsable de área.
4. Con viewport de 375 px: el aviso y el selector son visibles y «Terminar demo» se alcanza desde el panel.
5. 503 DEMO_NO_DISPONIBLE: se muestra el texto literal y «Intentar de nuevo» repite la entrada.
6. `[data-slot=organizacion]` existe y no es interactivo.
7. Siguen vigentes los criterios del antecedente (sin `.invalid`, sin tokens de gobernanza, prueba de dos pestañas).
