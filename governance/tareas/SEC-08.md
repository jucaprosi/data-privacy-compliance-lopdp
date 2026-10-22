+++
id = "SEC-08"
titulo = "ARCO+: reemplazar el router en memoria por el persistente, con identidad y aislamiento por tenant"
ola = "D"
estado = "hecha"
sala = "pasillo_central"
depende_de = ["SEC-02", "SEC-07", "FE-07", "ADPA-01", "SEC-09"]
propiedad = ["api/routers/arco.py", "api/routers/arco_router.py", "frontend/src/components/modules/ArcoModule.tsx", "tests/test_arco_seguro.py", "tests/test_api_integracion.py", "tests/test_e2e_flujo_completo.py", "frontend/tests/arco/**"]
arbitro = "pytest tests/test_arco_seguro.py tests/test_api_integracion.py tests/test_e2e_flujo_completo.py + suite completa; Playwright de frontend/tests/arco; tsc --noEmit y next build"
rastros = ["¤seguridad", "¤rbac-tenant"]
+++

# SEC-08 · ARCO+: reemplazar el router en memoria por el persistente, con identidad y aislamiento por tenant

**Objetivo.** SEC-02 (hallazgo H01, alto) dejó abierto que `/api/v1/arco` lo sirve `api/routers/arco.py`, un router semilla que guarda las solicitudes en una lista en memoria (`_arco_store`), no valida el tenant del cuerpo del `POST` (acepta el `tenant_id` que envíe el cliente) y en el `GET` usa como «tenant» todo el valor de la cabecera `Authorization` sin el prefijo `Bearer `. Existe el router persistente `api/routers/arco_router.py` (con `get_tenant_session` y el servicio `features/derechos_arco`), pero no es el montado. Además, **el frontend no coincide con ninguna de las dos APIs**: `ArcoModule` espera `{tipo, solicitante, cedula, dias_restantes}`; el router en memoria devuelve `{titular_id, tipo_derecho}` y el persistente `{tipo_solicitud, nombre_solicitante, cedula_solicitante, fecha_vencimiento}`. Las solicitudes ARCO son derechos de los titulares (LOPDP): perderlas al reiniciar el servidor, o mezclarlas entre organizaciones, no es aceptable.

## Entrega
- `api/routers/arco.py` deja de tener lógica: reexporta `router` de `arco_router`, de modo que `main.py` (`ROUTERS_MAP`, línea `("api.routers.arco", "arco")`) **no se toca** y no queda ningún `_arco_store`. Comprobar con `python -c "from main import app; ..."` que la ruta `/api/v1/arco/solicitudes` la sirve el módulo persistente.
- `api/routers/arco_router.py`:
  - El `POST` valida el cuerpo con un esquema (hoy recibe `dict` sin validar) y **ignora cualquier `tenant_id` del cuerpo**: el tenant sale de la sesión autenticada.
  - Ambos métodos exigen identidad verificada (como el resto de la API, `get_usuario_autenticado` o la dependencia vigente) y respetan el aislamiento por tenant (RLS con el rol de la aplicación).
  - No se cambia **quién** puede crear o consultar solicitudes: se documenta en el informe la decisión vigente y se deja como pregunta para el propietario.
- Un contrato único: la respuesta del router persistente es la fuente; `ArcoModule.tsx` se adapta a ella (mapeando `tipo_solicitud`, `nombre_solicitante`, `cedula_solicitante` y calculando los días restantes desde `fecha_vencimiento`). No se inventan campos en el backend para encajar la interfaz.
- Pruebas (`tests/test_arco_seguro.py`, con base de datos real y transacción que se revierte): persistencia (sobrevive a una nueva sesión), `POST` con `tenant_id` de otra organización en el cuerpo termina guardado en la del usuario, un tenant no ve las solicitudes de otro, sin identidad responde 401, el cuerpo inválido responde 422. Adaptar `tests/test_api_integracion.py` y `tests/test_e2e_flujo_completo.py` a la forma nueva sin debilitar sus aserciones.
- Playwright (`frontend/tests/arco/**`) con la API simulada y la sesión de `tests/auth/utilesAuth.ts`: el módulo muestra las solicitudes con la forma real del backend, el estado de error y el vacío. Antes de escribirlas, leer `frontend/tests/GUIA_PLAYWRIGHT.md`. Prueba negativa obligatoria.

## Límites
- No cambia migraciones ni el esquema de la tabla de solicitudes.
- No toca `main.py`, el servicio `features/derechos_arco` ni los roles.
- No toca `niif18`, `riesgos_mtge` ni `implementation_assistant` (hallazgos H02 y H03 de SEC-02, de otra decisión).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
