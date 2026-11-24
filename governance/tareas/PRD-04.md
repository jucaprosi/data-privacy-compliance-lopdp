+++
id = "PRD-04"
titulo = "Las decisiones del 2026-11-24 en el PRD y la §6 de sus especificaciones citando el apartado"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = ["PRD-03", "LEG-08", "BIB-403", "BIB-404", "NORM-04", "NORM-05", "NORM-06"]
propiedad = ["governance/artefactos/PRD.md", "governance/especificaciones/README.md", "governance/especificaciones/BIB-403.md", "governance/especificaciones/LEG-08.md", "governance/especificaciones/BIB-404.md", "governance/especificaciones/NORM-04.md", "governance/especificaciones/NORM-05.md", "governance/especificaciones/NORM-06.md", "governance/especificaciones/PRD-04.md", "governance/artefactos/VPA_MAP.md", "governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md", "governance/operaciones/BRIEF_PROPIETARIO_BUCKET_NORMATIVO.md", "features/inteligencia_normativa/services/almacen_normativo.py", "features/inteligencia_normativa/trabajo_monitoreo.py", "tests/test_norm04_almacen_y_trabajo.py", "governance/tareas/LEG-08.md", "governance/tareas/BIB-403.md", "governance/tareas/BIB-404.md", "governance/tareas/NORM-04.md", "governance/tareas/NORM-05.md", "governance/tareas/NORM-06.md"]
crea = ["governance/especificaciones/PRD-04.md"]
arbitro = "python scripts/verificar_especificaciones.py; python scripts/generar_indice_tareas.py --verificar; python scripts/verificar_reparto.py; pytest tests/test_vpa_map.py tests/test_ci29_sin_generados_compartidos.py tests/test_adpa_bulkhead.py tests/test_verificar_especificaciones.py tests/test_indice_tareas.py tests/test_reparto.py tests/test_inv_citados_existen.py"
rastros = ["¤sdd", "¤triaje", "¤vpa", "¤cita-verificada", "¤plantillas-demo", "¤monitoreo-job", "¤transcripcion-normativa"]
+++

# PRD-04 · Las decisiones del 2026-11-24 en el PRD

**Contrato:** `governance/especificaciones/PRD-04.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_PRD_DECISIONES_2026-11-24.v2.md` (base 07bd95b5), que sustituye al primero: las seis especificaciones del día citaban el brief, no el PRD, y sus rastros eran genéricos.

## Entrega (en este mismo PR de gobernanza)
- Cinco decisiones en el PRD, en positivo: leyes 6, 7 y 13; Módulos 6.1, 6.3 y 7.
- La §6 de LEG-08, BIB-403, BIB-404, NORM-04, NORM-05 y NORM-06 abre con `- **PRD:**` y el apartado.
- Cuatro rastros nuevos en VPA_MAP: `¤cita-verificada`, `¤plantillas-demo`, `¤monitoreo-job` y `¤transcripcion-normativa`, difundidos en las seis fichas, sus especificaciones, `CITAS_PLANTILLAS_VERIFICADAS.md`, el brief del bucket y la cabecera del código y la prueba de NORM-04.
- El README de especificaciones fija la línea PRD y el rastro para las especificaciones nuevas.

## Límites
- Sin código de negocio: en los `.py` de NORM-04 solo cambia la línea de rastros de la cabecera. No cambia ninguna regla de las seis especificaciones.
- `DEMO_COMERCIAL.md` es de DEMO-10 (pendiente): el rastro `¤plantillas-demo` lo pone esa ficha o BIB-404.
- GEN-01 (pendiente) también es dueña de `PRD.md`: parte de este texto al empezar.
