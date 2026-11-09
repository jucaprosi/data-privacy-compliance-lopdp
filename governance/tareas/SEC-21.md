+++
id = "SEC-21"
titulo = "Límite por IP en la ruta pública GET /api/v1/entorno"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-13"]
propiedad = ["app_core/limites/politicas.py", "api/middleware/limite_peticiones.py", "tests/test_limite_entorno_publico.py"]
crea = ["tests/test_limite_entorno_publico.py"]
arbitro = "pytest tests/test_limite_entorno_publico.py tests/test_sec13_limite_peticiones.py; mutaciones documentadas; revisión de Seguridad"
rastros = ["¤seguridad"]
+++

# SEC-21 · Límite por IP en /api/v1/entorno

Diseño del Arquitecto ADPA (2026-11-09). `GET /api/v1/entorno` es pública y no lleva token. Hoy cae en `api_general`, de ámbito «usuario». Sin token, la petición se resuelve con una Identidad anónima, así que todos los anónimos comparten una cubeta o quedan mal acotados. La prueba 1 lo confirma.

## Entrega
- **Política:** `Politica("entorno_publico", "ip", 60, MINUTO)`, ajustable con `LIMITE_ENTORNO_PUBLICO` como las demás.
- **Ruta:** en `politicas_de_ruta`, la constante `PREFIJOS_PUBLICOS_IP = ("/api/v1/entorno",)` devuelve `("entorno_publico",)` y se evalúa antes que `api_general`.
- **Clave:** la IP de `ip_cliente()`, corregida según «Saltos de proxy».
- **Fuera de alcance:** health (sigue en `RUTAS_LIBRES`), el router y tablas nuevas. `api/middleware/limite_peticiones.py` sí entra, solo por `ip_cliente()` y la lectura de la variable; sus dueñas, SEC-13 y SEC-13a, están hechas.

## Pruebas (cada una con su mutación)
1. `politicas_de_ruta("/api/v1/entorno", "GET") == ("entorno_publico",)`, también con «/» final. Mutación: quitar el prefijo.
2. Con el limitador en memoria o el PG16 del arnés, la petición 61 desde la misma IP en un minuto da 429 con `politica: "entorno_publico"`, y desde otra IP sigue en 200. Mutación: cambiar el ámbito a «usuario».
3. Con `LIMITE_ENTORNO_PUBLICO=5`, el tope cambia.
4. `/api/v1/health` sigue libre.

## Saltos de proxy (riesgo señalado por el CTO; regla del Arquitecto, 2026-11-09)
Detrás del balanceador de GCP, X-Forwarded-For llega como «<IP cliente>, <IP balanceador>». Tomar la última entrada daría un único cupo para todos.
- **`SALTOS_PROXY_CONFIABLES = n`:** entradas de proxies de confianza que se descartan por la derecha de XFF.
  - Por defecto n=0, el comportamiento de hoy (local, CI y arnés). En Cloud Run detrás del balanceador es n=1, como variable del servicio en el brief de GCP, que aplica el propietario. La ficha no toca workflows.
  - Se lee al arrancar, en una función pura, como entero ≥ 0. Si es inválida o negativa, el arranque falla con un error claro; nunca cae en silencio a 0.
- **Regla de `ip_cliente(scope)`:**
  1. XFF se separa por comas y se quitan los espacios y las entradas vacías; queda la lista E.
  2. Si len(E) > n, el candidato es E[len(E)-1-n].
  3. Si E está vacía o len(E) ≤ n, se usa la IP del par TCP (`scope["client"]`), y si no la hay, `"desconocida"`. Nunca se toma E[0], que la escribe el cliente.
  4. El candidato tiene que validar con `ipaddress.ip_address`. Si no valida, se aplica la misma salida que en el paso 3.
- **Pruebas** (mutaciones: contar desde la izquierda, quitar el respaldo a `scope["client"]` y aceptar un n inválido):
  - con n=1, «1.1.1.1, 35.0.0.1» y «2.2.2.2, 35.0.0.1» dan cupos distintos: 61 peticiones de la primera dan 429 y la segunda no se ve afectada;
  - con n=1, «falsa, 1.1.1.1, 35.0.0.1» da 1.1.1.1;
  - con n=0, se mantiene la última entrada;
  - con XFF vacío o con menos entradas que n, se usa `scope["client"]`;
  - si el candidato no es una IP, se usa `scope["client"]`;
  - n="-1" o "x" hace fallar el arranque.
- **Evidencia, no árbitro:** cuando exista el balanceador, el propietario anota en el brief de GCP un XFF real visto en los logs de Cloud Run y confirma n=1. Hasta entonces, SEC-21 se da por hecha con n=0 y sus pruebas en verde.

Sin `import yaml` ni migración. Lleva revisión de Seguridad; no pasa por UX/UI.
