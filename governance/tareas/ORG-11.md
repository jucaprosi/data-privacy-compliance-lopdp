+++
id = "ORG-11"
titulo = "Reemitir la invitación del administrador inicial mientras la organización no tenga administrador"
ola = "D"
estado = "hecha"
sala = "plataforma"
depende_de = ["ORG-10"]
propiedad = ["alembic/versions/*_invitacion_unica_emitida.py", "features/plataforma/domain/models.py", "features/plataforma/services/operador_engine.py", "features/plataforma/plataforma_service.py", "api/routers/plataforma.py", "tests/test_plataforma_reemision.py", "frontend/src/app/plataforma/page.tsx", "frontend/src/lib/plataforma/tipos.ts", "frontend/src/lib/plataforma/cliente.ts", "frontend/tests/plataforma/**"]
arbitro = "pytest tests/test_plataforma_reemision.py tests/test_plataforma_operador.py contra una rama Neon de revisión + Playwright de frontend/tests/plataforma + tsc --noEmit y next build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-11 · Reemitir la invitación del administrador inicial

**Objetivo.** Si la invitación inicial caduca, se revoca o se envió a un correo equivocado, hoy no hay forma de emitir otra: la organización queda creada y sin administrador. El operador debe poder reemitirla, **solo mientras la organización no tenga administrador**.

## Base legal y decisión
La plataforma es encargada del tratamiento (Art. 4 LOPDP) y el operador solo gestiona la «puerta de entrada» (ORG-09). Una vez la organización tiene `admin_organizacion`, sus administradores se gestionan dentro de ella; si el operador pudiera seguir emitiendo invitaciones de administrador, tendría una vía de acceso a una organización que ya es del cliente. Por eso la reemisión se rechaza con 409 si existe un `admin_organizacion` activo.

## Entrega
- `POST /api/v1/plataforma/organizaciones/{tenant_id}/invitaciones` (solo operadores): cuerpo opcional `{ "email_admin_inicial": ... }`; si no se envía, se reutiliza el correo de la última invitación. Responde como el alta: el código en claro **una sola vez**, el id y la caducidad.
  - 404 si la organización no existe; **409** si ya tiene un `admin_organizacion` activo, con un mensaje que lo explica.
  - La invitación `emitida` anterior (vigente o vencida) pasa a `revocada` en la **misma transacción**, con `revoked_by` del operador.
- **Una sola invitación `emitida` por organización, garantizada en la base:** migración `*_invitacion_unica_emitida.py` con un índice único parcial sobre `invitaciones_organizacion (tenant_id) WHERE estado = 'emitida'`. Antes de crearlo, la migración revoca las `emitida` duplicadas que hubiera (dejando la más reciente) y lo documenta. `down_revision` = la cabeza de `main` al crear la rama.
- **Sin duplicar código:** el alta (`crear_organizacion_e_invitacion`) y la reemisión usan una función común para emitir la invitación (código aleatorio, *hash*, caducidad de 7 días, inserción y evento en `auditoria_plataforma`).
- Evento `reemitir_invitacion` en `auditoria_plataforma` (operador, organización, correo, invitación nueva y revocada); nunca el código en claro.
- **Pantalla `/plataforma`:** botón «Reemitir invitación» en las organizaciones sin administrador cuya invitación esté `caducada` o `revocada`; muestra el código nuevo una sola vez, con el mismo componente que el alta.
- Pruebas con base real (`tests/test_plataforma_reemision.py`): reemitir tras caducar y tras revocar; la anterior queda `revocada`; 409 con administrador; 404 sin organización; un no operador recibe 403; la base rechaza una segunda `emitida` insertada directamente; el evento queda en `auditoria_plataforma` sin el código.
- Pruebas de Playwright con la API simulada: el botón solo aparece donde corresponde; el código se ve una vez; el 409 se explica.
- **Prueba de mutación documentada:** quitar la comprobación de administrador activo y comprobar que la prueba del 409 falla.

## Límites
- No cambia la aceptación de invitaciones ni los permisos dentro de la organización.
- No da al operador ningún acceso a los datos de las organizaciones.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks `Arnés Físico Determinista` y `Playwright Frontend` del PR están en verde. No modificó ningún archivo fuera de su propiedad.
