+++
id = "TEST-04"
titulo = "Prueba de que cada ruta que llama el frontend existe en el backend"
ola = "D"
estado = "hecha"
sala = "pasillo_central"
depende_de = ["FE-07"]
propiedad = ["tests/test_rutas_cliente_frontend.py"]
arbitro = "pytest tests/test_rutas_cliente_frontend.py + suite completa; prueba negativa documentada"
rastros = ["¤arbitro", "¤roadmap"]
+++

# TEST-04 · Prueba de que cada ruta que llama el frontend existe en el backend

**Objetivo.** El contrato congelado de la hoja de ruta (`tests/test_contrato_hoja_ruta.py`) cubre solo esa parte de la API. Las demás llamadas del frontend (ARCO, terceros, mitigaciones, organización, auditoría…) no tienen nada que detecte que una ruta cambió de nombre o dejó de existir, y todas las pruebas de Playwright simulan la API. Un renombrado en el backend solo se vería en producción como un 404. Esta prueba es un árbitro barato, sin base de datos ni navegador.

## Entrega
- `tests/test_rutas_cliente_frontend.py`:
  - Recorre los archivos del frontend que llaman a la API (`frontend/src/**/*.ts` y `*.tsx`, buscando las rutas pasadas a `fetchAutenticado`, a los clientes de `frontend/src/lib/**` y a cualquier otro `fetch` contra `/api/v1`) y extrae cada **método y ruta**.
  - Construye el conjunto de rutas reales del backend con `app.openapi()` (o `app.routes`), normalizando parámetros (`{id}` frente a plantillas del frontend).
  - Falla, **nombrando archivo, método y ruta**, si el frontend llama a una ruta que el backend no expone.
  - Lista aparte, sin fallar, las llamadas que no pudo resolver de forma estática (rutas armadas dinámicamente), para que sean visibles.
- Si hoy ya hay rutas del frontend que no existen en el backend, **no se corrige el frontend**: se listan en una tabla de excepciones dentro de la propia prueba, cada una con motivo, y se reportan en el informe.
- **Prueba negativa obligatoria:** romper a propósito una ruta (en una copia temporal de la tabla, nunca en código ajeno) y comprobar que la prueba falla con el mensaje esperado.

## Límites
- Solo lee el frontend y el backend: no modifica ningún archivo fuera de su propiedad.
- No ejecuta el backend ni Playwright, y no usa base de datos.
- No valida cuerpos ni respuestas, solo que método y ruta existen.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
