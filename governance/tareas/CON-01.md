+++
id = "CON-01"
titulo = "Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit"
ola = "D"
estado = "en_curso"
sala = "conservacion"
depende_de = ["ADPA-07", "ADPA-09", "RAT-07", "MARCA-01", "ORG-22c"]
propiedad = ["alembic/versions/20260429_01_con01_politicas_conservacion.py", "features/conservacion/models.py", "features/conservacion/schemas.py", "features/conservacion/conservacion_service.py#CON-01", "features/conservacion/domain/errores.py#CON-01", "features/conservacion/routes/__init__.py", "features/conservacion/routes/conservacion_routes.py", "app_core/pasillo/conservacion.py#CON-01", "app_core/pasillo/rat.py#CON-01", "app_core/pasillo/dpo_cockpit.py#CON-01", "main.py#CON-01", "frontend/src/components/layout/menus/index.ts#CON-01", "frontend/src/components/layout/pantallas/index.tsx#CON-01", "frontend/src/components/layout/pantallas/CON-01.tsx", "tests/test_con01_conservacion.py", "tests/matriz/CON-01.py", "frontend/tests/conservacion/con01.spec.ts", "tests/matriz/roles/auditor.py#CON-01"]
crea = ["tests/matriz/CON-01.py", "frontend/tests/conservacion/con01.spec.ts"]
arbitro = "pytest tests/test_con01_conservacion.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + vigilantes"
rastros = ["¤conservacion", "¤rat", "¤adpa"]
+++
# CON-01 · Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit

**Contrato:** `governance/especificaciones/CON-01.md` (manda sobre esta ficha).

## Entrega
- Tabla `politicas_conservacion` con RLS por `tenant_id` (`ENABLE/FORCE ROW LEVEL SECURITY`, permisos `SELECT, INSERT, UPDATE` a `lopdp_app`) vinculada a las actividades del RAT (`actividad_rat_id`, `plazo_meses`, `accion_vencimiento` en `{BLOQUEO, ANONIMIZACION, SUPRESION}`, `fecha_proxima_revision`, `estado` en `{ACTIVA, BLOQUEADA, EJECUTADA}`, `acta_ejecucion_hash`).
- Servicio `features/conservacion/conservacion_service.py#CON-01` que consulta las actividades del RAT exclusivamente vía `app_core/pasillo/rat.py#CON-01` y publica alertas de vencimiento de retención en el DPO Cockpit vía `app_core/pasillo/dpo_cockpit.py#CON-01`.
- Códigos de error en `features/conservacion/domain/errores.py#CON-01` (`CONSERVACION_POLITICA_NO_ENCONTRADA`, `CONSERVACION_PLAZO_INVALIDO`, `CONSERVACION_YA_EJECUTADA`).
- Router `/api/v1/conservacion` y pantalla `frontend/src/components/layout/pantallas/CON-01.tsx` registrada en `menus/index.ts#CON-01` y `pantallas/index.tsx#CON-01`.

## Pruebas
- `pytest tests/test_con01_conservacion.py` valida el ciclo completo de creación de política de retención, detección de vencimiento, generación de acta de bloqueo/anonimización con hash SHA-256 y aislamiento RLS entre inquilinos.

