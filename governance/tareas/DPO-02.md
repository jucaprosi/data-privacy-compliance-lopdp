+++
id = "DPO-02"
titulo = "Informe anual del DPO generado desde su bitácora y estado de inscripción ante la SPDP"
ola = "D"
estado = "pendiente"
sala = "dpo_cockpit, frontend"
depende_de = ["DPO-01", "FE-17"]
propiedad = ["alembic/versions/20261030_dpo_inscripcion.py", "features/dpo_cockpit/domain/inscripcion.py", "features/dpo_cockpit/services/informe_anual_engine.py", "features/dpo_cockpit/services/inscripcion_engine.py", "features/dpo_cockpit/dpo_cockpit_service.py#DPO-02", "api/routers/dpo_informe_anual.py", "tests/test_dpo_informe_anual.py", "frontend/src/components/modules/DpoCockpitModule.tsx", "frontend/src/lib/dpo/informeAnual.ts", "frontend/tests/dpo/informe-anual.spec.ts"]
arbitro = "pytest tests/test_dpo_informe_anual.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/dpo + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤dpo-cockpit", "¤dpo-informe-anual"]
+++

# DPO-02 · Informe anual del DPO generado desde su bitácora y estado de inscripción ante la SPDP

**Origen.** Menú 7 «DPO» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` (Informe anual, Registro SPDP). El delegado supervisa y asesora (art. 49 LOPDP; Reglamento del Delegado, Res. SPDP-SPD-2025-0028-R): el informe resume su actuación, no la ejecuta.

## Entrega
- **Informe anual:** el servidor lo arma desde la bitácora del DPO (DPO-01) para un año: actuaciones por tipo, consultas atendidas, dictámenes y escalamientos. Lo genera el `dpo`; los demás roles lo consultan. Se descarga como documento; la huella de la cadena de la bitácora va en el pie.
- **Inscripción ante la SPDP:** registro por organización de si el delegado está inscrito, fecha y número de trámite, con su historial (append-only). Lo registra `admin_organizacion`; el `dpo` lo consulta.
- `DpoCockpitModule.tsx`: dos pestañas nuevas, «Informe anual» e «Inscripción SPDP».
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- El informe de un año solo incluye actuaciones de ese año y de esa organización; un rol que no es `dpo` recibe 403 al generarlo.
- La inscripción no se edita ni se borra (42501 con `lopdp_app`); RLS entre organizaciones.
- Mutación documentada: incluir actuaciones de otro año y comprobar que la prueba falla.

## Límites
- **Sin plazos ni calendario de obligaciones:** los plazos siguen aplazados por decisión del propietario (LEG-02, LEG-03). El calendario se abre cuando el paquete normativo los tenga (REG-01).
