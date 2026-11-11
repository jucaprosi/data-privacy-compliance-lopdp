+++
id = "DIAG-07c"
titulo = "La interfaz y sus specs guardan las respuestas del diagnóstico como administrador"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["DIAG-07a", "EVI-01b"]
propiedad = ["frontend/src/lib/diagnostico/roles.ts", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/src/components/DiagnosticCanvas.tsx#DIAG-07c", "frontend/tests/diagnostico/simulador.ts", "frontend/tests/diagnostico/escala.spec.ts", "frontend/tests/diagnostico/escala-activa.spec.ts", "frontend/tests/diagnostico/no-aplica.spec.ts", "frontend/tests/diagnostico/persistencia.spec.ts", "frontend/tests/diagnostico/prueba-y-real.spec.ts", "frontend/tests/diagnostico/sellado.spec.ts", "frontend/tests/diagnostico/guardar-como-admin.spec.ts"]
crea = ["frontend/tests/diagnostico/guardar-como-admin.spec.ts"]
arbitro = "Playwright frontend/tests/diagnostico/guardar-como-admin.spec.ts (el administrador ve los controles de respuesta habilitados y guarda; el implementador los ve deshabilitados) + los specs migrados en verde + tsc --noEmit + npm run build; mutación documentada: volver a puedeSellar(roles) en la línea de puedeResponder de DiagnosticCanvas.tsx deja los controles del administrador deshabilitados y la prueba falla"
rastros = ["¤diagnostico"]
+++

# DIAG-07c · La interfaz y sus specs guardan las respuestas del diagnóstico como administrador

Partida el 2026-11-11 por el Arquitecto ADPA de DIAG-07 en expandir y contraer; orden: DIAG-07a → (DIAG-07b y DIAG-07c, en paralelo) → DIAG-07 → NEON-02. Borrador completo en la conversación del Arquitecto; lo que sigue es la entrega medida sobre origin/main d13d3bd6 por lectura.

## Entrega
- `roles.ts` añade `puedeGuardarRespuestas(roles)` (dpo o administrador, transitoria) sin cambiar `puedeSellar`. `clienteRespuestas.ts` y la línea `const puedeResponder = roles !== null && puedeSellar(roles)` de `DiagnosticCanvas.tsx` usan la nueva función.
- La línea de `DiagnosticCanvas.tsx` se envuelve en el mismo PR con las marcas `// === DIAG-07c ===` / `// === fin DIAG-07c ===`; la sección va como exención propia (`DIAG-07c|frontend/src/components/DiagnosticCanvas.tsx#DIAG-07c`) porque el archivo tiene muchas dueñas vivas (EVI-01, DIAG-04, DIAG-07, DIAG-15 y FE-27).
- Los specs que solo siembran respuestas pasan a `roles: ["admin_organizacion"]` (los de `frontend/tests/diagnostico` con `roles: ["dpo"]`: escala, escala-activa, no-aplica, persistencia, prueba-y-real, sellado y solo-dpo; vuelve a medir la lista al empezar, la de aquí es el mínimo). No toca `solo-dpo.spec.ts`: su asunto es el cambio y lo reescribe DIAG-07.
- Sin cambio visible para el DPO: no pasa por UX/UI. Los textos de «solo el DPO» los reescribe DIAG-07.
