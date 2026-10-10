+++
id = "SEC-03"
titulo = "Autenticación verificable con Google (OIDC)"
ola = "B"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["RM-01", "RM-00"]
propiedad = ["api/rbac.py", "api/dependencies.py", "alembic/versions/*_users_google_sub.py", "tests/test_autenticacion.py"]
arbitro = "pytest tests/test_autenticacion.py (tokens simulados) + suite completa"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-03 · Autenticación verificable con Google (OIDC)

**Objetivo.** Hoy la identidad llega en cabeceras que envía el propio cliente (`X-User-ID`, `X-Tenant-ID`, `X-Role`): quien conozca un identificador válido puede suplantarlo. Bloqueante para producción con clientes.

## Entrega
- El servidor valida el token de identidad de Google (emisor, audiencia, vigencia y correo verificado) y obtiene de él **solo el usuario**; el tenant y el rol declarados se autorizan contra `user_tenant_roles` del usuario verificado.
- Migración que añade `users.google_sub` (único, opcional); la cuenta se vincula por correo verificado.
- Prueba con tokens simulados: sin token ⟹ 401; emisor o audiencia ajenos ⟹ 401; correo no verificado ⟹ 401; `X-User-ID` suplantado ⟹ ignorado; tenant sin membresía ⟹ 403.

## Límites
- **Acción manual del usuario:** crear el cliente OAuth en Google Cloud y registrar los orígenes autorizados. Las vistas previas de Vercel cambian de dirección y no se pueden registrar una a una: el SSO se prueba en local y en producción.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
