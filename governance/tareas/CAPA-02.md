+++
id = "CAPA-02"
titulo = "Controles periódicos con frecuencia y responsable; el control vencido genera un hallazgo"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa, frontend"
depende_de = ["CAPA-01", "RM-21", "FE-22"]
propiedad = ["alembic/versions/20261030_controles_periodicos.py", "features/auditoria_capa/**", "api/routers/auditoria_capa_controles.py", "tests/test_controles_periodicos.py", "tests/test_matriz_permisos.py#CAPA-02", "frontend/src/components/controles/**", "frontend/src/lib/controles/**", "frontend/tests/controles/**", "frontend/src/components/layout/dashboardNavigation.ts#CAPA-02", "frontend/src/app/dashboard/page.tsx#CAPA-02"]
arbitro = "pytest tests/test_controles_periodicos.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes + Playwright de frontend/tests/controles + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤auditoria-capa", "¤controles-periodicos", "¤hallazgos"]
+++

# CAPA-02 · Controles periódicos con frecuencia y responsable; el control vencido genera un hallazgo

**Origen.** Optimización O-8 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` (menú 6 «Riesgos y auditoría» › Controles periódicos).

## Entrega
- Control periódico por organización: nombre, requisito o control, frecuencia (mensual, trimestral, semestral, anual), responsable (persona con rol vigente), próxima verificación y estado.
- Registrar una verificación (con referencia a evidencia, sin custodiarla: O-3) mueve la próxima fecha.
- **Vencido:** pasada la próxima verificación sin registro, el control pasa a `vencido` y produce **un** hallazgo por la compuerta de `roadmap` (`registrar_hallazgo`, RM-21, origen `control_periodico`); no crea tareas por su cuenta.
- Lo verifica `implementador` o el responsable; el `dpo` consulta (D-2). Fila en `tests/test_matriz_permisos.py` sección `#CAPA-02`.
- Pantalla en Riesgos y auditoría (secciones `#CAPA-02`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Un control vencido produce exactamente un hallazgo aunque se revise dos veces; registrar la verificación lo devuelve a vigente.
- Mutación documentada: crear la tarea directamente en lugar del hallazgo y comprobar que la prueba (sin tareas creadas desde `auditoria_capa`) falla.

## Límites
- La reapertura por **evidencia vencida** espera a la vigencia de evidencias (EVI-02). El acta por área (D-4) es otra tarea.
