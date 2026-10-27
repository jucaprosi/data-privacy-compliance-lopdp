+++
id = "DIAG-02"
titulo = "El banco de 80 preguntas de la plataforma vive en el servidor (hoy el backend usa 48 preguntas de relleno)"
ola = "D"
estado = "hecha"
sala = "diagnostico"
depende_de = ["DIAG-01", "MTGE-01", "RAT-01"]
propiedad = ["features/diagnostico/domain/banco_preguntas.json", "features/diagnostico/domain/models.py", "features/diagnostico/services/engine.py", "features/diagnostico/services/report_generator.py", "features/diagnostico/diagnostico_service.py#DIAG-02", "api/routers/diagnostico.py", "scripts/exportar_banco_preguntas.mjs", "tests/test_banco_preguntas.py", "tests/test_diagnostico_timebox.py", "tests/test_api_gateway.py", ".github/workflows/zero-regression-pipeline.yml"]
arbitro = "pytest tests/test_banco_preguntas.py tests/test_diagnostico_timebox.py tests/test_api_gateway.py + suite completa; node scripts/exportar_banco_preguntas.mjs --verificar con código 0; prueba de mutación documentada"
rastros = ["¤diagnostico"]
+++

# DIAG-02 · El banco de preguntas en el servidor

**Hallazgo (2026-10-25).** El diagnóstico y el assessment se hacen con las **80 preguntas de la plataforma** (`frontend/src/lib/bancoPreguntas/`). El equipo las redactó a partir de la matriz de madurez SMARTCIDI: lenguaje claro, ejemplos (`ejemplos.ts`), redacción y evidencia por tamaño de organización, criticidad, talla mínima y controles estructurales. **No coinciden con el Excel original**: los 80 enunciados son distintos y 65 de los 80 nombres de control también; en algunos casos cambia el tema (control 74: «Inducción a nuevos colaboradores» en el Excel, «Campañas de concienciación» en la plataforma).

El **backend no conoce ese banco**. `generar_banco_preguntas_diagnostico` (`features/diagnostico/services/engine.py`) devuelve **48 preguntas de relleno** («Control núcleo 1 para …», en 16 dominios G01-G16), y con ellas responden `POST /api/v1/diagnostico/preguntas` y los **informes Markdown y HTML** (`report_generator.py`).

**Decisión del propietario (2026-10-25):** la fuente de las preguntas es el banco de la plataforma, no el Excel.

## Entrega
- `features/diagnostico/domain/banco_preguntas.json`: las 80 preguntas con todos sus campos (`id`, `dimensionId`, `control`, `enunciado`, `enunciadoPorTamano`, `ejemplo`, `referenciaNormativa`, `criticidad`, `evidenciaEsperada`, `evidenciaPorTamano`, `tamanoMinimo`, `esEstructural`), **generado desde el banco del frontend** por `scripts/exportar_banco_preguntas.mjs`. El script compila los módulos TypeScript con la herramienta del propio proyecto (por ejemplo `typescript` o `esbuild` de `frontend/node_modules`); no se reescriben a mano.
- `node scripts/exportar_banco_preguntas.mjs --verificar` falla si el JSON y el banco del frontend difieren. `tests/test_banco_preguntas.py` valida el JSON (80 ids únicos 1-80, 8 por dimensión D01-D10, criticidad 1-5, tallas válidas, los 4 estructurales de `dimensiones_sgpdp.py`, ningún texto vacío) y lo compara con un resumen del banco del frontend que genera el script.
- El backend sustituye las 48 preguntas de relleno por el banco real: `generar_banco_preguntas_diagnostico` lee el JSON, `POST /diagnostico/preguntas` devuelve las preguntas que corresponden a la talla de la ficha (`tamanoMinimo`), con su redacción y evidencia por talla, y los informes Markdown y HTML citan el número, el nombre y el enunciado reales.
- Se actualizan las pruebas que dependían de las preguntas de relleno (`test_diagnostico_timebox.py`, `test_api_gateway.py`).
- **Prueba de mutación documentada:** cambiar un enunciado en el JSON y comprobar que `--verificar` falla; cambiar la talla mínima de una pregunta y comprobar que la prueba de la talla falla.

## Límites
- No cambia las preguntas, su redacción ni el banco del frontend. El frontend sigue usando su banco; desde ahora el JSON del servidor se regenera con el script cuando el banco cambie, y el árbitro lo exige.
- La poda por el perfil de operación de la ficha (selectores Sí/No) sigue en el frontend; si el backend la necesita, es otra tarea.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
