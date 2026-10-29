+++
id = "DIAG-03"
titulo = "El DPO responde y sella el diagnóstico; el resultado sellado se guarda en la base por organización y no se puede editar ni borrar"
ola = "D"
estado = "hecha"
sala = "diagnostico, frontend"
depende_de = ["CAPA-01", "DIAG-01", "DIAG-02", "FE-16", "FE-17", "FE-20", "TEST-02", "QA-08"]
propiedad = ["alembic/versions/20261028_diagnostico_resultados.py", "features/diagnostico/domain/resultados.py", "features/diagnostico/services/resultados_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-03", "api/routers/diagnostico_resultados.py", "api/routers/diagnostico_respuestas.py", "tests/test_diagnostico_resultados.py", "tests/test_diagnostico_respuestas.py", "frontend/src/lib/diagnostico/**", "frontend/src/components/DiagnosticCanvas.tsx", "frontend/src/components/AuditHistory.tsx", "frontend/src/app/actions/auditActions.ts", "frontend/src/app/actions/audit.ts", "frontend/data/snapshots.json", "frontend/tests/diagnostico/**", "frontend/tests/assessmentDashboard.spec.ts", "frontend/tests/purga/purga-normativa.spec.ts"]
arbitro = "pytest tests/test_diagnostico_resultados.py tests/test_diagnostico_respuestas.py contra una rama Neon de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤dpo-independencia", "¤rbac-tenant"]
+++

# DIAG-03 · Diagnóstico del DPO y resultado sellado en la base

**Hallazgo (2026-10-27, prueba de Aleczandra en producción).** «Guardar resultado definitivo» muestra «No se pudo inicializar la bóveda de snapshots inmutables»:
- `frontend/src/app/actions/auditActions.ts` escribe el resultado en un archivo del servidor de Next (`data/snapshots.json`). En Vercel ese disco es de solo lectura.
- Aunque funcionara, es **un solo archivo para todas las organizaciones**, sin control de quién guarda. El historial filtra por un texto que contenga la razón social: una organización podría ver los resultados de otra.
- `frontend/data/snapshots.json` está en el repositorio, con 21 resultados de 10 razones sociales.

**Decisión del propietario (2026-10-27), sustituida el 2026-10-28 por DIAG-07** (responden el administrador y los encargados que designe; el DPO revisa, objeta y sella; el sello sigue siendo del DPO). Texto original: **Solo el DPO responde y sella el diagnóstico.** Implementador, coordinador y administrador lo consultan.
- **Fundamento** (resumen del corpus del proyecto, F02 y F03): el delegado supervisa el cumplimiento y la gestión de riesgos (art. 49 LOPDP). Diagnosticar el cumplimiento es supervisarlo; implementar las medidas sigue siendo de la organización. El DPO diagnostica y sella, y el implementador ejecuta la hoja de ruta. El DPO lo designa la organización (art. 48) y coopera con la Superintendencia como punto de contacto (art. 49); no la representa.

