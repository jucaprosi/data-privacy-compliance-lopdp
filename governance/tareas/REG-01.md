+++
id = "REG-01"
titulo = "Paquete normativo como dato, editable solo por el operador de la plataforma, con plazos como parámetros"
ola = "backlog"
estado = "pendiente"
sala = "regulacion_rag, plataforma, frontend"
depende_de = ["LEG-03", "ORG-09", "ORG-10", "ORG-11", "FE-10", "ADPA-05", "ADPA-06"]
propiedad = ["alembic/versions/reg01_paquetes_normativos.py", "features/regulacion_rag/domain/paquete.py", "features/regulacion_rag/services/paquetes_engine.py", "features/regulacion_rag/services/paquetes_diff_engine.py", "features/regulacion_rag/regulacion_rag_service.py#REG-01", "features/regulacion_rag/domain/errores.py#REG-01", "app_core/pasillo/regulacion_rag.py#REG-01", "app_core/pasillo/diagnostico.py#REG-01", "app_core/pasillo/organizacion.py#REG-01", "api/routers/paquetes_normativos.py", "tests/test_paquetes_normativos.py", "tests/matriz/REG-01.py", "frontend/src/app/plataforma/paquetes/page.tsx", "frontend/src/app/plataforma/paquetes/[id]/page.tsx", "frontend/src/lib/plataforma/paquetes.ts", "frontend/tests/plataforma/paquetes.spec.ts"]
crea = ["alembic/versions/reg01_paquetes_normativos.py", "features/regulacion_rag/domain/paquete.py", "features/regulacion_rag/services/paquetes_engine.py", "features/regulacion_rag/services/paquetes_diff_engine.py", "api/routers/paquetes_normativos.py", "tests/test_paquetes_normativos.py", "tests/matriz/REG-01.py", "frontend/src/app/plataforma/paquetes/page.tsx", "frontend/src/app/plataforma/paquetes/[id]/page.tsx", "frontend/src/lib/plataforma/paquetes.ts", "frontend/tests/plataforma/paquetes.spec.ts"]
arbitro = "pytest tests/test_paquetes_normativos.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/plataforma/paquetes.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_REGULATION_AS_CODE_DIFF)"
rastros = ["¤regulation-code", "¤paquete-normativo"]
+++

# REG-01 · Paquete normativo como dato, editable solo por el operador de la plataforma, con plazos como parámetros

**Origen.** Optimizaciones O-5 y O-9 y conflicto D-9 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`. En backlog: los plazos están aplazados por decisión del propietario y la verificación legal es LEG-03.

## Entrega
- Requisitos, controles comunes, preguntas, plazos (con unidad: hábiles o calendario), plantillas y catálogos versionados como dato; solo el operador de la plataforma los edita; el motor de diff avisa qué plantillas y organizaciones afecta un cambio. NIIF 18 es otro paquete.
- Cada valor sin verificación lleva (*) y no se activa (LEG-03).

## Propiedad concreta (Arquitecto ADPA, 2026-11-13, medida contra main 3bb40557)
- Migración `reg01_paquetes_normativos.py` sin fecha; `down_revision` = la cabeza al implementar (FUSION_ALEMBIC).
- `domain/paquete.py`: requisito, control común, pregunta, plazo con unidad (hábiles o calendario), plantilla, catálogo y versión. `paquetes_engine.py`: versionado y activación; un valor con (*) no se activa. `paquetes_diff_engine.py`: qué plantillas y organizaciones afecta un cambio; no se edita `diff_engine.py`.
- Datos globales del operador, sin `tenant_id`: `lopdp_app` solo con `SELECT`; la escritura, por el rol del operador (ORG-09 a ORG-11). Prueba de que `lopdp_app` no puede hacer `INSERT`.
- Las secciones `REG-01` de `regulacion_rag_service.py`, `pasillo/diagnostico.py` y `pasillo/organizacion.py` las siembra el PR de gobernanza (solo comentarios).
- Sin menú: la entrada al panel de plataforma es de FE-10; un enlace desde `plataforma/page.tsx` es de MARCA-04 y va con `depende_de`.
- Mutación nueva: activar un valor con (*) → la prueba falla.
- Pasa por UX/UI antes de lanzarse (pantallas del operador).

## Límites
- No retira todavía los textos fijos de plazos de `derechos_arco`; eso lo hace la tarea que los conecte al paquete.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#REG-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#REG-01` sin modificar `app_core/errors.py`.
