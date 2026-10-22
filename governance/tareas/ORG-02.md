+++
id = "ORG-02"
titulo = "Excepciones de separación de funciones, explícitas y con fin, en lugar de «permitido por tamaño»"
ola = "D"
estado = "hecha"
sala = "organizacion"
depende_de = ["ORG-01", "ORG-07", "RM-10", "RM-16"]
propiedad = ["alembic/versions/*_sod_exceptions.py", "features/organizacion/services/excepcion_sod_engine.py", "features/organizacion/services/regla_tamano_engine.py", "api/routers/organizacion_excepciones_sod.py", "tests/test_excepciones_sod.py", "tests/test_matriz_permisos.py", "tests/test_encargado_responsable_tamano.py", "features/organizacion/services/roles_engine.py", "features/organizacion/services/solicitud_responsable_engine.py", "tests/test_responsable_requests.py", "tests/test_rol_coordinador.py", "features/organizacion/organizacion_service.py#RM-16", "features/organizacion/organizacion_service.py#ORG-02"]
arbitro = "pytest tests/test_excepciones_sod.py tests/test_encargado_responsable_tamano.py tests/test_matriz_permisos.py + suite completa"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-02 · Excepciones de separación de funciones, explícitas y con fin, en lugar de «permitido por tamaño»

**Objetivo.** Hoy una persona puede ser `coordinador` y `responsable_area` a la vez solo porque la organización es `micro` o `pequena` (RM-16): el permiso es automático, silencioso e indefinido, y depende de un dato (el tamaño) que cambia con el tiempo. Cuando la organización crece, esa misma persona pasa a violar la regla sin que nadie haya hecho nada. La regla debe depender de una **decisión explícita**, no del tamaño.

## Entrega
- Tabla `sod_exceptions` (RLS por tenant, `GRANT` explícito a `lopdp_app`, sin DELETE): quién (`user_id`), qué par de roles, motivo, control compensatorio, quién la aprueba, `valid_from`, `valid_to` **obligatorio** y estado (`activa`, `vencida`, `revocada`).
- La combinación `coordinador` + `responsable_area` se permite **solo con una excepción activa** de ese usuario en ese tenant. `regla_tamano_engine.verificar_encargado_responsable` y el trigger de RM-16 se sustituyen por esa comprobación (migración nueva que reemplaza la función del trigger). Sigue fallando cerrado.
- El tamaño deja de decidir la compatibilidad. Sin tamaño configurado no se aprueba ninguna excepción (`TENANT_SIZE_NOT_CONFIGURED`, como hasta ahora).
- Endpoints bajo `/api/v1/organizacion/excepciones-sod`: solicitar, listar, ver, aprobar y revocar. Quien se beneficia de una excepción no puede aprobarla y el `dpo` tampoco: solo recibe aviso de cada excepción solicitada y aprobada y puede dejar observaciones no vinculantes. Cada paso deja un evento en `audit_events`.
- **Migración de datos sin romper a nadie:** quienes hoy ya acumulan ambos roles en organizaciones `micro` o `pequena` reciben una excepción de origen `migracion`, con la fecha de fin que decida el propietario. La migración lo informa y no concede nada nuevo.
- Pruebas con base de datos (transacción que se revierte, ejecutando el SQL real de la migración): sin excepción rechaza, con excepción activa permite, vencida o revocada rechaza, el beneficiario no la aprueba, aislamiento por tenant y RLS con el rol de la aplicación.

- **Sin parches: ningún nombre del rol antiguo en lo que toques.** La regla que reemplazas tiene consumidores y todos se actualizan en esta tarea: `verificar_encargado_responsable` pasa a `verificar_excepcion_coordinador_responsable` (y sus importaciones en `roles_engine.py`, `solicitud_responsable_engine.py` y la sección `# === RM-16 ===` de la compuerta), el invariante `INV_LOPDP_ENCARGADO_RESPONSABLE_SIZE` pasa a `INV_LOPDP_COORDINADOR_RESPONSABLE_EXCEPCION`, y `tests/test_encargado_responsable_tamano.py` se **sustituye** por `tests/test_excepciones_sod.py` (se borra el archivo antiguo; lo que siga vigente pasa a la prueba nueva, sin debilitar aserciones). Las pruebas de `tests/test_responsable_requests.py` y `tests/test_rol_coordinador.py` que afirman la regla «permitido por tamaño» se actualizan a la regla nueva. El código de error `TENANT_SIZE_NOT_CONFIGURED` se conserva (no contiene el nombre antiguo). Las migraciones históricas no se tocan. Los restos fuera de lo tuyo (el alias `ROLE_ALIASES`, cadenas en otras pruebas, el generador de tipos del frontend) los retira ORG-08.

## Decisiones asumidas (con su base legal)
1. **Quién aprueba una excepción:** un `admin_organizacion` distinto del beneficiario. Si el único administrador es el propio beneficiario, la excepción exige la resolución firmada del representante legal (referencia del documento). **El `dpo` nunca aprueba**: Art. 18.3 del Reglamento del Delegado. El representante legal designa al delegado y representa a la organización (Art. 3), luego tiene autoridad sobre el `coordinador`. La ley no regula estas excepciones: es diseño de la plataforma, modelado sobre el Art. 15.2 (el delegado opina sin vincular).
2. **Control compensatorio:** obligatorio; se elige de una lista (observaciones periódicas del delegado, verificación por un tercero externo, aprobación de las decisiones por la alta dirección) y se detalla con texto libre.
3. **Fecha de fin:** obligatoria; su duración máxima se trata cuando se trabajen los plazos.

## Límites
- No cambia las reglas del DPO (ORG-01) ni el flujo de altas (RM-10).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
