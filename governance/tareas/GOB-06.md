+++
id = "GOB-06"
titulo = "Briefs y partes de relevo fuera del repositorio"
ola = "backlog"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["ADPA-10", "BIB-105", "CI-19", "CI-22", "CI-23", "CI-25", "CI-26", "CI-29", "CI-31", "CI-33", "CI-34", "CI-35", "GOB-02", "GOB-03", "GOB-05", "LEG-06", "MARCA-06", "OPS-05", "PRD-01", "QA-11", "REP-01", "RET-09", "SEC-02", "SEC-12"]
propiedad = ["scripts/verificar_reparto.py", "scripts/verificar_alcance_pr.py", "scripts/generar_indice_tareas.py", "tests/test_reparto.py", "tests/test_ci29_sin_generados_compartidos.py", "tests/test_verificar_alcance_pr.py", "tests/test_indice_tareas.py", "scripts/verificar_briefs_locales.py", "tests/test_verificar_briefs_locales.py", "governance/apoyo/BRIEFS_POR_BLOQUE.md", "governance/apoyo/BRIEFS_TAREAS_LIBRES.md", "governance/apoyo/briefs/FE-29.md", "governance/apoyo/briefs/IA-13.md", "governance/apoyo/briefs/IA-14.md", "governance/apoyo/briefs/IA-15.md", "governance/apoyo/briefs/IA-16.md", "scripts/migrar_reparto_ci31.py", "tests/test_ci31_reparto_por_ficha.py", "tests/test_reparto_copias.py", "governance/tareas/FE-29.md", "governance/tareas/IA-13.md", "governance/tareas/IA-14.md", "governance/tareas/IA-15.md", "governance/tareas/IA-16.md", "governance/tareas/LEG-07.md", "governance/METODOLOGIAS.md", "governance/Metodología de trabajo en equipo.md", "governance/apoyo/DISENO_PORTALES_EXTERNOS.md", "governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md", "governance/apoyo/LANZAMIENTO_TANDA_ORTOGONAL.md", "governance/apoyo/LANZAMIENTO_TANDA_SECUENCIAL.md"]
crea = ["scripts/verificar_briefs_locales.py", "tests/test_verificar_briefs_locales.py"]
arbitro = "pytest tests/test_reparto.py tests/test_verificar_briefs_locales.py tests/test_ci29_sin_generados_compartidos.py tests/test_verificar_alcance_pr.py tests/test_indice_tareas.py; verificar_reparto, índice, especificaciones y verificar_alcance_pr con código 0; git grep de «apoyo/briefs|BRIEFS_TAREAS_LIBRES|BRIEFS_POR_BLOQUE|agente =» vacío fuera de fichas hechas, especificaciones hechas, partes y aportes; verificar_briefs_locales en la carpeta real da OK para las tandas 93 a 96; mutaciones m1 a m5."
rastros = ["¤arbitro"]
agente = "ninguno"
+++

# GOB-06 · Briefs y partes de relevo fuera del repositorio

**Contrato:** `governance/especificaciones/GOB-06.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO, aprobado por el propietario el 2026-11-23. Cada brief cuesta un PR, unos 6 min de CI y una fusión, y solo lo lee una vez una sesión de esta misma máquina.

## Entrega
- Los briefs, los partes de relevo y la hoja de tareas libres pasan a la carpeta local `C:\Users\Juan Carlos\compartido\evydentia\`, sin git.
- La tanda pasa al campo `tanda` de la ficha, y el CI sigue comprobando orden y ortogonalidad con las fichas.
- `scripts/verificar_briefs_locales.py`, que corre el Tech Lead antes de lanzar una tanda.

## Límites
- Se lanza sola, cuando ninguna de las fichas de la propiedad (FE-29, IA-13 a IA-16, LEG-07) está en `en_curso` (R7).
- Mientras no se fusione, los briefs siguen yendo al repositorio.
