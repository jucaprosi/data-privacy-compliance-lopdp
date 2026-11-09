+++
id = "NEON-00"
titulo = "Árbitro sin Neon: git grep fuera de una lista blanca cerrada y de los pendientes por ficha"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = []
propiedad = ["tests/test_sin_neon.py", "tests/sin_neon/permitidos.txt", "tests/sin_neon/pendientes/NEON-01.txt", "tests/sin_neon/pendientes/NEON-02.txt", "tests/sin_neon/pendientes/NEON-03.txt", "tests/sin_neon/pendientes/NEON-04.txt", "tests/sin_neon/pendientes/FIRMA-02.txt"]
crea = ["tests/test_sin_neon.py", "tests/sin_neon/permitidos.txt", "tests/sin_neon/pendientes/NEON-01.txt", "tests/sin_neon/pendientes/NEON-02.txt", "tests/sin_neon/pendientes/NEON-03.txt", "tests/sin_neon/pendientes/NEON-04.txt", "tests/sin_neon/pendientes/FIRMA-02.txt"]
arbitro = "pytest tests/test_sin_neon.py + python scripts/generar_indice_tareas.py --verificar; mutaciones M1 a M3"
rastros = ["¤arbitro"]
+++

# NEON-00 · Árbitro sin Neon

Diseño del Arquitecto ADPA (`DISENO_RETIRO_NEON_2026-11-09.md`), a partir del brief del CTO. Decisiones del propietario (2026-11-09):
- solo EVYDENTIA en `main`; el PMV congelado (rama `produccion`) no se toca;
- `app_core/huellas_produccion.py` se mantiene mientras exista la base Neon del PMV;
- la historia se conserva: fichas hechas, aportes, bibliografía, informes fechados y migraciones.

No borra ni crea recursos en Neon. No toca `.github/workflows/`, `verificadores/` ni migraciones. Sin `import yaml`.

**Reemplazo de la «rama Neon propia» (§0):**
- en local, la única base de pruebas es el contenedor PostgreSQL 16 del arnés (127.0.0.1), el mismo del CI desde CI-17;
- en el entorno desplegado, `evydentia-pruebas` de Cloud SQL (EP-05);
- una prueba con base corre si `TEST_DATABASE_URL` apunta a un host local o si `ARNES_BASE=postgresql_local`;
- una URL remota no habilita ninguna prueba con base.

## Entrega
`tests/test_sin_neon.py`:
- corre `git grep -n -i neon`;
- descuenta la lista blanca cerrada `tests/sin_neon/permitidos.txt` (`archivo|motivo`, solo puede decrecer);
- descuenta los pendientes `tests/sin_neon/pendientes/<ID>.txt` (`archivo:línea`), uno por ficha dueña: NEON-01, NEON-02, NEON-03, NEON-04 y FIRMA-02, generados a partir de la medición;
- queda en rojo si aparece una mención en cualquier otro lugar.

Además, la lista blanca acepta `governance/tareas/*.md` de fichas `hecha` (las lee del índice), `alembic/versions/**`, `governance/historico/pmv/**`, `APORTES_INEDITOS.md`, `FUENTES_Y_BIBLIOGRAFIA.md` e `INFORME_PARA_ZERAG_2026-10-21.md`.

Lista blanca inicial (medida en `main` b6acc55):
- `app_core/huellas_produccion.py`: guardia de la huella de producción del PMV (decisión 2 del propietario)
- `tests/test_sec20_huella_cloudsql.py`: prueba de la guardia de la huella
- `tests/test_bib117_capacidades.py`: hosts *.neon.invalid que prueban la guardia
- `tests/test_bib_108_importacion.py`: patrón que detecta credenciales y su caso
- `tests/test_ci17_ci_sin_neon.py`: árbitro de que el CI no usa Neon
- `tests/test_hook_pre_push.py`: guardia del hook contra la base de producción
- `tests/test_crear_organizacion_dev.py`: solo HOST_PRODUCCION de la guardia
- `tests/test_conftest_guardias.py`: solo URL_PRODUCCION de la guardia (URL_PRUEBAS la quita NEON-01)
- `governance/artefactos/PRD.md`: PRD del PMV congelado
- `governance/artefactos/TASKS.md`: índice generado; las menciones vienen de títulos de fichas hechas
- `verificadores/README.md`: gobernanza reservada; el parche va en el brief del propietario de NEON-04
- `verificadores/arnes_local.py`: gobernanza reservada; el parche va en el brief del propietario de NEON-04

## Pruebas
- Una mención nueva fuera de las listas falla.
- La lista blanca y los pendientes no crecen: se comparan con un recuento escrito en la prueba.
- Un archivo de pendientes de un ID desconocido falla.

**Mutaciones:**
- M1: añadir «neon» a un archivo vigente deja la prueba en rojo.
- M2: añadir una línea a `permitidos.txt` la deja en rojo.
- M3: crear `pendientes/OTRA.txt` la deja en rojo.

Al fusionarse, cualquier PR abierto que **añada** una mención queda en rojo. El Tech Lead lo avisa a los sub chats activos.
