+++
id = "DER-01"
titulo = "Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia"
ola = "D"
estado = "hecha"
sala = "derechos_arco, frontend"
depende_de = ["EVI-02", "FE-22", "ADPA-05", "ADPA-06", "DER-03", "DER-05", "DER-06a", "DER-06b"]
propiedad = ["alembic/versions/der01_derechos_respuestas.py", "features/derechos_arco/services/respuestas_engine.py", "features/derechos_arco/derechos_arco_service.py#DER-01", "api/routers/derechos_respuestas.py", "tests/test_derechos_respuestas.py", "tests/matriz/DER-01.py", "frontend/src/components/derechos/**", "frontend/src/lib/derechos/respuestas.ts", "frontend/src/types/arco.ts", "frontend/tests/derechos/respuestas.spec.ts", "features/derechos_arco/domain/errores.py#DER-01", "app_core/pasillo/derechos_arco.py#DER-01", "app_core/pasillo/evidencias.py#DER-01", "app_core/pasillo/firma_electronica.py#DER-01", "app_core/pasillo/notificaciones.py#DER-01", "app_core/pasillo/dpo_cockpit.py#DER-01", "frontend/src/components/modules/ArcoModule.tsx", "tests/matriz/roles/auditor.py#DER-01"]
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
- Pruebas contra un PostgreSQL 16 local en contenedor validado con `exigir_base_de_pruebas()`.
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

## Textos cerrados por UX/UI (2026-11-15)
Citas de `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md` (LOPDP arts. 13 a 20) y `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md` (art. 62). Los modelos de respuesta (siguiente subsección) son datos que siembra el backend (`derechos_modelos`) y los lee la prueba; **están en la especificación, §4.1 «Modelos de respuesta»**.

**Decidido por el CTO (2026-11-15): el botón es «Registrar la respuesta».** Con NOTIF-01 pendiente la plataforma no envía nada al titular y un botón «Enviar» sería falso. Va con la línea fija «La respuesta queda registrada como evidencia. Entrégala al titular por el medio que indicó en su solicitud.» y el enlace «Descargar la respuesta». Cuando llegue NOTIF-01, el envío será una acción aparte. «Respondida» se mantiene. La migración fija el CHECK de `resultado` en `concedido`, `parcial` y `denegado` (decisión del Arquitecto sobre la queja).

### Modelos de respuesta
Viven en la especificación, `governance/especificaciones/DER-01.md` §4.1 «Modelos de respuesta»; manda la especificación. **Queja al responsable** (decisión del Arquitecto, 2026-11-15): se reutilizan `concedido`, `parcial` y `denegado`, con las etiquetas «Atendida», «Atendida en parte» y «No atendida». El CHECK de `resultado` queda en esos tres valores, así que la migración puede fijarlo.

### Textos de pantalla
**Bloque «Identidad».** Grupo «Método de verificación»: documento → «Documento de identidad»; correo → «Correo electrónico verificado»; presencial → «Presencial». Ayuda: «Comprueba que quien pide es el titular o su representante antes de responder.» Botón «Verificar» (nombre accesible «Verificar la identidad del titular»). Tras verificar, `role=status` «Identidad verificada por {nombre} el {fecha} · {método}.» Sin método, el botón queda con `aria-disabled` y la línea «Elige cómo verificaste la identidad.» Ya verificada: bloque de solo lectura con esa línea.

**Bloque «Respuesta»** (solo con identidad verificada; si no, la nota «Verifica la identidad del titular para poder responder.»):
- «Resultado»: Concedida, Parcial, Denegada (radiogroup «Resultado»).
- «Modelo de respuesta» (selector). Vacío: «No hay un modelo para este derecho y resultado. Escribe al equipo de EVYDENTIA para añadirlo.»
- Variables: un campo por variable con etiqueta en español (Acción realizada, Motivo, Contacto del DPO…). Error por campo: «Completa este dato.»
- «Vista previa» (región «Vista previa de la respuesta»): texto plano resuelto; variables vacías como «[Falta: {etiqueta}]», que no se pueden registrar.
- Botón «Registrar la respuesta», solo para `admin_organizacion` e implementador; `aria-disabled` mientras falten variables, con la línea «Completa los datos que faltan en la vista previa.» Confirmación: «¿Registrar esta respuesta? Después no se puede cambiar.» con «Cancelar» (foco inicial) y «Registrar la respuesta».
- Para el DPO y otros roles sin permiso no hay botón, sino la línea «Responde la persona administradora o el implementador de la organización.»

**Estado «Respondida».** Etiqueta «Respondida» y «Respondida el {fecha} · {resultado}», con el enlace «Ver la respuesta registrada» (abre la evidencia) y el enlace «Descargar la respuesta». «Huella de integridad: {8 primeros caracteres}», nunca «hash».

**Éxito.** `role=status` «Respuesta registrada como evidencia. Entrégala al titular por el medio que indicó.»

**Errores** (fijos por código; nunca el texto del servidor):
- 409 `IDENTIDAD_NO_VERIFICADA`: «Antes de responder, verifica la identidad del titular.»
- 409 `SOLICITUD_RESPONDIDA`: «Esta solicitud ya tiene una respuesta registrada. Actualizamos la ficha.» (y recarga)
- 422 `VARIABLES_INCOMPLETAS`: «Faltan datos en la respuesta. Revisa la vista previa.»
- 422 `RESPUESTA_SIN_EVIDENCIA`: «No pudimos guardar la respuesta como evidencia, así que no se registró. Inténtalo de nuevo.»
- 422 de validación: «No pudimos registrar la respuesta. Vuelve a cargar la página e inténtalo de nuevo.»
- 403: «No tienes permiso para esta acción.» · 401: manejo global · otros: «No pudimos guardar los cambios. Inténtalo de nuevo.»
- Cargando: «Cargando la solicitud…» (status). Error de carga: «No pudimos cargar la solicitud. Inténtalo de nuevo.» + «Volver a cargar».

**Accesibilidad para Playwright.** Método: radiogroup «Método de verificación» · Verificar: button «Verificar la identidad del titular» · Resultado: radiogroup «Resultado» · Modelo: combobox «Modelo de respuesta» · Vista previa: region «Vista previa de la respuesta» · Registrar: button «Registrar la respuesta» · Evidencia: link «Ver la respuesta registrada». Contraste 4.5:1, tokens del tema, sin `¤` ni `¦`, sin desbordar a 375 px.

**Criterios de prueba.** Con una variable vacía la vista previa muestra «[Falta: …]» y el botón tiene `aria-disabled`; el DPO no ve el botón; ningún texto visible promete un envío («te enviaremos», «enviada al titular»); la vista previa no muestra «hash» ni ids.
