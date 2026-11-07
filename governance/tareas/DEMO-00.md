+++
id = "DEMO-00"
titulo = "Contrato de la sala demo: compuerta, dominio, repositorio, pasillo y migración"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["EP-01", "GCP-04", "SEC-10"]
propiedad = ["features/demo/__init__.py", "features/demo/demo_service.py", "features/demo/domain/sesion.py", "features/demo/domain/errores.py", "features/demo/domain/eventos.py", "features/demo/domain/plantilla.py", "features/demo/domain/personas.py", "features/demo/domain/contrato.py", "features/demo/repo/", "app_core/pasillo/demo.py", "alembic/versions/20261121_demo_sesiones.py", "tests/test_demo_contrato.py"]
arbitro = "pytest tests/test_demo_contrato.py + tests/test_alembic_una_cabeza.py + tests/test_rls_todas_las_tablas.py en verde + linter ADPA sin cruces"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-00 · Contrato de la sala demo: compuerta, dominio, repositorio, pasillo y migración

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `demo`. Tanda 53.

**Por qué.** Es la pieza común que deja repartir el resto en paralelo. Fija una sola vez la compuerta, el dominio, el repositorio, el pasillo y la tabla; después las demás fichas solo los leen. Va sola en su tanda.

## Entrega
- `demo_service.py` con las firmas definitivas: `entrar`, `terminar`, `estado`, `cambiar_persona`, `resolver_usuario`, `vencer_inactivas`. Cada una delega en el motor de su ficha con importación diferida; si falta, lanza `NotImplementedError` con el id de la ficha. Después nadie edita la compuerta.
- `app_core/pasillo/demo.py`, el único camino de otras salas hacia la demo.
- `domain/sesion.py`: `SesionDemo` con una **lista** de `tenant_id` (hoy siempre uno, §5.6.6), `esta_vencida(ultima_actividad, ahora, minutos=60)` y `TOPE = 20`.
- `domain/errores.py`: `DEMO_NO_AUTORIZADO` 403, `DEMO_OCUPADA` 409, `DEMO_VENCIDA` 401, `DEMO_PERSONA_AJENA` 403 y `DEMO_NO_DISPONIBLE` 503, con el texto literal del §5.6.1 y el cuerpo `{codigo, mensaje}`.
- `domain/personas.py`: `PersonaDemo(usuario_id, nombre, rol, rol_etiqueta, unidad)`, el orden fijo de las seis personas de UX_DEMO_EVYDENTIA.md, sus etiquetas y el rol inicial (administrador de la organización).
- `domain/contrato.py`: forma congelada de `GET /api/v1/demo/estado`, con `personas[]`.
- `domain/eventos.py`: `DEMO_INICIADA`, `DEMO_CAMBIO_PERSONA`, `DEMO_TERMINADA`, `DEMO_VENCIDA`.
- `domain/plantilla.py`: el protocolo escrito de `clonar_desde_plantilla(session, origen, destino, mapa_ids) -> mapa_ids` que implementan DEMO-03a…03f, y el orden de las salas (organización primero).
- `repo/sesiones_repo.py`: obtener la activa por `sub`, contar activas con `pg_advisory_xact_lock`, insertar, renovar actividad y marcar vencida. Sin `DELETE`.
- Migración: tabla `demo_sesiones` y columna `tenants.es_demo boolean not null default false`. `lopdp_app` con SELECT, INSERT y UPDATE, sin DELETE (invariante 63). `demo_sesiones` entra en las exenciones de RLS con su motivo.

## Pruebas
- La compuerta expone exactamente las seis firmas y se importa sin ningún motor.
- `esta_vencida`: 59 minutos no, 60 sí.
- Los cinco errores producen `{codigo, mensaje}` con su estado HTTP y el texto del PRD.
- El repositorio no contiene `DELETE` y la migración no concede DELETE a `lopdp_app`.
- Una sola cabeza de Alembic.

## Límites
- Contrato congelado: rutas, cuerpos y códigos de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, para y consulta a Tech Lead.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS ni `main.py`.
- En archivos con secciones `#ID` escribe solo dentro de tus marcas `# --- INICIO <ID> --- … # --- FIN <ID> ---`.
- Nunca uses la base ni el proyecto de producción; solo datos ficticios con correos `.invalid`.

## Fuentes
- `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` §5.6 (demo comercial) y §5.6.8 (corte confirmado por el Arquitecto ADPA y el CTO, 2026-11-07).
- `governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, invariantes 60 a 63.
- Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Interfaz: `governance/apoyo/UX_DEMO_EVYDENTIA.md` (lo que cambia) sobre `governance/apoyo/UX_DEMO_COMERCIAL.md`.
