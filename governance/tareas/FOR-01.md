+++
id = "FOR-01"
titulo = "Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación"
ola = "D"
estado = "pendiente"
sala = "formacion, frontend"
depende_de = ["ORG-17", "EVI-02", "FE-22", "ADPA-06", "ADPA-07", "ADPA-09", "EVI-04"]
propiedad = ["alembic/versions/for01_formacion.py", "features/formacion/models.py", "features/formacion/schemas.py", "features/formacion/domain/formacion.py", "features/formacion/services/__init__.py", "features/formacion/services/contenidos_engine.py", "features/formacion/services/acciones_engine.py", "features/formacion/services/examen_engine.py", "features/formacion/services/diploma_engine.py", "features/formacion/services/cobertura_engine.py", "features/formacion/formacion_service.py#FOR-01", "features/formacion/domain/errores.py#FOR-01", "app_core/pasillo/formacion.py#FOR-01", "app_core/pasillo/evidencias.py#FOR-01", "app_core/pasillo/dpo_cockpit.py#FOR-01", "app_core/pasillo/organizacion.py#FOR-01", "features/organizacion/organizacion_service.py#FOR-01", "api/routers/formacion.py", "tests/test_formacion.py", "tests/matriz/FOR-01.py", "frontend/src/lib/formacion/formacion.ts", "frontend/src/components/formacion/ContenidosPanel.tsx", "frontend/src/components/formacion/AccionesPanel.tsx", "frontend/src/components/formacion/CoberturaTarjeta.tsx", "frontend/src/components/formacion/MiFormacion.tsx", "frontend/src/components/layout/menus/FOR-01.ts", "frontend/src/components/layout/pantallas/FOR-01.tsx", "frontend/src/components/layout/menus/index.ts#FOR-01", "frontend/src/components/layout/pantallas/index.tsx#FOR-01", "frontend/tests/formacion/examen.spec.ts", "frontend/tests/formacion/gestion.spec.ts"]
crea = ["alembic/versions/for01_formacion.py", "features/formacion/models.py", "features/formacion/schemas.py", "features/formacion/domain/formacion.py", "features/formacion/services/__init__.py", "features/formacion/services/contenidos_engine.py", "features/formacion/services/acciones_engine.py", "features/formacion/services/examen_engine.py", "features/formacion/services/diploma_engine.py", "features/formacion/services/cobertura_engine.py", "api/routers/formacion.py", "tests/test_formacion.py", "tests/matriz/FOR-01.py", "frontend/src/lib/formacion/formacion.ts", "frontend/src/components/formacion/ContenidosPanel.tsx", "frontend/src/components/formacion/AccionesPanel.tsx", "frontend/src/components/formacion/CoberturaTarjeta.tsx", "frontend/src/components/formacion/MiFormacion.tsx", "frontend/src/components/layout/menus/FOR-01.ts", "frontend/src/components/layout/pantallas/FOR-01.tsx", "frontend/tests/formacion/examen.spec.ts", "frontend/tests/formacion/gestion.spec.ts"]
arbitro = "pytest tests/test_formacion.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/formacion + tsc --noEmit + npm run build; adpa_linter (sala nueva con compuerta formacion_service.py); prueba de mutación documentada"
rastros = ["¤evidencias", "¤rbac-tenant"]
+++

# FOR-01 · Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación

**Origen.** Menú 5 «Operación › Formación» y PRD Módulo 2 («Formación, sala formacion, fase posterior»).

**Contrato:** `governance/especificaciones/FOR-01.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Sala nueva `features/formacion/` con compuerta `formacion_service.py` (la primera tarea de una sala crea la sala, ADPA).
- Contenidos (PDF o enlace a video) y banco de preguntas; acción formativa con personas (ORG-17), fechas, examen, nota mínima; seguimiento por persona (enviado, iniciado, terminado, nota) y cobertura = personas formadas / personas que tratan datos.
- El diploma y el registro de notas se custodian como evidencia del control de capacitación (EVI-02, control P-correspondiente del catálogo).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Una persona con nota ≥ mínima queda «formada» y existe su evidencia; la cobertura se calcula sobre personas activas; RLS entre organizaciones.
- Mutación documentada: contar como formada una nota inferior a la mínima y comprobar que la prueba falla.

## Límites
- Sin cursos base de la plataforma (fase 5); sin SCORM.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#FOR-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#FOR-01` sin modificar `app_core/errors.py`.

