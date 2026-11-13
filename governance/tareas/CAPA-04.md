+++
id = "CAPA-04"
titulo = "Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa, frontend"
depende_de = ["CAPA-02", "RM-21", "EVI-02", "DIAG-03", "ADPA-05", "ADPA-06", "ADPA-07", "ORG-22", "CAPA-03", "DIAG-07", "DPO-03", "RM-23"]
propiedad = ["alembic/versions/capa04_auditoria_grilla.py", "features/auditoria_capa/domain/auditoria.py", "features/auditoria_capa/services/grilla_engine.py", "features/auditoria_capa/auditoria_capa_service.py#CAPA-04", "api/routers/auditoria_grilla.py", "tests/test_auditoria_grilla.py", "tests/matriz/CAPA-04.py", "frontend/src/components/layout/menus/CAPA-04.ts", "frontend/src/components/layout/pantallas/CAPA-04.tsx", "features/auditoria_capa/domain/errores.py#CAPA-04", "app_core/pasillo/auditoria_capa.py#CAPA-04", "frontend/src/components/layout/menus/index.ts#CAPA-04", "frontend/src/components/layout/pantallas/index.tsx#CAPA-04", "features/roadmap/services/cierre_hallazgos_engine.py#CAPA-04", "app_core/pasillo/roadmap.py#CAPA-04", "app_core/pasillo/diagnostico.py#CAPA-04", "app_core/pasillo/evidencias.py#CAPA-04", "app_core/pasillo/organizacion.py#CAPA-04", "frontend/src/components/auditoria/AuditoriasView.tsx", "frontend/src/components/auditoria/GrillaAuditoria.tsx", "frontend/src/components/auditoria/ActasPorArea.tsx", "frontend/src/components/auditoria/CierresPorVerificar.tsx", "frontend/src/lib/auditoria/auditorias.ts", "frontend/tests/auditoria/auditorias.spec.ts"]
siembra = ["features/roadmap/services/cierre_hallazgos_engine.py#CAPA-04", "app_core/pasillo/roadmap.py#CAPA-04", "app_core/pasillo/diagnostico.py#CAPA-04", "app_core/pasillo/evidencias.py#CAPA-04", "app_core/pasillo/organizacion.py#CAPA-04"]
crea = ["frontend/src/components/auditoria/AuditoriasView.tsx", "frontend/src/components/auditoria/GrillaAuditoria.tsx", "frontend/src/components/auditoria/ActasPorArea.tsx", "frontend/src/components/auditoria/CierresPorVerificar.tsx", "frontend/src/lib/auditoria/auditorias.ts", "frontend/tests/auditoria/auditorias.spec.ts"]
arbitro = "pytest tests/test_auditoria_grilla.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/auditoria + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤auditoria-capa", "¤hallazgos"]
+++

# CAPA-04 · Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción

**Origen.** Menú 6 «Auditorías» y conflicto D-4 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: acta de auditoría por área, nunca certificado (Doctrina 1).

**Contrato:** `governance/especificaciones/CAPA-04.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Auditoría con alcance (tratamientos, áreas, equipo auditor); grilla por control: lo declarado (último resultado sellado, DIAG-03), riesgo inicial, lo verificado, evidencia (referencia EVI-02), riesgo final, revisado por.
- Conclusiones y **acta por área** (alcance, lo verificado, evidencia revisada) custodiada como evidencia; la palabra «certificado» no aparece.
- Cada fila `verificado < declarado` produce un hallazgo `auditoria`. El auditor no audita controles que él ejecutó (SoD).
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Una fila verificada por debajo de lo declarado genera un hallazgo; el acta existe por área y no contiene «certificado»; quien ejecutó un control no puede verificarlo (403).
- Mutación documentada: permitir que el ejecutor verifique y comprobar que la prueba falla.

## Límites
- Sin programa anual automático (fechas: REG-01).


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#CAPA-04` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#CAPA-04` sin modificar `app_core/errors.py`.

