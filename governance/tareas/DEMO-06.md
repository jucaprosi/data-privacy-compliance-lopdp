+++
id = "DEMO-06"
titulo = "Envíos apagados en modo demo: ningún correo sale con DEMO_MODE=1"
ola = "D"
estado = "pendiente"
sala = "notificaciones"
depende_de = ["NOTIF-01"]
propiedad = ["features/notificaciones/services/adaptadores.py", "tests/test_demo_sin_envios.py"]
arbitro = "pytest tests/test_demo_sin_envios.py + pruebas de notificaciones existentes en verde"
rastros = ["¤demo"]
+++

# DEMO-06 · Envíos apagados en modo demo: ningún correo sale con DEMO_MODE=1

**Por qué.** Las personas de la demo tienen correos `.invalid` y los vendedores no deben recibir avisos de una organización ficticia. Ningún envío puede salir con `DEMO_MODE=1`.

## Entrega
- **`features/notificaciones/services/adaptadores.py`:** con `DEMO_MODE=1` se elige siempre el adaptador nulo (`NotificadorFalso` o equivalente), aunque haya clave del proveedor de correo.

## Pruebas (`tests/test_demo_sin_envios.py`)
- Con `DEMO_MODE=1` y una clave simulada del proveedor, el adaptador elegido es el nulo y no se hace ninguna llamada de red.
- Sin `DEMO_MODE`, la elección no cambia respecto de hoy.

## Límites
- Solo ese archivo y su prueba. No toca `notificaciones_service.py`.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
