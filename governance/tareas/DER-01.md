+++
id = "DER-01"
titulo = "Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia"
ola = "D"
estado = "pendiente"
sala = "derechos_arco, frontend"
depende_de = ["EVI-02", "FE-22", "ADPA-05", "ADPA-06", "DER-03", "DER-05", "DER-06a", "DER-06b"]
propiedad = ["alembic/versions/der01_derechos_respuestas.py", "features/derechos_arco/services/respuestas_engine.py", "features/derechos_arco/derechos_arco_service.py#DER-01", "api/routers/derechos_respuestas.py", "tests/test_derechos_respuestas.py", "tests/matriz/DER-01.py", "frontend/src/components/derechos/**", "frontend/src/lib/derechos/respuestas.ts", "frontend/src/types/arco.ts", "frontend/tests/derechos/respuestas.spec.ts", "features/derechos_arco/domain/errores.py#DER-01", "app_core/pasillo/derechos_arco.py#DER-01", "app_core/pasillo/evidencias.py#DER-01", "app_core/pasillo/firma_electronica.py#DER-01", "app_core/pasillo/notificaciones.py#DER-01", "app_core/pasillo/dpo_cockpit.py#DER-01"]
arbitro = "pytest tests/test_derechos_respuestas.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/derechos/respuestas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; las pruebas de la evidencia obligatoria (test_contestar_sin_evidencia_422, test_hash_del_cliente_rechazado, test_check_contestada_exige_hash y test_migracion_der01_aborta_con_contestadas_sin_hash) cada una con su mutación"
rastros = ["¤evidencias", "¤rbac-tenant"]
+++

# DER-01 · Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia

**Origen.** Menú 5 «Operación › Solicitudes de titulares» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md` sobre `derechos_arco_solicitudes` (SEC-09).

**Contrato:** `governance/especificaciones/DER-01.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Verificación de identidad proporcional antes de responder: método (documento, correo verificado, presencial), quién verificó y cuándo; sin ella no se puede responder.
- Modelos de respuesta por derecho y resultado (concedido, denegado, parcial) con variables; la respuesta enviada se custodia como evidencia (EVI-02) vinculada a la solicitud.
- El `responsable_area` o `coordinador` prepara; el `admin_organizacion` o `implementador` aprueba y envía; el `dpo` consulta (decisión 1). **Sin plazo calculado** (LEG-03, REG-01): el semáforo llega con REG-01.
- **Sin contestar sin evidencia (`INV_ARCO_EVIDENCIA_E1`, brecha cerrada aquí).** Hoy no existe ninguna ruta que resuelva solicitudes: esta ficha la crea y exige la evidencia. El servicio solo pasa a `CONTESTADA` en la misma transacción que custodia la respuesta (EVI-02, mismo tenant); el hash `evidencia_respuesta_hash` lo calcula el servidor, el cuerpo se declara con `extra="forbid"` y un hash o una URL del cliente da 422; si la custodia no devuelve un sha256, 422 `RESPUESTA_SIN_EVIDENCIA` (código nuevo en `features/derechos_arco/domain/errores.py#DER-01`) y el estado no cambia.
- **La migración** es `alembic/versions/der01_derechos_respuestas.py` (sin fecha, como `bib301_biblioteca_aprobaciones.py`; `down_revision` = cabeza de `main` al implementar). Añade `ck_arco_contestada_con_evidencia CHECK (estado <> 'CONTESTADA' OR (evidencia_respuesta_hash ~ '^[0-9a-f]{64}$' AND respondida_en IS NOT NULL))`. Antes del `ADD CONSTRAINT` cuenta exactamente las filas que ese CHECK rechazaría, `NOT (estado <> 'CONTESTADA' OR (evidencia_respuesta_hash ~ '^[0-9a-f]{64}$' AND respondida_en IS NOT NULL))`, incluida una `CONTESTADA` con hash y sin `respondida_en`; si hay alguna, aborta con un mensaje que da el recuento, sin `UPDATE` silencioso.
- **Frontend:** retira el tipo huérfano `ResolverSolicitudArcoInput` de `frontend/src/types/arco.ts` (de DER-06b, que va antes; la propiedad de ese archivo es solo para esto); `frontend/src/lib/derechos/respuestas.ts` envía solo `{modelo_id, variables, resultado}`.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Responder sin verificación de identidad da 409; la respuesta queda como evidencia con el modelo y las variables resueltas; el `dpo` no envía (403).
- Mutación documentada: permitir responder sin verificar y comprobar que la prueba falla.
- Responder sin evidencia: 422 `RESPUESTA_SIN_EVIDENCIA` y el estado no cambia (`test_contestar_sin_evidencia_422`); el hash o la URL del cliente da 422 (`test_hash_del_cliente_rechazado`); un `UPDATE` directo a `CONTESTADA` sin hash lo rechaza el CHECK (`test_check_contestada_exige_hash`); la migración aborta con el recuento si hay `CONTESTADA` sin hash válido o sin `respondida_en` (`test_migracion_der01_aborta_con_contestadas_sin_hash`). Mutaciones: quitar la validación del servicio, aceptar el hash del cliente, quitar el CHECK, y sustituir el recuento por un `UPDATE` que rellena el hash; cada una hace fallar su prueba.

## Límites
- Sin portal público (DER-02) ni plazos.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#DER-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#DER-01` sin modificar `app_core/errors.py`.
