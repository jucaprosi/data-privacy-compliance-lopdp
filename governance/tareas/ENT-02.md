+++
id = "ENT-02"
titulo = "Un solo punto de entrada fija el bucle de eventos compatible con psycopg en Windows"
ola = "backlog"
estado = "pendiente"
sala = "operaciones"
depende_de = ["RM-00", "RM-02"]
propiedad = ["app_core/bucle_eventos.py", "main.py", "tests/test_bucle_eventos.py"]
arbitro = "pytest tests/test_bucle_eventos.py + suite completa"
rastros = ["¤arbitro", "¤seguridad"]
+++

# ENT-02 · Un solo punto de entrada fija el bucle de eventos compatible con psycopg en Windows

**Objetivo.** Cerrar el Aporte 100: en Windows, `uvicorn main:app` sin `--reload` ni varios trabajadores usa `ProactorEventLoop` y toda ruta con base de datos responde 500 (`psycopg` asíncrono no lo admite). Hoy solo se evita porque `python main.py` arranca con `reload=True` y porque `tests/conftest.py` fija la política para las pruebas.

## Entrega
- `app_core/bucle_eventos.py` con una función que, solo en `win32`, fija `asyncio.WindowsSelectorEventLoopPolicy`; en otras plataformas no hace nada. Es idempotente.
- `main.py` la invoca antes de crear la aplicación y el motor de base de datos. Es el único punto de entrada que la llama.
- Una prueba que simula `win32` y comprueba que la política queda fijada, y que en otra plataforma no se modifica.

## Límites
- No cambia `uvicorn`, `psycopg` ni la estrategia de arranque (`reload`).
- No toca Linux, Vercel ni la CI, que no están afectados.
- `tests/conftest.py` conserva su propia política para las pruebas.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
