+++
id = "RAT-08"
titulo = "Área responsable del tratamiento como referencia al área de la organización"
ola = "backlog"
estado = "pendiente"
sala = "rat, frontend"
depende_de = ["RAT-01", "RAT-05", "RAT-02", "RAT-06", "API-01", "RAT-07"]
propiedad = ["alembic/versions/rat08_area_id.py", "tests/test_rat08_area_id.py", "frontend/src/types/rat_area.ts", "features/rat/domain/models.py", "features/rat/services/rat_engine.py", "api/routers/rat.py", "frontend/src/components/modules/RatModule.tsx", "features/rat/rat_service.py#RAT-08", "app_core/pasillo/organizacion.py#RAT-08"]
crea = ["alembic/versions/rat08_area_id.py", "tests/test_rat08_area_id.py", "frontend/src/types/rat_area.ts"]
arbitro = "pytest tests/test_rat08_area_id.py contra PostgreSQL 16 local + alembic heads con una sola cabeza + tsc --noEmit; mutaciones m1 a m3"
rastros = ["¤rat"]
+++

# RAT-08 · Área responsable del tratamiento como referencia al área de la organización

Decisión del CTO (2026-11-13), en backlog y sin urgencia. Hoy `area_responsable` del RAT es texto libre (`features/rat/domain/models.py:53`, `str = ""`), así que no se puede derivar de forma fiable qué personas tienen tratamientos asignados.

## Entrega
- `rat_actividades.area_id` como FK a las áreas de organización (por su compuerta), con migración de datos que empareja por nombre (en minúsculas y sin espacios en los extremos) y deja `NULL` lo que no case; `area_responsable` se conserva como texto mientras haya filas sin emparejar.
- Migración sin fecha, con FUSION_ALEMBIC.
- Cuando exista, FOR-01 o una ficha hija puede afinar el denominador de la cobertura por área.

## Mutaciones
m1 emparejar sin normalizar mayúsculas → falla la prueba de emparejado; m2 inventar un área para un texto que no casa → falla; m3 borrar `area_responsable` con filas sin emparejar → falla.

**Medición del Arquitecto (2026-11-13).** FK compuesta `(area_id, tenant_id)` a las áreas de organización; `area_responsable` se conserva. La migración empareja por `lower(trim)` solo si la coincidencia es única e imprime los recuentos (emparejadas, sin emparejar, ambiguas). Se ordena después de RAT-07, que toca los mismos archivos del RAT.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#RAT-08` (ADR 0001).

## Textos cerrados por UX/UI (2026-11-15)
Diseñados sobre el brief del Arquitecto (§4 de su especificación, PR #818); UX/UI no leyó el PR ni corrió pantalla.

**Selector.** `<select>` nativo con etiqueta visible «Área responsable», obligatorio y con las opciones ordenadas por nombre. Primera opción sin valor: «Elige un área». Ayuda: «Las áreas son las de la estructura de tu organización.» Error al guardar sin elegir: «Elige el área responsable.» Si una organización pasa de 15 áreas se valora un buscador en otra ficha. El valor inicial deja de ser «Contabilidad y Finanzas».

**Respaldo.** (a) Tratamiento existente sin área enlazada, con áreas en la organización: texto de solo lectura «Área registrada: {area_responsable}» y, debajo, el botón con estilo de enlace «Elegir un área de la organización»; al pulsarlo aparece el selector con el foco y la línea «Al guardar, el tratamiento queda enlazado al área que elijas.» El texto antiguo no se borra hasta guardar. (b) Organización sin áreas: campo de texto «Área responsable», con la nota (role=note) «Tu organización aún no tiene áreas registradas. Puedes escribir el área a mano por ahora.»; al administrador se le añade «Registrar las áreas de la organización» solo si esa pantalla existe.

**Tabla.** Siempre muestra `area_responsable`. Decide el Arquitecto si el backend sincroniza `area_responsable` al renombrar un área; si no, la tabla muestra el nombre antiguo hasta volver a guardar el tratamiento.

**422 AREA_NO_VALIDA.** «El área elegida ya no está disponible. Elige otra.», como error del campo (aria-invalid y aria-describedby), y se vuelve a cargar la lista de áreas. Nunca el texto del servidor.

**Estados del selector.** Cargando: aria-busy y aria-disabled, con la opción «Cargando las áreas…». Error al cargar: role=alert «No pudimos cargar las áreas de tu organización.» con el botón «Volver a cargar las áreas», y mientras tanto se aplica el respaldo (a) o (b). Otros errores al guardar: «No pudimos guardar el tratamiento. Inténtalo de nuevo.» 401: manejo global.

**Accesibilidad para Playwright.** `getByRole("combobox", { name: "Área responsable" })` · `getByRole("button", { name: "Elegir un área de la organización" })` · `getByRole("textbox", { name: "Área responsable" })` · `getByText("El área elegida ya no está disponible. Elige otra.")`. Contraste 4.5:1, solo tokens del tema, sin ¤ ni ¦, y a 375 px el selector ocupa el ancho del formulario.

**Criterios de prueba añadidos.** (1) Con áreas, el formulario nuevo muestra el selector en «Elige un área» y ningún texto «Contabilidad y Finanzas». (2) Un tratamiento sin área muestra «Área registrada: …» y el botón; al pulsarlo aparece el selector con el foco. (3) Sin áreas: campo de texto y la nota. (4) Un 422 AREA_NO_VALIDA simulado muestra el texto fijo y recarga la lista. (5) Las opciones están ordenadas por nombre.

**Migración.** `uq_areas_id_tenant` y `rat08_area_id` sin fecha, con FUSION_ALEMBIC (Arquitecto). La ficha va detrás de RAT-07 (hecha). Se lanza cuando la especificación (#818) esté en main.
