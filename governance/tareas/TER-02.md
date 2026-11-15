+++
id = "TER-02"
titulo = "Cuestionario de garantías del encargado por portal externo, con revisión e informe"
ola = "D"
estado = "pendiente"
sala = "terceros, frontend"
depende_de = ["TER-01", "SEC-12", "FE-23", "ADPA-05", "ADPA-06", "ADPA-08"]
propiedad = ["alembic/versions/20261107_terceros_cuestionario.py", "features/terceros/services/cuestionario_engine.py", "features/terceros/terceros_service.py#TER-02", "api/routers/publico_terceros.py", "api/routers/terceros_cuestionario.py", "tests/test_terceros_cuestionario.py", "tests/matriz/TER-02.py", "frontend/src/app/proveedor/**", "frontend/src/components/terceros/**", "frontend/tests/terceros/cuestionario.spec.ts", "features/transferencias/domain/errores.py#TER-02", "app_core/pasillo/transferencias.py#TER-02", "app_core/pasillo/terceros.py#TER-02", "app_core/pasillo/rat.py#TER-02", "app_core/pasillo/dpo_cockpit.py#TER-02"]
arbitro = "pytest tests/test_terceros_cuestionario.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/terceros/cuestionario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12"
rastros = ["¤seguridad", "¤evidencias"]
+++

# TER-02 · Cuestionario de garantías del encargado por portal externo, con revisión e informe

**Origen.** Menú 6 «Garantías de encargados» y asistente «Garantías del encargado» de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

**Contrato:** `governance/especificaciones/TER-02.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Envío del cuestionario desde la ficha del tercero por enlace con caducidad; el proveedor responde por portal externo con evidencias; revisión por el responsable (conforme, pedir corrección, rechazar); informe y próxima fecha de revisión.
- Límites de abuso de SEC-12; el portal no muestra datos de la organización más allá del nombre.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor validado con `exigir_base_de_pruebas()`.
- Colores solo con las variables del tema (`--ui-*`, `badge-render-*`); sin tokens de gobernanza en la interfaz.
- Llamadas a la API por `fetchAutenticado`; los roles se resuelven con `/organizacion/me/roles`.

## Pruebas
- Enlace caducado 410; el proveedor solo ve su cuestionario; la revisión «conforme» cierra el hallazgo de garantía (TER-01) si aplica.
- Mutación documentada: permitir ver otro cuestionario con el token y comprobar que la prueba falla.

## Inconsistencia por resolver antes de implementar (detectada por SEC-12)
- La ficha (Pruebas: «Enlace caducado 410») y el contrato `governance/especificaciones/TER-02.md` (tabla de errores y el escenario del token usado) devuelven **410** para un token caducado o ya respondido y **404** para uno desconocido.
- El diseño propuesto en `governance/apoyo/DISENO_PORTALES_EXTERNOS.md` (§4, PR de SEC-12, aún en borrador) dice que un 410 distinto del 404 revela qué tokens existieron, y propone **una única respuesta 404** para desconocido, caducado, usado y revocado.
- Decisión pendiente de la propietaria: no se ha cambiado el contrato ni esta ficha. Quien implemente TER-02 **se detiene y consulta** antes de escribir el manejo de esos códigos; no elige por su cuenta.

## Límites
- Sin cuenta de proveedor.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#TER-02` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#TER-02` sin modificar `app_core/errors.py`.

## Huecos abiertos (UX/UI, 2026-11-15): no se lanza hasta resolverlos
1. **Las preguntas del cuestionario** no están en la especificación ni en la ficha (qué se pregunta y con qué tipos de campo). Sin la lista no se cierran los textos de cada paso. Decide el CTO o el Arquitecto.
2. **Dónde vive el botón «Enviar cuestionario»:** la ficha del tercero está en `frontend/src/components/modules/TercerosModule.tsx`, que es de TER-01; la propiedad de TER-02 solo tiene `components/terceros/**` y `app/proveedor/**`. Hace falta una sección `TercerosModule.tsx#TER-02` o un punto de montaje.
3. **Vigencia del enlace:** `dias_vigencia` no tiene rango; propuesta de UX/UI: de 1 a 30 días, 7 por defecto (estimado).
4. **410 frente a 404:** decisión pendiente de la propietaria; la pantalla no depende de ella (mismo texto para ambos).
Seguridad del portal (para SEC-12): `/proveedor/<token>` lleva `<meta name="robots" content="noindex">` y `Referrer-Policy: no-referrer`.

## Textos cerrados por UX/UI (2026-11-15)
Diseñados contra la ficha y la especificación; UX/UI no corrió pantalla.

**A. Ficha del tercero (implementador y coordinador).** Estado siempre con texto e icono: «Enviado» · «Respondido, por revisar» · «Aceptado» · «Corrección pedida» · «Rechazado» · «Sin cuestionario». Nunca «conforme» ni «garantías adecuadas». Botón «Enviar cuestionario» (nombre accesible «Enviar el cuestionario a {tercero}»), solo si no hay uno enviado y vigente; con uno enviado: «Enviado el {fecha} · el enlace vence el {fecha}». Diálogo «Enviar cuestionario a {tercero}»: ayuda «Creamos un enlace para que el proveedor responda sin crear una cuenta. El enlace funciona una sola vez y vence en los días que elijas.»; campo «Vigencia del enlace (días)» (1 a 30, 7 por defecto; error «Elige entre 1 y 30 días.»); botones «Cancelar» (foco inicial) y «Crear enlace». Paso «Copia el enlace ahora» (se muestra una sola vez): «Este enlace solo se muestra ahora. Envíalo al proveedor por el canal que usas habitualmente; la plataforma no lo envía.»; campo de solo lectura «Enlace del cuestionario»; «Copiar el enlace» (status «Enlace copiado.»); «Ya lo copié». Al cerrar, el enlace no queda en pantalla, URL ni almacenamiento local.

