+++
id = "RET-06"
titulo = "Pruebas con una sola guardia de base común y sin avisos de plataforma anterior"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = ["RET-00", "RET-01", "DIAG-07", "DPO-03", "MTGE-03", "EVI-04", "FIRMA-02", "BIB-103", "BIB-117", "BIB-120", "BIB-202", "BIB-208", "BIB-305", "BIB-307", "CI-07", "CI-08", "CI-13", "FIRMA-05", "NEON-01", "NEON-03", "ORG-15", "ORG-24", "ORG-24b", "SEC-19", "RM-25a"]
propiedad = ["frontend/playwright.humo.config.ts", "frontend/playwright.integracion.config.ts", "tests/conftest.py", "tests/matriz/FIRMA-03.py", "tests/matriz/FIRMA-04.py", "tests/plataforma_unica/pendientes/RET-06.txt", "tests/test_bib118_capacidades_mias.py", "tests/test_bib_102_catalogo.py", "tests/test_bib_103_ficha.py", "tests/test_bib_104_descarga.py", "tests/test_bib_105_editorial.py", "tests/test_bib_106_externos.py", "tests/test_bib_107_documentos.py", "tests/test_bib_108_importacion.py", "tests/test_bib_109_plantillas_md.py", "tests/test_bib_201_formularios.py", "tests/test_bib_202_procedencia.py", "tests/test_bib_204_aplicabilidad.py", "tests/test_bib_208_fichas.py", "tests/test_bib_303_evidencia.py", "tests/test_bib_305_indicadores.py", "tests/test_bib_307_integracion.py", "tests/test_bib_402_vinculos.py", "tests/test_capa_persistencia.py", "tests/test_controles_periodicos.py", "tests/test_crear_organizacion_dev.py", "tests/test_diag13_evidencia_declarada.py", "tests/test_diagnostico_comparativo.py", "tests/test_diagnostico_escala_smartcidi.py", "tests/test_diagnostico_resultados.py", "tests/test_dpo_bitacora.py", "tests/test_dpo_consultas.py", "tests/test_dpo_informe_anual.py", "tests/test_eipd_guiada.py", "tests/test_evi04_custodia_generados.py", "tests/test_evidencias_persistencia.py", "tests/test_evidencias_retencion.py", "tests/test_evidencias_vigencia.py", "tests/test_fe26_sin_subida_pmv.py", "tests/test_firma_aceptaciones.py", "tests/test_firma_anf_stb.py", "tests/test_firma_router.py", "tests/test_firma_session_persistencia.py", "tests/test_hook_pre_push.py", "tests/test_incidentes.py", "tests/test_org24_ficha_organizacion.py", "tests/test_organizacion_cartera.py", "tests/test_organizaciones_por_persona.py", "tests/test_plugin_contar_consultas.py", "tests/test_rat_persistencia.py", "tests/test_rm25a_primera_validacion.py", "tests/test_roadmap_cierre_recordatorios.py", "tests/test_roadmap_hallazgos.py", "tests/test_sec19_descarga_con_sesion.py"]
crea = []
arbitro = "pytest tests/test_plataforma_unica.py con tests/plataforma_unica/pendientes/RET-06.txt vacío + suite completa en el CI; git diff limitado a docstrings y a la llamada a la guardia común; prueba de mutación documentada"
rastros = ["¤arbitro"]
+++

# RET-06 · Una sola guardia de base en las pruebas

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-06.md`. Modelo sugerido: sonnet. Absorbe a NEON-02 (sus archivos pasan a esta ficha; NEON-02 conserva solo lo que no está aquí y depende de RET-06).

**Problema.** Unos 57 archivos de pruebas repiten un aviso en el docstring y una comprobación propia del host de la base. La regla R5 de RET-00 exige una sola guardia: `exigir_base_de_pruebas()` de `tests/conftest.py` (RET-01).

**Entrega.** Sustitución mecánica con un script cuyo diff se revisa archivo por archivo: el docstring nuevo describe la prueba sobre el PostgreSQL 16 local o el del CI y la comprobación propia se reemplaza por la llamada a la guardia común. Lo que afirma cada prueba no cambia. Las configuraciones de Playwright `humo` e `integracion` y `tests/humo/servidor_humo.py` entran aquí.

**NEON-02.** Sus archivos pasan a esta ficha de forma explícita (ya no figuran en la propiedad de NEON-02). NEON-02 no se cierra como hecha: queda pendiente y depende de RET-06, y la retira RET-07 junto con las demás de esa historia.

**Un PR por dominio** (biblioteca, diagnóstico, roadmap, organización, evidencias, firma y resto). Cada PR reduce `tests/plataforma_unica/pendientes/RET-06.txt`. El dominio diagnóstico espera a DIAG-07; los archivos con dueña abierta (DPO-03, MTGE-03, EVI-04, FIRMA-02) entran cuando esa ficha esté fusionada, por eso figuran en `depende_de`. `tests/test_diag12_estados.py` lo posee RM-25b y lo limpia esa ficha: queda fuera de la propiedad de esta y del pendiente hasta entonces.

