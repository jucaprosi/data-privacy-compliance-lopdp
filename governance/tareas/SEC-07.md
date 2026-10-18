+++
id = "SEC-07"
titulo = "Retirar la compatibilidad del token simulado en el modo headers"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-03", "FE-07", "RM-02"]
propiedad = ["app_core/security.py", "tests/test_autenticacion.py", "tests/test_api_integracion.py", "tests/test_e2e_flujo_completo.py"]
arbitro = "pytest tests/test_autenticacion.py tests/test_api_integracion.py tests/test_e2e_flujo_completo.py tests/test_ai_copilot.py + suite completa; Playwright de frontend/tests/auth"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-07 · Retirar la compatibilidad del token simulado en el modo headers

**Objetivo.** SEC-03 dejó en `get_current_tenant` (`app_core/security.py`) una compatibilidad solo del modo `headers`: si falta `X-Tenant-ID`, acepta `Bearer jwt_mock_tenant_<tenant>`, porque `ArcoModule`, `TercerosModule` y `MitigationTracker` lo enviaban. FE-07 los migró a `fetchAutenticado`, que envía `X-Tenant-ID`, y el frontend ya no contiene ese token. Mantener la compatibilidad deja viva una identidad que cualquiera puede fabricar si conoce el prefijo.

## Entrega
- Eliminar `PREFIJO_TOKEN_SIMULADO` y `_tenant_de_token_simulado`. En modo `headers`, sin `X-Tenant-ID`, `get_current_tenant` responde 401; en `oidc` no cambia nada.
- Dos pruebas del backend aún dependen del token simulado: `tests/test_api_integracion.py` y `tests/test_e2e_flujo_completo.py`. Se adaptan para enviar `X-Tenant-ID`, sin debilitar sus aserciones.
- En `tests/test_autenticacion.py`, las pruebas de la compatibilidad pasan a comprobar lo contrario: el token simulado ya no resuelve ningún tenant ni en `headers` ni en `oidc`.
- Comprobar que ninguna otra parte lo usa: `git grep jwt_mock` no devuelve código de producción ni del frontend; solo las pruebas que fijan que ya no vale.
- Playwright de `frontend/tests/auth` en verde: los tres módulos siguen funcionando en modo `headers` enviando `X-Tenant-ID`.

## Límites
- No cambia el modo `oidc`, `get_context` ni la verificación del token de Google.
- No toca el frontend: ya está migrado.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
