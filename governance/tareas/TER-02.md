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
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).
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
