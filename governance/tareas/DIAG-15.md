+++
id = "DIAG-15"
titulo = "Textos sin jerga en DiagnosticCanvas (Poka-Yoke, timebox y etiqueta de la huella) y retiro de su excepción en FE-28"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["EVI-01", "DIAG-07", "DIAG-11", "FE-28", "DIAG-14"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx", "frontend/tests/textos/excepciones/DIAG-15.txt"]
arbitro = "npx playwright test frontend/tests/textos/sin-jerga.spec.ts + pytest tests/test_fe28_textos_sin_jerga.py + suites del diagnóstico; la lista de excepciones baja"
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# DIAG-15 · Textos sin jerga en DiagnosticCanvas

**Origen.** Nota del Arquitecto ADPA al validar FE-28 (2026-11-08). En `DiagnosticCanvas.tsx` quedan tres textos fuera de las secciones vivas (EVI-01, DIAG-07 y DIAG-11), así que hoy ninguna ficha puede corregirlos legalmente:
- l.615: `title="Temporizador Poka-Yoke: Cota de 60 minutos"`;
- l.616: «timebox» → «tiempo restante»;
- l.1164: la etiqueta de la huella → «Huella de integridad (SHA-256)».

FE-28 los deja en `frontend/tests/textos/excepciones/DIAG-15.txt`. Esta ficha posee ese archivo y `DiagnosticCanvas.tsx`, no el spec ni la prueba estática de FE-28.

## Cuándo se abre
Cuando EVI-01, DIAG-07 y DIAG-11 estén hechas: toma el archivo entero. Si antes hace falta, se cambia por un andamiaje que siembre una sección para estos textos. No se abre todavía.

## Entrega
1. Los tres textos, con las redacciones de arriba (el `title` de la l.615 dice qué mide el temporizador, sin «Poka-Yoke»).
2. Borra `frontend/tests/textos/excepciones/DIAG-15.txt`.

## No hagas
- No cambies lógica del diagnóstico: solo textos.

**Textos pendientes de DIAG-11 (UX/UI, 2026-11-09).** En `DiagnosticCanvas.tsx`, fuera de la sección `#DIAG-11`: (a) después del sello real, «Revisar Respuestas» pasa a «Ver respuestas» (~l.1365); (b) la fecha del sello deja `toLocaleString()` y pasa a `toLocaleString("es-EC", { dateStyle: "short", timeStyle: "short" })` (~l.1273).
