+++
id = "TER-02"
titulo = "Cuestionario de garantías del encargado por portal externo, con revisión e informe"
ola = "D"
estado = "pendiente"
sala = "terceros, frontend"
depende_de = ["TER-01", "SEC-12", "FE-23", "ADPA-05", "ADPA-06", "ADPA-08"]
propiedad = ["alembic/versions/20261107_terceros_cuestionario.py", "features/terceros/domain/cuestionario.py", "features/terceros/services/cuestionario_engine.py", "features/terceros/terceros_service.py#TER-02", "features/terceros/domain/errores.py#TER-02", "api/routers/publico_terceros.py", "api/routers/terceros_cuestionario.py", "tests/test_terceros_cuestionario.py", "tests/matriz/TER-02.py", "frontend/src/app/proveedor/[token]/page.tsx", "frontend/src/components/terceros/EnvioCuestionario.tsx", "frontend/src/components/terceros/RevisionCuestionario.tsx", "frontend/src/lib/terceros/cuestionario.ts", "frontend/src/components/modules/TercerosModule.tsx", "frontend/tests/terceros/cuestionario.spec.ts", "app_core/pasillo/terceros.py#TER-02", "app_core/pasillo/evidencias.py#TER-02", "app_core/pasillo/roadmap.py#TER-02", "app_core/pasillo/dpo_cockpit.py#TER-02"]
crea = ["alembic/versions/20261107_terceros_cuestionario.py", "features/terceros/domain/cuestionario.py", "features/terceros/services/cuestionario_engine.py", "api/routers/publico_terceros.py", "api/routers/terceros_cuestionario.py", "tests/test_terceros_cuestionario.py", "tests/matriz/TER-02.py", "frontend/src/app/proveedor/[token]/page.tsx", "frontend/src/components/terceros/EnvioCuestionario.tsx", "frontend/src/components/terceros/RevisionCuestionario.tsx", "frontend/src/lib/terceros/cuestionario.ts", "frontend/tests/terceros/cuestionario.spec.ts"]
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
- Enlace no válido con `CODIGO_ENLACE_NO_VALIDO`; el proveedor solo ve su cuestionario; la revisión «conforme» cierra el hallazgo de garantía (TER-01) si aplica.
- Mutación documentada: permitir ver otro cuestionario con el token y comprobar que la prueba falla.

## Decisiones fijadas en la especificación
- Vigencia del enlace de 1 a 30 días, 7 por defecto.
- El portal lleva `noindex`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store` (SEC-12).
- Todo token no válido responde con `CODIGO_ENLACE_NO_VALIDO`, una sola constante. Vale 404 hasta que el propietario decida entre 404 y 410; la pantalla y las pruebas no dependen del valor.
- `TercerosModule.tsx` pasa entero a esta ficha por cesión de TER-01, que está hecha. El diff se limita a dos bloques `=== TER-02 ===`: la importación y el montaje de `EnvioCuestionario` (especificación §4).

## Límites
- Sin cuenta de proveedor.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#TER-02` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#TER-02` sin modificar `app_core/errors.py`.