## Textos cerrados por UX/UI (2026-11-15)
Diseñados contra `governance/especificaciones/CON-01.md` y `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`. Los tres huecos que UX/UI detectó los resolvió el CTO el 2026-11-15 y la especificación corregida (#824) los recoge (ver «Decisiones»); los textos de abajo ya los asumen.

### Decisiones (CTO, 2026-11-15; especificación corregida en #824)
1. **Alcance de la ejecución.** R2 solo calcula el acta y cambia el estado; no bloquea, anonimiza ni suprime datos. Por eso la pantalla dice que se REGISTRA la ejecución y que la organización la hace en sus sistemas. Decidido: CON-01 solo registra; la plataforma no accede a los sistemas de la organización, así que bloquear o suprimir de verdad no va en otra ficha. El acta con su hash es la evidencia.
2. **Cita equivocada.** El título de la especificación dice «Art. 10 y 20 LOPDP»; el art. 20 es el de las decisiones automatizadas (`LOPDP-art-20`) y no trata la conservación. La única cita verificada que corresponde es `LOPDP-art-10-lit-i` (Conservación). En pantalla solo va esa; corregido en la especificación.
3. **Sin especificar.** Quién ejecuta, el umbral de «por vencer» y la ruta de la pantalla. Aceptado: ejecutan `admin_organizacion` e implementador (ESTIMADO); el DPO ve las alertas pero no ejecuta; «por vencer» = 30 días o menos (ESTIMADO); ruta `frontend/src/components/layout/pantallas/CON-01.tsx` (la especificación dice `components/pantallas/`, pero el registro usa `components/layout/pantallas/`). El submenú va inline en `menus/index.ts#CON-01`.

### Textos de pantalla
Ubicación: Inventario › «Conservación de datos», subtítulo «Plazos de conservación por tratamiento». h1 «Conservación de datos». Ayuda: «Define cuánto tiempo se conservan los datos de cada tratamiento y qué hacer cuando se cumple el plazo.» Cita al pie: «LOPDP, art. 10, lit. i».

**Listado** (tabla «Políticas de conservación»; tarjetas a 375 px): Tratamiento · Plazo («{n} meses») · Al vencer · Próxima revisión (dd/mm/aaaa) · Estado · Acción.
- «Al vencer»: BLOQUEO → «Bloquear», ANONIMIZACION → «Anonimizar», SUPRESION → «Suprimir».
- Estado: ACTIVA → «Activa», BLOQUEADA → «Bloqueo registrado», EJECUTADA → «Ejecución registrada».
- Semáforo sobre la próxima revisión, con texto e icono y nunca solo color: «Vigente» (más de 30 días), «Por vencer» (30 días o menos, ámbar), «Vencida» (fecha cumplida, rojo). Las políticas ya ejecutadas no llevan semáforo.

**Nueva política** (botón «Nueva política»; diálogo): «Tratamiento» (selector del RAT), «Plazo de conservación (meses)» (entero mayor que 0; error «Escribe un plazo de al menos 1 mes.»), «Al vencer» (Bloquear, Anonimizar, Suprimir), «Próxima revisión» (fecha). Botones «Cancelar» (foco inicial) y «Guardar política».

**Ejecutar.**
- Botón por fila, solo en políticas «Activa». Texto visible: «Registrar bloqueo», «Registrar anonimización» o «Registrar supresión». Nombre accesible: «Registrar {acción} de {tratamiento}».
- Diálogo, título: «¿Registrar la {acción} de los datos de {tratamiento}?»
- Texto: «Queda registrado que los datos de este tratamiento se {bloquearon|anonimizaron|suprimieron} al cumplirse el plazo de {n} meses. La plataforma guarda el acta como evidencia; la {acción} de los datos la hace tu organización en sus sistemas.»
- Aviso: «Este registro no se puede deshacer.»
- Casilla: «Confirmo que la {acción} ya se hizo o se hará en los sistemas de la organización.»
- Botones «Cancelar» (foco inicial) y «Registrar la {acción}», este último deshabilitado hasta marcar la casilla.
- Tras registrar, status «{Acción} registrada. El acta quedó guardada como evidencia.» y «Huella de integridad: {8 primeros caracteres}», sin «hash».

**Estados.** Cargando (status): «Cargando las políticas de conservación…». Vacío: «Aún no hay políticas de conservación. Crea una para cada tratamiento del inventario.» Error de carga (alert): «No pudimos cargar las políticas de conservación. Inténtalo de nuevo.» con el botón «Volver a cargar».

**Errores** (fijos por código; nunca el texto del servidor):
- `CONSERVACION_POLITICA_NO_ENCONTRADA`: «No encontramos esta política. Actualizamos la lista.» (recarga)
- `CONSERVACION_PLAZO_INVALIDO`: «El plazo debe ser de al menos 1 mes.» (en el campo)
- `CONSERVACION_YA_EJECUTADA`: «Esta política ya tiene la ejecución registrada. Actualizamos su estado.» (recarga)
- `CONSERVACION_ACTIVIDAD_NO_ENCONTRADA`: «El tratamiento elegido ya no está en el inventario. Elige otro.»
- 403: «No tienes permiso para esta acción.» · 401: manejo global · otros: «No pudimos guardar los cambios. Inténtalo de nuevo.»

**Roles.** Quien no ejecuta (DPO, auditor y el resto) ve el listado sin botones y con la línea «Registran la ejecución la persona administradora o el implementador.»

**Accesibilidad para Playwright.** Vista: main «Conservación de datos» · Tabla: table «Políticas de conservación» · Nueva: button «Nueva política» · Ejecutar: button «Registrar {acción} de {tratamiento}» · Diálogo: dialog «¿Registrar la {acción} de los datos de {tratamiento}?» · Casilla: checkbox «Confirmo que la {acción} ya se hizo o se hará en los sistemas de la organización.» · Plazo: spinbutton «Plazo de conservación (meses)». Foco atrapado en los diálogos, Escape, retorno del foco, contraste 4.5:1, tokens del tema, sin `¤` ni `¦`.

**Criterios de prueba.**
1. Las tres etiquetas del semáforo con fechas simuladas.
2. El botón de registrar queda deshabilitado hasta marcar la casilla.
3. Un segundo registro muestra el texto de `CONSERVACION_YA_EJECUTADA`.
4. Ningún texto visible dice «se suprimen», «se eliminan» ni «se bloquean» en presente como algo que haga la plataforma, y ninguno cita el «art. 20».
5. El DPO no ve los botones.
6. A 375 px no hay desplazamiento horizontal.
