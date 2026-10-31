+++
id = "ORG-16"
titulo = "Alta de la organización en el servidor con el asistente de siete pasos, en lugar de la configuración local"
ola = "D"
estado = "pendiente"
sala = "organizacion, frontend"
depende_de = ["ORG-14", "ORG-07", "FE-08", "FE-16", "FE-22", "FE-23", "RM-21", "CAPA-02"]
propiedad = ["features/organizacion/services/alta_engine.py", "features/organizacion/organizacion_service.py#ORG-16", "api/routers/organizacion_alta.py", "tests/test_organizacion_alta.py", "tests/matriz/ORG-16.py", "frontend/src/components/ProjectConfig.tsx", "frontend/src/components/organizacion/alta/**", "frontend/src/lib/organizacion/alta.ts", "frontend/tests/organizacion/alta.spec.ts", "frontend/src/components/layout/menus/ORG-16.ts", "frontend/src/components/layout/pantallas/ORG-16.tsx", "alembic/versions/20261101_org16_perfil_alta.py", "app_core/models_base.py", "app_core/models.py", "features/organizacion/services/configuracion_engine.py", "features/organizacion/services/datos_documentales_engine.py", "features/organizacion/services/invitaciones_personas_engine.py", "frontend/tests/navegacion/menus.spec.ts"]
arbitro = "pytest tests/test_organizacion_alta.py contra una rama Neon de revisión con lopdp_app + suite completa + Playwright de frontend/tests/organizacion/alta.spec.ts + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤alta-organizacion", "¤asistente"]
+++

# ORG-16 · Alta de la organización en el servidor con el asistente de siete pasos, en lugar de la configuración local

**Origen.** Optimización O-7 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` y Doctrina 9 (la ficha antecede al cuestionario). Hoy el Módulo 0 (`ProjectConfig.tsx`) guarda la configuración en el navegador (`isConfigured` en Zustand).

## Entrega
- Asistente de siete pasos con el patrón de FE-23: perfil, sedes, áreas, tratamientos sugeridos, terceros típicos, personas clave y resumen. Cada paso guarda en el servidor al terminarlo.
- Lo que ya tiene sala se escribe por su compuerta: datos documentales (ORG-14), sedes y áreas (ORG-07). Tratamientos y terceros sugeridos se ofrecen como **estructura** (catálogo), nunca datos personales de otra organización (D-5).
- Personas clave: solo nombre, cargo, área y correo (D-6); nada de cédula.
- El alta la hace `admin_organizacion` o `implementador`; el `dpo` no (D-2). Sus filas de la matriz en `tests/matriz/ORG-16.py`.
- `ProjectConfig.tsx` lanza el asistente y lee el estado del servidor; deja de decidir con `isConfigured` local. Pantalla en Configuración (`frontend/src/components/layout/menus/ORG-16.ts` y `frontend/src/components/layout/pantallas/ORG-16.tsx`).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- **Propiedad ampliada (2026-10-31).** `tenants` no tiene naturaleza, rol de datos, actividades de riesgo ni provincia, y `invitaciones_organizacion` no sirve para el paso 6 (sin rol propuesto ni `area_id`, índice único de una sola invitación emitida por organización, tabla exenta de RLS por ser de plataforma). Decisión de la propietaria (vía A, 2026-10-31): una migración propia, `alembic/versions/20261101_org16_perfil_alta.py` con `down_revision` igual a la cabeza de `dev/aleczandra` al empezar (hoy `20261030_dpo_inscripcion`), que añade las cuatro columnas a `tenants` con su CHECK y crea una **tabla nueva por organización** para las invitaciones de personas del paso 6, con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`. No se toca `invitaciones_organizacion` ni su índice, ni los archivos de ORG-10, ORG-11 y ORG-13. Archivos que se suman: el modelo de `tenants` (`app_core/models_base.py` y `app_core/models.py`), la compuerta de razón social, nombre comercial y RUC (`configuracion_engine.py`, de RM-15), la provincia en los campos documentales (`datos_documentales_engine.py`, de ORG-14) y el motor nuevo `invitaciones_personas_engine.py`; los dueños anteriores están «hechos».
- **Propiedad ampliada (2026-10-31, menús).** Al añadir el submenú «Alta de la organización» en Configuración, la prueba «nueve menús en orden» de `frontend/tests/navegacion/menus.spec.ts` (FE-22) falla: esperaba Configuración sin submenú visible tras configurar el proyecto. Se suma ese archivo a la propiedad para que la prueba admita el submenú, como hizo CAPA-02 con el suyo; CAPA-02 también lo posee, de ahí `depende_de` CAPA-02 (su trabajo ya está fusionado). Solo se toca la expectativa de Configuración; el resto de la prueba no cambia.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Los siete pasos guardan en el servidor y sobreviven a una sesión nueva en otro navegador; el `dpo` recibe 403.
- Mutación documentada: guardar solo en el navegador y comprobar que la prueba de «sobrevive a otro navegador» falla.

## Límites
- **Crear** la organización (tenant) sigue siendo del operador de la plataforma (ORG-09/ORG-10); esto completa su perfil.
- No toca `useAuditStore.ts` (lo tienen EVI-01 y BIB-110): si `isConfigured` queda sin uso, se anota para esas tareas.
- Activos, soportes y personas completas son de ORG-17.
