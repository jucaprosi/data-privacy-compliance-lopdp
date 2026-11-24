+++
id = "PRD-04"
titulo = "Las decisiones del 2026-11-24 en el PRD y la §6 de sus especificaciones citando el apartado"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = ["PRD-03", "LEG-08", "BIB-403", "BIB-404", "NORM-04", "NORM-05", "NORM-06"]
propiedad = ["governance/artefactos/PRD.md", "governance/especificaciones/README.md", "governance/especificaciones/BIB-403.md", "governance/especificaciones/LEG-08.md", "governance/especificaciones/BIB-404.md", "governance/especificaciones/NORM-04.md", "governance/especificaciones/NORM-05.md", "governance/especificaciones/NORM-06.md", "governance/especificaciones/PRD-04.md"]
crea = ["governance/especificaciones/PRD-04.md"]
arbitro = "python scripts/verificar_especificaciones.py; python scripts/generar_indice_tareas.py --verificar; python scripts/verificar_reparto.py; pytest tests/test_verificar_especificaciones.py tests/test_indice_tareas.py tests/test_reparto.py tests/test_inv_citados_existen.py"
rastros = ["¤sdd", "¤triaje"]
+++

# PRD-04 · Las decisiones del 2026-11-24 en el PRD

**Contrato:** `governance/especificaciones/PRD-04.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_PRD_DECISIONES_2026-11-24.md` (base 07bd95b5): las seis especificaciones del día citaban el brief, no el PRD.

## Entrega (en este mismo PR de gobernanza)
- Cinco decisiones en el PRD, en positivo: leyes 6, 7 y 13; Módulos 6.1, 6.3 y 7.
- La §6 de LEG-08, BIB-403, BIB-404, NORM-04, NORM-05 y NORM-06 abre con `- **PRD:**` y el apartado.
- El README de especificaciones fija esa primera línea para las especificaciones nuevas.

## Límites
- Sin código. No cambia ninguna regla de las seis especificaciones.
- GEN-01 (pendiente) también es dueña de `PRD.md`: parte de este texto al empezar.
