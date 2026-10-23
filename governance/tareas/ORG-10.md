+++
id = "ORG-10"
titulo = "El operador revoca cualquier invitación pendiente desde el listado y ve las caducadas como caducadas"
ola = "D"
estado = "hecha"
sala = "plataforma"
depende_de = ["ORG-09", "FE-10"]
propiedad = ["features/plataforma/domain/models.py", "features/plataforma/services/operador_engine.py", "tests/test_plataforma_operador.py", "frontend/src/app/plataforma/page.tsx", "frontend/src/lib/plataforma/tipos.ts", "frontend/tests/plataforma/**"]
arbitro = "pytest tests/test_plataforma_operador.py contra una rama Neon de revisión + Playwright de frontend/tests/plataforma con la API simulada + tsc --noEmit y next build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-10 · Revocar invitaciones desde el listado del operador

**Objetivo.** Hoy el operador solo puede revocar una invitación en el momento de crear la organización: el listado de ORG-09 no devuelve el identificador de la invitación, así que una invitación emitida días atrás no se puede revocar desde ninguna pantalla. Además, desde que ORG-09 retiró el `UPDATE` a «caducada» (la excepción posterior lo revertía), una invitación vencida sigue apareciendo como «emitida».

## Entrega
- **Listado (`GET /api/v1/plataforma/organizaciones`):** cada organización añade `invitacion_id` (la invitación más reciente, o `null` si no hay) y `invitacion_expira_en`. El estado que se devuelve es el **efectivo**: `caducada` cuando el registro dice `emitida` pero `expira_en` ya pasó. No se escribe nada en la base al listar.
- El resto de campos y la regla de ORG-09 no cambian: solo los metadatos permitidos (nada de lo que trata la organización). La prueba que fija las claves exactas del listado se actualiza con las dos nuevas.
- **Revocar** sigue siendo `POST /invitaciones/{id}/revocar`, solo para invitaciones `emitida` y vigentes; revocar una caducada, aceptada o ya revocada responde 400 con un mensaje que lo explica.
- **Pantalla `/plataforma`:** cada fila con una invitación `emitida` vigente muestra el botón «Revocar», con confirmación; tras revocar, la fila pasa a «Revocada» sin recargar la página. Las caducadas se ven como «Caducada» y sin botón.
- Pruebas con base real (`test_plataforma_operador.py`): el listado devuelve `invitacion_id` y `invitacion_expira_en`; una invitación con `expira_en` pasada aparece `caducada` sin que cambie la fila en la base; revocar desde el id del listado funciona; revocar una caducada da 400.
- Pruebas de Playwright con la API simulada: botón solo en las vigentes, confirmación, fila actualizada tras revocar, error del servidor visible.
- **Prueba de mutación documentada:** devolver el estado almacenado en lugar del efectivo y comprobar que una prueba falla.

## Límites
- No reemite invitaciones (emitir una nueva para una organización existente queda para otra tarea).
- No cambia la aceptación ni las tablas de ORG-09; no hay migración.
- No da al operador acceso a datos de las organizaciones.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks `Arnés Físico Determinista` y `Playwright Frontend` del PR están en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
