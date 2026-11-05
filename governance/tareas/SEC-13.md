+++
id = "SEC-13"
titulo = "Límite de peticiones por organización, usuario, ruta e IP (Cloud Armor + Memorystore), bloqueo de inicio de sesión y cuota mensual de IA por paquete"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-01", "GCP-04", "GCP-05", "SEC-12"]
propiedad = ["app_core/limites/__init__.py", "app_core/limites/limitador.py", "app_core/limites/cuota_ia.py", "governance/operaciones/cloud_armor_politicas.yaml", "tests/test_sec13_limite_peticiones.py"]
arbitro = "pytest tests/test_sec13_limite_peticiones.py + suite completa + vigilantes"
rastros = ["¤seguridad", "¤seguridad-tenant", "¤copiloto-ia"]
+++
# SEC-13 · Límite de peticiones por organización, usuario, ruta e IP (Cloud Armor + Memorystore), bloqueo de inicio de sesión y cuota mensual de IA por paquete

## Entrega
- Módulo `app_core/limites/limitador.py` con un limitador de ventana deslizante sobre Memorystore for Redis, con claves `tenant_id:usuario:ruta` y `ip:ruta`, que responde `429 Too Many Requests` con `Retry-After`.
- Bloqueo de inicio de sesión al quinto intento fallido por cuenta y por IP en 15 minutos, y techo de 10 envíos por IP y hora en los portales públicos (`DER-02`, `TER-02`), sin revelar si la cuenta o el expediente existen.
- Módulo `app_core/limites/cuota_ia.py` que, antes de cada llamada a Vertex AI, compara el consumo mensual de tokens de la organización con el techo de su paquete (§2.3 del PRD), avisa al 80 % y rechaza al 100 % sin consumir saldo.
- Manifiesto `governance/operaciones/cloud_armor_politicas.yaml` con reglas OWASP preconfiguradas y reglas de límite por IP (`rate_based_ban`) asociadas al balanceador de `GCP-04`.

## Pruebas
- `pytest tests/test_sec13_limite_peticiones.py` comprueba el `429` con `Retry-After`, la independencia de contadores entre organizaciones, el bloqueo al quinto intento y la suspensión de la IA al 100 % sin afectar las rutas con plazo legal (`INV_RATE_LIMIT_PER_TENANT_USER_ROUTE`, `INV_AUTH_AND_PUBLIC_PORTAL_THROTTLING`, `INV_AI_SPEND_QUOTA_PER_TENANT`).
