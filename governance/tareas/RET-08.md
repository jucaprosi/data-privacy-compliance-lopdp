+++
id = "RET-08"
titulo = "El notificador opera tras puerto desacoplado con doble de pruebas"
ola = "backlog"
estado = "hecha"
sala = "notificaciones"
depende_de = ["RET-00", "RET-01a", "NOTIF-01"]
propiedad = ["features/notificaciones/services/adaptadores.py", "features/notificaciones/services/__init__.py", "features/notificaciones/notificaciones_service.py", "tests/test_notificaciones.py"]
crea = []
arbitro = "pytest tests/test_notificaciones.py + suite completa en el CI"
rastros = ["¤arbitro"]
+++

# RET-08 · El notificador como puerto desacoplado

Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md` (fila RET-08 y §3). Especificación del Arquitecto: `governance/especificaciones/RET-08.md`. Modelo sugerido: sonnet.

**Problema.** Desacoplar el despacho de notificaciones tras el puerto `Notificador` hasta que el propietario seleccione el proveedor corporativo en Google Cloud (mapa §3: recomendado, Gmail API de Google Workspace).

**Entrega.**
- `features/notificaciones/services/adaptadores.py` expone `NotificadorNoConfigurado` y `NotificadorEntornoPermitido`, junto con el puerto `Notificador` y el doble de pruebas `NotificadorFalso`.
- La fábrica `notificador_configurado()` falla cerrado con estado `PENDIENTE` hasta configurar un adaptador productivo.
- `tests/test_notificaciones.py` valida el puerto, `NotificadorFalso` y el fallo cerrado sin proveedor.

**Para el propietario.** Elegir el proveedor y dar la delegación de envío (brief tras esta ficha, `governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`, tabla «Lo que haces fuera del repositorio»).
