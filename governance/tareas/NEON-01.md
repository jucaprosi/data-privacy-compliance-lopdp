+++
id = "NEON-01"
titulo = "Pruebas y scripts sin la rama Neon propia: base local o evydentia-pruebas y guardias generalizadas a base remota"
ola = "backlog"
estado = "en_curso"
sala = "pruebas"
depende_de = ["NEON-00", "BIB-120", "RM-21", "SEC-03", "BIB-102", "BIB-117", "BIB-201", "BIB-202", "CI-02", "CI-03", "CI-08", "CI-09", "CI-10", "CI-12", "CI-13", "CI-17", "CI-18", "GCP-01", "BIB-108", "BIB-204", "BIB-208", "BIB-303", "BIB-305", "BIB-307", "BIB-402"]
propiedad = ["tests/conftest.py", "tests/test_bib_103_ficha.py", "tests/test_bib_104_descarga.py", "tests/test_bib_107_documentos.py", "tests/test_base_por_trabajador.py", "scripts/corrida_cubierta.py", "tests/test_corrida_cubierta.py", "scripts/contar_consultas_pruebas.py", "tests/test_plugin_contar_consultas.py", "scripts/medir_variacion_ci.py", "tests/test_medir_variacion_ci.py", "tests/test_bib_102_catalogo.py", "tests/test_bib_105_editorial.py", "tests/test_bib_109_plantillas_md.py", "tests/test_bib_201_formularios.py", "tests/test_bib_202_procedencia.py", "tests/test_ci_migrar_contenedor.py", "tests/test_gcp01_cloudrun_rls_single_rtt.py", "tests/test_servidor_humo.py", "tests/sin_neon/pendientes/NEON-01.txt", "tests/test_bib_108_importacion.py", "tests/test_bib_204_aplicabilidad.py", "tests/test_bib_208_fichas.py", "tests/test_bib_303_evidencia.py", "tests/test_bib_305_indicadores.py", "tests/test_bib_307_integracion.py", "tests/test_bib_402_vinculos.py"]
crea = []
arbitro = "suite completa con el arnés local en verde, sin más omitidas; pytest tests/test_sin_neon.py con pendientes/NEON-01.txt vacío; git grep -E _RAMA_PROPIA sobre tests/ da 0; mutaciones"
rastros = ["¤arbitro"]
+++

# NEON-01 · Lógica de pruebas y scripts

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
- **`conftest.py`:** `_paralelo_sobre_neon` pasa a ser `_paralelo_sobre_base_remota`, que mira si el host no es local. Ya no nombra Neon y la protección cubre también Cloud SQL.
- **`contar_consultas_pruebas.py`:** `_HOSTS_PROHIBIDOS` pasa a «solo host local».
- **`corrida_cubierta.py`:** `RAMA_NEON = "main"` quedó obsoleto con CI-17. Se cambia la lógica del script, pero no el workflow (`zero-regression-pipeline.yml:99`), que es del propietario.
  - Prueba: un PR hacia main adopta la corrida del push con el mismo SHA.
  - Mutación: devolver la regla de Neon deja esa prueba en rojo.
- **`medir_variacion_ci.py` y su prueba:** ningún workflow ni script los llama. Se borran.
- **Variables `*_RAMA_PROPIA`:** se retiran y queda la regla del §0.
  - Prueba: con una URL remota, cada prueba con base se omite.
  - Mutación: aceptar una URL remota la deja en rojo.
- **`test_conftest_guardias.py`:** está en la lista blanca solo por `URL_PRODUCCION`, así que aquí no se toca.
- **`test_bib_103_ficha.py`, `test_bib_104_descarga.py` y `test_bib_107_documentos.py`:** ya no dicen «neon», pero usan `BIB103_RAMA_PROPIA` (103:163), `BIB104_RAMA_PROPIA` (104:264) y `BIB107_RAMA_PROPIA` (107:166). Pasan a la regla del §0. Árbitro: `git grep -E "_RAMA_PROPIA" -- tests/` da 0. Mutación: dejar un `*_RAMA_PROPIA` deja la prueba en rojo (Arquitecto, revisión del #543).
- Al terminar, `pendientes/NEON-01.txt` queda vacío o se borra.
