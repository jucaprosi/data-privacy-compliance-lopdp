+++
id = "INC-02"
titulo = "Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica"
ola = "D"
estado = "pendiente"
sala = "incidentes, frontend"
depende_de = ["INC-01", "FE-23", "RM-21", "EVI-02", "ADPA-05", "ADPA-06", "ADPA-07"]
propiedad = ["alembic/versions/20261104_incidentes_asistente.py", "features/incidentes/domain/vulneracion.py", "features/incidentes/services/asistente_engine.py", "features/incidentes/services/informes_engine.py", "features/incidentes/incidentes_service.py#INC-02", "api/routers/incidentes_asistente.py", "tests/test_incidentes_asistente.py", "tests/matriz/INC-02.py", "frontend/src/components/incidentes/**", "frontend/src/lib/incidentes/asistente.ts", "frontend/tests/incidentes/asistente.spec.ts", "frontend/src/components/layout/menus/INC-02.ts", "frontend/src/components/layout/pantallas/INC-02.tsx", "features/incidentes/domain/errores.py#INC-02", "app_core/pasillo/incidentes.py#INC-02", "app_core/pasillo/evidencias.py#INC-02", "app_core/pasillo/notificaciones.py#INC-02", "app_core/pasillo/dpo_cockpit.py#INC-02", "frontend/src/components/layout/menus/index.ts#INC-02", "frontend/src/components/layout/pantallas/index.tsx#INC-02"]
arbitro = "pytest tests/test_incidentes_asistente.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/incidentes/asistente.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤incidentes", "¤hallazgos"]
+++

# INC-02 · Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica

**Origen.** Menú 5 «Operación › Vulneraciones» y asistente de ocho secciones de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`; norma técnica Res. SPDP-SPD-2026-0040-R (LEG-02).

**Contrato:** `governance/especificaciones/INC-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Asistente (FE-23) de ocho secciones sobre el registro de INC-01: identificación, tratamientos afectados, titulares y datos, descripción y tipo, efectos y medidas, resolución, decisión de notificar con justificación, informes y evidencia de notificación.
- Informes para la SPDP y para titulares con el contenido mínimo de la norma técnica, generados como documento y custodiados como evidencia (EVI-02).
- Las lecciones aprendidas producen hallazgos (`origen = incidente`). **Los plazos no se calculan** (aplazados: LEG-03 y REG-01); el asistente muestra las fechas y deja el cálculo al paquete normativo.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Un incidente completado tiene decisión con justificación obligatoria; el informe contiene las secciones mínimas; cada lección genera un hallazgo.
- Mutación documentada: permitir decidir sin justificación y comprobar que la prueba falla.

## Precondición de cierre (INC-03, decisión del CTO 2026-11-12; ESTIMADO, el plazo del art. 43 sigue aplazado)
- Con INC-02 en `main`, **no se cierra un incidente con `afecta_datos_personales` sin la decisión de notificar registrada**: el cierre responde 409 con un código del catálogo que la nombra. La precondición vive en la sección `INC-02` de `incidentes_service.py`, sin tocar los archivos de INC-03. Hasta entonces, INC-03 cierra con `decision_notificacion = 'pendiente'`. Prueba con mutación: quitar la comprobación → el cierre pasa y la prueba falla.

## Límites
- Sin cuenta regresiva de plazos; sin envío al SISPDP.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#INC-02` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#INC-02` sin modificar `app_core/errors.py`.

## Textos cerrados por UX/UI y decisiones del CTO (2026-11-13)
Diseñado contra la ficha, `governance/especificaciones/INC-02.md` y `CITAS_LEGALES_VERIFICADAS.md`; UX/UI no corrió pantalla. Menú Operación › Vulneraciones (vista `incidentes`, ya existe); el asistente es una vista del mismo submenú sobre el asistente genérico de FE-23.

**Decisiones del CTO.**
- Adjunto de la notificación: se elige entre las evidencias ya custodiadas (EVI-02), nunca se sube directo. Una sola custodia, con su sha256.
- Roles: implementador y coordinador completan los pasos 1 a 6; dpo e implementador, los pasos 7 y 8 y los informes; el coordinador ve 7 y 8 sin escribir. El registro de «notificado» guarda quién lo marcó y cuándo; si lo marca el implementador, el dpo lo ve en su bandeja. Los informes los firma quien los emite.
- Plazo: texto sin cifras ni código interno: «Los plazos legales no se calculan aquí. La ley fija términos para avisar a la Autoridad y a los titulares: consúltalos con tu DPO o tu asesor jurídico.» Cuando LEG-03 calcule los términos citando el texto oficial verificado, se cambia por el cálculo. Ninguna cifra de memoria.

