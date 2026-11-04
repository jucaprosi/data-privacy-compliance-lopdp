+++
id = "FIRMA-02"
titulo = "Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash"
ola = "D"
estado = "pendiente"
sala = "firma_electronica, frontend"
depende_de = ["FIRMA-01", "EVI-02", "BIB-107", "ADPA-05", "ADPA-06", "ADPA-07"]
propiedad = ["alembic/versions/20261103_aceptaciones.py", "features/firma_electronica/domain/aceptacion.py", "features/firma_electronica/services/aceptacion_engine.py", "features/firma_electronica/firma_electronica_service.py#FIRMA-02", "api/routers/firma_aceptaciones.py", "api/routers/publico_aceptacion.py", "tests/test_firma_aceptaciones.py", "tests/matriz/FIRMA-02.py", "frontend/src/app/aceptar/**", "frontend/src/components/firma/**", "frontend/src/lib/firma/aceptaciones.ts", "frontend/tests/firma/aceptacion.spec.ts", "features/firma_electronica/domain/errores.py#FIRMA-02", "app_core/pasillo/firma_electronica.py#FIRMA-02", "app_core/pasillo/evidencias.py#FIRMA-02", "app_core/pasillo/rat.py#FIRMA-02", "app_core/pasillo/riesgos_mtge.py#FIRMA-02", "app_core/pasillo/derechos_arco.py#FIRMA-02", "frontend/src/components/layout/menus/index.ts#FIRMA-02", "frontend/src/components/pantallas/index.tsx#FIRMA-02"]
arbitro = "pytest tests/test_firma_aceptaciones.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/firma/aceptacion.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤firma-electronica", "¤evidencias"]
+++

# FIRMA-02 · Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash

**Origen.** Decisión 4 del propietario (2026-10-28), PRD Biblioteca G («Firmas») y menú 4 › Firmas y Configuración › Verificar documento.

**Contrato:** `governance/especificaciones/FIRMA-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Envío de un documento aprobado a una o varias personas de la organización (ORG-17) por enlace con caducidad; la persona acepta con un clic y el servidor registra nombre, correo, fecha y hora, IP y `sha256` del documento; el acuse se custodia como evidencia (EVI-02).
- Verificar documento: subir un archivo y comprobar si su hash coincide con un documento aprobado o un acuse de la organización.
- La firma con certificado (ANF, Radical) sigue fuera del alcance (FIRMA-01, §5.9).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Un enlace caducado o ya usado responde 410; el acuse queda como evidencia con el hash del documento; verificar un archivo alterado responde «no coincide».
- Mutación documentada: aceptar sin registrar la IP y comprobar que la prueba falla.

## Límites
- No firma con certificado; no envía correos (los enlaces se entregan por NOTIF-01 si está disponible, o se copian).


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#FIRMA-02` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#FIRMA-02` sin modificar `app_core/errors.py`.
