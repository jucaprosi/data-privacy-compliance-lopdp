+++
id = "RET-08"
titulo = "Boceto del proveedor de correo anterior retirado; queda el puerto con su doble de pruebas"
ola = "backlog"
estado = "pendiente"
sala = "notificaciones"
depende_de = ["RET-00", "RET-01a", "NOTIF-01"]
propiedad = ["features/notificaciones/services/adaptadores.py", "features/notificaciones/services/__init__.py", "features/notificaciones/notificaciones_service.py", "tests/test_notificaciones.py"]
crea = []
arbitro = "pytest tests/test_notificaciones.py + suite completa en el CI"
rastros = ["¤arbitro"]
+++

# RET-08 · Boceto del proveedor de correo anterior retirado

Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md` (fila RET-08 y §3). Especificación del Arquitecto: `governance/especificaciones/RET-08.md` (por redactar; la ficha no se lanza sin ella). Modelo sugerido: sonnet.

**Problema.** `features/notificaciones/` conserva un boceto de adaptador para el proveedor de correo anterior, que nunca envió nada, y su configuración. Google Cloud no tiene correo transaccional gestionado y el propietario aún no elige proveedor (mapa §3: recomendado, la Gmail API de Google Workspace).

**Entrega.**
- Se borra el boceto del adaptador en `features/notificaciones/services/adaptadores.py` y sus exportaciones en `services/__init__.py` y `notificaciones_service.py`, con sus variables de entorno.
- Queda el puerto `Notificador` con el doble de pruebas (`NotificadorFalso`). La fábrica de la API falla cerrado mientras no haya proveedor: no devuelve el falso, que dice haber enviado.
- `tests/test_notificaciones.py` se reescribe contra el puerto: deja de importar el boceto y conserva lo que afirma sobre el puerto y el doble.
- Mientras el propietario no decida el proveedor, no se crea ningún adaptador nuevo.

**Para el propietario.** Elegir el proveedor y dar la delegación de envío (brief tras esta ficha, `governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`, tabla «Lo que haces fuera del repositorio»).
