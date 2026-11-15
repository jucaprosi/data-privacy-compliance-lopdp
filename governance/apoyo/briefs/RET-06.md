### BL-315 · pruebas-una-sola-guardia-de-base  (tanda 73)

**Contexto.** Sala: `pruebas`. Depende de: `RET-00`, `RET-01`, `DIAG-07`, `DPO-03`, `MTGE-03`, `EVI-04`, `FIRMA-02`, `CI-28`. Especificaciones: `governance/tareas/RET-06.md`.

**Objetivo** (en este orden):

1. `RET-06` — Pruebas con una sola guardia de base común y sin avisos de plataforma anterior

**Rastro ¤**:

- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `frontend/playwright.humo.config.ts`
  - `frontend/playwright.integracion.config.ts`
  - `tests/conftest.py`
  - `tests/matriz/FIRMA-03.py`
  - `tests/matriz/FIRMA-04.py`
  - `tests/plataforma_unica/pendientes/RET-06.txt`
  - `tests/test_bib118_capacidades_mias.py`
  - `tests/test_bib_102_catalogo.py`
  - `tests/test_bib_103_ficha.py`
  - `tests/test_bib_104_descarga.py`
  - `tests/test_bib_105_editorial.py`
  - `tests/test_bib_106_externos.py`
  - `tests/test_bib_107_documentos.py`
  - `tests/test_bib_108_importacion.py`
  - `tests/test_bib_109_plantillas_md.py`
  - `tests/test_bib_201_formularios.py`
  - `tests/test_bib_202_procedencia.py`
  - `tests/test_bib_204_aplicabilidad.py`
  - `tests/test_bib_208_fichas.py`
  - `tests/test_bib_303_evidencia.py`
  - `tests/test_bib_305_indicadores.py`
  - `tests/test_bib_307_integracion.py`
  - `tests/test_bib_402_vinculos.py`
  - `tests/test_capa_persistencia.py`
  - `tests/test_controles_periodicos.py`
  - `tests/test_crear_organizacion_dev.py`
  - `tests/test_diag13_evidencia_declarada.py`
  - `tests/test_diagnostico_comparativo.py`
  - `tests/test_diagnostico_escala_smartcidi.py`
  - `tests/test_diagnostico_resultados.py`
  - `tests/test_dpo_bitacora.py`
  - `tests/test_dpo_consultas.py`
  - `tests/test_dpo_informe_anual.py`
  - `tests/test_eipd_guiada.py`
  - `tests/test_evi04_custodia_generados.py`
  - `tests/test_evidencias_persistencia.py`
  - `tests/test_evidencias_retencion.py`
  - `tests/test_evidencias_vigencia.py`
  - `tests/test_fe26_sin_subida_pmv.py`
  - `tests/test_firma_aceptaciones.py`
  - `tests/test_firma_anf_stb.py`
  - `tests/test_firma_router.py`
  - `tests/test_firma_session_persistencia.py`
  - `tests/test_hook_pre_push.py`
  - `tests/test_incidentes.py`
  - `tests/test_org24_ficha_organizacion.py`
  - `tests/test_organizacion_cartera.py`
  - `tests/test_organizaciones_por_persona.py`
  - `tests/test_plugin_contar_consultas.py`
  - `tests/test_rat_persistencia.py`
  - `tests/test_rm25a_primera_validacion.py`
  - `tests/test_roadmap_cierre_recordatorios.py`
  - `tests/test_roadmap_hallazgos.py`
  - `tests/test_sec19_descarga_con_sesion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-06`: pytest tests/test_plataforma_unica.py con tests/plataforma_unica/pendientes/RET-06.txt vacío + suite completa en el CI; git diff limitado a docstrings y a la llamada a la guardia común; prueba de mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.


