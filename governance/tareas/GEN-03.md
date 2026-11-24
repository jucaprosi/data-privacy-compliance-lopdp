+++
id = "GEN-03"
titulo = "Biblioteca sin marca: la fuente de plantillas catalogo, el código BIB_COPIA_SOLO_CATALOGO y un solo término visible"
ola = "backlog"
estado = "pendiente"
tanda = 100
sala = "biblioteca, frontend"
depende_de = ["GEN-01", "BIB-102", "BIB-103", "BIB-109"]
propiedad = ["features/biblioteca/services/catalogo.py", "features/biblioteca/services/ficha.py", "features/biblioteca/services/mis_plantillas.py", "features/biblioteca/services/plantillas_cuenta_engine.py", "features/biblioteca/domain/errores.py", "frontend/src/lib/biblioteca/catalogo.ts", "frontend/src/lib/biblioteca/fichas.ts", "frontend/src/components/biblioteca/fichas/FichaPlantilla.tsx", "docs/biblioteca-pmv.md", "tests/test_bib_102_catalogo.py", "tests/test_bib_103_ficha.py", "frontend/tests/biblioteca/catalogo.spec.ts", "frontend/tests/biblioteca/ficha.spec.ts", "frontend/tests/biblioteca/formularios.spec.ts"]
crea = []
arbitro = "pytest tests/test_bib_102_catalogo.py tests/test_bib_103_ficha.py contra PostgreSQL; Playwright frontend/tests/biblioteca/catalogo.spec.ts ficha.spec.ts formularios.spec.ts + tsc --noEmit + npm run build; mutaciones m1 y m2."
rastros = ["¤biblioteca", "¤frontend-ide", "¤arbitro"]
+++

# GEN-03 · Biblioteca sin marca: la fuente de plantillas catalogo, el código BIB_COPIA_SOLO_CATALOGO y un solo término visible

**Contrato:** `governance/especificaciones/GEN-03.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- La fuente de plantillas `"catalogo"` y el código `BIB_COPIA_SOLO_CATALOGO`, en backend y frontend en el mismo PR, porque cambian el contrato de la API.
- Un solo término visible para las plantillas de la fuente `"catalogo"`, el que fija UX/UI.

## Límites
- No se lanza sin el término de UX/UI anotado en la especificación §4.
- El contrato OpenAPI lo regenera GEN-05. Sin migración: la fuente no se guarda en la base (especificación §1).
