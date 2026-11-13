+++
id = "MTGE-03"
titulo = "EIPD guiada de ocho pasos con asistente de obligatoriedad, decisión documentada e informe final"
ola = "D"
estado = "en_curso"
sala = "riesgos_mtge, frontend"
depende_de = ["MTGE-02", "FE-23", "RM-21", "EVI-02", "ADPA-05", "ADPA-06", "ADPA-07"]
propiedad = ["alembic/versions/mtge03_eipd_guiada.py", "features/riesgos_mtge/domain/eipd.py", "features/riesgos_mtge/services/eipd_engine.py", "features/riesgos_mtge/riesgos_mtge_service.py#MTGE-03", "api/routers/eipd_guiada.py", "tests/test_eipd_guiada.py", "tests/matriz/MTGE-03.py", "frontend/src/components/eipd/**", "frontend/src/lib/eipd/**", "frontend/tests/eipd/**", "frontend/src/components/layout/menus/MTGE-03.ts", "frontend/src/components/layout/pantallas/MTGE-03.tsx", "features/riesgos_mtge/domain/errores.py#MTGE-03", "app_core/pasillo/riesgos_mtge.py#MTGE-03", "app_core/pasillo/rat.py#MTGE-03", "app_core/pasillo/organizacion.py#MTGE-03", "app_core/pasillo/firma_electronica.py#MTGE-03", "app_core/pasillo/dpo_cockpit.py#MTGE-03", "frontend/src/components/layout/menus/index.ts#MTGE-03", "frontend/src/components/layout/pantallas/index.tsx#MTGE-03", "app_core/pasillo/roadmap.py#MTGE-03", "app_core/pasillo/evidencias.py#MTGE-03", "tests/matriz/roles/auditor.py#MTGE-03"]
arbitro = "pytest tests/test_eipd_guiada.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/eipd + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤riesgos-eipd", "¤mtge-granescala", "¤hallazgos"]
+++

# MTGE-03 · EIPD guiada de ocho pasos con asistente de obligatoriedad, decisión documentada e informe final

**Origen.** Menú 6 «Riesgos y auditoría › Evaluaciones de impacto» y asistente de ocho pasos de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`; PRD Módulo 3 («EIPD guiada»).

**Contrato:** `governance/especificaciones/MTGE-03.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Asistente (FE-23): identificación y obligatoriedad precargada desde el RAT y el motor MTGE (`INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER`); consulta a titulares; ciclo de vida y amenazas; necesidad y proporcionalidad; incumplimientos (→ hallazgos `eipd`); riesgos inherente y residual; decisión (aceptar, nuevas medidas, consulta previa a la SPDP (*)); informe final custodiado como evidencia.
- Un riesgo residual alto impide cerrar sin decisión documentada.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Con MTGE obligatorio la EIPD no puede marcarse «no obligatoria»; con residual alto no cierra sin decisión; cada incumplimiento genera hallazgo.
- Mutación documentada: cerrar con residual alto sin decisión y comprobar que la prueba falla.

## Límites
- Catálogos de amenazas y medidas en código hasta REG-01; sin firma electrónica del informe (FIRMA-02 lo puede enviar a aceptación).


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#MTGE-03` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#MTGE-03` sin modificar `app_core/errors.py`.

## Decisiones del Tech Lead (2026-11-13)
- La custodia del informe por `pasillo/evidencias.py#MTGE-03` espera a EVI-04. No se declara como dependencia porque rompería R4: va detrás de un puerto con doble y falla cerrado.
