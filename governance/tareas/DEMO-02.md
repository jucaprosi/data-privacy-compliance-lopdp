+++
id = "DEMO-02"
titulo = "Una organización demo por sesión: copia de la plantilla, vencimiento lógico y purga nocturna"
ola = "D"
estado = "pendiente"
sala = "demo, organizacion"
depende_de = ["DEMO-01", "DEMO-03", "SEC-10"]
propiedad = ["features/demo/demo_service.py#DEMO-02", "features/demo/services/sesiones_engine.py", "api/routers/demo_sesiones.py", "features/organizacion/organizacion_service.py#DEMO-02", "features/organizacion/services/plantilla_engine.py", "scripts/demo/purgar_demos_vencidas.py", "tests/demo/test_demo_sesiones.py", "tests/demo/test_demo_purga.py"]
arbitro = "pytest tests/demo/test_demo_sesiones.py tests/demo/test_demo_purga.py contra una rama Neon de prueba + linter ADPA sin cruces; prueba de mutación documentada"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-02 · Una organización demo por sesión: copia de la plantilla, vencimiento lógico y purga nocturna

**Por qué.** Varios vendedores usan la demo a la vez sin verse: cada entrada recibe su propia organización. La aplicación no puede borrar (SEC-10 e `INV_LOPDP_AUDIT_LOG_APPEND_ONLY`), así que el borrado va en dos tiempos.

## Entrega
- **`POST /demo/entrar` (router propio `api/routers/demo_sesiones.py`, `AUTO_REGISTRO` solo con `DEMO_MODE=1`):** vendedor autorizado (DEMO-01) ⟹ vence las organizaciones demo inactivas por más de 60 minutos ⟹ vence la demo anterior del mismo vendedor (motivo `reemplazo`) ⟹ comprueba el tope de 20 activas (si está lleno, 409 `DEMO_OCUPADA`) ⟹ copia la plantilla ⟹ crea la sesión con la persona Administrador ⟹ devuelve el mismo cuerpo que `GET /demo/estado`.
- **`POST /demo/terminar`:** marca la sesión y su organización como vencidas (motivo `terminar`). Desde ese momento cualquier petición de esa sesión responde 401 `DEMO_VENCIDA`.
- **Actividad:** cada petición de una sesión activa renueva `ultima_actividad`. Una sesión que pasó 60 minutos sin actividad responde 401 `DEMO_VENCIDA` y queda marcada.
- **`organizacion_service.clonar_organizacion_plantilla(origen, marcar_demo=True)` (`#DEMO-02`)**, implementada en `services/plantilla_engine.py`: copia la plantilla a un tenant nuevo con sus cuatro personas y sus roles. **Se niega a funcionar sin `DEMO_MODE=1`** y solo acepta como origen un tenant `es_demo` marcado como plantilla. `features/demo` la llama solo a través de `organizacion_service`.
- **`scripts/demo/purgar_demos_vencidas.py`:** borra todas las filas de las organizaciones demo vencidas, en todas las tablas con `tenant_id`, más sus filas de `users`, `user_tenant_roles` y `demo_sesiones`. Aborta si `apunta_a_produccion()` es verdadero. Nunca toca la plantilla. Lo ejecuta cada noche un flujo de GitHub Actions con la credencial del dueño de la rama `demo`, que no existe en Vercel. El flujo es gobernanza reservada: esta tarea entrega su parche en el informe y lo aplica una persona (DEMO-05).

## Pruebas
- `test_demo_sesiones.py`: dos entradas crean dos tenants distintos y uno no ve los datos del otro; la entrada 21 responde 409; una segunda entrada del mismo vendedor vence la primera, que recibe 401 `DEMO_VENCIDA`; «Terminar» y luego cualquier petición, 401; reloj simulado a 61 minutos, 401 y estado `vencida`; sin `DEMO_MODE`, `clonar_organizacion_plantilla` lanza error.
- `test_demo_purga.py`: tras purgar, ninguna tabla con `tenant_id` conserva filas del tenant purgado; la plantilla queda intacta; con la URL de producción aborta.
- Mutación documentada: quitar el filtro `es_demo` de la purga hace fallar «plantilla intacta».

## Límites
- **`organizacion_service#DEMO-02` es solo aditivo (CTO, 2026-11-06):** funciones nuevas para clonar o vencer la organización demo, sin cambiar ninguna firma existente de la compuerta de `organizacion`. Ninguna otra ficha de la sala `organizacion` va en su tanda (55).
- Sin migraciones y sin tocar `app_core/security.py` ni `api/routers/demo.py` (dueña: DEMO-01). Solo añade su sección `#DEMO-02` a la compuerta `demo_service.py`.
- La aplicación no ejecuta DELETE. Solo el script de purga borra.
- No cambia `roles.py`, el trigger del DPO ni la RLS.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y proyección ADPA del Arquitecto de soluciones: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; vencimiento a los 60 minutos sin actividad; tope de 20 demos activas; lista `DEMO_VENDEDORES` en Vercel; dirección `*.vercel.app`; una sola demo activa por vendedor (la nueva entrada vence la anterior, motivo `reemplazo`).
