+++
id = "OPS-03"
titulo = "Script de verificación de despliegue"
ola = "indep"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["scripts/verificar_despliegue.py", "tests/test_verificar_despliegue.py"]
arbitro = "pytest tests/test_verificar_despliegue.py"
rastros = ["¤arbitro", "¤ci-cd"]
+++

# OPS-03 · Script de verificación de despliegue

**Objetivo.** Árbitro exógeno de cada despliegue.

## Entrega
- `python scripts/verificar_despliegue.py <dominio>` devuelve 0 si `GET /api/v1/health` responde 200 con `OPERATIONAL` y todos los routers cargados, y las rutas esperadas están en `/openapi.json`; si no, 1 con el motivo.
- La prueba usa un servidor simulado.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
