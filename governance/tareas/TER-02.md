+++
id = "TER-02"
titulo = "Cuestionario de garantías del encargado por portal externo, con revisión e informe"
ola = "D"
estado = "pendiente"
sala = "terceros, frontend"
depende_de = ["TER-01", "SEC-12", "FE-23"]
propiedad = ["alembic/versions/20261107_terceros_cuestionario.py", "features/terceros/services/cuestionario_engine.py", "features/terceros/terceros_service.py#TER-02", "api/routers/publico_terceros.py", "api/routers/terceros_cuestionario.py", "tests/test_terceros_cuestionario.py", "tests/matriz/TER-02.py", "frontend/src/app/proveedor/**", "frontend/src/components/terceros/**", "frontend/tests/terceros/cuestionario.spec.ts"]
arbitro = "pytest tests/test_terceros_cuestionario.py contra una rama Neon de revisión + suite completa + Playwright de frontend/tests/terceros/cuestionario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12"
rastros = ["¤seguridad", "¤evidencias"]
+++

# TER-02 · Cuestionario de garantías del encargado por portal externo, con revisión e informe

**Origen.** Menú 6 «Garantías de encargados» y asistente «Garantías del encargado» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/TER-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Envío del cuestionario desde la ficha del tercero por enlace con caducidad; el proveedor responde por portal externo con evidencias; revisión por el responsable (conforme, pedir corrección, rechazar); informe y próxima fecha de revisión.
- Límites de abuso de SEC-12; el portal no muestra datos de la organización más allá del nombre.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Enlace caducado 410; el proveedor solo ve su cuestionario; la revisión «conforme» cierra el hallazgo de garantía (TER-01) si aplica.
- Mutación documentada: permitir ver otro cuestionario con el token y comprobar que la prueba falla.

## Límites
- Sin cuenta de proveedor.
