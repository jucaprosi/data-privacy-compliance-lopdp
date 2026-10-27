+++
id = "INC-01"
titulo = "La bitácora de incidentes se guarda en la base por organización, con permisos por rol, y deja de mostrar un plazo legal que no está en la ley"
ola = "D"
estado = "pendiente"
sala = "incidentes, frontend"
depende_de = ["CAPA-01", "DPO-01", "FE-17", "FE-20", "LEG-02"]
propiedad = ["alembic/versions/20261028_bitacora_incidentes.py", "features/incidentes/**", "api/routers/incidentes.py", "tests/test_incidentes.py", "frontend/src/lib/incidentes/**", "frontend/src/components/IncidentPlaybook.tsx", "frontend/src/app/actions/incidentActions.ts", "frontend/src/types/incidente.ts", "frontend/data/incident_logs.json", "frontend/tests/incidentes/**"]
arbitro = "pytest tests/test_incidentes.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/incidentes + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤incidentes", "¤rbac-tenant", "¤seguridad"]
+++

# INC-01 · Bitácora de incidentes en la base

**Hallazgo (2026-10-27, revisión del coordinador).** «Playbook Incidentes» (`IncidentPlaybook.tsx` y `incidentActions.ts`) tiene el mismo defecto que la bóveda del diagnóstico (DIAG-03), y otros propios:
- Guarda los incidentes en un archivo del servidor de Next (`frontend/data/incident_logs.json`). En Vercel ese disco es de solo lectura: registrar falla.
- Es **un solo archivo para todas las organizaciones** y la acción no comprueba quién llama: cualquier sesión lee los incidentes de todas. El detalle de una vulneración es información reservada de cada organización.
- Quién reporta es un texto libre que manda el navegador (`reportadoPor`), y el navegador puede cambiar el plazo (`slaHorasPersonalizado`).
- El archivo está en el repositorio con incidentes de ejemplo.
- La pantalla exige adjuntar un archivo de evidencia para registrar, pero ese archivo **nunca se envía ni se guarda**.
- La pantalla muestra un «SLA legal de 72 horas perentorias» y cita la «Ley de Ciberseguridad 2026» y el «Art. 40 LOPDP». Contraste con el texto vinculante:
  - La notificación de vulneraciones está en el **art. 43** de la LOPDP, no en el 40. Para la notificación a la Autoridad fija un **término de cinco días**, no 72 horas.
  - La norma técnica SPDP-SPD-2026-0040-R no fija 72 horas (resumen de LEG-02 en `governance/apoyo/NORMA_TECNICA_VULNERACIONES.md`, apartados 2.5 y 4).
  - La «Ley de Ciberseguridad 2026» no está en el corpus verificado del proyecto.

**Decisiones del coordinador (diseño propio, conforme a la regla «la ley primero»; cada una en un solo sitio para poder cambiarla):**
- **Plazos:** siguen aplazados por decisión del propietario (LEG-02). Esta tarea no calcula plazos legales. Retira el reloj de 72 horas y las citas no verificadas, y muestra solo el tiempo transcurrido desde la detección, sin llamarlo plazo legal.
- **Quién registra:** `admin_organizacion`, `coordinador`, `responsable_area` e `implementador`. La obligación de notificar y documentar es del responsable del tratamiento (art. 43).
- **Quién consulta:** los cuatro anteriores y el `dpo`. El delegado supervisa y asesora (art. 49) y no registra, como en el resto de la plataforma (ORG-01, el DPO sin funciones operativas). Si conoce un incidente, lo comunica a quien registra.
- **Evidencia:** la pantalla deja de pedir un archivo que no guarda. La bóveda de evidencias (`features/evidencias`) también vive en la memoria del servidor, así que adjuntar se retoma cuando esa bóveda persista (ver «Notas para el propietario»).

## Entrega
- **Sala `incidentes`** (`features/incidentes/`, en el catálogo del PRD como «planificada, sin código»):
  - compuerta `incidentes_service.py`;
  - dominio y motor;
  - router `api/routers/incidentes.py` con `AUTO_REGISTRO = True`, bajo `/api/v1/incidentes`.
  - Lo que necesite de otra sala, por su compuerta. Errores de negocio con `ErrorNegocio`.
