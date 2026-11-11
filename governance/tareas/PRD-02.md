+++
id = "PRD-02"
titulo = "Los invariantes citados existen en el archivo de EVYDENTIA; escala de madurez y mapa de rastros sobre sus archivos"
ola = "backlog"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["DIAG-10", "GOB-01"]
propiedad = ["governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md", "scripts/verificar_escala_madurez.py", "tests/test_vpa_map.py", "governance/artefactos/VPA_MAP_EVYDENTIA_REVENTA_NUBE.md", "tests/test_inv_citados_existen.py"]
crea = ["tests/test_inv_citados_existen.py"]
arbitro = "pytest tests/test_inv_citados_existen.py tests/test_vpa_map.py tests/test_escala_madurez.py: todo INV_ citado fuera de los cuatro archivos inhabilitados y de APORTES existe en INVARIANTS_EVYDENTIA_REVENTA_NUBE.md; mutación documentada: borrar uno de los INV heredados del archivo hace fallar la prueba; otra con la escala 0 a 3 en el archivo nuevo"
rastros = ["¤triaje"]
+++

# PRD-02 · Los invariantes citados existen en el archivo de EVYDENTIA; escala de madurez y mapa de rastros sobre sus archivos

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Orden
PRD-00 (el CTO, en su PR: apartado `### 7.1 Catálogo de salas` en `PRD_EVYDENTIA_REVENTA_NUBE.md` y decisión sobre los 25 INV heredados) se fusiona antes. PRD-01 y PRD-02 pueden ir en paralelo; PRD-03, al final. **Bloqueante:** `PRD_EVYDENTIA_REVENTA_NUBE.md` no tiene el apartado 7.1 que lee `salas_del_prd`; devuelve 0 salas frente a 35 y cambiar solo la ruta rompería todas las fichas.

## Entrega
- Los INV del archivo viejo que siguen vivos se **trasladan con el mismo ID** a un apartado «Heredados del PMV» de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, **tras la decisión del CTO** sobre cuáles siguen rigiendo (no se renombran los ID en el código). Los 7 sin uso no se trasladan (`DEMO_NUNCA_PRODUCCION`, `ESCALA_MADUREZ_UNICA`, `EVIDENCE_DOMAIN_PURGE`, `LAST_ADMIN_PROTECTED`, `PRUNING_TREE_ANTECEDENCE`, `UI_ACHROMATIC_INVERTED_HIERARCHY`, `UI_ANTIGRAVITY_CURSOR`). Entre los vivos, `MULTIDIMENSIONAL_METRICS` (21 archivos) y `PMV_DECLARED_EVIDENCE` (6; choca con la evidencia real en GCS de EVYDENTIA). Los que el CTO derogue: sus referencias en código pasan a comentario de historia o se quitan en la ficha de la sala dueña.
- `scripts/verificar_escala_madurez.py`: la lista `DOCTRINA` cambia `INVARIANTS.md` por `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`; el inhabilitado deja de revisarse.
- `tests/test_vpa_map.py`: `MAPA` pasa a `VPA_MAP_EVYDENTIA_REVENTA_NUBE.md`; antes, dar de alta en ese mapa los rastros que faltan (`¤aportes`, `¤arquitectura`, `¤auditoria`, `¤doctrinas`, `¤dpo`, `¤fuentes`, `¤metodologias`, `¤regulacion`, `¤riesgos`, `¤triaje`) o medir cuáles siguen usándose y dar de alta solo esos.
- El docstring de `tests/test_diag13_evidencia_declarada.py` (cita `INV_LOPDP_PMV_DECLARED_EVIDENCE`) lo cambia su dueña (NEON-02 o la ficha de DIAG-07b), no esta ficha.
