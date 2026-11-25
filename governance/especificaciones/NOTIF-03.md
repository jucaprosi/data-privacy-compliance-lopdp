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
- **R3 · Texto** (UX/UI, 2026-11-25):
  - **Asunto:** «Versión por revisar: {plantilla}».
  - **Cuerpo:** «Hola, {nombre}: Hay una versión nueva de la plantilla «{plantilla}» pendiente de revisión técnica. {línea de motivo} Revísala en la plataforma: {enlace}. Recibes este correo porque tienes el permiso de revisión técnica de la Biblioteca.»
  - **Línea de motivo**, una sola según el caso:
    - (a) resolución con fecha futura: «Motivo del cambio: {norma}, {artículo}, que entra en vigencia el {fecha}.»;
    - (b) resolución con fecha pasada: «Motivo del cambio: {norma}, {artículo}, que entró en vigencia el {fecha}.»;
    - resolución que entra en vigencia hoy: «Motivo del cambio: {norma}, {artículo}, que entra en vigencia hoy.»;
    - (c) resolución sin fecha: «Motivo del cambio: {norma}, {artículo}. La norma no indica fecha de vigencia.»;
    - (d) petición: con texto, «Motivo del cambio: petición de {nombre}: «{texto}».»; sin texto, «Motivo del cambio: petición de {nombre}.». Sin norma, artículo ni fecha. El texto se corta a 200 caracteres, con «…» si se corta, y va como texto plano: no se interpreta como formato ni como enlace.
    - Sin {artículo}, se quita «, {artículo}» entero.
  - **Recordatorio:** asunto «Recordatorio: {plantilla} sigue por revisar». En el cuerpo, según el caso:
    - fecha futura: «…sigue sin revisión técnica. La norma que motiva el cambio entra en vigencia el {fecha} (faltan {n} días).»; con {n} = 1, «(falta 1 día)»;
    - la vigencia es hoy: «…sigue sin revisión técnica. La norma que motiva el cambio entra en vigencia hoy.»;
    - sin fecha, fecha pasada o petición (días desde la creación, D3): «…sigue sin revisión técnica desde hace {n} días.»; con {n} = 1, «desde hace 1 día».
  - {fecha} va en largo y en español, sin cero a la izquierda en el día («5 de diciembre de 2026»), en hora de Ecuador y sin hora. «Hoy» se calcula también en hora de Ecuador.
  - Ningún campo se imprime vacío ni como «None»: si un dato falta, se usa la variante que no lo nombra.
  - Las variantes de la bandeja de avisos (NOTIF-02, `avisos_plataforma.py`) usan los mismos textos, para que el aviso y el correo digan lo mismo. Redacción del UX/UI, 2026-11-25.
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
| **Dado** un recordatorio, **entonces** el correo dice «faltan {n} días» y ninguna de las palabras de R3. Mutación m3: escribir «cumple» da rojo. | ídem |
| **Dado** un aviso de una resolución sin fecha y otro de una petición, **entonces** el primero dice «La norma no indica fecha de vigencia.» y su recordatorio cuenta días desde la creación; el segundo nombra a quien la pidió y no tiene norma, artículo ni fecha. Mutación m4: un correo sin fecha que imprime «entra en vigencia el None» o deja el hueco vacío da rojo. | ídem |
| **Dado** cada variante de R3 (a, b, hoy, c, d con y sin texto, sin artículo, y cada recordatorio con {n} = 1 y {n} > 1), **entonces** el correo y el aviso dicen el mismo texto, y ninguno contiene «undefined», «null», «None», «{», «}», «, ,» ni dos espacios seguidos. Mutación m5: dejar «, ,» al faltar el artículo da rojo. Mutación m6: «faltan 1 días» da rojo. Mutación m7: una petición de 300 caracteres sin cortar da rojo. | ídem |
| **Dado** la sala, **entonces** solo importa otras salas por sus pasillos. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** notificaciones de la plataforma y Módulo 7.
- Decisión D7 del CTO (2026-11-25) y textos del UX/UI (2026-11-25), brief `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS`, base `origin/main` ed575cd2.
