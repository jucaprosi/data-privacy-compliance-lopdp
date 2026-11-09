+++
id = "NEON-02"
titulo = "Comentarios y docstrings sin Neon en pruebas y en la configuración de ejemplo"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = ["NEON-00", "ORG-13", "ORG-14", "ORG-16", "RAT-01", "RAT-02", "RAT-05", "RM-01", "RM-21", "RM-23", "SEC-07", "SEC-08", "BIB-203", "BIB-205", "BIB-206", "BIB-207", "DER-03", "DIAG-13", "DPO-02", "FE-26", "FIRMA-03", "FIRMA-05", "FIRMA-06", "GCP-01", "INC-01"]
propiedad = [".env.example", "app_core/cloud/gcp_runtime.py", "tests/matriz/FIRMA-03.py", "tests/matriz/FIRMA-04.py", "tests/test_bib_203_tablas.py", "tests/test_bib_205_generacion.py", "tests/test_bib_206_preview.py", "tests/test_bib_207_concurrencia.py", "tests/test_capa_persistencia.py", "tests/test_controles_periodicos.py", "tests/test_diag13_evidencia_declarada.py", "tests/test_diagnostico_escala_smartcidi.py", "tests/test_diagnostico_respuestas.py", "tests/test_diagnostico_resultados.py", "tests/test_dpo_bitacora.py", "tests/test_dpo_informe_anual.py", "tests/test_e2e_flujo_completo.py", "tests/test_fe26_sin_subida_pmv.py", "tests/test_firma_session_persistencia.py", "tests/test_incidentes.py", "tests/test_org_14_datos_documentales.py", "tests/test_organizacion_alta.py", "tests/test_organizaciones_por_persona.py", "tests/test_rat_persistencia.py", "tests/test_rat_plantilla_salud.py", "tests/test_roadmap_cierre_recordatorios.py", "tests/test_roadmap_hallazgos.py", "tests/sin_neon/pendientes/NEON-02.txt"]
crea = []
arbitro = "pytest tests/test_sin_neon.py con pendientes/NEON-02.txt vacío; git diff limitado a comentarios, docstrings y .env.example"
rastros = ["¤arbitro"]
+++

# NEON-02 · Comentarios de pruebas

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
- Cambia solo comentarios y docstrings. En `.env.example`, solo el texto de ejemplo, sin valores reales. Ninguna aserción cambia.
- La lista se generó del inventario quitando NEON-01, NEON-03, NEON-04, FIRMA-02 y la lista blanca.
- `verificadores/README.md` y `verificadores/arnes_local.py` no entran, porque son gobernanza reservada: van en la lista blanca, y NEON-04 entrega su parche en el brief del propietario.
- Al terminar, `pendientes/NEON-02.txt` queda vacío o se borra.
