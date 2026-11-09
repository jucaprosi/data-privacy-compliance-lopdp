+++
id = "SEC-21"
titulo = "Límite por IP en la ruta pública GET /api/v1/entorno"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-13"]
propiedad = ["app_core/limites/politicas.py", "tests/test_limite_entorno_publico.py"]
crea = ["tests/test_limite_entorno_publico.py"]
arbitro = "pytest tests/test_limite_entorno_publico.py tests/test_sec13_limite_peticiones.py; mutaciones documentadas; revisión de Seguridad"
rastros = ["¤seguridad"]
+++

# SEC-21 · Límite por IP en /api/v1/entorno

Diseño del Arquitecto ADPA (2026-11-09). `GET /api/v1/entorno` es pública y no lleva token. Hoy cae en `api_general`, de ámbito «usuario». Sin token, la petición se resuelve con una Identidad anónima, así que todos los anónimos comparten una cubeta o quedan mal acotados. La prueba 1 lo confirma.

## Entrega
- **Política:** `Politica("entorno_publico", "ip", 60, MINUTO)`, ajustable con `LIMITE_ENTORNO_PUBLICO` como las demás.
- **Ruta:** en `politicas_de_ruta`, la constante `PREFIJOS_PUBLICOS_IP = ("/api/v1/entorno",)` devuelve `("entorno_publico",)` y se evalúa antes que `api_general`.
- **Clave:** la IP de `ip_cliente()`, que ya toma la última entrada de X-Forwarded-For. No hay clave nueva.
- **Fuera de alcance:** health (sigue en `RUTAS_LIBRES`), el router, tablas nuevas y `api/middleware/limite_peticiones.py`, que ya trata el ámbito «ip» con `Identidad()`.

## Pruebas (cada una con su mutación)
1. `politicas_de_ruta("/api/v1/entorno", "GET") == ("entorno_publico",)`, también con «/» final. Mutación: quitar el prefijo.
2. Con el limitador en memoria o el PG16 del arnés, la petición 61 desde la misma IP en un minuto da 429 con `politica: "entorno_publico"`, y desde otra IP sigue en 200. Mutación: cambiar el ámbito a «usuario».
3. Con `LIMITE_ENTORNO_PUBLICO=5`, el tope cambia.
4. `/api/v1/health` sigue libre.

Sin `import yaml` ni migración. Lleva revisión de Seguridad; no pasa por UX/UI.
