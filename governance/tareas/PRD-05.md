+++
id = "PRD-05"
titulo = "Los documentos rectores con un solo modelo de generación, remitiendo a modelos_permitidos.py"
ola = "backlog"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["IA-13", "IA-14", "PRD-04"]
propiedad = ["governance/artefactos/PRD.md", "governance/artefactos/INVARIANTS.md", "governance/artefactos/VPA_MAP.md", "governance/artefactos/TASKS.md", "governance/especificaciones/IA-06.md", "governance/especificaciones/VTX-01.md", "governance/especificaciones/NORM-03.md", "governance/apoyo/LANZAMIENTO_TANDA_ORTOGONAL.md", "governance/operaciones/BRIEF_PROPIETARIO_IA-11.md", "governance/especificaciones/PRD-05.md"]
crea = ["governance/especificaciones/PRD-05.md"]
arbitro = "python scripts/verificar_especificaciones.py; python scripts/generar_indice_tareas.py --verificar; python scripts/verificar_reparto.py; pytest tests/test_vpa_map.py tests/test_inv_citados_existen.py tests/test_reparto.py tests/test_indice_tareas.py tests/test_verificar_especificaciones.py tests/test_ci29_sin_generados_compartidos.py"
rastros = ["¤sdd", "¤gemini-vertex"]
+++

# PRD-05 · Los documentos rectores con un solo modelo de generación

**Contrato:** `governance/especificaciones/PRD-05.md` (manda sobre esta ficha).

**Origen.** Brief del CTO `ARQUITECTO_MODELOS_GEMINI_DOCUMENTOS.md` (2026-11-24, base c5f8c69a). El código ya está en el estado de IA-13: un solo modelo de generación, `gemini-3.8-flash`, en `features/inferencia/domain/modelos_permitidos.py`. El PRD, la invariante 20, VPA_MAP, TASKS y cuatro documentos de apoyo seguían nombrando los modelos retirados.

## Entrega (en este mismo PR de gobernanza)
- PRD: ley 7, Módulos 3, 5, 6 y 6.5, NIIF 18, tabla de salas, diagrama de la Capa 4, resumen de módulos, árbitro 14 y glosario.
- Invariante 20 y las filas `¤roadmap` y `¤gemini-vertex` de VPA_MAP.
- TASKS: el resumen y las filas de VTX-01 y NORM-03.
- Especificaciones IA-06, VTX-01 y NORM-03; `LANZAMIENTO_TANDA_ORTOGONAL.md` y `BRIEF_PROPIETARIO_IA-11.md`.

## Límites
- Sin código. IA-13, IA-14, `APORTES_INEDITOS.md` y `alembic/` no cambian.
- Las fichas de tareas hechas, `EVIDENCIA_HUMO_VERTEX.md` y `BRIEF_PROPIETARIO_VERTEX.md` son historia o medición fechada: no cambian.
