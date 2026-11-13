+++
id = "CAPA-04"
titulo = "Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa, frontend"
depende_de = ["CAPA-02", "RM-21", "EVI-02", "DIAG-03", "ADPA-05", "ADPA-06", "ADPA-07"]
propiedad = ["alembic/versions/20261106_auditoria_grilla.py", "features/auditoria_capa/domain/auditoria.py", "features/auditoria_capa/services/grilla_engine.py", "features/auditoria_capa/auditoria_capa_service.py#CAPA-04", "api/routers/auditoria_grilla.py", "tests/test_auditoria_grilla.py", "tests/matriz/CAPA-04.py", "frontend/src/components/auditoria/**", "frontend/src/lib/auditoria/**", "frontend/tests/auditoria/**", "frontend/src/components/layout/menus/CAPA-04.ts", "frontend/src/components/layout/pantallas/CAPA-04.tsx", "features/auditoria_capa/domain/errores.py#CAPA-04", "app_core/pasillo/auditoria_capa.py#CAPA-04", "frontend/src/components/layout/menus/index.ts#CAPA-04", "frontend/src/components/layout/pantallas/index.tsx#CAPA-04"]
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
