+++
id = "NOTIF-03"
titulo = "Correo de las versiones por revisar y de sus recordatorios, por el proveedor que active el propietario"
ola = "D"
estado = "pendiente"
tanda = 113
sala = "notificaciones"
depende_de = ["NOTIF-02"]
propiedad = ["features/notificaciones/services/adaptadores.py", "features/notificaciones/services/correo_versiones.py", "features/notificaciones/notificaciones_service.py", "features/notificaciones/services/avisos_plataforma.py", "tests/test_notif03_correo.py"]
crea = ["features/notificaciones/services/correo_versiones.py", "tests/test_notif03_correo.py"]
arbitro = "pytest tests/test_notif03_correo.py tests/test_adpa_bulkhead.py; mutaciones m1 a m5."
rastros = ["¤arbitro"]
+++

# NOTIF-03 · Correo de las versiones por revisar

**Contrato:** `governance/especificaciones/NOTIF-03.md` (manda sobre esta ficha).

**Origen.** Decisión D7 del CTO (2026-11-25): `main` no tiene proveedor de correo activo, así que el correo va en una ficha aparte de NOTIF-02, con su brief al propietario (`C:\Users\Juan Carlos\compartido\evydentia\briefs\PROPIETARIO_CORREO_Y_PROGRAMACION_AVISOS.md`).

## Entrega
- Adaptador del proveedor de correo detrás del puerto `Notificador`.
- Correo del aviso y de los recordatorios de NOTIF-02.
- Prueba exógena con mutaciones, sin red.

## Límites
- La implementación no empieza hasta que el propietario elija el proveedor de correo en el brief `PROPIETARIO_CORREO_Y_PROGRAMACION_AVISOS.md` (R1). Hasta entonces, la tanda 111 no se lanza.
- No toca la nube. El proveedor, su secreto y su activación son del propietario, por el brief.
- En `avisos_plataforma.py` (NOTIF-02, tanda anterior) y `notificaciones_service.py` solo se añade el envío del correo. En `adaptadores.py` solo se añade el adaptador; `NotificadorNoConfigurado` sigue siendo el de por defecto.
