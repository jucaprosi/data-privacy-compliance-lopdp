# NOTIF-03 · Correo de las versiones por revisar
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hechos medidos en `origin/main` ed575cd2:
- `notificador_configurado()` devuelve `NotificadorEntornoPermitido(NotificadorNoConfigurado())` (`notificaciones_service.py:132-134`), y el adaptador responde `PENDIENTE` con «proveedor de correo no configurado» (`services/adaptadores.py:62`). Hoy no sale ningún correo.
- NOTIF-02 crea y actualiza los avisos (`avisos_plataforma`), con sus recordatorios.

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · Proveedor elegido por el propietario.** El adaptador del proveedor que elija el propietario en el brief implementa `Notificador.enviar_correo`. Sus credenciales salen de Secret Manager por variable de entorno, nunca del repositorio. Si la variable no está, `notificador_configurado()` sigue devolviendo `NotificadorNoConfigurado` y no se envía nada.
- **R2 · Cuándo.** Se envía un correo al crearse el aviso de NOTIF-02 y en cada recordatorio, a la misma persona del aviso.
- **R3 · Texto** (UX/UI, 2026-11-25). El correo usa los textos de NOTIF-02 R2 y R3, por la misma función que la bandeja, sin una copia propia; solo añade su asunto y su saludo:
  - **Asunto:** «Versión por revisar: {plantilla}»; en un recordatorio, «Recordatorio: {plantilla} sigue por revisar».
  - **Cuerpo:** «Hola, {nombre}: Hay una versión nueva de la plantilla «{plantilla}» pendiente de revisión técnica. {línea de motivo de NOTIF-02 R2} Revísala en la plataforma: {enlace}. Recibes este correo porque tienes el permiso de revisión técnica de la Biblioteca.»
  - **Recordatorio:** el mismo cuerpo, con el texto de recordatorio de NOTIF-02 R3 tras la línea de motivo, en los mismos momentos (D3).
  - Sin «conforme», «cumple», «garantiza», «certificado» ni «legal», y sin nombres de proveedores.
- **R4 · Fallo.** Si el envío falla, el aviso en la plataforma queda igual y el fallo se registra; no se reintenta en la misma corrida.
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
| **Dado** la sala, **entonces** solo importa otras salas por sus pasillos. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** notificaciones de la plataforma y Módulo 7.
- Decisión D7 del CTO (2026-11-25) y textos del UX/UI (2026-11-25), brief `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS`, base `origin/main` ed575cd2.
