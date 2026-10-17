+++
id = "TEST-02"
titulo = "Reparar el arnés de Playwright de la raíz y valorar ejecutarlo en el CI"
ola = "indep"
estado = "pendiente"
sala = "pruebas"
depende_de = []
propiedad = ["frontend/tests/utiles.ts", "frontend/tests/fixtures.ts", "frontend/tests/assessmentDashboard.spec.ts", "frontend/tests/commandPalette.spec.ts", "frontend/tests/exampleWithAudit.spec.ts"]
arbitro = "npx playwright test tests/assessmentDashboard.spec.ts tests/commandPalette.spec.ts tests/exampleWithAudit.spec.ts y npx playwright test tests/roadmap, con código 0"
rastros = ["¤arbitro", "¤frontend-ide"]
+++

# TEST-02 · Reparar el arnés de Playwright de la raíz y valorar ejecutarlo en el CI

**Objetivo.** Desde el commit `c92490e` («perfil de operación obligatorio») la ficha exige responder todas las preguntas del perfil, y `configurarProyecto` de `frontend/tests/utiles.ts` solo rellena la razón social: las pruebas que lo usan fallan al preparar el proyecto: `assessmentDashboard.spec.ts` (5 casos) y `commandPalette.spec.ts` (2 casos), medido el 2026-10-16. La tercera, `exampleWithAudit.spec.ts`, no falla: todos sus casos llevan `test.skip` a propósito (son demostraciones). No se vio porque el CI solo ejecuta `typecheck` y `build` del frontend.

## Entrega
- Un helper que complete la ficha como hoy la exige la interfaz (los grupos de respuesta Sí/No del perfil).
- `assessmentDashboard.spec.ts` y `commandPalette.spec.ts` en verde sin debilitar sus aserciones.
- Decidir qué hacer con `exampleWithAudit.spec.ts`: activar sus demostraciones si aportan, o retirarlas; deja la decisión razonada en el informe.
- Propuesta de un job de Playwright para el CI como parche para el propietario (el workflow es de gobernanza reservada), con el tiempo medido y lo que habría que instalar; no toques `.github/`.
- Si `frontend/tests/roadmap/integracion.spec.ts` puede reutilizar el helper en lugar de su copia, propón el cambio en el informe; ese archivo no es de tu propiedad.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