## Entrega
- **Respuestas** (`api/routers/diagnostico_respuestas.py`): escribe solo el `dpo`; consultan `dpo`, `implementador`, `coordinador` y `admin_organizacion`. Hoy escriben el implementador y el coordinador.
- **Migración** `20261028_diagnostico_resultados` (id de 32 caracteres como máximo), con `down_revision` igual a la cabeza de `main` al empezar. Compruébalo con `alembic heads` al empezar y otra vez antes de empujar: ORG-13 también lleva migración, y la que se fusione segunda se vuelve a encadenar.
  - Tabla de resultados sellados por organización, con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`).
  - Contenido: quién selló y cuándo, normativa y versión, las respuestas usadas y los cuatro indicadores (cumplimiento, madurez, respaldo con documentos, riesgo que queda).
  - Huella SHA-256 encadenada **por organización**, como la bitácora del DPO (DPO-01).
  - Permisos de `lopdp_app`: **solo SELECT e INSERT**. Sin UPDATE ni DELETE: un resultado sellado no se edita ni se borra.
- **Sellar** (`POST`, router nuevo `api/routers/diagnostico_resultados.py` con `AUTO_REGISTRO = True`): solo el `dpo`; quien sella es el usuario autenticado.
  - **El servidor sella lo que tiene:** las respuestas guardadas de la organización (DIAG-01) y los indicadores calculados por el motor del servidor. No acepta respuestas ni puntajes enviados por el navegador (lección de RM-19).
  - La regla de respaldo se mantiene: un control cuyo documento adjunto el servidor no puede comprobar se sella como E0. Nunca se inventa respaldo.
  - El alta deja un evento en `audit_events`.
  - **Paridad:** para un conjunto fijo de respuestas, los cuatro indicadores del servidor coinciden con los que muestra la pantalla. Si hoy no coinciden, se informa como hallazgo; no se ajusta un lado para que cuadre sin explicarlo.
- **Historial** (`GET`): lista los resultados de la organización, del más reciente al más antiguo, para los roles que consultan. Una función verifica la cadena de huellas y devuelve el primer resultado alterado, si lo hay.
- **Pantallas:**
  - `DiagnosticCanvas.tsx`: solo el DPO puede responder y ve «Guardar resultado definitivo». Los demás roles ven el diagnóstico en modo lectura, con un aviso de que lo responde el DPO.
  - **Organización sin DPO con rol vigente:** el aviso lo explica y orienta a designar uno, que puede ser externo (ORG-13). No se habilita a otro rol en su lugar.
  - `AuditHistory.tsx`: lee el historial del servidor; nunca de un archivo.
  - Las llamadas van en `frontend/src/lib/diagnostico/` con `fetchAutenticado`; colores solo con las variables del tema.
- **Se retiran** `auditActions.ts` y `audit.ts` (o queda solo lo que no escriba en disco, si algo más lo usa; comprobarlo con una búsqueda), y `frontend/data/snapshots.json` sale del repositorio.
- **Pruebas:**
  - un rol distinto del `dpo` no puede responder ni sellar (403);
  - el resultado sobrevive a una sesión nueva;
  - el servidor ignora respuestas y puntajes enviados en el cuerpo;
  - `lopdp_app` no puede actualizar ni borrar un resultado (42501);
  - RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`;
  - alterar un resultado en la base rompe la verificación de la cadena;
  - paridad de indicadores;
  - Playwright: el DPO responde y sella; los demás ven el modo lectura; el historial muestra lo sellado;
  - las pruebas de DIAG-01 se adaptan a la nueva regla de escritura;
  - `frontend/tests/assessmentDashboard.spec.ts` (de TEST-02) y `frontend/tests/purga/purga-normativa.spec.ts` (de QA-08) responden controles, suben evidencia o piden el preanálisis con el rol por defecto (implementador): pasan a simular el rol `dpo`, sin cambiar lo que verifican.
  - La prueba debe correr también en la rama Neon `test` del CI; la única base prohibida es producción (`ep-late-hall`).
- **Prueba de mutación documentada:** permitir que el implementador selle y comprobar que la prueba del 403 falla.

## Límites
- No cambia el contenido del banco de preguntas ni el cálculo de los indicadores (DIAG-02), salvo lo que revele la prueba de paridad, que se informa.
- No toca `frontend/src/store/useAuditStore.ts` (de BIB-101). Si la sincronización del store necesita cambiar (por ejemplo, para no intentar escribir sin rol de DPO), se describe en «PARCHES PARA EL PROPIETARIO».
- La ficha de la organización sigue en el navegador.

## Notas para el propietario
- Migrar la rama Neon `test` antes de que el CI del PR llegue a las pruebas, y producción después de fusionar.
- Hallazgo relacionado, fuera de esta tarea: «Playbook Incidentes» (`incidentActions.ts`) también escribe en un archivo del servidor de Next (`data/incident_logs.json`), que está en el repositorio. En Vercel falla igual. Merece su propia ficha.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
