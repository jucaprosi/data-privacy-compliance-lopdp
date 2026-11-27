+++
id = "GOB-07"
titulo = "El tema claro es el predeterminado y la referencia de diseño"
ola = "D"
estado = "pendiente"
tanda = 113
sala = "gobernanza"
depende_de = []
propiedad = ["governance/artefactos/PRD.md", "governance/METODOLOGIAS.md"]
crea = []
arbitro = "verificar_especificaciones, generar_indice_tareas --verificar y pytest tests/test_reparto.py tests/test_indice_tareas.py; revisión del CTO de los textos de §1."
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# GOB-07 · El tema claro es el predeterminado y la referencia de diseño

**Contrato:** `governance/especificaciones/GOB-07.md` (manda sobre esta ficha).

**Origen.** El propietario (2026-11-27), por el CTO: «Se debe corregir de fondo, el tema claro es el predeterminado y en base a él se realizan los desarrollos». Brief `ARQUITECTO_UXUI_TEMA_CLARO_PREDETERMINADO.md`.

## Entrega
- PRD §6 y criterio 23 con el claro como predeterminado y referencia.
- `METODOLOGIAS.md` §12 reescrita partiendo del claro.

## Límites
- En `governance/artefactos/PRD.md`, solo el párrafo de §6 sobre los temas y el criterio 23.
- En `governance/METODOLOGIAS.md`, solo §12.
- Sin código.