- **Migración** `20261028_bitacora_incidentes` (id de 32 caracteres como máximo), con `down_revision` igual a la cabeza de `main` al empezar.
  - Compruébalo con `alembic heads` al empezar y otra vez antes de empujar: en la tanda 19 también llevan migración ORG-13, DIAG-03 y BIB-108, y la que se fusione después se vuelve a encadenar.
  - Tabla de incidentes por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`).
  - Contenido: fecha de detección, título, descripción, severidad (`Baja`, `Media`, `Alta`, `Crítica`), si afecta datos personales, categorías de datos afectados y medidas inmediatas. También quién registró y cuándo.
  - Huella SHA-256 encadenada **por organización**, como la bitácora del DPO (DPO-01).
  - Permisos de `lopdp_app`: **solo SELECT e INSERT**. Un incidente registrado no se edita ni se borra; las actuaciones posteriores no son parte de esta tarea.
- **Registrar** (`POST`), solo los roles que registran:
  - quién registra es el usuario autenticado; se ignora cualquier nombre o id del cuerpo;
  - la hora de registro la pone el servidor;
  - el cuerpo no fija plazos, huellas ni fechas de registro;
  - una fecha de detección futura se rechaza con 422;
  - el alta deja un evento en `audit_events`.
- **Consultar** (`GET`): los incidentes de la organización, del más reciente al más antiguo, para los roles que consultan. Una función verifica la cadena de huellas y devuelve el primer incidente alterado, si lo hay.
- **Pantalla `IncidentPlaybook.tsx`** (conserva su nombre y su exportación, que monta `frontend/src/app/dashboard/page.tsx`):
  - lee y registra por `frontend/src/lib/incidentes/` con `fetchAutenticado`;
  - el formulario solo lo ven los roles que registran; el `dpo` ve la bitácora en modo lectura;
  - sin campo «reportado por»: lo pone el servidor;
  - sin zona de adjuntos;
  - sin «SLA legal 72h», sin «Ley de Ciberseguridad 2026» y sin «Art. 40 LOPDP». Muestra el tiempo transcurrido desde la detección y un aviso de que los plazos de notificación se incorporarán en una tarea propia;
  - colores solo con las variables del tema (`--ui-*`, `badge-render-*`).
- **Se retiran** `frontend/src/app/actions/incidentActions.ts` y `frontend/data/incident_logs.json`. Comprueba con una búsqueda que nada más los use. `frontend/src/types/incidente.ts` se queda solo con lo que use la pantalla nueva.
- **Pruebas:**
  - un rol que no registra (por ejemplo, el `dpo`) recibe 403 al registrar y puede consultar;
  - quien registró es el usuario autenticado aunque el cuerpo traiga otro nombre o id;
  - una fecha de detección futura da 422;
  - el incidente sobrevive a una sesión nueva;
  - `lopdp_app` no puede actualizar ni borrar un incidente (42501);
  - RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`;
  - alterar un incidente en la base rompe la verificación de la cadena;
  - Playwright, con la API simulada:
    - un rol que registra crea un incidente y lo ve en la bitácora;
    - el `dpo` no ve el formulario;
    - la pantalla no muestra «72» como plazo legal ni cita la «Ley de Ciberseguridad 2026».
  - Las pruebas deben correr también en la rama Neon `test` del CI; la única base prohibida es producción (`ep-late-hall`).
- **Prueba de mutación documentada:** permitir que el `dpo` registre y comprobar que la prueba del 403 falla.

## Límites
- No implementa plazos legales, notificación a la Superintendencia ni a los titulares, ni la clasificación de la norma técnica (tipos y dimensiones de la vulneración, número de trámite del SISPDP). Siguen aplazados; cuando se retomen, la base es LEG-02.
- No toca la sala `evidencias` ni `frontend/src/app/dashboard/page.tsx`.
- No migra los incidentes de ejemplo del archivo.
- No edita `governance/artefactos/INVARIANTS.md`: el invariante `INV_LOPDP_INCIDENT_TIMELOCK` cita la «Ley de Ciberseguridad 2026» y queda como nota para el propietario.

## Notas para el propietario
- Migrar la rama Neon `test` antes de que el CI del PR llegue a las pruebas, y producción después de fusionar.
- **Hallazgo relacionado, fuera de esta tarea:** la bóveda de evidencias (`features/evidencias/services/evidencias_engine.py`, `InMemoryEvidenciasRepository`) guarda los registros en la memoria del servidor: cada reinicio o despliegue los borra. Afecta al diagnóstico (DIAG-03 sella como E0 lo que no puede comprobar) y a cualquier adjunto. Merece su propia ficha.
- El invariante `INV_LOPDP_INCIDENT_TIMELOCK` y el PRD (Módulo 2, «Incidentes y Vulneraciones») citan la «Ley de Ciberseguridad 2026» y un reloj de notificación al CSIRT. Antes de volver a mostrarlo hay que verificar esa ley con su Registro Oficial, o retirar la cita.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
