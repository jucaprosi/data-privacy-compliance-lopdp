+++
id = "NOTIF-03"
titulo = "Correo de las versiones por revisar y de sus recordatorios, por SMTP con TLS"
ola = "D"
estado = "pendiente"
tanda = 113
sala = "notificaciones"
depende_de = ["NOTIF-02"]
propiedad = ["features/notificaciones/services/adaptadores.py", "features/notificaciones/services/correo_versiones.py", "features/notificaciones/notificaciones_service.py#NOTIF-03", "features/notificaciones/services/avisos_plataforma.py", "tests/test_notif03_correo.py", "requirements.txt"]
crea = ["features/notificaciones/services/correo_versiones.py", "tests/test_notif03_correo.py"]
arbitro = "pytest tests/test_notif03_correo.py tests/test_adpa_bulkhead.py; mutaciones m1 a m8."
rastros = ["¤arbitro"]
+++

# NOTIF-03 · Correo de las versiones por revisar

**Contrato:** `governance/especificaciones/NOTIF-03.md` (manda sobre esta ficha).

**Origen.** Decisión D7 del CTO (2026-11-25): `main` no tiene proveedor de correo activo, así que el correo va en una ficha aparte de NOTIF-02, con su brief al propietario (`C:\Users\Juan Carlos\compartido\evydentia\briefs\PROPIETARIO_CORREO_Y_PROGRAMACION_AVISOS.md`).

## Entrega
- Adaptador `NotificadorSmtp` detrás del puerto `Notificador`, independiente del proveedor (hoy el SMTP de Banahost, aprobado por el CTO el 2026-11-27).
- Correo del aviso y de los recordatorios de NOTIF-02.
- Prueba exógena con mutaciones, contra un servidor SMTP falso local con TLS (`aiosmtpd` y `trustme`), sin red real.

## Límites
- No toca la nube. El buzón, el secreto `evydentia-notif-smtp`, su montaje en Cloud Run y el DMARC son del propietario, por el brief.
- En `requirements.txt` solo añade `aiosmtpd` y `trustme`.
- En `avisos_plataforma.py` (NOTIF-02, tanda anterior) y en la sección `NOTIF-03` de `notificaciones_service.py` solo se añade el envío del correo. En `adaptadores.py` solo se añade el adaptador; `NotificadorNoConfigurado` sigue siendo el de por defecto.