## Textos cerrados por UX/UI (2026-11-13)
Diseñado contra la ficha y `governance/especificaciones/CAPA-04.md`; UX/UI no corrió pantalla. **Huecos abiertos** (deciden el CTO y el Arquitecto; no bloquean la pantalla): (1) quién cierra: la especificación deja `cerrar` al `implementador` y la demo dice que el auditor «levanta actas por área»; el diseño sigue la especificación. (2) Actas descargables: la API solo devuelve `{area_id, acta_sha256}` sin ruta de lectura ni descarga; «Descargar acta» queda «si entra». (3) Nombres de los seis niveles (0 a 5): los del diagnóstico, por confirmar; si no, «Nivel 0» a «Nivel 5». (4) El rol `auditor` aún no está en `main` (ORG-22, #675).

**Ubicación y roles.** Menú «Riesgos y auditoría», submenú «Auditorías», subtítulo «Verifica los controles y levanta las actas». Vista `capa04_auditorias`. La ven implementador, coordinador y auditor. Crean implementador y coordinador; llena la grilla el equipo auditor; cierra el implementador. Los demás no ven el submenú; la autorización la hace el servidor.

**Lista.** h1 «Auditorías». Línea «Cada auditoría verifica los controles de las áreas elegidas y termina en un acta por área.» Botón «Nueva auditoría» (implementador y coordinador). Lista: nombre, áreas, fecha, estado «Abierta» o «Cerrada», avance «{n} de {total} controles verificados». Vacío: «Aún no hay auditorías. Crea una para verificar los controles declarados en el diagnóstico.»

**Nueva auditoría (diálogo).** «Nombre de la auditoría» (obligatorio), «Áreas a auditar» (al menos una), «Equipo auditor» (al menos una persona con rol auditor). Ayuda «Los controles se cargan con el último diagnóstico sellado.» Botones «Cancelar» (foco inicial) y «Crear auditoría». Errores «Escribe el nombre.», «Elige al menos un área.», «Elige al menos una persona del equipo.» 404 `DIAG_SIN_RESULTADO`: `role=alert` «Aún no hay un diagnóstico sellado. Sella el diagnóstico antes de crear una auditoría.»

**Grilla.** Columnas: Control (código y nombre) · Declarado · Riesgo inicial · Verificado · Evidencia · Riesgo final · Revisado por; en móvil, una tarjeta por control. Declarado: nivel del último diagnóstico sellado, solo lectura. Riesgo: valor y etiqueta «Medio», «Alto», «Crítico» con el corte de R2 (crítica ≥15, alta ≥9); «Bajo» solo si hay corte inferior. Verificado: selector «Nivel verificado» 0 a 5, editable solo por el equipo auditor con la auditoría abierta. Evidencia: «Adjuntar evidencia» elige entre las ya custodiadas (referencia, no subida); la fila muestra el nombre, no la huella. «Guardar» por fila con `role=status` «Control {código} guardado.» Verificado menor que declarado: «Por debajo de lo declarado» (texto e icono) y «Se registrará un hallazgo al cerrar.»; después, «Hallazgo registrado». 403 `AUDITOR_EJECUTOR`: «No puedes verificar este control porque participaste en su ejecución. Lo verifica otra persona del equipo.» Avance `progressbar` «Controles verificados» «{n} de {total}». «Cerrar auditoría» (implementador) con `aria-disabled` y «Faltan {n} controles por verificar.» mientras falten. Diálogo «¿Cerrar la auditoría {nombre}?», «Se genera un acta por cada área auditada y se guarda como evidencia. Después de cerrar no se pueden cambiar los controles.», botones «Cancelar» (foco inicial) y «Cerrar auditoría». 409 `AUDITORIA_INCOMPLETA`: «Aún hay controles sin verificar. Complétalos antes de cerrar.»

**Actas.** Sección «Actas por área»: una fila por área con «Ver acta» (y «Descargar acta» si entra). Encabezado «Acta de auditoría · {área}»; pie «Esta acta recoge lo verificado por el equipo auditor en la fecha indicada y no sustituye otras verificaciones.» La palabra «certificado» no aparece en ninguna parte; ninguna pantalla afirma conformidad.

**Errores fijos.** Cargando `role=status` «Cargando las auditorías…». Carga: `role=alert` «No pudimos cargar las auditorías. Inténtalo de nuevo.» y «Volver a cargar». Guardar fila: «No pudimos guardar este control. Inténtalo de nuevo.» Crear: «No pudimos crear la auditoría. Inténtalo de nuevo.» Cerrar: «No pudimos cerrar la auditoría. Sigue abierta.» 401 global; 403 general, no se pinta la vista.

**Accesibilidad.** `main` «Auditorías»; `list` «Auditorías»; `table` «Verificación de controles»; `combobox` «Nivel verificado del control {código}»; botón «Guardar el control {código}»; `progressbar` «Controles verificados»; botón «Cerrar auditoría»; `list` «Actas por área». Foco inicial en «Cancelar»; vuelve al botón al cerrar. Contraste 4.5:1, tokens del tema; estado y avance nunca solo por color.

**Criterios de prueba.** (1) Declarado 3 y verificado 1: «Por debajo de lo declarado» y, tras cerrar, «Hallazgo registrado». (2) Con filas sin verificar, «Cerrar auditoría» con `aria-disabled`; se habilita al verificar la última. (3) Un revisor ejecutor ve el texto del 403 y la fila no cambia. (4) Una acta por área, sin «certificado». (5) Rol sin acceso no ve el submenú; el coordinador no ve «Cerrar auditoría». (6) Sin diagnóstico sellado, el texto fijo del 404. (7) A 375 px, tarjetas sin desplazamiento horizontal.

## Corrección del Arquitecto ADPA (2026-11-13, medido en main 4123107a)
Especificación `governance/especificaciones/CAPA-04.md` (commit e30eee15).
- Los hallazgos viven en la sala `roadmap`: no hay sala «hallazgos», y el estado es `cerrado`, no «resuelto».
- La acción del plan es la tarea del roadmap; su cierre ya existe (`PATCH /roadmaps/tasks/{task_id}`).
- R5: con `conforme`, el auditor cierra el hallazgo por `app_core/pasillo/roadmap.py` → `cerrar_hallazgo`; con `no_conforme`, el hallazgo sigue `en_tratamiento`. 409 `ACCION_NO_CERRADA` si una tarea no está completada o no tiene evidencia aprobada.
- `cerrar_por_tareas` (RM-23) excluye `origen = 'auditoria'`. Prueba `test_hallazgo_cerrado_solo_con_verificacion`; mutación: quitar la exclusión. Si la exclusión no cabe en una sección porque va dentro de la consulta SQL, CAPA-04 asume el archivo entero.
- Migración sin fecha `capa04_auditoria_grilla.py`. Sin comodines de frontend.
- No se lanza antes de `ORG-22` (rol auditor).


### Corrección de UX/UI tras la especificación nueva (2026-11-13)
Sustituye en la sección anterior lo relativo a «Cerrar auditoría», las actas, los errores de cierre y los criterios 2, 4 y 5. Se mantienen la lista, la nueva auditoría, las columnas de la grilla y la accesibilidad.

**Niveles.** «Nivel verificado del control {código}» con opciones 1 a 5 y los nombres de la escala del diagnóstico (leídos por la compuerta; sin nivel 0); si no hay nombres, «Nivel 1» a «Nivel 5». Riesgo: «Crítico» (≥ 15), «Alto» (≥ 9), «Medio» (el resto); sin «Bajo».

**Acta por área** (no existe «Cerrar auditoría»). h2 «Actas por área», una tarjeta por área con nombre, «{n} de {total} controles verificados» y estado «Sin firmar» o «Firmada». Botón «Firmar acta» solo para el equipo auditor (nombre accesible «Firmar el acta de {área}»); con controles pendientes, `aria-disabled` y «Faltan {n} controles de esta área por verificar.»; firmada, el botón desaparece y aparece «Ver acta». Diálogo «¿Firmar el acta de {área}?»: «El acta recoge los controles que verificaste en esta área y la evidencia revisada. Al firmar queda guardada con tu nombre y la fecha, y las filas del área ya no se pueden cambiar.», botones «Cancelar» (foco inicial) y «Firmar el acta». Tras firmar: `role=status` «Acta de {área} firmada y guardada.» y las filas del área quedan en solo lectura. Bajo el título: «La auditoría se cierra cuando todas las áreas tienen su acta firmada.»; con todas firmadas, etiqueta «Cerrada» y «Todas las áreas tienen su acta firmada.» Implementador y coordinador ven «Ver acta» sin «Firmar acta» y la línea «Solo el equipo auditor firma las actas.» Ver acta (solo lectura): «Acta de auditoría · {área}», el contenido como texto plano, «Huella de integridad: {8 primeros caracteres}» (aria-label «Huella de integridad») y el pie «Esta acta recoge lo verificado por el equipo auditor en la fecha indicada y no sustituye otras verificaciones.» 404 `ACTA_NO_ENCONTRADA`: «No encontramos el acta de esta área.» Sin descarga.

**Cierres por verificar.** Pestaña dentro de «Auditorías» (`tablist` «Auditorías»: «Auditorías» y «Cierres por verificar»), solo para el equipo auditor (ubicación ESTIMADO). Lista: hallazgo (título y control), «{Nombre} · {Rol}» de quien cerró la acción, fecha y estado «Por verificar», «Verificado» o «No verificado»; vacío «No hay cierres pendientes de verificar.» Diálogo «Verificar el cierre»: resumen y evidencia; `radiogroup` «Resultado de la verificación» con «Cierre verificado» (valor `conforme`) y «Cierre no verificado» (valor `no_conforme`); «Motivo» obligatorio, mínimo 10 caracteres, con contador «{n} de 10 caracteres como mínimo»; error «Explica tu resultado con al menos 10 caracteres.»; botones «Cancelar» (foco inicial) y «Guardar verificación». Línea fija: «El hallazgo se marca como cerrado solo si el cierre queda verificado.»; con «Cierre no verificado»: «El hallazgo sigue abierto hasta que se vuelva a cerrar y verificar.» Tras guardar: `role=status` «Verificación guardada.» 403 `AUDITOR_EJECUTOR`: el texto ya definido. En pantalla no aparecen «conforme» ni «no conforme».

**Errores.** 409 `AUDITORIA_INCOMPLETA` al firmar: «Aún hay controles de esta área sin verificar. Complétalos antes de firmar el acta.» 409 `ACTA_YA_FIRMADA`: «El acta de esta área ya está firmada.» y se recarga. Firmar: «No pudimos firmar el acta. Sigue sin firmar.» Verificar: «No pudimos guardar la verificación. Inténtalo de nuevo.»

**Accesibilidad (añadido).** Botones «Firmar el acta de {área}» y «Ver el acta de {área}»; `tab` «Auditorías» / «Cierres por verificar»; `radiogroup` «Resultado de la verificación»; `textbox` «Motivo».

**Criterios de prueba que cambian.** (2) Con filas sin verificar en un área, «Firmar el acta de {área}» en `aria-disabled` con la línea de faltantes; se habilita al verificar la última; no existe «Cerrar auditoría». (4) Firmar el área A la deja «Firmada» y en solo lectura; la auditoría queda «Cerrada» solo con todas firmadas; una segunda firma muestra el texto de `ACTA_YA_FIRMADA`. (5) Implementador y coordinador ven «Ver acta» sin «Firmar acta»; el acta muestra contenido y huella, sin «certificado». (9) Con motivo de 9 caracteres no se guarda; «Cierre verificado» con motivo válido deja el hallazgo «Cerrado»; «Cierre no verificado», «Abierto». (10) Ningún texto con «conforme», «no conforme», «certificado», «hash» ni caracteres de gobernanza.
