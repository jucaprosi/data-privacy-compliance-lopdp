+++
id = "TEST-01"
titulo = "Cobertura pendiente de endpoints de evidencia HTTP"
ola = "backlog"
estado = "hecha"
sala = "pruebas"
depende_de = ["RM-01"]
propiedad = ["tests/test_evidencia_http.py"]
arbitro = "pytest tests/test_evidencia_http.py"
rastros = ["¤arbitro"]
+++

# TEST-01 · Cobertura pendiente de endpoints de evidencia HTTP

**Objetivo.** Pruebas HTTP de los endpoints de evidencia y validación de contrato.

## Entrega
- Un archivo de pruebas por tema, sin ampliar los existentes.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
