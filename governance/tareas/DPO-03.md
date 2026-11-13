+++
id = "DPO-03"
titulo = "Consultas de la organización al DPO con historial como evidencia de asesoría"
ola = "D"
estado = "pendiente"
sala = "dpo_cockpit, frontend"
depende_de = ["DPO-02", "EVI-02", "ADPA-05", "ADPA-06", "ADPA-07", "ADPA-09"]
propiedad = ["alembic/versions/20261104_dpo_consultas.py", "features/dpo_cockpit/domain/consulta.py", "features/dpo_cockpit/services/consultas_engine.py", "features/dpo_cockpit/dpo_cockpit_service.py#DPO-03", "api/routers/dpo_consultas.py", "tests/test_dpo_consultas.py", "tests/matriz/DPO-03.py", "frontend/src/components/dpo/Consultas.tsx", "frontend/src/lib/dpo/consultas.ts", "frontend/tests/dpo/consultas.spec.ts", "frontend/src/components/layout/menus/DPO-03.ts", "frontend/src/components/layout/pantallas/DPO-03.tsx", "features/dpo_cockpit/domain/errores.py#DPO-03", "app_core/pasillo/dpo_cockpit.py#DPO-03", "app_core/pasillo/auditoria_capa.py#DPO-03", "app_core/pasillo/derechos_arco.py#DPO-03", "app_core/pasillo/diagnostico.py#DPO-03", "app_core/pasillo/incidentes.py#DPO-03", "app_core/pasillo/rat.py#DPO-03", "app_core/pasillo/riesgos_mtge.py#DPO-03", "app_core/pasillo/roadmap.py#DPO-03", "app_core/pasillo/terceros.py#DPO-03", "app_core/pasillo/transferencias.py#DPO-03", "app_core/pasillo/formacion.py#DPO-03", "app_core/pasillo/conservacion.py#DPO-03", "frontend/src/components/layout/menus/index.ts#DPO-03", "frontend/src/components/layout/pantallas/index.tsx#DPO-03"]
arbitro = "pytest tests/test_dpo_consultas.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/dpo/consultas.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤dpo-cockpit", "¤evidencias"]
+++

# DPO-03 · Consultas de la organización al DPO con historial como evidencia de asesoría

**Origen.** Menú 5 «Operación › Consultas» y menú 7 «DPO › Consultas atendidas» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/DPO-03.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Tickets de consulta de cualquier rol de la organización al DPO: asunto, texto, adjuntos por referencia; el DPO responde y cierra; la respuesta entra en su bitácora (DPO-01) como `OPINION_CONSULTIVA` y el hilo se custodia como evidencia de asesoría (EVI-02).
- Pantallas: Operación › Consultas (quien pregunta) y DPO › Consultas atendidas.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Solo el `dpo` responde y cierra; al cerrar existe una entrada en la bitácora y una evidencia; una consulta de A no se ve desde B.
- Mutación documentada: cerrar sin crear la entrada de bitácora y comprobar que la prueba falla.

## Límites
- Sin plazos de respuesta.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#DPO-03` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#DPO-03` sin modificar `app_core/errors.py`.

## Textos cerrados por UX/UI (2026-11-13)
Diseñado contra la ficha y `governance/especificaciones/DPO-03.md`; UX/UI no corrió pantalla. **Adjuntos:** la especificación no tiene campo ni ruta de adjuntos (solo asunto y texto); el diseño no los incluye. Pendiente de decisión del CTO: retirarlos del texto de la ficha o abrir otra ficha (cargas en EVI-01b).

**Dos vistas, un solo `Consultas.tsx` con dos modos**, registradas en `menus/DPO-03.ts` y `pantallas/DPO-03.tsx`:
- «Mis consultas»: menú Operación › «Consultas al DPO», subtítulo «Pregunta al DPO y consulta sus respuestas». La ven todos los roles de la organización.
- «Consultas atendidas»: menú DPO › «Consultas atendidas», subtítulo «Consultas de la organización y sus respuestas». La ven `dpo`, `admin_organizacion` y `coordinador`; solo el DPO responde y cierra. ESTIMADO: que los menús «Operación» y «DPO» existan con ese nombre en el registro.

