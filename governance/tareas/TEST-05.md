+++
id = "TEST-05"
titulo = "Medir pruebas redundantes y consolidarlas sin perder cobertura ni mutaciones detectadas"
ola = "indep"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["scripts/medir_redundancia_pruebas.py", "tests/test_medir_redundancia_pruebas.py", "governance/operaciones/CONSOLIDACION_PRUEBAS.md"]
arbitro = "pytest tests/test_medir_redundancia_pruebas.py + suite completa; el informe CONSOLIDACION_PRUEBAS.md lista, por sala, las pruebas pytest candidatas con su cobertura y sus mutaciones exclusivas, y los specs de Playwright con su duración y las rutas que recorren"
rastros = ["¤arbitro"]
+++

# TEST-05 · Consolidar pruebas redundantes

**Origen.** Pregunta del propietario del 2026-11-07: ¿se pueden consolidar las pruebas que son parches de otras anteriores? La suite completa tiene unas 2440 pruebas. Varias fichas sumaron pruebas sobre el mismo invariante (por ejemplo, «`lopdp_app` no puede borrar» en cada tabla nueva), y otras quedaron superadas por una prueba más completa.

**Cuándo (decisión del CTO, 2026-11-07).** TEST-05 va ya, en la tanda 30 junto a SEC-18: solo mide y tiene tres archivos nuevos. Las fichas de consolidación (TEST-05a, 05b…) van después de las salas de la Etapa I, porque tocan archivos `tests/` que esas fichas todavía escriben.

**Dónde está el tiempo.** En la primera corrida de `main` sin Neon (42422811800), pytest completo tardó 69 s y Playwright Frontend 9 min 29 s. Consolidar pytest mejora el mantenimiento, pero el tiempo está en Playwright.

## Entrega (esta ficha solo mide; no borra pruebas)
- `scripts/medir_redundancia_pruebas.py`:
  1. Corre la suite con cobertura por contexto de pytest (`--cov-context=test`) y, para cada prueba, obtiene el conjunto de líneas que cubre.
  2. Marca como **candidata** una prueba cuyas líneas cubiertas están contenidas en las de otra prueba de la misma sala.
  3. Sobre las candidatas, corre mutación acotada a esas líneas y registra qué mutaciones detecta **solo** la candidata.
  4. **Playwright:** a partir del reporte de una corrida, obtiene la duración de cada spec y las pantallas o rutas que recorre (`page.goto` y navegación). Marca los specs que repiten el mismo recorrido. En Playwright no se corre mutación, porque es cara: basta con la duración y el solapamiento de rutas.
- `governance/operaciones/CONSOLIDACION_PRUEBAS.md`: el informe por sala, con las candidatas, la prueba que las contiene, las mutaciones exclusivas y una recomendación (retirar, fusionar o conservar).

## Criterio
- **Se puede retirar o fusionar:** una candidata sin mutaciones exclusivas.
- **Se conserva siempre:** una prueba con alguna mutación exclusiva, o que nació por un error real (lo dice su docstring o su ficha), aunque se parezca a otra.
- Las pruebas de fichas obsoletas (Vercel, Neon) se retiran con su ficha, no aquí.

## Después de esta ficha
La consolidación se hace en una ficha por sala (TEST-05a, TEST-05b, …), creadas a partir del informe. Cada una tiene como propiedad solo los archivos de prueba de su sala que no pertenecen a fichas abiertas. Su árbitro:
- la cobertura de la sala no baja;
- las mutaciones detectadas de la sala no bajan;
- la suite completa tarda menos que antes, medido con `tests/duraciones.json`;
- **el tiempo total de la corrida de `main` no sube** (pytest más Playwright, según el registro de la corrida).

## No hagas
- No borres ni edites pruebas existentes.
- No toques `.github/workflows/`.