**Lista.** Cada incidente: título, fecha, estado y «Sección {n} de 8» con `progressbar` «Avance del asistente»; botón «Continuar» (nombre accesible «Continuar el asistente de {título}»). Vacío: «Aún no hay vulneraciones registradas.» (INC-01).

**Asistente de ocho pasos.** `ol` «Pasos del asistente» con «Paso n de 8: {nombre}»: 1 «Identificación», 2 «Tratamientos afectados», 3 «Titulares y datos», 4 «Descripción y tipo», 5 «Efectos y medidas», 6 «Resolución», 7 «Decisión de notificar», 8 «Informes y notificación»; estado «Completo» o «Pendiente»; el actual con `aria-current="step"`. Botones «Anterior» y «Guardar y continuar»; paso incompleto: `role=alert` «Completa este paso antes de continuar: {lo que falta}.»; 409 `SECCION_ANTERIOR_INCOMPLETA`: «Antes de seguir, completa el paso {n}: {nombre}.» con enlace al paso.
- Paso 3, ayuda: «Indica un número aproximado de titulares y de registros; si no lo sabes aún, escribe tu mejor estimación y anótalo en la descripción.»
- Paso 4, «Tipo de vulneración»: «Confidencialidad (alguien accedió a datos sin permiso)», «Integridad (los datos se alteraron sin permiso)», «Disponibilidad (los datos dejaron de estar accesibles)».
- Paso 6, lista «Lecciones aprendidas» con «Añadir lección»; ayuda «Cada lección se guarda como un hallazgo del plan de acción.»; al guardar, `role=status` «Lección guardada como hallazgo.»

**Paso 7.** `radiogroup` «Decisión»: «Notificar a la Autoridad», «Notificar a los titulares», «Notificar a ambos», «No notificar» («Documenta por qué esta vulneración no requiere aviso.»). «Justificación» obligatoria siempre, mínimo 20 caracteres, contador «{n} de 20 caracteres como mínimo»; 422 `DECISION_SIN_JUSTIFICACION`: «Explica tu decisión con al menos 20 caracteres.» Nota fija: «Esta decisión es tuya como responsable. La plataforma la registra con su justificación; no sustituye el criterio de tu DPO ni de tu asesor jurídico.» Bloque de plazos con el texto aprobado. Ningún texto dice «cumple», «cumplió» ni «dentro del plazo».

**Paso 8.** «Generar informe para la Autoridad» y «Generar comunicación a los titulares», solo los que pide la decisión; con «No notificar»: «Decidiste no notificar; no hay informes que generar.» Al generar: `role=status` «Informe generado y guardado como evidencia.» con «Abrir el informe para la Autoridad» / «Abrir la comunicación a los titulares». Aviso: «Revisa el contenido antes de usarlo. El informe se arma con lo que registraste en los pasos anteriores.»; para la Autoridad: «Presenta el informe en el SISPDP (servicios.spdp.gob.ec).» «Fecha de notificación» y «Evidencia de la notificación» (entre evidencias custodiadas); «Registrar notificación» → `role=status` «Notificación registrada.» La fecha no se compara con ningún plazo. 409 al generar sin 1 a 6: «Completa los pasos del 1 al 6 antes de generar los informes.» El coordinador ve los botones con `aria-disabled` y «Solo el DPO o el implementador generan los informes.»

**Errores fijos.** Cargando `role=status` «Cargando el asistente…»; carga `role=alert` «No pudimos cargar el asistente. Inténtalo de nuevo.» y «Volver a cargar»; guardar paso «No pudimos guardar este paso. Inténtalo de nuevo.»; generar «No pudimos generar el informe. Inténtalo de nuevo.»; registrar «No pudimos registrar la notificación. Inténtalo de nuevo.»; 403 en acciones «No tienes permiso para esta acción.»; 401 global.

**Accesibilidad.** `main` «Asistente de vulneración»; `list` «Pasos del asistente»; `progressbar` «Avance del asistente»; `radiogroup` «Decisión»; `textbox` «Justificación»; botones «Guardar y continuar», «Generar informe para la Autoridad», «Generar comunicación a los titulares», «Registrar notificación». Foco al primer campo con error; contraste 4.5:1; tokens del tema; estado nunca solo por color.

**Criterios de prueba.** (1) Con el paso 3 vacío no se avanza al 7 y el texto dice qué falta. (2) Justificación de 10 caracteres: 422 y no avanza; con 20, sí; «No notificar» también la exige. (3) En el paso 8 solo los botones que pide la decisión. (4) Al generar, «Abrir informe» y el status; el coordinador ve los botones con `aria-disabled`. (5) Dos lecciones guardan dos hallazgos. (6) Ningún texto con «LEG-03», «REG-01», «hash», ids, caracteres de gobernanza, ni afirmación de cumplimiento o de plazo cumplido. (7) A 375 px, sin desplazamiento horizontal.
