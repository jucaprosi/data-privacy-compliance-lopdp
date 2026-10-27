+++
id = "DPO-01"
titulo = "La bitácora del DPO se guarda en la base, con permisos por rol y cadena de huellas por organización"
ola = "D"
estado = "pendiente"
sala = "dpo_cockpit, frontend"
depende_de = ["MTGE-02", "API-01", "ORG-06", "FE-17"]
propiedad = ["alembic/versions/20261027_dpo_bitacora.py", "features/dpo_cockpit/**", "api/routers/dpo_cockpit.py", "tests/test_dpo_bitacora.py", "frontend/src/components/modules/DpoCockpitModule.tsx", "frontend/src/lib/dpo/**", "frontend/tests/dpo/**"]
arbitro = "pytest tests/test_dpo_bitacora.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/dpo + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤dpo-independencia", "¤rbac-tenant"]
+++

# DPO-01 · Bitácora del DPO persistida

**Hallazgo (2026-10-26).** La bitácora de dictámenes del DPO (`features/dpo_cockpit/services/bitacora_service.py`) vive **en la memoria del servidor**: cada reinicio o despliegue la borra. Es la constancia de que el delegado asesoró y advirtió, y de que la alta dirección lo recibió (LOPDP, funciones del delegado en los arts. 49 y 50).

Además, las rutas de `api/routers/dpo_cockpit.py` **no comprueban el rol**:
- `POST /dpo/dictamenes` acepta un `dpo_id` cualquiera enviado por el navegador: cualquier usuario puede emitir un dictamen a nombre del DPO.
- `POST /dpo/dictamenes/{id}/acuse` no comprueba la organización: con un id ajeno se firmaría el acuse de otra organización.
- La cadena de huellas es una sola para todas las organizaciones.

## Entrega
- **Migración Alembic** `20261027_dpo_bitacora` (id de revisión de 32 caracteres como máximo), con `down_revision = "20261025_gran_escala_obligacion"`. Tabla de dictámenes por organización con RLS (ENABLE y FORCE, política USING y WITH CHECK por `tenant_id`), con:
  - tipo, asunto, referencia normativa, cuerpo, autor y fecha de emisión;
  - huella SHA-256 y huella anterior, encadenadas **por organización**;
  - acuse: quién y cuándo.
  - Permisos de `lopdp_app`: sin DELETE. La única actualización permitida es registrar el acuse una vez (la sentencia exige que el acuse esté vacío).
- **Servicio:** `bitacora_service.py` deja la memoria y usa la base con la sesión del pedido (patrón de RAT-01 y MTGE-02). Una función verifica la cadena de una organización y devuelve el primer dictamen alterado, si lo hay.
- **Permisos en las rutas:**
  - emite solo el `dpo`; el autor es el usuario autenticado, nunca un id enviado en el cuerpo;
  - consultan la bitácora `dpo`, `admin_organizacion` y `coordinador`;
  - firma el acuse solo `admin_organizacion` (alta dirección), de un dictamen de su organización y una sola vez (409 si ya tenía acuse);
  - cada alta y cada acuse dejan un evento en `audit_events`.
- **Pantalla `DpoCockpitModule.tsx`:**
  - formulario para emitir un dictamen, visible solo para el `dpo`;
  - botón de acuse, visible solo para `admin_organizacion` en dictámenes sin acuse;
  - las llamadas van en `frontend/src/lib/dpo/` con `fetchAutenticado`; no se toca `frontend/src/lib/api.ts`, que es de LIM-01;
  - colores solo con las variables del tema (`--ui-*`, `badge-render-*`).
- **Pruebas:**
  - el dictamen sobrevive a una sesión nueva;
  - un rol distinto del `dpo` no puede emitir (403);
  - el autor es el usuario autenticado aunque el cuerpo traiga otro `dpo_id`;
  - acuse de otra organización: 404; segundo acuse: 409;
  - RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`;
  - alterar el cuerpo de un dictamen en la base rompe la verificación de la cadena;
  - Playwright: el `dpo` emite y ve el dictamen; `admin_organizacion` firma el acuse; otros roles no ven el formulario ni el botón.
- **Prueba de mutación documentada:** quitar la comprobación de rol al emitir y comprobar que la prueba del 403 falla.

## Límites
- No cambia la designación del DPO ni sus incompatibilidades (ORG-06 y ORG-07).
- No se migran dictámenes antiguos: los que había en memoria ya no existen.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
