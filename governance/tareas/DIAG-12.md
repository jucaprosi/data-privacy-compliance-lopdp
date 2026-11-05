+++
id = "DIAG-12"
titulo = "Estados: el assessment actual, como cortes sellados que parten del diagnóstico real y suman las tareas cerradas con evidencia validada"
ola = "D"
estado = "pendiente"
sala = "diagnostico, frontend"
depende_de = ["DIAG-11", "DIAG-06", "EVI-01", "ADPA-05", "ADPA-06", "ADPA-07"]
propiedad = ["alembic/versions/20261107_diagnostico_estados.py", "features/diagnostico/services/estados_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-12", "api/routers/diagnostico_estados.py", "app_core/pasillo/roadmap.py#DIAG-12", "features/diagnostico/domain/errores.py#DIAG-12", "tests/test_diag12_estados.py", "frontend/src/components/diagnostico/Estados.tsx", "frontend/src/lib/diagnostico/estados.ts", "frontend/src/components/layout/menus/DIAG-12.ts", "frontend/src/components/layout/pantallas/DIAG-12.tsx", "frontend/tests/diagnostico/estados.spec.ts"]
arbitro = "pytest tests/test_diag12_estados.py contra una base de revisión (incluido RLS con lopdp_app) + suite completa + vigilantes + Playwright de frontend/tests/diagnostico/estados.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤diagnostico-comparativo", "¤roadmap"]
+++

# DIAG-12 · Estados: el assessment actual

**Decisión del propietario (2026-11-05).** Después del diagnóstico real (`DIAG-11`) no se repite el diagnóstico: se comparan **estados**, que dan el assessment actual. Contrato: `PRD_EVYDENTIA_REVENTA_NUBE.md`, Módulo 1, e invariante 58 de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`.

**Supuesto del coordinador, por confirmar.**
- Un estado parte de los niveles del diagnóstico real y suma, por control, las tareas del plan de acción cerradas con cuatro ojos y con evidencia validada por el DPO (`INV_LOPDP_FOUR_EYES_CLOSURE`).
- Lo emite el DPO y queda sellado con huella.
- Nunca cambia un diagnóstico sellado.

## Entrega
- **Migración** `20261107_diagnostico_estados`: tabla de estados por organización (fecha de corte, quién lo emitió, niveles por control y por dimensión, huella encadenada). Solo SELECT e INSERT para `lopdp_app`.
- **Motor** `estados_engine.py`:
  - exige el diagnóstico real sellado (409 si no lo está);
  - lee las tareas cerradas y su control de origen por `app_core/pasillo/roadmap.py#DIAG-12`, nunca de las tablas de la hoja de ruta;
  - calcula los indicadores con el mismo motor de `DIAG-08`, sin cifra única.
- **API** `api/routers/diagnostico_estados.py`:
  - el `dpo` emite un estado;
  - consultan el `dpo`, el `coordinador`, el `implementador` y el `admin_organizacion`;
  - compara un estado con el diagnóstico real o con el estado anterior, reutilizando `comparativo_engine.py` de `DIAG-06` dentro de la sala.
- **Pantalla** Diagnóstico › Estado actual (`menus/DIAG-12.ts`, `pantallas/DIAG-12.tsx`, `Estados.tsx`): la lista de estados, el actual y su comparación por dimensión y dominio.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`) y su pasillo; errores de negocio con `ErrorNegocio` y códigos en `features/diagnostico/domain/errores.py#DIAG-12`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar. Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una base de revisión; nunca producción.
- Colores solo con las variables del tema; sin tokens de gobernanza en la interfaz. Llamadas a la API por `fetchAutenticado`.

## Pruebas
- Sin diagnóstico real sellado, 409.
- Un estado suma solo las tareas cerradas con evidencia validada.
- No ve otra organización (RLS).
- `lopdp_app` no puede modificar un estado (42501).
- Emitir un estado no cambia ninguna fila de `diagnostico_resultados`.
- Mutación documentada: contar una tarea sin evidencia validada; la prueba debe fallar.

## Límites
- No reabre las 80 preguntas ni escribe en el diagnóstico.
- No cambia el cierre de tareas de la hoja de ruta.
