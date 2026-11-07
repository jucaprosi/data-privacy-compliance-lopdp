+++
id = "DEMO-00"
titulo = "Contrato de la sala demo: compuerta con firmas definitivas, dominio, repositorio y migración"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["SEC-10", "RM-00"]
propiedad = ["features/demo/__init__.py", "features/demo/demo_service.py", "features/demo/domain/sesion.py", "features/demo/domain/errores.py", "features/demo/domain/eventos.py", "features/demo/repo/", "alembic/versions/20261121_demo_sesiones.py", "tests/test_demo_contrato.py"]
arbitro = "pytest tests/test_demo_contrato.py + tests/test_alembic_una_cabeza.py + tests/test_rls_todas_las_tablas.py en verde + linter ADPA sin cruces"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-00 · Contrato de la sala demo: compuerta con firmas definitivas, dominio, repositorio y migración

**Por qué.** Es la pieza común que permite repartir el resto en paralelo. Fija una sola vez la compuerta, el dominio, el repositorio y la tabla; después las demás fichas solo los leen. Va sola en la primera tanda y se fusiona antes de abrir la siguiente.

## Entrega
- **`features/demo/demo_service.py`**, compuerta con las firmas definitivas: `entrar`, `terminar`, `estado`, `cambiar_persona`, `resolver_usuario`, `vencer_inactivas`. Cada una delega en el motor de su ficha con **importación diferida dentro de la función**, así la compuerta se importa aunque el motor aún no exista. Si el motor falta, la llamada lanza `NotImplementedError` con el nombre de la ficha que lo crea. Después de esta ficha **nadie edita la compuerta**.
- **`domain/sesion.py`:** entidad `SesionDemo`; regla pura `esta_vencida(ultima_actividad, ahora, minutos=60)`; `TOPE = 20`.
- **`domain/errores.py`:** `DEMO_NO_AUTORIZADO` (403), `DEMO_OCUPADA` (409), `DEMO_VENCIDA` (401) y `DEMO_PERSONA_AJENA` (403), cada uno con su texto de `UX_DEMO_COMERCIAL.md` y el cuerpo `{codigo, mensaje}`.
- **`domain/eventos.py`:** `DEMO_INICIADA`, `DEMO_CAMBIO_PERSONA`, `DEMO_TERMINADA`, `DEMO_VENCIDA`.
- **`repo/sesiones_repo.py`:** todas las consultas a `demo_sesiones`: obtener la activa por `sub`, contar activas con bloqueo (`FOR UPDATE`), insertar, renovar actividad y marcar vencida. **Sin DELETE.**
- **Migración `20261121_demo_sesiones.py`:** tabla `demo_sesiones` (`id`, `vendedor_email`, `vendedor_sub`, `tenant_id`, `persona_usuario_id`, `estado` activa/vencida, `creada_en`, `ultima_actividad`, `vencida_en`, `motivo` terminar/inactividad/reemplazo) y columna `tenants.es_demo boolean not null default false`. `lopdp_app`: SELECT, INSERT y UPDATE, sin DELETE (SEC-10). Es aditiva y llega también a producción, donde la tabla queda vacía. `demo_sesiones` entra en las `EXENCIONES` de `tests/test_rls_todas_las_tablas.py` con su motivo: el resolutor la lee antes de conocer el tenant.

## Pruebas (`tests/test_demo_contrato.py`)
- La compuerta expone exactamente las seis firmas y se importa sin ningún motor presente.
- `esta_vencida`: 59 minutos, no; 60 minutos, sí (límite incluido).
- Los cuatro errores producen `{codigo, mensaje}` con su estado HTTP.
- El repositorio no contiene `DELETE` (búsqueda en el código fuente) y la migración no concede DELETE a `lopdp_app`.
- Una sola cabeza de Alembic.

## Límites
- **Contrato congelado (CTO, 2026-11-06):** rutas, cuerpos, códigos 401/403/409 y `X-Role` de `FLUJOS_DEMO_COMERCIAL.md` §3, y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, se para y se consulta a la Coordinadora; las fichas afectadas se ajustan en la misma tanda.
- No toca `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS, `api/rbac.py` ni `main.py`.
- Sin rutas, sin resolutor y sin lógica de entrada: solo contrato. Seguridad y la Coordinadora revisan las firmas antes de fusionar.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
