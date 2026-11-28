# NOTIF-03 · Correo de las versiones por revisar
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hechos medidos en `origin/main` ed575cd2:
- `notificador_configurado()` devuelve `NotificadorEntornoPermitido(NotificadorNoConfigurado())` (`notificaciones_service.py:132-134`), y el adaptador responde `PENDIENTE` con «proveedor de correo no configurado» (`services/adaptadores.py:62`). Hoy no sale ningún correo.
- NOTIF-02 crea y actualiza los avisos (`avisos_plataforma`), con sus recordatorios.

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · Adaptador SMTP.** `NotificadorSmtp`, en `services/adaptadores.py`, implementa `Notificador.enviar_correo` con `smtplib` de la biblioteca estándar y no conoce al proveedor: cambiar de proveedor es solo cambiar el secreto. Hoy el proveedor es el SMTP de Banahost (cPanel), aprobado por el CTO el 2026-11-27.
- **R1a · TLS obligatorio.** Puerto 465 con `SMTP_SSL`, o 587 con `starttls()`. En los dos casos, con `ssl.create_default_context()`, que verifica el certificado y el nombre del host. Cualquier otro puerto, un `starttls` que falla o un servidor sin STARTTLS es un error de configuración: no se envía nada, y nunca hay texto plano ni puerto 25.
- **R1b · Configuración.** Un único secreto de Secret Manager, `evydentia-notif-smtp`, montado en Cloud Run como la variable de entorno `NOTIF_SMTP_CONFIG`. Contiene un JSON con `host`, `puerto`, `usuario`, `contrasena` y `remitente`. Si la variable falta, no es JSON válido o le falta un campo, `notificador_configurado()` sigue devolviendo `NotificadorNoConfigurado` y lo registra sin mostrar el valor. Las credenciales nunca se escriben en el registro ni en el repositorio.
- **R1c · Remitente.** El remitente es un buzón dedicado del dominio, `avisos@evydentia.com`, que crea el propietario en cPanel. Su DMARC inicial es `v=DMARC1; p=none; rua=mailto:avisos@evydentia.com`.
- **R1d · Después del commit.** El correo nunca bloquea ni deshace el aviso de la campana. Se envía después del commit de la transacción que crea el aviso o el recordatorio, con un timeout de conexión y envío de 10 s.
- **R1e · Tope.** Como máximo 50 correos por hora y por instancia, contados en una ventana deslizante en memoria y configurable con `tope_hora` en el mismo JSON (ese valor por defecto queda por debajo del límite del hosting). Al llegar al tope, el correo no se envía y queda registrado como `TOPE`. No hay reintentos ni bucles: cada correo se intenta una sola vez (R4).
- **R2 · Cuándo.** Se envía un correo al crearse el aviso de NOTIF-02 y en cada recordatorio, a la misma persona del aviso.
- **R3 · Texto** (UX/UI, 2026-11-25). El correo usa los textos de NOTIF-02 R2 y R3, por la misma función que la bandeja, sin una copia propia; solo añade su asunto y su saludo:
  - **Asunto:** «Versión por revisar: {plantilla}»; en un recordatorio, «Recordatorio: {plantilla} sigue por revisar».
  - **Cuerpo:** «Hola, {nombre}: Hay una versión nueva de la plantilla «{plantilla}» pendiente de revisión técnica. {línea de motivo de NOTIF-02 R2} Revísala en la plataforma: {enlace}. Recibes este correo porque tienes el permiso de revisión técnica de la Biblioteca.»
  - **Recordatorio:** el mismo cuerpo, con el texto de recordatorio de NOTIF-02 R3 tras la línea de motivo, en los mismos momentos (D3).
  - Sin «conforme», «cumple», «garantiza», «certificado» ni «legal», y sin nombres de proveedores.
- **R4 · Fallo.** Si el envío falla, el aviso en la plataforma queda igual y el fallo se registra con el tipo de error y el id del aviso, sin destinatario, asunto ni cuerpo. No se reintenta en la misma corrida.
- **R6 · Pruebas sin red.** `tests/test_notif03_correo.py` levanta un servidor SMTP falso local con `aiosmtpd`, con un certificado de `trustme` en `127.0.0.1`, y no abre ninguna conexión a otra máquina. `aiosmtpd` y `trustme` entran en `requirements.txt`.
- **R5 · Entornos.** `NotificadorEntornoPermitido` sigue filtrando por entorno, como hoy (`destinatarios_entorno.py`).

## 4. Interfaz

Sin pantalla: solo correo.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el proveedor configurado y un aviso nuevo, **entonces** sale un correo con el asunto y el enlace de R3. Mutación m1: no enviarlo al crear el aviso da rojo. | `tests/test_notif03_correo.py` |
| **Dado** el proveedor sin configurar, **entonces** `notificador_configurado()` es `NotificadorNoConfigurado` y el aviso se crea igual. Mutación m2: lanzar error sin proveedor da rojo. | ídem |
| **Dado** un recordatorio de fecha futura, **entonces** el correo lleva el texto de NOTIF-02 R3 («faltan {n} días») y ninguna de las palabras de R3. Mutación m3: escribir «cumple» da rojo. | ídem |
| **Dado** cada variante de NOTIF-02 R2 y R3, **entonces** el correo contiene exactamente la misma línea que el aviso y no contiene «undefined», «null», «None», «{», «}», «, ,» ni dos espacios seguidos. Mutación m4: un correo sin fecha que imprime «entra en vigencia el None» da rojo. Mutación m5: un texto del correo distinto del del aviso da rojo. | ídem |
| **Dado** un servidor falso que solo acepta texto plano (sin STARTTLS) o un certificado que no es de confianza, **entonces** no se envía nada y se registra un error de configuración. Mutación m6: aceptar texto plano o desactivar la verificación del certificado da rojo. | `tests/test_notif03_correo.py` |
| **Dado** `tope_hora` igual a 2 y tres avisos en la misma hora, **entonces** salen dos correos, el tercero queda como `TOPE` y los tres avisos están en la campana. Mutación m7: quitar el tope, o reintentar el correo frenado, da rojo. | ídem |
| **Dado** un servidor falso que no responde, **entonces** el aviso queda confirmado en la base, el envío termina por el timeout y el registro no contiene ni el destinatario ni el cuerpo. Mutación m8: enviar antes del commit, o escribir el cuerpo en el registro, da rojo. | ídem |
| **Dado** la sala, **entonces** solo importa otras salas por sus pasillos. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** notificaciones de la plataforma y Módulo 7.
- Proveedor SMTP de Banahost y condiciones del CTO (2026-11-27), por el Tech Lead.
- Decisión D7 del CTO (2026-11-25) y textos del UX/UI (2026-11-25), brief `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS`, base `origin/main` ed575cd2.
