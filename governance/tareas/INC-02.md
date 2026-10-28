+++
id = "INC-02"
titulo = "Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica"
ola = "D"
estado = "pendiente"
sala = "incidentes, frontend"
depende_de = ["INC-01", "FE-23", "RM-21", "EVI-02"]
propiedad = ["alembic/versions/20261104_incidentes_asistente.py", "features/incidentes/domain/vulneracion.py", "features/incidentes/services/asistente_engine.py", "features/incidentes/services/informes_engine.py", "features/incidentes/incidentes_service.py#INC-02", "api/routers/incidentes_asistente.py", "tests/test_incidentes_asistente.py", "tests/matriz/INC-02.py", "frontend/src/components/incidentes/**", "frontend/src/lib/incidentes/asistente.ts", "frontend/tests/incidentes/asistente.spec.ts", "frontend/src/components/layout/menus/INC-02.ts", "frontend/src/components/layout/pantallas/INC-02.tsx"]
arbitro = "pytest tests/test_incidentes_asistente.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/incidentes/asistente.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤incidentes", "¤hallazgos"]
+++

# INC-02 · Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica

**Origen.** Menú 5 «Operación › Vulneraciones» y asistente de ocho secciones de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`; norma técnica Res. SPDP-SPD-2026-0040-R (LEG-02).

**Contrato:** `governance/especificaciones/INC-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Asistente (FE-23) de ocho secciones sobre el registro de INC-01: identificación, tratamientos afectados, titulares y datos, descripción y tipo, efectos y medidas, resolución, decisión de notificar con justificación, informes y evidencia de notificación.
- Informes para la SPDP y para titulares con el contenido mínimo de la norma técnica, generados como documento y custodiados como evidencia (EVI-02).
- Las lecciones aprendidas producen hallazgos (`origen = incidente`). **Los plazos no se calculan** (aplazados: LEG-03 y REG-01); el asistente muestra las fechas y deja el cálculo al paquete normativo.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Un incidente completado tiene decisión con justificación obligatoria; el informe contiene las secciones mínimas; cada lección genera un hallazgo.
- Mutación documentada: permitir decidir sin justificación y comprobar que la prueba falla.

## Límites
- Sin cuenta regresiva de plazos; sin envío al SISPDP.
