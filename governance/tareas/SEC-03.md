+++
id = "SEC-03"
titulo = "Autenticación verificable con Google (OIDC)"
ola = "B"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["RM-01", "RM-00", "ENT-01", "RM-02"]
propiedad = ["api/rbac.py", "api/dependencies.py", "app_core/security.py", "requirements.txt", "alembic/versions/*_users_google_sub.py", "tests/test_autenticacion.py", "tests/test_ai_copilot.py", "tests/conftest.py", "tests/test_contrato_hoja_ruta.py"]
arbitro = "pytest tests/test_autenticacion.py (tokens simulados) + suite completa"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-03 · Autenticación verificable con Google (OIDC)

**Objetivo.** Hoy la identidad llega en cabeceras que envía el propio cliente (`X-User-ID`, `X-Tenant-ID`, `X-Role`): quien conozca un identificador válido puede suplantarlo. Bloqueante para producción con clientes.

## Entrega
- El servidor valida el token de identidad de Google (emisor, audiencia, vigencia y correo verificado) y obtiene de él **solo el usuario**; el tenant y el rol declarados se autorizan contra `user_tenant_roles` del usuario verificado.
- Migración que añade `users.google_sub` (único, opcional); la cuenta se vincula por correo verificado.
- Prueba con tokens simulados: sin token ⟹ 401; emisor o audiencia ajenos ⟹ 401; correo no verificado ⟹ 401; `X-User-ID` suplantado ⟹ ignorado; tenant sin membresía ⟹ 403.

- **Los tres mecanismos de identidad pasan a uno solo.** Hoy conviven `api/rbac.py::get_context` (cabeceras `X-User-ID`/`X-Tenant-ID`/`X-Role`), `api/dependencies.py` (falla abierto: sin cabeceras concede `tenant-default` y `GESTOR_PROCESO`) y `app_core/security.py::get_current_tenant` (acepta `Bearer jwt_mock_tenant_<id>`, falsificable por cualquiera). Los tres deben resolver la identidad con la misma verificación; ninguno puede conceder acceso sin token válido.
- **`AUTH_MODE`:** `oidc` por defecto; `headers` solo si se configura de forma explícita (desarrollo y pruebas). Un valor desconocido o ausente en producción cae en `oidc`, nunca en `headers`.
- **Dependencia autorizada por el propietario:** `PyJWT[crypto]` en `requirements.txt` (verificación RS256 con las claves públicas de Google, JWKS con caché y sin consultar la red en cada petición). No se añade ninguna otra dependencia.
- **Contrato congelado:** `X-User-ID` deja de ser obligatorio (en `oidc` se ignora) y FastAPI lo publica como «string o nulo»; el verificador de `tests/test_contrato_hoja_ruta.py` trataba eso como cambio de tipo. Se corrige el verificador para que un tipo anulable (`anyOf [T, null]`) cuente como T, conservando que un tipo distinto sí rompe el contrato.
- **Pruebas existentes:** `tests/conftest.py` fija `AUTH_MODE=headers` para la suite, y `tests/test_ai_copilot.py` deja de depender del token simulado `jwt_mock_tenant_`. Las pruebas de `tests/test_autenticacion.py` ejercitan `oidc` con tokens simulados y firmados con una clave de prueba.

## Límites
- No cambia el frontend (FE-07). La API en `oidc` exige el token; hasta FE-07 el frontend sigue necesitando `AUTH_MODE=headers` en Vercel (acción del propietario, no del agente).
- **Acción manual del usuario:** crear el cliente OAuth en Google Cloud y registrar los orígenes autorizados. Las vistas previas de Vercel cambian de dirección y no se pueden registrar una a una: el SSO se prueba en local y en producción.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