## Textos cerrados por UX/UI y decisiones del CTO (2026-11-13)
Diseñado contra la ficha y `governance/especificaciones/FOR-01.md`; UX/UI no corrió pantalla. **No se lanza hasta que el Arquitecto cierre dos huecos de API en la especificación:** rutas del banco de preguntas (crear y leer por contenido), y para la persona, una ruta GET con las preguntas de su participación sin el campo `correcta` y otra que marque `iniciado_en`.

**Decisiones del CTO.**
- Contenido: se elige entre documentos custodiados (EVI-02) o se pega un enlace; sin subida directa. El enlace solo con `https`, y la vista muestra el dominio al que lleva.
- Un solo intento (R4); no hay «Reabrir examen» en FOR-01 y el aviso antes de empezar se queda. Si se necesita, irá en una ficha aparte: motivo obligatorio, el intento anterior intacto, el nuevo registrado con quién reabrió y cuándo, y quien reabre no puede ser el examinado.
- Texto visible «Constancia de formación», nunca «diploma» ni «certificado» (Doctrina 1: la plataforma no emite certificados ni acreditaciones). El código interno no cambia.

**Ubicación y roles.** «Operación» › «Formación» (subtítulo «Contenidos, capacitaciones y avance»): escriben implementador, coordinador y admin_organizacion; los demás roles con lectura ven solo cobertura y avance. «Operación» › «Mi formación» (subtítulo «Tus capacitaciones y tu examen»): la ve quien tenga una participación; sin participaciones, el submenú no aparece (`visible(ctx)`).

**Formación** (`tablist` «Formación» con «Cobertura», por defecto, «Acciones» y «Contenidos»).
- Cobertura: h2 «Cobertura de formación»; «{formadas} de {obligadas} personas formadas ({porcentaje} %)»; ayuda «Cuenta a las personas activas que tratan datos personales. Quienes no tienen tratamientos asignados no entran en el cálculo.»; con 0 obligadas: «Aún no hay personas con tratamientos asignados. La cobertura se calcula cuando las haya.»; `progressbar` «Personas formadas» con `aria-valuetext` «{formadas} de {obligadas}». Sin «cumple» ni «suficiente».
- Acciones: lista con nombre, contenido, «Del {inicio} al {fin}», nota mínima y «{n} de {total} terminaron»; «Nueva acción formativa» con «Nombre de la acción», «Contenido», «Fecha de inicio», «Fecha de fin» (error «La fecha de fin debe ser posterior a la de inicio.»), «Nota mínima para aprobar» (0 a 100; ayuda «Por ejemplo, 70.»), botones «Cancelar» (foco inicial) y «Crear acción». Detalle: «Añadir participantes» («Se enviará la formación a las personas elegidas.») y tabla «Avance por persona» (Persona · Estado · Nota · Constancia) con estados «Enviada», «Iniciada», «Aprobó», «No aprobó», «Fuera de fechas», con texto e icono. Vacío: «Aún no hay acciones formativas. Crea una para empezar.»
- Contenidos: título, tipo («PDF» o «Video»), fecha; «Nuevo contenido» con «Título», «Tipo», «Enlace o documento» y «Preguntas del examen» (enunciado, 2 a 5 opciones, «Respuesta correcta»); ayuda «Cada persona rinde el examen una sola vez.» Vacío: «Aún no hay contenidos. Añade un PDF o un enlace a un video.»

**Mi formación.** h1 «Mi formación»; lista con nombre, fechas y estado. Detalle con «Abrir el contenido» y el bloque «Examen». Aviso antes de empezar: «Tienes un solo intento. Una vez que lo envíes no podrás repetirlo. Nota mínima: {n}.» y «Empezar el examen»; fuera de fechas: «Esta formación se puede rendir del {inicio} al {fin}.» con el botón en `aria-disabled`. Cada pregunta en un `radiogroup` con el enunciado como nombre; «Enviar respuestas» en `aria-disabled` con «Te faltan {n} preguntas por responder.»; confirmación «¿Enviar tus respuestas? Tienes un solo intento y no podrás cambiarlas después.» con «Cancelar» (foco inicial) y «Enviar respuestas». Resultado `role=status`: «Aprobaste con {nota}. Tu constancia de formación quedó guardada.» y «Abrir tu constancia»; o «No alcanzaste la nota mínima ({nota} de {mínima}). Consulta con tu coordinador cómo continuar.», sin reintento. 409 `EXAMEN_YA_RENDIDO`: «Ya rendiste este examen.» con la nota si existe.

