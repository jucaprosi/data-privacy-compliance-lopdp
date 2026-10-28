+++
id = "ORG-20"
titulo = "Papelera (archivar y restaurar) y exportación completa de los datos de la organización"
ola = "D"
estado = "pendiente"
sala = "organizacion, plataforma, frontend"
depende_de = ["ORG-17", "EVI-02"]
propiedad = ["alembic/versions/20261107_papelera.py", "features/organizacion/services/papelera_engine.py", "features/organizacion/services/exportacion_engine.py", "features/organizacion/organizacion_service.py#ORG-20", "features/plataforma/plataforma_service.py#ORG-20", "api/routers/organizacion_papelera.py", "tests/test_organizacion_papelera.py", "tests/matriz/ORG-20.py", "frontend/src/components/organizacion/papelera/**", "frontend/tests/organizacion/papelera.spec.ts", "frontend/src/components/layout/menus/ORG-20.ts", "frontend/src/components/layout/pantallas/ORG-20.tsx"]
arbitro = "pytest tests/test_organizacion_papelera.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/organizacion/papelera.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-20 · Papelera (archivar y restaurar) y exportación completa de los datos de la organización

**Origen.** Menú 9 «Configuración › Papelera» y «Exportar datos» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`; PRD apartado 7 («Papelera y exportación»).

**Contrato:** `governance/especificaciones/ORG-20.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Papelera: todo registro retirado (`retirado_en`) de inventario, RAT, documentos y terceros se lista y se puede restaurar; nada se borra físicamente desde la aplicación.
- Exportación completa de la organización (ZIP con JSON por entidad, documentos y evidencias) que pide el `admin_organizacion`; el archivo se genera en segundo plano y se descarga por enlace con caducidad; queda evento de auditoría.
- El borrado definitivo solo existe al cerrar la organización y lo hace el operador de la plataforma (ORG-09) tras una exportación.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Restaurar devuelve el registro; la exportación contiene todas las entidades y la huella de cada evidencia; `lopdp_app` no puede `DELETE` (42501).
- Mutación documentada: borrar físicamente al retirar y comprobar que la prueba falla.

## Límites
- Sin transferencia de organización entre cuentas (decisión abierta).
