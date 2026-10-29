+++
id = "CAPA-04"
titulo = "Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa, frontend"
depende_de = ["CAPA-02", "RM-21", "EVI-02", "DIAG-03"]
propiedad = ["alembic/versions/20261106_auditoria_grilla.py", "features/auditoria_capa/domain/auditoria.py", "features/auditoria_capa/services/grilla_engine.py", "features/auditoria_capa/auditoria_capa_service.py#CAPA-04", "api/routers/auditoria_grilla.py", "tests/test_auditoria_grilla.py", "tests/matriz/CAPA-04.py", "frontend/src/components/auditoria/**", "frontend/src/lib/auditoria/**", "frontend/tests/auditoria/**", "frontend/src/components/layout/menus/CAPA-04.ts", "frontend/src/components/layout/pantallas/CAPA-04.tsx"]
arbitro = "pytest tests/test_auditoria_grilla.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/auditoria + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤auditoria-capa", "¤hallazgos"]
+++

# CAPA-04 · Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción

**Origen.** Menú 6 «Auditorías» y conflicto D-4 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: acta de auditoría por área, nunca certificado (Doctrina 1).

**Contrato:** `governance/especificaciones/CAPA-04.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Auditoría con alcance (tratamientos, áreas, equipo auditor); grilla por control: lo declarado (último resultado sellado, DIAG-03), riesgo inicial, lo verificado, evidencia (referencia EVI-02), riesgo final, revisado por.
- Conclusiones y **acta por área** (alcance, lo verificado, evidencia revisada) custodiada como evidencia; la palabra «certificado» no aparece.
- Cada fila `verificado < declarado` produce un hallazgo `auditoria`. El auditor no audita controles que él ejecutó (SoD).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Una fila verificada por debajo de lo declarado genera un hallazgo; el acta existe por área y no contiene «certificado»; quien ejecutó un control no puede verificarlo (403).
- Mutación documentada: permitir que el ejecutor verifique y comprobar que la prueba falla.

## Límites
- Sin programa anual automático (fechas: REG-01).
