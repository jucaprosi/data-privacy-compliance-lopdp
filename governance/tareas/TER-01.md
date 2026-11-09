+++
id = "TER-01"
titulo = "Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía"
ola = "D"
estado = "pendiente"
sala = "terceros, transferencias"
depende_de = ["RM-21", "EVI-02", "ADPA-05", "ADPA-06", "ADPA-08", "FE-28"]
propiedad = ["alembic/versions/20261106_terceros_garantias.py", "features/terceros/services/garantias_engine.py", "features/terceros/terceros_service.py#TER-01", "features/transferencias/transferencias_service.py#TER-01", "api/routers/terceros_garantias.py", "tests/test_terceros_garantias.py", "tests/matriz/TER-01.py", "frontend/src/components/modules/TercerosModule.tsx", "frontend/src/lib/terceros/garantias.ts", "frontend/tests/terceros/garantias.spec.ts", "features/terceros/domain/errores.py#TER-01", "app_core/pasillo/terceros.py#TER-01", "app_core/pasillo/rat.py#TER-01", "frontend/tests/textos/excepciones/TER-01.txt"]
arbitro = "pytest tests/test_terceros_garantias.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/terceros/garantias.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤hallazgos", "¤evidencias"]
+++

# TER-01 · Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía

**Origen.** Menú 3 «Encargados y terceros» y documento maestro RN-TER-01 y RN-TER-02, vía `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/TER-01.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Por tercero: rol (encargado, destinatario, corresponsable, transferencia internacional), país, contrato (referencia a evidencia) con vigencia, garantía de transferencia (tipo y referencia), criticidad y próxima revisión.
- Un encargado sin contrato vigente ⇒ hallazgo `tercero` de severidad `alta`; una transferencia internacional sin garantía ⇒ hallazgo `critica`; al corregir, se cierran.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).

- **Texto de carga** (FE-28, Arquitecto 2026-11-08): `TercerosModule.tsx:79` deja de decir «… desde FastAPI...» y dice «Cargando terceros…». Si existe `frontend/tests/textos/excepciones/TER-01.txt` (lo crea FE-28), TER-01 lo borra.

## Pruebas
- Los dos hallazgos se generan y cierran; son idempotentes; RLS.
- Mutación documentada: no generar el de transferencia y comprobar que la prueba falla.

## Límites
- El cuestionario por portal externo es TER-02.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#TER-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#TER-01` sin modificar `app_core/errors.py`.