**Mis consultas.** h1 «Consultas al DPO». Línea «Escribe tu pregunta al delegado de protección de datos. Su respuesta queda guardada con la consulta.» Botón «Nueva consulta»: «Asunto» (obligatorio, máx. 120; ayuda «Resume el tema en una línea.») y «Tu consulta» (obligatorio); botones «Cancelar» y «Enviar consulta»; errores «Escribe el asunto.» y «Escribe tu consulta.» Lista con asunto, fecha y estado «Abierta», «Respondida» o «Cerrada». Hilo por fecha con «{Nombre} · {Rol}» y hora. Abierta: campo «Tu mensaje» y botón «Enviar mensaje». Cerrada: «Esta consulta está cerrada. Para otra pregunta, crea una nueva consulta.» Vacío: «Aún no hiciste ninguna consulta al DPO.»

**Consultas atendidas.** h1 «Consultas atendidas»; filtro «Estado» (Todas, Abiertas, Respondidas, Cerradas; por defecto Abiertas); vacío «No hay consultas {abiertas|respondidas|cerradas}.» Solo el DPO ve «Responder y cerrar» (aria-label «Responder y cerrar la consulta {asunto}»): diálogo «Responder y cerrar la consulta», campo «Tu respuesta final» (obligatorio; error «Escribe tu respuesta final.»), aviso «Al cerrar, la consulta ya no admite más mensajes. Tu respuesta y el hilo quedan guardados en tu bitácora y como evidencia de asesoría.», botones «Cancelar» (foco inicial) y «Responder y cerrar». El DPO también escribe mensajes intermedios («Enviar mensaje») y la consulta pasa a «Respondida». Tras cerrar: `role=status` «Consulta cerrada. Tu respuesta quedó guardada en la bitácora.» y la línea «Respuesta guardada como evidencia de asesoría» con los 8 primeros caracteres de la huella (aria-label «Huella de integridad»). Admin y coordinador: «Solo el DPO responde y cierra las consultas.»

**Errores (fijos por código).** Cargar: `role=alert` «No pudimos cargar las consultas. Inténtalo de nuevo.» y «Volver a cargar». Enviar: «No pudimos enviar tu mensaje. Inténtalo de nuevo.» 409 `CONSULTA_CERRADA`: «Esta consulta ya está cerrada. Para otra pregunta, crea una nueva consulta.» y se recarga el hilo. Cerrar: «No pudimos cerrar la consulta. Sigue abierta.» 403: «Solo el DPO puede responder y cerrar consultas.» 401 global.

**Independencia del DPO.** Ningún texto dice que el DPO «aprueba» o «garantiza» el cumplimiento; se habla de «respuesta» u «opinión». No salen en pantalla «dictamen», «OPINION_CONSULTIVA», «hash», ids ni correos. El texto de las consultas se muestra como texto plano.

**Accesibilidad.** `main` «Consultas al DPO» / «Consultas atendidas»; `list` «Mis consultas» / «Consultas de la organización»; `combobox` «Estado»; hilo `log` o `list` «Mensajes de la consulta»; botones «Enviar consulta» y «Responder y cerrar la consulta {asunto}»; `dialog` «Responder y cerrar la consulta»; estado `status`. Foco inicial en «Cancelar»; al cerrar vuelve al botón. Contraste 4.5:1, tokens del tema.

**Criterios de prueba.** (1) El coordinador ve la bandeja sin «Responder y cerrar». (2) El DPO cierra: «Cerrada», el autor ve la respuesta y desaparece el campo. (3) Un mensaje tras el cierre muestra el texto fijo del 409. (4) Un rol sin acceso no ve «Consultas atendidas». (5) Sin «dictamen», «OPINION_CONSULTIVA», «hash», ids ni caracteres de gobernanza. (6) A 375 px, sin desplazamiento horizontal.
