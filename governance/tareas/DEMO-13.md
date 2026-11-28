+++
id = "DEMO-13"
titulo = "La demo no arranca si le falta el clon de una sala"
ola = "D"
estado = "pendiente"
tanda = 129
sala = "demo"
depende_de = []
propiedad = ["features/demo/services/entrada_engine.py", "tests/test_demo13_salas_completas.py", "tests/test_demo_ciclo.py"]
crea = ["tests/test_demo13_salas_completas.py"]
arbitro = "pytest tests/test_demo13_salas_completas.py; suite de la demo; mutaciones m1 y m2."
rastros = ["¤demo", "¤arbitro"]
+++

# DEMO-13 · La demo no arranca si le falta el clon de una sala

**Contrato:** `governance/especificaciones/DEMO-13.md` (manda sobre esta ficha).

**Origen.** Análisis de brechas de la tanda 129 (brief del CTO del 2026-11-28): PRD §5.6. Prioridad 2: lo que la demo comercial enseña.

## Entrega
- `copiar_plantilla` falla si una sala de `ORDEN_DE_SALAS` no tiene clon (R1).
- `tests/test_demo13_salas_completas.py`.

## Límites
- En `tests/test_demo_ciclo.py`, solo `test_una_sala_sin_clon_se_omite_y_el_evento_la_nombra` (l. 326) y su mutación (l. 16), que pasan a esperar `DEMO_INCOMPLETA` (R3).
- En `features/demo/services/entrada_engine.py`, solo `copiar_plantilla` y el registro del evento `DEMO_INICIADA`.
- No cambia `ORDEN_DE_SALAS` ni los clonadores de las salas.
