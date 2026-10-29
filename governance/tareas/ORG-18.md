+++
id = "ORG-18"
titulo = "Sedes de la organización y clientes cuando actúa como encargada"
ola = "D"
estado = "pendiente"
sala = "organizacion, frontend"
depende_de = ["ORG-16", "ORG-17"]
propiedad = ["alembic/versions/20261102_sedes_clientes.py", "features/organizacion/services/sedes_engine.py", "features/organizacion/organizacion_service.py#ORG-18", "api/routers/organizacion_sedes.py", "tests/test_organizacion_sedes.py", "tests/matriz/ORG-18.py", "frontend/src/components/organizacion/sedes/**", "frontend/tests/organizacion/sedes.spec.ts", "frontend/src/components/layout/menus/ORG-18.ts", "frontend/src/components/layout/pantallas/ORG-18.tsx"]
arbitro = "pytest tests/test_organizacion_sedes.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/organizacion/sedes.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤inventario"]
+++

# ORG-18 · Sedes de la organización y clientes cuando actúa como encargada

**Origen.** Menú 3 «Inventario › Sedes y áreas» y «Clientes (si es encargado)» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/ORG-18.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Sedes: nombre, dirección, ciudad, provincia, medidas físicas, punto de contacto para la SPDP y para titulares; una sede principal.
- Clientes: cuando `rol_datos ∈ {encargado, ambos}`, organizaciones para las que trata datos, con contrato recibido (referencia a evidencia) y vigencia.
- Entrada en el menú Inventario (`menus/ORG-18.ts`, `pantallas/ORG-18.tsx`); al aparecer después de FE-22, posee también `menus/index.ts#ORG-18` y `pantallas/index.tsx#ORG-18`.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Solo una sede principal (409 al marcar otra); clientes solo si la organización es encargada (409).
- Mutación documentada: permitir dos principales y comprobar que la prueba falla.

## Límites
- No crea contratos: referencia evidencias (EVI-02) o documentos (BIB).
