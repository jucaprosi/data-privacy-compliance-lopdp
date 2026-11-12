+++
id = "ORG-17b"
titulo = "La prueba de la clave de cifrado del inventario acepta la referencia a Secret Manager y sigue detectando un valor real"
ola = "backlog"
estado = "hecha"
sala = "organizacion"
depende_de = ["ORG-17"]
propiedad = ["tests/test_organizacion_inventario.py"]
crea = []
arbitro = "pytest tests/test_organizacion_inventario.py: la prueba test_la_clave_de_cifrado_no_esta_escrita_en_ningun_archivo da verde con la referencia `--set-secrets \"...,INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest\"` y rojo con un valor Fernet real pegado (44 caracteres base64); mutaciones documentadas: pegar un valor real en deploy-gcp.yml (o en una copia temporal) hace fallar la prueba; la referencia no"
rastros = ["¤rbac-tenant"]
+++

# ORG-17b · La prueba de la clave de cifrado del inventario acepta la referencia a Secret Manager

**Origen.** Hallazgo de Antigravity, trasladado por el CTO (2026-11-11). `tests/test_organizacion_inventario.py::test_la_clave_de_cifrado_no_esta_escrita_en_ningun_archivo` usa el patrón `INVENTARIO_CLAVE_CIFRADO\s*[:=]\s*["']?[A-Za-z0-9_\-=]{20,}`, que da falso positivo con la referencia legítima a Secret Manager que debe llevar el workflow de despliegue: `--set-secrets "...,INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest"` (el nombre del secreto tiene 24 caracteres y casa). Se arregla la prueba, no el workflow. Va **antes** del PR del workflow que abrirá el propietario.

## Entrega
- Solo la línea del patrón de esa prueba (líneas ~337-348 de `tests/test_organizacion_inventario.py`): debe **aceptar** la forma `=INVENTARIO_CLAVE_CIFRADO:(latest|\d+)` (referencia a Secret Manager) y **seguir detectando** un valor Fernet real (44 caracteres base64 url-safe, con o sin comillas).
- ORG-17 está hecha: esta ficha la reabre solo para esa línea; no cambia ninguna otra aserción ni ninguna otra prueba del archivo.

## Pruebas (con su mutación)
- Un valor Fernet real pegado (por ejemplo generado en la prueba con `Fernet.generate_key()`, sin escribirlo en ningún archivo versionado) da rojo; la referencia `=INVENTARIO_CLAVE_CIFRADO:latest` y `=INVENTARIO_CLAVE_CIFRADO:3` dan verde.
- Mutación: volver al patrón anterior hace fallar el caso de la referencia.
