+++
id = "REG-01"
titulo = "Paquete normativo como dato, editable solo por el operador de la plataforma, con plazos como parámetros"
ola = "backlog"
estado = "pendiente"
sala = "regulacion_rag, plataforma, frontend"
depende_de = ["LEG-03", "ORG-09", "ORG-10", "ORG-11", "FE-10", "ADPA-05", "ADPA-06"]
propiedad = ["alembic/versions/*_paquetes_normativos.py", "features/regulacion_rag/paquetes/**", "api/routers/paquetes_normativos.py", "tests/test_paquetes_normativos.py", "frontend/src/app/plataforma/paquetes/**", "frontend/tests/plataforma/paquetes.spec.ts", "features/regulacion_rag/domain/errores.py#REG-01", "app_core/pasillo/regulacion_rag.py#REG-01", "app_core/pasillo/diagnostico.py#REG-01", "app_core/pasillo/organizacion.py#REG-01"]
arbitro = "pytest tests/test_paquetes_normativos.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/plataforma/paquetes.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada (INV_LOPDP_REGULATION_AS_CODE_DIFF)"
rastros = ["¤regulation-code", "¤paquete-normativo"]
+++

# REG-01 · Paquete normativo como dato, editable solo por el operador de la plataforma, con plazos como parámetros

**Origen.** Optimizaciones O-5 y O-9 y conflicto D-9 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`. En backlog: los plazos están aplazados por decisión del propietario y la verificación legal es LEG-03.

## Entrega
- Requisitos, controles comunes, preguntas, plazos (con unidad: hábiles o calendario), plantillas y catálogos versionados como dato; solo el operador de la plataforma los edita; el motor de diff avisa qué plantillas y organizaciones afecta un cambio. NIIF 18 es otro paquete.
- Cada valor sin verificación lleva (*) y no se activa (LEG-03).

## Límites
- No retira todavía los textos fijos de plazos de `derechos_arco`; eso lo hace la tarea que los conecte al paquete.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#REG-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#REG-01` sin modificar `app_core/errors.py`.
