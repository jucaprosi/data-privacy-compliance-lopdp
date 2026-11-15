+++
id = "RET-00"
titulo = "Eliminar las pruebas que vigilaban plataformas retiradas"
ola = "backlog"
estado = "en_curso"
sala = "pruebas"
depende_de = ["CI-24", "NEON-00"]
propiedad = ["tests/plataforma_unica/catalogos.py", "tests/plataforma_unica/dependencias.txt", "tests/plataforma_unica/despliegue.txt", "tests/plataforma_unica/servicios_externos.txt", "tests/plataforma_unica/variables.txt", "tests/plataforma_unica/pendientes/RET-01.txt", "tests/plataforma_unica/pendientes/RET-02.txt", "tests/plataforma_unica/pendientes/RET-03.txt", "tests/plataforma_unica/pendientes/RET-05.txt", "tests/plataforma_unica/pendientes/RET-06.txt", "tests/plataforma_unica/pendientes/IA-04.txt", "tests/plataforma_unica/pendientes/IA-06.txt", "tests/plataforma_unica/pendientes/IA-08.txt", "tests/test_plataforma_unica.py", "tests/sin_neon/permitidos.txt", "tests/sin_neon/pendientes/FIRMA-02.txt", "tests/sin_neon/pendientes/NEON-01.txt", "tests/sin_neon/pendientes/NEON-02.txt", "tests/sin_neon/pendientes/NEON-03.txt", "tests/sin_neon/pendientes/NEON-04.txt", "tests/test_sin_neon.py", "tests/test_ci17_ci_sin_neon.py", "tests/test_vercel_despliegue.py"]
crea = []
arbitro = "suite completa en verde en el CI + pytest tests/test_indice_tareas.py tests/test_reparto.py; ninguno de los archivos de la propiedad existe tras el merge (revisión del PR)"
rastros = ["¤arbitro", "¤seguridad"]
+++

# RET-00 · Eliminar las pruebas que vigilaban plataformas retiradas

Especificación del Arquitecto ADPA (2026-11-14, estado final): `governance/especificaciones/RET-00.md`. Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`. Modelo sugerido: sonnet. Va primero con RET-01a: sin estas pruebas, cada ficha de eliminación siguiente solo borra código y su árbitro es la suite en verde.

**Problema.** Cuatro familias de pruebas existen solo para vigilar plataformas que Google Cloud reemplazó: el árbitro de catálogos cerrados, la guardia de menciones de la base anterior y su carpeta de permitidos, la comprobación de que el CI no usaba esa base y la prueba del despliegue anterior. Con la plataforma única ya no vigilan nada y obligan a mantener listas.

**Entrega.**
- Se borra cada archivo de la propiedad, entero: `tests/plataforma_unica/` con sus pendientes, `tests/test_plataforma_unica.py`, `tests/sin_neon/` con sus pendientes, `tests/test_sin_neon.py`, `tests/test_ci17_ci_sin_neon.py` y `tests/test_vercel_despliegue.py`. No queda un sustituto, una lista vacía ni una prueba que compruebe que se borró.
- La ficha confirma la lista con los nombres exactos de `origin/main` al empezar.
- Se retiran las referencias a esos archivos en `pytest.ini`, en las fichas y en los briefs. `tests/duraciones.json` lo posee CI-28: la entrada de `test_vercel_despliegue.py` la retira CI-28 al regenerarlo; si CI-28 ya está fusionada cuando llegue esta ficha, se retira aquí.
- Si un workflow o un archivo de `verificadores/` nombra uno de estos archivos, el cambio va en un brief al propietario (`governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`), no en este PR.
- No se toca `exigir_base_de_pruebas()`: es de RET-01a.