**Errores fijos.** Carga `role=alert` «No pudimos cargar la formación. Inténtalo de nuevo.» y «Volver a cargar». Guardar: «No pudimos guardar los cambios. Inténtalo de nuevo.» Examen: «No pudimos enviar tus respuestas. Inténtalo de nuevo.», y «Tu intento no se ha consumido.» solo si el servidor lo garantiza (lo confirma el Arquitecto y lo prueba la ficha). 409 `ACCION_FUERA_DE_FECHAS`: «Esta formación se puede rendir del {inicio} al {fin}.» 403 en escritura: «No tienes permiso para esta acción.»; 401 global.

**Accesibilidad.** `main` «Formación» / «Mi formación»; `tab` «Acciones», «Contenidos», «Cobertura»; `progressbar` «Personas formadas»; `table` «Avance por persona»; `radiogroup` {enunciado}; botón «Enviar respuestas»; enlace «Abrir tu constancia». Foco inicial en «Cancelar»; contraste 4.5:1; tokens del tema; estado nunca solo por color.

**Criterios de prueba.** (1) 4 obligadas y 2 formadas: «2 de 4 personas formadas (50 %)». (2) El coordinador ve «Nueva acción formativa»; un rol de solo lectura no. (3) Sin participaciones no aparece «Mi formación». (4) «Enviar respuestas» deshabilitado hasta contestar todo y con confirmación. (5) Aprobado con enlace a la constancia; reprobado sin reintento. (6) Segundo intento o fuera de fechas con el texto fijo. (7) Ningún texto con «diploma», «certificado», «hash», ids ni caracteres de gobernanza. (8) A 375 px, tablas en tarjetas sin desplazamiento horizontal.

## Propiedad concreta y huecos de API cerrados (Arquitecto ADPA, 2026-11-13)
Especificación `governance/especificaciones/FOR-01.md` (R4 a R7):
- banco de preguntas por contenido: el GET devuelve `correcta`, el POST asigna el orden en el servidor y, con una participación iniciada, el banco se congela (409 `PREGUNTAS_CONGELADAS`);
- `GET /formacion/participaciones/{id}/examen` sin `correcta` (`extra="forbid"`);
- `POST …/iniciar` idempotente;
- el envío, en una sola transacción que termina en `UPDATE … WHERE terminado_en IS NULL`: **solo un 200 consume el intento**.

La migración pasa a `for01_formacion.py`, sin fecha. Sin comodines: la lista de archivos sustituye a `services/**`, `components/formacion/**`, `lib/formacion/**` y `tests/formacion/**`. Siembra `app_core/pasillo/evidencias.py#FOR-01` y retira su exención.

Pruebas nuevas en `tests/test_formacion.py`, cada una con su mutación: `test_examen_fallido_no_consume_intento` (fijar `terminado_en` antes de custodiar), `test_examen_concurrente_un_solo_intento` (quitar `AND terminado_en IS NULL`), `test_examen_sin_correcta` (incluir `correcta`), `test_iniciar_idempotente` y `test_banco_congelado`.

Con esto, «Tu intento no se ha consumido.» se muestra con cualquier respuesta distinta de 200, salvo `EXAMEN_YA_RENDIDO`. Los nombres de los componentes son propuesta de corte: si UX/UI los nombra distinto, se cambian solo los nombres.

## Decisiones del CTO tras la medición del Arquitecto (2026-11-13)
FOR-01 vuelve a pendiente y espera a `EVI-04`.

- **Constancia:** se custodia con `custodiar_documento_generado` de EVI-04 por `app_core/pasillo/evidencias.py`, vinculada a `["P73"]` y `tipo_evidencia = "capacitacion"`.
- **Persona que rinde:** sin migración y sin `user_id`. Es la persona del inventario cuyo `email` coincide con el correo del usuario autenticado, comparando los dos en minúsculas y sin espacios, del mismo tenant y no archivada. Sin persona: 403 `PERSONA_NO_VINCULADA`, con el texto «Tu correo no está registrado en el inventario de personas. Pide al administrador de tu organización que lo registre.» La prueba cubre las mayúsculas, la persona archivada y la persona de otro tenant. Las funciones `persona_de_usuario(session, tenant_id, email)` y `personas_activas(session, tenant_id, ids)` van en `app_core/pasillo/organizacion.py#FOR-01` y leen `inventario_engine` por `organizacion_service.py#FOR-01`.
- **Denominador de la cobertura (v1):** todas las personas activas, no archivadas, de la organización. La interfaz dice «Cobertura sobre todas las personas activas del inventario». Esto sustituye el texto de ayuda anterior. Afinarlo por área espera a `RAT-08`.
- La especificación cambia «persona.user_id» por «persona del inventario con el correo del usuario autenticado» (rama espec-for01 del Arquitecto).
