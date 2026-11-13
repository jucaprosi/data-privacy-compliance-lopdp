+++
id = "SEC-23"
titulo = "El asistente de implementación exige autenticación y toda ruta de la API la exige salvo lista blanca"
ola = "backlog"
estado = "pendiente"
sala = "seguridad"
depende_de = ["SEC-03", "IA-02"]
propiedad = ["api/routers/implementation_assistant.py", "tests/test_sec23_rutas_autenticadas.py", "tests/matriz/SEC-23.py"]
crea = ["tests/test_sec23_rutas_autenticadas.py", "tests/matriz/SEC-23.py"]
arbitro = "pytest tests/test_sec23_rutas_autenticadas.py + test_matriz_permisos.py + suite completa; mutaciones m1 a m3"
rastros = ["¤seguridad", "¤seguridad-tenant"]
+++

# SEC-23 · El asistente de implementación exige autenticación y toda ruta de la API la exige salvo lista blanca

Decisión del CTO (2026-11-13), medida por el CTO y el Arquitecto ADPA en main. **La revisa Seguridad.** No depende de IA-07.

## Hueco
`api/routers/implementation_assistant.py:16` tiene su propio `validar_tenant`, que solo comprueba que la cabecera `X-Tenant-ID` no esté vacía y mida 120 caracteres o menos. Así, `POST /api/v1/ai_copilot/consulta` y `GET /estado` no exigen token ni membresía: cualquiera puede llamar al modelo, y el límite por organización se esquiva cambiando la cabecera. No hay fuga de datos (el corpus es público), pero el endpoint cuesta.

Los demás routers que leen la cabecera usan `obtener_tenant_id_actual`, que en modo oidc verifica el token y la membresía (403 «Sin membresía activa»): están bien.

## Entrega
- Las dos rutas pasan a `Depends(obtener_tenant_id_actual)` o `get_context`: identidad y organización salen del token. Se retiran `validar_tenant` y la lectura directa de `x_tenant_id`.
- Prueba estructural en `tests/test_sec23_rutas_autenticadas.py`: recorre las rutas de la app bajo `/api/v1` y falla si alguna no exige autenticación, salvo una lista blanca explícita (health, entorno, login y las que diga Seguridad). Así no vuelve a pasar con un router nuevo.
- Matriz de permisos `tests/matriz/SEC-23.py`.

## Mutaciones
- m1: sin token, la ruta debe responder 401; falla si lo acepta.
- m2: token de un usuario sin membresía en la organización de la cabecera → 403.
- m3: volver a `validar_tenant` hace fallar m1 y la prueba estructural.
