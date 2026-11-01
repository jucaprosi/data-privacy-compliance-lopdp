+++
id = "REG-02"
titulo = "Centro de conocimiento: normativa de Ecuador, resúmenes y ayuda contextual que cita la base legal"
ola = "D"
estado = "hecha"
sala = "regulacion_rag, frontend"
depende_de = ["FE-22"]
propiedad = ["features/regulacion_rag/services/conocimiento_engine.py", "features/regulacion_rag/regulacion_rag_service.py#REG-02", "api/routers/conocimiento.py", "tests/test_conocimiento.py", "tests/matriz/REG-02.py", "frontend/src/components/conocimiento/**", "frontend/src/lib/conocimiento/**", "frontend/src/components/AyudaContextual.tsx", "frontend/tests/conocimiento/**", "frontend/src/components/layout/menus/REG-02.ts", "frontend/src/components/layout/pantallas/REG-02.tsx"]
arbitro = "pytest tests/test_conocimiento.py + suite completa + Playwright de frontend/tests/conocimiento + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_AI_RAG_STRICT_CITATION)"
rastros = ["¤regulation-code", "¤frontend-ide"]
+++

# REG-02 · Centro de conocimiento: normativa de Ecuador, resúmenes y ayuda contextual que cita la base legal

**Origen.** Menú 8 «Conocimiento» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` y PRD apartado 6 («Centro de conocimiento»).

**Contrato:** `governance/especificaciones/REG-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Pantallas Conocimiento › Normativa Ecuador (corpus versionado de `regulacion_rag`, por fuente y artículo), Resúmenes y guías (documentos del catálogo marcados como guía) y Ayuda.
- Componente `AyudaContextual` reutilizable: dado un `control_ref` o un artículo, muestra el texto del corpus con su cita; si no hay fuente, dice «sin fuente en el corpus» (Doctrina 7).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Toda ayuda muestra artículo y fuente o el aviso de ausencia; nunca texto sin cita.
- Mutación documentada: devolver ayuda sin cita y comprobar que la prueba falla.

## Límites
- Sin cursos base ni material comercial (fase 5).
