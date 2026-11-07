+++
id = "DEMO-01"
titulo = "Modo demo seguro: barrera contra producción, vendedores autorizados y persona decidida por el servidor"
ola = "D"
estado = "pendiente"
sala = "demo, pasillo_central"
depende_de = ["SEC-03", "SEC-07", "SEC-15", "ENT-02", "RM-00", "NOTIF-01"]
propiedad = ["features/demo/__init__.py", "features/demo/demo_service.py#DEMO-01", "features/demo/domain/", "features/demo/services/identidad_engine.py", "features/demo/services/vendedores_engine.py", "app_core/security.py#DEMO-01", "main.py#DEMO-01", "api/routers/demo.py#DEMO-01", "features/notificaciones/notificaciones_service.py#DEMO-01", "alembic/versions/20261121_demo_sesiones.py", "tests/demo/test_demo_modo_seguro.py"]
arbitro = "pytest tests/demo/test_demo_modo_seguro.py + suite de seguridad y RLS existente en verde + linter ADPA sin cruces; pruebas de mutación documentadas"
rastros = ["¤demo", "¤seguridad", "¤rbac-tenant"]
+++

# DEMO-01 · Modo demo seguro: barrera contra producción, vendedores autorizados y persona decidida por el servidor

**Por qué.** El vendedor no es un usuario de la base demo: `usuario_de_identidad` (`app_core/security.py`) responde 403 a quien no está en `users`. En modo demo, después de verificar el token de Google, el servidor **traduce** la identidad del vendedor a la persona ficticia activa de su sesión (un `users.id` con un solo rol). A partir de ahí `roles_activos`, `X-Role`, la RLS, la segregación del DPO y el trigger `fn_utr_dpo_sod` funcionan sin cambios.

## Entrega
- **Sala nueva `features/demo/`**, compuerta `demo_service.py` (sección `#DEMO-01`): `estado`, `resolver_usuario`, `cambiar_persona`, y el registro del resolutor al arrancar.
- **`app_core/security.py#DEMO-01`:** `registrar_resolutor_identidad(fn)`. `usuario_verificado()` consulta el resolutor registrado, si lo hay, después de `verificar_token_google`. `app_core` no importa `features/demo` (inversión de dependencia).
- **`main.py#DEMO-01`:** con `DEMO_MODE=1`, llama a `demo_service` para registrar el resolutor y monta `api/routers/demo.py`. Sin `DEMO_MODE`, no hace nada.
- **Migración `20261121_demo_sesiones.py`:** tabla `demo_sesiones` (`id`, `vendedor_email`, `vendedor_sub`, `tenant_id`, `persona_usuario_id`, `estado` activa/vencida, `creada_en`, `ultima_actividad`, `vencida_en`, `motivo` terminar/inactividad/reemplazo) y columna `tenants.es_demo boolean not null default false`. `lopdp_app`: SELECT, INSERT y UPDATE sobre `demo_sesiones`, **sin DELETE** (SEC-10). La migración es aditiva y se aplica también a producción, donde la tabla queda vacía.
- **Rutas (`#DEMO-01`):** `GET /demo/estado` (ligero; renueva la actividad) y `POST /demo/persona` (cambia de persona y devuelve el `X-Role` que el frontend debe usar). Respuesta de estado como en el §3 de los flujos; las personas van **sin correo**. Errores siempre `{codigo, mensaje}` con `DEMO_NO_AUTORIZADO`, `DEMO_PERSONA_AJENA` y `DEMO_VENCIDA`.
- **Vendedores:** `DEMO_VENDEDORES`, lista de correos separados por comas; se compara en minúsculas. Un correo fuera de la lista recibe 403 `DEMO_NO_AUTORIZADO`.
- **Notificaciones (`#DEMO-01`):** con `DEMO_MODE=1`, el envío queda apagado.
- **Auditoría:** cada cambio de persona registra `DEMO_CAMBIO_PERSONA` con el **correo del vendedor real**, la persona y la hora, por `app_core/audit.py` (solo inserción).

## Controles de seguridad obligatorios (revisión de la Coordinadora, 2026-11-06)
1. `registrar_resolutor_identidad` lanza `RuntimeError` si `DEMO_MODE` no es `1`, si `apunta_a_produccion()` es verdadero, o si ya hay un resolutor registrado.
2. El resolutor solo devuelve personas cuyo `tenant_id` tiene `es_demo = true` y coincide con el de la sesión demo vigente del vendedor. Lo comprueba la consulta, no solo el código.
3. La auditoría lleva siempre al vendedor real.
4. `DEMO_MODE=1` con la base de producción hace fallar el arranque (reutiliza `apunta_a_produccion()`, SEC-15). El modo `headers` sigue prohibido en la nube: `exigir_arranque_seguro()` no cambia.
5. Sin `DEMO_MODE`: `/demo/*` responde 404 y no hay resolutor registrado.
6. `demo_sesiones` no se expone en ninguna respuesta. Los correos de los vendedores no salen del servidor.
7. CORS del backend demo: solo el origen del frontend demo (variable de despliegue, DEMO-05).

## Pruebas (`tests/demo/test_demo_modo_seguro.py`)
- Arranque con `DEMO_MODE=1` y el host de producción: error.
- Sin `DEMO_MODE`: `/demo/estado` 404, resolutor ausente; `registrar_resolutor_identidad` lanza error.
- Un segundo registro lanza error.
- Correo fuera de `DEMO_VENDEDORES`: 403 `DEMO_NO_AUTORIZADO` y ninguna fila nueva.
- Persona de otra organización, o de un tenant sin `es_demo`: 403 `DEMO_PERSONA_AJENA`.
- Cambio de persona: devuelve el `X-Role`, y la auditoría tiene el evento con el correo del vendedor.
- Las pruebas de segregación del DPO y `tests/test_rls_todas_las_tablas.py` siguen en verde (`demo_sesiones` entra en `EXENCIONES` con su motivo: la lee el resolutor antes de conocer el tenant).
- Mutaciones documentadas: quitar la comprobación de `es_demo` en el resolutor rompe «persona ajena»; quitar la barrera de producción del registro rompe su prueba.

## Límites
- No toca `features/organizacion/domain/roles.py` ni el trigger `fn_utr_dpo_sod`.
- No crea organizaciones ni copia la plantilla (DEMO-02). No ejecuta DELETE.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y proyección ADPA del Arquitecto de soluciones: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; vencimiento a los 60 minutos sin actividad; tope de 20 demos activas; lista `DEMO_VENDEDORES` en Vercel; dirección `*.vercel.app`; una sola demo activa por vendedor (la nueva entrada vence la anterior, motivo `reemplazo`).
