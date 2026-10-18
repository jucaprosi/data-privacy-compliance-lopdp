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
- **Tipo de cargo y cargos incompatibles con el delegado.** `tipo_cargo` toma un valor de un catálogo cerrado definido en un solo sitio: `oficial_cumplimiento`, `oficial_seguridad_informacion`, `apoderado_especial_extranjero` (Art. 16.1 a 16.3 del Reglamento del Delegado), `miembro_administracion_o_control` (Art. 56.1 del Reglamento General: administradores, directores y comisarios), `implementador_proteccion_datos` (quien implementa la normativa de protección de datos en la organización: Art. 15.1 y 15.5 del Reglamento del Delegado, que no define el término), `nivel_superior_sector_publico` (Art. 16.4: solo aplica a organizaciones del sector público, y no se hace cumplir hasta que la configuración de la organización pueda marcarla como pública), `delegado_proteccion_datos` y `otro` (por defecto). Los seis primeros impiden ser delegado. El cargo de delegado es de **asesoría**, no de línea: reporta a la alta dirección (Art. 50 de la ley) y no puede ser jefatura de una unidad operativa. La compuerta expone `cargos_incompatibles_con_dpd(user_id)`, con los cargos vigentes de una persona que le impiden ser delegado; lo usa ORG-06.
- **La alta dirección como unidad:** sobre ella el `coordinador` ejerce su supervisión como sobre cualquier otra, y se puede designar un `responsable_area` de la alta dirección.
- **Reglas:** el árbol de unidades y el de cargos no admiten ciclos; un cargo no reporta a sí mismo; **quien es titular del cargo de delegado no puede serlo de ningún otro** (el Art. 18.1 veta ejecutar o participar en actividades de tratamiento y el 18.2 asesorar en defensa de la organización); cada cambio deja evento en `audit_events`.
- Pruebas con base de datos (transacción que se revierte, ejecutando el SQL real de la migración): árbol, ciclos, única raíz, única jefatura, vacantes, informe de cobertura, aislamiento por tenant y RLS con el rol de la aplicación.

## Decisiones asumidas (con su base legal)
1. **Niveles jerárquicos:** alta dirección (representante legal, gerencia general y órganos de administración y control), dirección, jefatura y unidad. La ley no prescribe una estructura interna: la raíz es el representante legal, que designa al delegado (Art. 3 del Reglamento del Delegado), y los órganos de administración y control deben ser identificables porque de ellos salen impedimentos (Art. 56.1 del Reglamento General). El responsable de área se asigna a la unidad **dueña de los tratamientos**.
2. **De la jefatura al responsable de área:** la jefatura se **propone** y nunca se asigna sola. Designar responsables es una decisión del `coordinador` por el flujo de RM-10; la ley atribuye las obligaciones al responsable y no a un cargo concreto (Art. 47).
3. **Jefaturas múltiples:** una por unidad. La ley no dice nada y el subrogante se evalúa después.
4. **Catálogo de tipos de cargo:** los ocho indicados. «Implementador» se lee como quien implementa de forma directa la normativa de protección de datos en la organización: es la función que el Art. 15.1 del Reglamento del Delegado veta al delegado y que el Art. 15.5 repite con ese nombre.
5. **Los catálogos son datos en un solo sitio.** La Superintendencia puede definir más supuestos de conflicto (Art. 48 de la ley, último párrafo; Art. 55 y 56.4 del Reglamento General). Adaptarse es cambiar ese módulo y, si afecta a roles, la migración del trigger de ORG-01.

## Límites
- No importa organigramas desde archivos (CSV o Excel): se evalúa después.
- No crea la pantalla: es FE-09.
- No cambia roles ni reglas de incompatibilidad.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
