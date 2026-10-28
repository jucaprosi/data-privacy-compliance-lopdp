+++
id = "FOR-01"
titulo = "Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación"
ola = "D"
estado = "pendiente"
sala = "formacion, frontend"
depende_de = ["ORG-17", "EVI-02", "FE-22"]
propiedad = ["features/formacion/**", "alembic/versions/20261105_formacion.py", "api/routers/formacion.py", "tests/test_formacion.py", "tests/matriz/FOR-01.py", "frontend/src/components/formacion/**", "frontend/src/lib/formacion/**", "frontend/tests/formacion/**", "frontend/src/components/layout/menus/FOR-01.ts", "frontend/src/components/layout/pantallas/FOR-01.tsx"]
arbitro = "pytest tests/test_formacion.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/formacion + tsc --noEmit + npm run build; adpa_linter (sala nueva con compuerta formacion_service.py); prueba de mutación documentada"
rastros = ["¤evidencias", "¤rbac-tenant"]
+++

# FOR-01 · Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación

**Origen.** Menú 5 «Operación › Formación» y PRD Módulo 2 («Formación, sala formacion, fase posterior»).

**Contrato:** `governance/especificaciones/FOR-01.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Sala nueva `features/formacion/` con compuerta `formacion_service.py` (la primera tarea de una sala crea la sala, ADPA).
- Contenidos (PDF o enlace a video) y banco de preguntas; acción formativa con personas (ORG-17), fechas, examen, nota mínima; seguimiento por persona (enviado, iniciado, terminado, nota) y cobertura = personas formadas / personas que tratan datos.
- El diploma y el registro de notas se custodian como evidencia del control de capacitación (EVI-02, control P-correspondiente del catálogo).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Una persona con nota ≥ mínima queda «formada» y existe su evidencia; la cobertura se calcula sobre personas activas; RLS entre organizaciones.
- Mutación documentada: contar como formada una nota inferior a la mínima y comprobar que la prueba falla.

## Límites
- Sin cursos base de la plataforma (fase 5); sin SCORM.
