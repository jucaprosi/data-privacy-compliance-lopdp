+++
id = "ORG-07"
titulo = "Estructura orgánica: unidades, cargos y jefaturas como base de los responsables de área"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["ORG-00", "RM-01", "RM-10"]
propiedad = ["alembic/versions/*_estructura_organica.py", "features/organizacion/services/estructura_engine.py", "api/routers/organizacion_estructura.py", "tests/test_estructura_organica.py", "features/organizacion/organizacion_service.py#ORG-07"]
arbitro = "pytest tests/test_estructura_organica.py tests/test_matriz_permisos.py + suite completa"
rastros = ["¤rbac-tenant"]
+++

# ORG-07 · Estructura orgánica: unidades, cargos y jefaturas como base de los responsables de área

**Objetivo.** La gobernanza empieza por la **estructura orgánica regular** de la organización. Hoy la plataforma sabe qué áreas existen (`areas`, con `parent_area_id`) y quién tiene qué rol, pero no tiene las **jefaturas**: qué cargos hay en cada unidad, quién los ocupa y a quién reporta cada uno. Sin eso, los responsables de área se nombran uno a uno y a ciegas, no se ve qué unidades quedan sin cubrir, y el `coordinador` no puede supervisar «todas las áreas, incluidas las de mayor jerarquía» porque la alta dirección ni siquiera existe como unidad. De la estructura salen las jefaturas y, de ellas, los responsables de área.

## Entrega
- **Modelo.** Una columna `nivel` en `areas` (`alta_direccion`, `direccion`, `jefatura`, `unidad`; por defecto `unidad`) con una única unidad `alta_direccion` por organización, que es la raíz del árbol. Una tabla `cargos_organicos` (RLS por tenant, `GRANT` explícito a `lopdp_app`, sin DELETE): área, nombre del cargo, `tipo_cargo` (catálogo cerrado, ver más abajo), `es_jefatura`, `reporta_a_cargo_id` (el cargo del que depende), `titular_user_id` (vacío = vacante) y vigencia. Una sola jefatura activa por área (índice único parcial).
- **Endpoints** bajo `/api/v1/organizacion/estructura`: el árbol completo (unidades, cargos, titulares y vacantes), crear y editar unidades y cargos, y asignar o quitar titular. Escribe el `admin_organizacion`; leen `coordinador`, `implementador` y `dpo` (este último solo lectura: audita).
- **Informe de cobertura:** unidades sin jefatura, jefaturas vacantes y unidades con jefatura pero **sin `responsable_area`**. De ahí sale la lista de **«responsables por designar»**, que alimenta el flujo de RM-10 (la solicitud del `coordinador`) con los datos ya precargados. **No concede roles automáticamente: propone.**
- **Tipo de cargo y cargos incompatibles con el delegado.** `tipo_cargo` toma un valor de un catálogo cerrado definido en un solo sitio: `oficial_cumplimiento`, `oficial_seguridad_informacion`, `apoderado_especial_extranjero`, `miembro_administracion_o_control` y `otro` (por defecto). Cada tipo incompatible con ser delegado de protección de datos lleva su **nivel de confianza** (alta o baja) según las fuentes que lo respaldan. La compuerta expone `cargos_incompatibles_con_dpd(user_id)`, que devuelve los cargos vigentes de una persona cuyo tipo impide ser delegado (impedimentos del Reglamento del Delegado), con ese nivel; lo usa ORG-06.
- **La alta dirección como unidad:** sobre ella el `coordinador` ejerce su supervisión como sobre cualquier otra, y se puede designar un `responsable_area` de la alta dirección.
- **Reglas:** el árbol de unidades y el de cargos no admiten ciclos; un cargo no reporta a sí mismo; cada cambio deja evento en `audit_events`.
- Pruebas con base de datos (transacción que se revierte, ejecutando el SQL real de la migración): árbol, ciclos, única raíz, única jefatura, vacantes, informe de cobertura, aislamiento por tenant y RLS con el rol de la aplicación.

## Decisiones del propietario (antes de implementar)
1. **Niveles jerárquicos.** Propuesta: alta dirección, dirección, jefatura, unidad. ¿Se necesitan otros, o con otros nombres?
2. **Del jefe al responsable de área.** Propuesta: la jefatura de una unidad se **propone** como su responsable de área, y nunca se asigna sola. ¿Es así?
3. **Jefaturas múltiples.** Propuesta: una por unidad; el subrogante se evalúa después.
4. **Catálogo de tipos de cargo.** Propuesta: los cinco indicados; se amplía cuando se contraste el texto vinculante del Reglamento del Delegado.

## Límites
- No importa organigramas desde archivos (CSV o Excel): se evalúa después.
- No crea la pantalla: es FE-09.
- No cambia roles ni reglas de incompatibilidad.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
