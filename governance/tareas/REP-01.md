+++
id = "REP-01"
titulo = "Árbitro de copias en BRIEFS_POR_BLOQUE.md: Hecho si, Depende de, Objetivo y Sala(s) iguales a los de sus fichas"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = []
propiedad = ["scripts/verificar_reparto.py", "tests/test_reparto_copias.py"]
crea = ["tests/test_reparto_copias.py"]
arbitro = "pytest tests/test_reparto_copias.py tests/test_reparto.py; mutaciones 1 a 5 documentadas"
rastros = ["¤arbitro"]
+++

# REP-01 · Árbitro de copias en BRIEFS_POR_BLOQUE.md: Hecho si, Depende de, Objetivo y Sala(s) iguales a los de sus fichas

Diseño del Arquitecto ADPA (2026-11-09), pedido por el propietario y el CTO. Medido sobre `origin/main` fca16d4f: de 62 bloques, 27 líneas «Hecho si» difieren del `arbitro` de su ficha (26 solo por la redacción de un proveedor retirado, 1 de contenido), seis bloques omiten una dependencia pendiente y uno cita una que su ficha no tiene. Cada bloque copia a mano lo que dice su ficha y ningún árbitro lo compara.

## Entrega
Reglas nuevas en `revisar()` de `scripts/verificar_reparto.py` (que `tests/test_reparto.py` ya ejecuta en el CI, sin tocar workflows):
- **R6, «Hecho si»:** cada task del «Objetivo» tiene una línea «- `ID`: texto» igual a su `arbitro` (normalizando espacios; usa el campo `arbitro` que `cargar_tareas` ya devuelve). Falla si falta, sobra o difiere.
- **R7, «Depende de»:** toda dependencia de las tasks del bloque que no está hecha y no está en el mismo bloque aparece citada con su ID. Citar de más no falla (aviso).
- **R8, «Objetivo» y «Sala(s)»:** el título de cada task es igual a su `titulo` y las salas del bloque son la unión de las `sala` de sus tasks.
- **`--regenerar`:** reescribe en el sitio las líneas «Hecho si» desde el `arbitro`. Lo ejecuta la coordinadora; esta ficha no es dueña del documento. «Depende de» es prosa con anotaciones: solo se comprueba, no se regenera.

## Orden
No entra sola: `tests/test_reparto.py` falla si la regla nueva se fusiona con el documento viejo. Regenerar y fusionar van en el **mismo PR** de la coordinadora: aplica `--regenerar`, añade a mano los seis ids pendientes y corrige la dependencia de BL-236, y publica todo junto. Va antes que NEON-04, que también lista el documento.

## Propiedad
`scripts/verificar_reparto.py` y, en `crea`, `tests/test_reparto_copias.py`. No toca `tests/test_reparto.py`. Sin migración ni frontend.

## Árbitro, cada uno con su mutación (sobre copias temporales del documento)
1. Cambiar el `arbitro` de una ficha sin regenerar el bloque falla R6.
2. Reintroducir a mano un proveedor retirado en un «Hecho si» falla R6.
3. Quitar una dependencia pendiente del «Depende de» falla R7.
4. Cambiar el título de una task en la ficha falla R8.
5. `--regenerar` sobre un bloque viejo lo deja igual al `arbitro` y R6 pasa; regenerar dos veces no cambia nada.
