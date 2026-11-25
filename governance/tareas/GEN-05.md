+++
id = "GEN-05"
titulo = "Contrato OpenAPI regenerado tras la escala y la Biblioteca sin marca"
ola = "backlog"
estado = "en_curso"
tanda = 101
sala = "plataforma"
depende_de = ["GEN-02", "GEN-03", "MARCA-01"]
propiedad = ["governance/contratos/hoja_de_ruta.openapi.json"]
crea = []
arbitro = "python scripts/exportar_contrato_hoja_ruta.py; pytest tests/test_contrato_hoja_ruta.py; mutación m1."
rastros = ["¤adpa", "¤arbitro"]
+++

# GEN-05 · Contrato OpenAPI regenerado tras la escala y la Biblioteca sin marca

**Contrato:** `governance/especificaciones/GEN-05.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- `hoja_de_ruta.openapi.json` regenerado con `scripts/exportar_contrato_hoja_ruta.py` desde la API de main, después de fusionar GEN-02 y GEN-03.

## Límites
- No se edita a mano. Solo ese archivo.
