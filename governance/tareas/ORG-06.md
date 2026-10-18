+++
id = "ORG-06"
titulo = "Designaciones formales: delegado de protección de datos (con inscripción y declaración) y mandato de la alta dirección al coordinador"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["ORG-01", "ORG-07", "RM-10"]
propiedad = ["alembic/versions/*_designaciones_formales.py", "features/organizacion/services/designacion_engine.py", "api/routers/organizacion_designaciones.py", "tests/test_designaciones_formales.py", "features/organizacion/organizacion_service.py#ORG-06"]
arbitro = "pytest tests/test_designaciones_formales.py tests/test_matriz_permisos.py + suite completa"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-06 · Designaciones formales: delegado de protección de datos (con inscripción y declaración) y mandato de la alta dirección al coordinador

**Objetivo.** La ley obliga a **designar** al delegado de protección de datos en ciertos casos (Art. 48) y el reglamento de 2025, según los resúmenes consultados, exige inscribir esa designación ante la Superintendencia y que el delegado declare no tener conflicto de intereses. La plataforma hoy asigna el rol `dpo` como cualquier otro, sin rastro de quién lo designó ni de si se inscribió. Lo mismo ocurre con el `coordinador`, que ejerce la función del responsable del tratamiento y supervisa todas las áreas, incluidas las de mayor jerarquía: eso exige un **mandato escrito de la alta dirección** que hoy no queda registrado.

## Entrega
- Tabla `designaciones_formales` (RLS por tenant, `GRANT` explícito a `lopdp_app`, sin DELETE): `tipo` (`dpd` o `coordinador`), `user_id`, el **representante legal o apoderado que designa** (nombre, identificación y cargo: Art. 3 del Reglamento del Delegado), `fecha_designacion`, referencia del documento de designación y vigencia. Solo para `dpd`: `vinculo` (`relacion_dependencia` o `prestacion_servicios`, Art. 49 del Reglamento General), `aceptacion_at` (aceptación del cargo, Art. 4.7), `inscripcion_spdp_fecha`, `inscripcion_spdp_ref` y la **declaración previa de conflictos** (Art. 17): `declaracion_at` y el texto declarado (conflictos reales, potenciales o aparentes, parentesco con administradores, condición de socio o accionista).
- Endpoints bajo `/api/v1/organizacion/designaciones`: crear, listar, ver, registrar la inscripción ante la Superintendencia, declarar y revocar. Crea y revoca el `admin_organizacion`; **la declaración la hace solo la propia persona designada**: nadie declara por otro.
- **Validación contra la estructura orgánica.** Al designar un `dpd`, el sistema consulta `cargos_incompatibles_con_dpd` (ORG-07) y **rechaza con 409** la designación si la persona ocupa un cargo de tipo oficial de cumplimiento, oficial de seguridad de la información, apoderado especial de una entidad extranjera o miembro de un órgano de administración o control (Art. 16 del Reglamento del Delegado y Art. 56 del Reglamento General), e indica los cargos. Si en la declaración consta que es socio o accionista, o pariente de un administrador, director o comisario, también se rechaza. Si el conflicto **sobreviene** (la persona pasa a ocupar uno de esos cargos), el estado lo marca y la organización debe corregirlo: abstenerse, reestructurar funciones o revocar (Art. 17).
- Informe de estado de solo lectura: delegado designado o no, con declaración o sin ella, inscrito o no, y con o sin cargo incompatible; coordinador con mandato o sin él. **No bloquea nada**: señala lo pendiente.
- Cada paso deja un evento en `audit_events`.
- Pruebas con base de datos: designar, declarar (solo el designado), inscribir, revocar, aislamiento por tenant y RLS con el rol de la aplicación.

## Decisiones del propietario (antes de implementar)
1. ¿Se **bloquea** que un `dpo` opere mientras no tenga designación inscrita? Propuesta: no; solo se informa, porque la inscripción depende de un trámite externo.

## Límites
- No decide por sí sola el conflicto de intereses general: lo recogen la declaración de la persona y la revisión de la Superintendencia.
- No inscribe nada en el sistema de la Superintendencia: solo guarda la constancia que aporte la organización.
- No fija plazos de inscripción: se tratan cuando se trabajen los plazos.
- No cambia la matriz de incompatibilidades (ORG-01) ni las excepciones (ORG-02).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
