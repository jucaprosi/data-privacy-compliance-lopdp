+++
id = "TEST-01"
titulo = "Cobertura pendiente de evidencia y Redis"
ola = "backlog"
estado = "pendiente"
sala = "tests"
depende_de = ["RM-01"]
propiedad = ["tests/test_evidencia_http.py", "tests/test_redis_client.py"]
arbitro = "pytest tests/test_evidencia_http.py tests/test_redis_client.py"
rastros = ["¤arbitro"]
+++

# TEST-01 · Cobertura pendiente de evidencia y Redis

**Objetivo.** Pruebas HTTP de los endpoints de evidencia y pruebas de `redis_client` con *mock*.

## Entrega
- Un archivo de pruebas por tema, sin ampliar los existentes.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
