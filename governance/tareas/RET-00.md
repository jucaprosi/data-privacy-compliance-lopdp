+++
id = "RET-00"
titulo = "Árbitro de plataforma única: main solo depende de Google Cloud"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = []
propiedad = ["tests/plataforma_unica/dependencias.txt", "tests/plataforma_unica/servicios_externos.txt", "tests/plataforma_unica/variables.txt", "tests/plataforma_unica/despliegue.txt", "tests/plataforma_unica/catalogos.py", "tests/plataforma_unica/pendientes/RET-01.txt", "tests/plataforma_unica/pendientes/RET-02.txt", "tests/plataforma_unica/pendientes/RET-03.txt", "tests/plataforma_unica/pendientes/RET-05.txt", "tests/plataforma_unica/pendientes/RET-06.txt", "tests/plataforma_unica/pendientes/IA-04.txt", "tests/plataforma_unica/pendientes/IA-06.txt", "tests/plataforma_unica/pendientes/IA-08.txt", "tests/test_plataforma_unica.py"]
crea = ["tests/plataforma_unica/dependencias.txt", "tests/plataforma_unica/servicios_externos.txt", "tests/plataforma_unica/variables.txt", "tests/plataforma_unica/despliegue.txt", "tests/plataforma_unica/catalogos.py", "tests/plataforma_unica/pendientes/RET-01.txt", "tests/plataforma_unica/pendientes/RET-02.txt", "tests/plataforma_unica/pendientes/RET-03.txt", "tests/plataforma_unica/pendientes/RET-05.txt", "tests/plataforma_unica/pendientes/RET-06.txt", "tests/plataforma_unica/pendientes/IA-04.txt", "tests/plataforma_unica/pendientes/IA-06.txt", "tests/plataforma_unica/pendientes/IA-08.txt", "tests/test_plataforma_unica.py"]
arbitro = "pytest tests/test_plataforma_unica.py + tests/test_sin_neon.py + tests/test_alembic_una_cabeza.py; mutaciones documentadas por cada prueba nueva"
rastros = ["¤arbitro", "¤seguridad"]
+++

# RET-00 · Árbitro de plataforma única

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-00.md`. Modelo sugerido: sonnet. Primera ficha del programa de retiro de plataformas (`governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`).

**Problema.** `main` debe quedar como si se hubiera construido de forma nativa sobre Google Cloud. Hoy ninguna prueba comprueba la estructura: de qué paquetes depende, de dónde saca su configuración, con qué servicios externos habla y cómo se despliega.

**Entrega.**
- `tests/test_plataforma_unica.py`: análisis por AST con las reglas R1 a R9 de la especificación (dependencias, configuración solo por el proceso, servicios externos, despliegue único, una sola guardia de base en las pruebas, catálogos que crecen a la vista, pendientes que solo decrecen).
- Cuatro catálogos cerrados y los pendientes por ficha en `tests/plataforma_unica/`, generados midiendo el árbol: lo que hoy incumple entra como pendiente de la ficha que lo retira (RET-01, RET-02, RET-03, RET-05, RET-06, IA-04, IA-06, IA-08).
- No toca código de producto ni retira nada (R8). Convive con el árbitro de menciones vigente hasta que lo retire RET-07.

**Para el propietario.** Si la lista de árbitros mínimos de cada fusión vive en `.github/workflows/` o en `verificadores/`, es suya: el Arquitecto entrega un brief para añadir `tests/test_plataforma_unica.py`.