**B. Portal `/proveedor/<token>` (público, sin el armazón del tablero).** h1 «Cuestionario de garantías para {organización}»; solo el nombre de la organización y las preguntas. Introducción: «{organización} te pide responder este cuestionario sobre cómo tratas los datos personales que te confía. Puedes adjuntar documentos de respaldo.» Aviso (role=note): «Tus respuestas no se guardan hasta que las envíes. Solo puedes enviarlas una vez.» Asistente de FE-23: «Paso {n} de {total}», «Anterior», «Siguiente»; si falta un campo: «Completa este paso antes de continuar: {lo que falta}.» Adjuntos: «Adjuntar documento», «Hasta 10 MB por archivo.», error «El archivo {nombre} supera los 10 MB.», «Quitar {nombre}». Último paso «Revisar y enviar» con «Enviar respuestas»; confirmación «¿Enviar tus respuestas? Después no podrás cambiarlas.» («Cancelar» con foco inicial). Enviando: aria-busy y «Enviando tus respuestas…». Éxito (role=status): «Respuestas enviadas» / «Recibimos tus respuestas. {organización} las revisará. Ya puedes cerrar esta página.» Enlace no válido, igual para 404 y 410: «Este enlace ya no está disponible» / «Puede que haya vencido o que ya se hayan enviado las respuestas. Si necesitas responder, pide un enlace nuevo a la organización que te lo envió.» (sin ningún otro dato). 429: «Hubo demasiados intentos. Espera unos minutos e inténtalo de nuevo.» Errores: «No pudimos cargar el cuestionario. Vuelve a intentarlo en unos minutos.» (con «Volver a cargar») y «No pudimos enviar tus respuestas. Tus datos siguen en esta página; inténtalo de nuevo.» Cargando: «Cargando el cuestionario…».

**C. Revisión (implementador y coordinador).** Con «Respondido, por revisar»: botón «Revisar respuestas» (nombre «Revisar las respuestas de {tercero}»). Vista «Respuestas de {tercero}»: cada pregunta con su respuesta en texto plano y «Documentos adjuntos» con «Abrir {nombre}»; sin documentos: «El proveedor no adjuntó documentos.» Grupo «Decisión» (radiogroup): «Aceptar las respuestas» («Se genera el informe y se cierra el hallazgo de garantía, si lo hay.»), «Pedir corrección» («Se crea un enlace nuevo para que el proveedor corrija sus respuestas.») y «Rechazar» («Se registra un hallazgo de prioridad alta en el plan de acción.»). «Comentario»: obligatorio en corrección y rechazo (estimado; error «Explica tu decisión.»), opcional al aceptar. «Próxima revisión»: obligatoria solo al aceptar (R2; error «Elige la fecha de la próxima revisión.»). Botones «Cancelar» y «Guardar la revisión». Tras guardar: aceptar → «Revisión guardada. El informe quedó guardado como evidencia.» con «Huella de integridad: {8 primeros caracteres}»; corrección → paso «Copia el enlace ahora»; rechazo → «Revisión guardada. Se registró un hallazgo en el plan de acción.» 409 CUESTIONARIO_NO_RESPONDIDO: «El proveedor aún no respondió. Podrás revisarlo cuando envíe sus respuestas.»

**D. Errores internos (fijos por código; nunca el texto del servidor).** «No pudimos crear el enlace. Inténtalo de nuevo.» · «No pudimos guardar la revisión. Inténtalo de nuevo.» · «No pudimos cargar el cuestionario de {tercero}. Inténtalo de nuevo.» (con «Volver a cargar») · 403 «No tienes permiso para esta acción.» · 401 manejo global. Otros roles ven el estado, no los botones.

**E. Accesibilidad para Playwright.** Botón enviar (button, «Enviar el cuestionario a {tercero}») · diálogo («Enviar cuestionario a {tercero}» / «Copia el enlace ahora») · vigencia (spinbutton) · enlace (textbox de solo lectura, «Enlace del cuestionario») · «Copiar el enlace» · portal (main, «Cuestionario de garantías para {organización}») · pasos (list, «Pasos del cuestionario») · «Adjuntar documento» · «Enviar respuestas» · «Revisar las respuestas de {tercero}» · «Decisión» (radiogroup) · «Guardar la revisión». Foco atrapado en los diálogos; Escape cierra (salvo en el paso del enlace, que exige «Ya lo copié»); el foco vuelve al botón de origen; contraste 4.5:1; tokens del tema; sin ¤ ni ¦; sin desbordar a 375 px.

**F. Criterios de prueba añadidos.** (1) En el portal, un token simulado con 404 y otro con 410 muestran exactamente el mismo título y el mismo texto, y no muestran el nombre de la organización ni ningún otro dato de ella; el nombre solo aparece con un token válido. (2) Con token válido solo aparecen el nombre de la organización y las preguntas. (3) Enviar deja el estado interno en «Respondido, por revisar». (4) Un archivo de más de 10 MB muestra el error y no se adjunta. (5) «Aceptar las respuestas» sin fecha no se guarda; con fecha aparece la huella. (6) Tras «Ya lo copié» ningún nodo del DOM ni `localStorage` contiene el enlace. (7) Ningún texto visible contiene «conforme», «garantías adecuadas», «hash», ids, ¤ ni ¦.
