+++
id = "DIAG-10"
titulo = "Escala de madurez como fuente única: contrato SMARTCIDI, doctrina alineada y árbitro de consumidores"
ola = "D"
estado = "hecha"
sala = "diagnostico"
depende_de = ["RM-00"]
propiedad = ["governance/contratos/escala_madurez.json", "governance/ESCALA_MADUREZ.md", "scripts/verificar_escala_madurez.py", "tests/test_escala_madurez.py"]
arbitro = "python scripts/verificar_escala_madurez.py + pytest tests/test_escala_madurez.py"
rastros = ["¤diagnostico-scoring"]
+++

# DIAG-10 · Escala de madurez como fuente única

**Origen:** DIAG-08 retiró `score_ponderado` y `nivel_ajustado` mientras `features/roadmap/services/contexto_generacion.py`, de otra sala, los seguía leyendo. La escala estaba repartida entre metodologías, doctrina, fichas y código, y `governance/METODOLOGIAS.md` aún definía la 0 a 3.

## Entrega
- Contrato legible por máquina con la escala, los umbrales y las dimensiones, comprobado contra el archivo de assessment SMARTCIDI.
- `governance/ESCALA_MADUREZ.md`: cálculo, diferencias deliberadas con el archivo y procedimiento para cambiar la escala.
- Árbitro con trinquete: un uso nuevo de vocabulario retirado falla y la lista de consumidores pendientes solo puede encoger.
- Doctrina, invariantes y PRD remiten al contrato.

## Límites
- No cambia el comportamiento del servidor ni de la pantalla: los consumidores pendientes quedan anotados con la tarea que los retira (DIAG-08, DIAG-09, EVI-01).
