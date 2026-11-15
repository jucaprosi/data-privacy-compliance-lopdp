# Inventario de pruebas de parche
`¤sdd` `¤arbitro`

Arquitecto ADPA, 2026-11-15. Especificación: `governance/especificaciones/QA-09.md`. Medido en `origin/main` 4fd81e99.

- 297 archivos `tests/**/test_*.py`, 2711 funciones de prueba.
- Candidatos: los 139 archivos que leen `governance/`, código fuente, workflows o configuración como texto, o que no ejercitan código. Los 158 restantes ejercitan código y quedan fuera del inventario.
- Resultado: 71 archivos con funciones afectadas, 138 funciones. En 23 de ellos la regla no tiene otra prueba de comportamiento: su ficha escribe la prueba nueva antes de borrar la textual (QA-09 R3).
- Fuera de alcance: `test_plataforma_unica.py`, `test_sin_neon.py`, `test_ci17_ci_sin_neon.py` y `test_vercel_despliegue.py`, que borra RET-00.
- Ningún archivo de `verificadores/`, `.github/workflows/`, `scripts/` ni de los `.bat` invoca un archivo con funciones afectadas. Solo citan `test_banco_preguntas.py` y `test_escala_madurez.py`, que se conservan. No hace falta brief al propietario.
- Las celdas «propia» indican que el archivo es la prueba de comportamiento. En «BORRAR/FUSIONAR» parcial, la ficha confirma la función exacta al empezar.

| Archivo | Decisión | Funciones afectadas / total | Regla que protege | Cobertura de comportamiento que queda | Ficha |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/test_adpa05_secciones_y_errores.py` | CONSERVAR | 0/4 | marcas de reparto; registrar idempotente | propia | — |
| `tests/test_adpa06_pasillos_secciones.py` | CONSERVAR | 0/2 | secciones de pasillos | propia | — |
| `tests/test_adpa07_secciones_frontend.py` | CONSERVAR | 0/2 | marcas equilibradas en el frontend | propia | — |
| `tests/test_adpa08_terceros_transferencias_schema.py` | CONSERVAR | 0/4 | RLS y permisos | propia | — |
| `tests/test_adpa09_salas_prd.py` | BORRAR | 2/2 | catálogo de salas | test_adpa_bulkhead.py::test_cada_sala_tiene_su_compuerta | QA-10 |
| `tests/test_adpa11_seccion_solo_dpo.py` | BORRAR | 4/4 | quien no es DPO no elige nivel | equilibrio: test_adpa07_secciones_frontend.py; regla: NINGUNA — requiere prueba de comportamiento nueva | QA-10 |
| `tests/test_adpa12_compuerta_modular.py` | CONSERVAR | 0/5 | compuerta modular | propia | — |
| `tests/test_adpa_bulkhead.py` | CONSERVAR | 0/5 | aislamiento ADPA | propia | — |
| `tests/test_adpa_bulkheads.py` | FUSIONAR | 2/2 | compuerta por sala | test_adpa_bulkhead.py::test_cada_sala_tiene_su_compuerta | QA-10 |
| `tests/test_adpa_dependencias.py` | CONSERVAR | 0/9 | deuda lateral y ciclos | propia | — |
| `tests/test_alembic_una_cabeza.py` | CONSERVAR (parcial BORRAR) | 1/2 | una cabeza de Alembic | test_alembic_una_cabeza.py::test_alembic_tiene_exactamente_una_cabeza | QA-10 |
| `tests/test_arnes_archivos_rastreados.py` | CONSERVAR | 0/1 | el arnés ignora lo no rastreado | propia | — |
| `tests/test_arnes_local.py` | CONSERVAR | 0/11 | base local por worktree | propia | — |
| `tests/test_auditor_secciones.py` | CONSERVAR | 0/2 | matriz del auditor | propia | — |
| `tests/test_bib115_identidad_biblioteca.py` | CONSERVAR (parcial BORRAR) | 3/8 | X-Role y X-User-ID | test_bib115_identidad_biblioteca.py::test_sin_x_role_responde_422; frontend/tests/biblioteca/identidad.spec.ts | QA-09 |
| `tests/test_bib117_capacidades.py` | CONSERVAR (parcial BORRAR) | 2/10 | capacidades sin endpoint ni borrado | test_bib117_capacidades.py::test_lopdp_app_no_puede_escribir_capacidades | QA-09 |
| `tests/test_bib_101_acceso.py` | CONSERVAR (parcial BORRAR) | 4/7 | organización solo en cabeceras | test_bib_101_acceso.py::test_organizacion_ajena_se_deniega_por_api; frontend/tests/biblioteca/acceso.spec.ts | QA-09 |
| `tests/test_bib_104_descarga.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 2/11 | RLS de descargas | test_bib_104_descarga.py::test_db_aislamiento_rls_auditoria_descargas | QA-09 |
| `tests/test_bib_105_editorial.py` | CONSERVAR | 0/34 | cuatro ojos, publicación | propia | — |
| `tests/test_bib_106_externos.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 2/14 | RLS de cargas externas | test_bib_106_externos.py::test_db_rls_forzada_aisla_las_cargas | QA-09 |
| `tests/test_bib_107_documentos.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 2/21 | RLS de documentos | test_bib_107_documentos.py::test_db_rls_con_lopdp_app_aisla_lee_y_escribe_por_organizacion | QA-09 |
| `tests/test_bib_108_importacion.py` | CONSERVAR | 0/19 | importación idempotente | propia | — |
| `tests/test_bib_109_plantillas_md.py` | CONSERVAR (parcial FUSIONAR) | 1/21 | una cabeza | test_alembic_una_cabeza.py::test_alembic_tiene_exactamente_una_cabeza | QA-09 |
| `tests/test_bib_112_secciones.py` | CONSERVAR | 0/6 | marcas por ficha | propia | — |
| `tests/test_bib_201_formularios.py` | CONSERVAR (parcial FUSIONAR) | 1/28 | RLS de formularios | por verificar al empezar la ficha; si falta, prueba nueva | QA-09 |
| `tests/test_bib_202_procedencia.py` | CONSERVAR (parcial BORRAR) | 1/13 | el router no escribe en las fuentes | test_bib_202_procedencia.py::test_db_proponer_correccion_no_modifica_el_dato_canonico | QA-09 |
| `tests/test_bib_205_generacion.py` | CONSERVAR (parcial FUSIONAR) | 1/19 | instantánea sin UPDATE | NINGUNA — requiere prueba de comportamiento nueva | QA-09 |
| `tests/test_bib_207_concurrencia.py` | CONSERVAR (parcial FUSIONAR) | 1/12 | petición inmutable | test_bib_207_concurrencia.py::test_db_peticion_inmutable_y_sin_borrado | QA-09 |
| `tests/test_bib_302_enlaces.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 3/5 | sin cambio automático de estado | NINGUNA — requiere prueba de comportamiento nueva | QA-09 |
| `tests/test_bib_303_evidencia.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 2/15 | expediente solo anexar | test_bib_303_evidencia.py::test_db_expediente_inmutable_para_la_aplicacion | QA-09 |
| `tests/test_bib_304_impacto.py` | CONSERVAR (parcial BORRAR) | 3/5 | documento aprobado inmutable | NINGUNA — requiere prueba de comportamiento nueva (disparador contra la base) | QA-09 |
| `tests/test_bib_305_indicadores.py` | CONSERVAR (parcial BORRAR) | 2/10 | sin cifra global de cumplimiento | NINGUNA — requiere prueba de comportamiento nueva | QA-09 |
| `tests/test_bib_306_conservacion.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 3/7 | historial inmutable | NINGUNA — requiere prueba de comportamiento nueva | QA-09 |
| `tests/test_bib_402_vinculos.py` | CONSERVAR (parcial BORRAR/FUSIONAR) | 3/11 | límite ADPA; RLS de vínculos | test_adpa_bulkhead.py::test_solo_se_importa_la_compuerta_de_la_sala; test_bib_402_vinculos.py::test_db_rls_y_permisos_con_lopdp_app | QA-09 |
| `tests/test_bib_estado_revision.py` | BORRAR | 2/2 | estado solo por SECURITY DEFINER | NINGUNA — requiere prueba de comportamiento nueva | QA-09 |
| `tests/test_bov01_paquetes_cuotas.py` | CONSERVAR | 0/14 | cuotas y RLS | propia | — |
| `tests/test_bucle_eventos.py` | CONSERVAR | 0/5 | bucle de eventos en win32, un punto de entrada | propia | — |
| `tests/test_cabeceras_seguridad.py` | CONSERVAR (parcial BORRAR) | 2/8 | cabeceras de seguridad HTTP | NINGUNA — requiere prueba de comportamiento nueva | QA-11 |
| `tests/test_ci16_pruebas_sin_proyecto.py` | CONSERVAR | 0/6 | toda spec de Playwright tiene proyecto | propia | — |
| `tests/test_ci21_sin_import_yaml.py` | CONSERVAR | 0/14 | lector YAML propio | propia | — |
| `tests/test_ci22_exenciones_secciones.py` | CONSERVAR | 0/13 | exenciones válidas | propia | — |
| `tests/test_ci29_sin_generados_compartidos.py` | CONSERVAR | 0/6 | índice y reparto | propia | — |
| `tests/test_ci30_playwright_por_salas.py` | CONSERVAR | 0/9 | Playwright por sala | propia | — |
| `tests/test_ci_migrar_contenedor.py` | CONSERVAR | 0/3 | la migración nunca va a una base remota | propia | — |
| `tests/test_compuertas_arco_terceros_transferencias.py` | CONSERVAR | 0/6 | compuertas ADPA y transferencias | propia | — |
| `tests/test_conftest_entorno.py` | CONSERVAR | 0/2 | intérprete incompleto detiene la suite | propia | — |
| `tests/test_conftest_guardias.py` | CONSERVAR | 0/6 | nunca probar contra producción | propia | — |
| `tests/test_contrato_hoja_ruta.py` | CONSERVAR | 0/8 | contrato OpenAPI | propia | — |
| `tests/test_controles_periodicos.py` | CONSERVAR (parcial BORRAR) | 1/12 | auditoría CAPA no crea tareas | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_core01_zona_unica.py` | CONSERVAR (parcial BORRAR) | 1/3 | zona de negocio con una fuente | test_core01_zona_unica.py::test_la_zona_de_negocio_vive_solo_en_app_core | QA-10 |
| `tests/test_corrida_cubierta.py` | CONSERVAR (parcial BORRAR) | 1/16 | el PR reutiliza la corrida del push | test_corrida_cubierta.py::test_el_pr_adopta_la_corrida_del_push_cuando_su_arnes_pasa | QA-10 |
| `tests/test_demo_ciclo.py` | CONSERVAR | 0/19 | ciclo de la demo | propia | — |
| `tests/test_demo_clon_biblioteca.py` | CONSERVAR (parcial BORRAR) | 1/13 | el clonado no hace commit | test_demo_clon_biblioteca.py::test_no_hace_commit_y_restaura_el_contexto | QA-12 |
| `tests/test_demo_clon_diagnostico.py` | CONSERVAR | 0/12 | clonado aislado y RLS | propia | — |
| `tests/test_demo_clon_evidencias.py` | CONSERVAR | 0/10 | clonado aislado y RLS | propia | — |
| `tests/test_demo_clon_organizacion.py` | CONSERVAR | 0/12 | clonado, RLS y ADPA | propia | — |
| `tests/test_demo_clon_roadmap.py` | CONSERVAR | 0/10 | clonado aislado y RLS | propia | — |
| `tests/test_demo_contrato.py` | CONSERVAR (parcial BORRAR) | 1/16 | la demo no borra | test_demo_contrato.py::test_la_migracion_no_concede_delete_a_lopdp_app | QA-12 |
| `tests/test_demo_gancho_identidad.py` | CONSERVAR (parcial BORRAR) | 1/13 | resolutor solo en demo | test_demo_gancho_identidad.py::test_resolutor_ignorado_si_el_entorno_no_es_demo | QA-12 |
| `tests/test_demo_siembra.py` | CONSERVAR (parcial BORRAR) | 1/12 | id de plantilla centralizado | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_der03_tenant_solicitud.py` | CONSERVAR (parcial BORRAR) | 1/7 | migración expand/contract | test_der03_tenant_solicitud.py::test_04_migracion_aborta_con_huerfanos_y_no_toca_la_tabla | QA-12 |
| `tests/test_der04_contraccion.py` | CONSERVAR (parcial BORRAR) | 1/10 | columna retirada | test_der04_contraccion.py::test_03_sin_huerfanos_retira_columna_y_disparador | QA-12 |
| `tests/test_der05_plazos.py` | CONSERVAR (parcial BORRAR) | 1/5 | plazos ARCO por tipo | test_der05_plazos.py::test_a_plazo_y_vencimiento_por_tipo | QA-12 |
| `tests/test_der06b_tipos_activos.py` | CONSERVAR (parcial BORRAR) | 3/6 | tipos activos y aviso a la autoridad | test_der06b_tipos_activos.py::test_crear_cada_tipo_nuevo_da_fila_y_plazo_de_diez_dias; aviso de la interfaz: NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_der07_textos_legales.py` | BORRAR | 3/3 | textos legales ARCO (art. 37, 72 h) | NINGUNA — requiere prueba de comportamiento nueva (render de ArcoModule) | QA-12 |
| `tests/test_diag07b_siembra_como_admin.py` | CONSERVAR | 0/4 | siembras no actúan como DPO | propia | — |
| `tests/test_diag16_referencias_normativas.py` | CONSERVAR (parcial BORRAR) | 1/5 | referencias normativas coherentes | test_diag16_referencias_normativas.py::test_referencias_backend_igual_frontend | QA-12 |
| `tests/test_dlp01_sampling_discovery.py` | CONSERVAR | 0/12 | DLP sin persistir PII | propia | — |
| `tests/test_entorno_arnes.py` | CONSERVAR (parcial BORRAR) | 2/8 | .bat portables | test_entorno_arnes.py::test_entorno_bat_resuelve_el_interprete_principal_desde_un_worktree_sin_venv | QA-10 |
| `tests/test_ep03_sembrar_entorno.py` | CONSERVAR (parcial BORRAR) | 1/19 BORRAR (test_ningun_correo_inventado_sale_de_example_test) | correos sintéticos solo @example.test | test_ep10_datos_modulos.py::test_2_3_4_5_siembra_por_compuerta_idempotente_y_sin_correos (parcial) | QA-11 |
| `tests/test_ep04_computo_pruebas.py` | CONSERVAR | 0/30 | paridad del manifiesto de pruebas con producción | propia | — |
| `tests/test_ep05_datos_pruebas.py` | CONSERVAR (parcial BORRAR) | 3/10 BORRAR | sin retención bloqueada; sin secretos de correo | NINGUNA — requiere prueba de comportamiento nueva | QA-11 |
| `tests/test_ep06_ciclo_version.py` | CONSERVAR (parcial BORRAR) | 1/17 BORRAR (test_los_scripts_no_imprimen_la_variable_de_la_url) | la URL de la base no se imprime | test_ep06_ciclo_version.py::test_la_url_de_conexion_no_se_imprime | QA-11 |
| `tests/test_ep07_verificar_entorno.py` | CONSERVAR | 0/16 | verificador del entorno | propia | — |
| `tests/test_ep10_datos_modulos.py` | CONSERVAR | 0/4 | siembra solo por compuertas | propia | — |
| `tests/test_evidencia_validacion_servidor.py` | CONSERVAR (parcial FUSIONAR) | 1/9 | lista blanca MIME y tamaño | test_evidencia_validacion_servidor.py::test_tipo_fuera_de_la_lista_blanca_se_rechaza_con_415 | QA-12 |
| `tests/test_evidencias_retencion.py` | CONSERVAR | 0/4 | retención de 1825 días | propia | — |
| `tests/test_evidencias_rutas_estables.py` | CONSERVAR (parcial BORRAR) | 1/5 BORRAR (test_la_bandera_se_lee_solo_en_el_backend) | bandera solo en el backend | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_fe28_textos_sin_jerga.py` | CONSERVAR (parcial BORRAR) | 1/7 BORRAR (test_las_cadenas_corregidas_ya_no_estan) | interfaz sin jerga | test_fe28_textos_sin_jerga.py::test_ningun_componente_muestra_jerga | QA-12 |
| `tests/test_gcp01_cloudrun_rls_single_rtt.py` | CONSERVAR (parcial BORRAR) | 1/4 (parte de texto) | RLS en un solo viaje | test_gcp01_cloudrun_rls_single_rtt.py::test_rls_set_config_valores_activos_en_transaccion | QA-11 |
| `tests/test_gcp02_tia_adpa_selector.py` | CONSERVAR | 0/27 | selector de pruebas | propia | — |
| `tests/test_gcp03_app_env_por_servicio.py` | BORRAR (parcial) | 2/3 | APP_ENV por servicio | test_gcp03_app_env_por_servicio.py::test_imagen_produccion_sirve_robots_allow | QA-11 |
| `tests/test_gcp03_frontend_cloudrun.py` | BORRAR | 3/3 | contenedor sin root | NINGUNA — requiere prueba de comportamiento nueva | QA-11 |
| `tests/test_gcp04_cloudsql_migration_cutover.py` | CONSERVAR (parcial BORRAR) | 3/13 BORRAR | Postgres 16, PITR, /api/v1 | NINGUNA — requiere prueba de comportamiento nueva | QA-11 |
| `tests/test_gcp05_escalado.py` | CONSERVAR (parcial BORRAR) | 2/15 | presupuesto de conexiones | test_gcp05_escalado.py::test_m3_todo_cloudrun_con_pool_cabe_en_el_presupuesto | QA-11 |
| `tests/test_gcp06_cache.py` | CONSERVAR | 0/8 | caché aislada por tenant | propia | — |
| `tests/test_gcp07_despliegue_progresivo.py` | CONSERVAR | 0/12 | migraciones destructivas rechazadas | propia | — |
| `tests/test_gcp08_proxy_e_imagen.py` | CONSERVAR (parcial BORRAR) | 1/15 BORRAR (test_06_las_sondas_usan_health) | sondas en /health | test_gcp08_proxy_e_imagen.py::test_04_health_responde_sin_tocar_el_backend | QA-11 |
| `tests/test_gcp09_dominio_e_ingress.py` | BORRAR (parcial CONSERVAR) | 6/10 BORRAR | ingress interno; CORS https | NINGUNA — requiere prueba de comportamiento nueva | QA-11 |
| `tests/test_gcp10_dockerignore.py` | CONSERVAR | 0/6 | secretos fuera de la imagen | propia | — |
| `tests/test_gcp11_brief_solo_lectura.py` | BORRAR | 6/6 | ninguna (prosa de un brief) | no aplica | QA-11 |
| `tests/test_gcp11_manifiesto_secretos.py` | CONSERVAR (parcial BORRAR) | 1/3 | secretos desde Secret Manager | test_gcp11_manifiesto_secretos.py::test_el_manifiesto_toma_la_base_de_secret_manager | QA-11 |
| `tests/test_gcp11_secretos_sin_bom.py` | CONSERVAR | 0/6 | secretos sin BOM | propia | — |
| `tests/test_generar_indice_tareas_arbol.py` | CONSERVAR | 0/21 | índice y reparto | propia | — |
| `tests/test_hook_pre_push.py` | CONSERVAR | 0/13 | bloqueo del push a main | propia | — |
| `tests/test_ia07_asistente_inferencia.py` | CONSERVAR (parcial BORRAR) | 3/8 BORRAR | avisos sin proveedor ni jerga | test_ia07_asistente_inferencia.py::test_avisos_al_cliente_sin_jerga_ni_proveedor | QA-12 |
| `tests/test_ia10_huellas_prompts.py` | CONSERVAR | 0/10 | prompts versionados | propia | — |
| `tests/test_ia11_evaluacion.py` | CONSERVAR | 0/16 | evaluación de prompts | propia | — |
| `tests/test_indice_tareas.py` | CONSERVAR | 0/19 | índice de tareas | propia | — |
| `tests/test_inv_citados_existen.py` | CONSERVAR | 0/2 | todo INV citado existe | propia | — |
| `tests/test_leg03_citas_legales.py` | CONSERVAR | 0/6 | citas legales con fuente | propia | — |
| `tests/test_marca_lanzadores.py` | BORRAR | 2/2 | ninguna (nombre de marca) | no aplica | QA-10 |
| `tests/test_merkle_anchoring.py` | CONSERVAR | 0/2 | Merkle y TSA | propia | — |
| `tests/test_ops07_observabilidad.py` | CONSERVAR (parcial BORRAR) | 1/7 | correlación montada en la app | NINGUNA — requiere prueba de comportamiento nueva (request-id con main.app) | QA-11 |
| `tests/test_orden_por_duracion.py` | CONSERVAR | 0/8 | orden por duración | propia | — |
| `tests/test_org22_rol_auditor.py` | CONSERVAR | 0/6 | rol auditor y SoD | propia | — |
| `tests/test_organizacion_inventario.py` | CONSERVAR | 0/14 | aislamiento por tenant, RLS | propia | — |
| `tests/test_pasillo_central.py` | CONSERVAR | 0/8 | ADPA y cuatro ojos | propia | — |
| `tests/test_plugin_contar_consultas.py` | CONSERVAR | 0/11 | medición de consultas | propia | — |
| `tests/test_proxy_timeout.py` | CONSERVAR | 0/1 | timeout del proxy ≥ peor caso | propia | — |
| `tests/test_reparto.py` | CONSERVAR | 0/8 | reparto | propia | — |
| `tests/test_reparto_copias.py` | CONSERVAR | 0/12 | reparto R6-R8 | propia | — |
| `tests/test_roadmap_hallazgos.py` | CONSERVAR | 0/20 | hallazgos críticos | propia | — |
| `tests/test_rol_coordinador.py` | CONSERVAR (parcial BORRAR) | 1/6 | sentido legal de «encargado del tratamiento» | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_rutas_cliente_frontend.py` | CONSERVAR | 0/2 | rutas del cliente en OpenAPI | propia | — |
| `tests/test_sec14_frontend_sin_mapas.py` | CONSERVAR | 0/8 | sin sourcemaps ni secretos | propia | — |
| `tests/test_sec15_guarda_arranque.py` | CONSERVAR (parcial FUSIONAR) | 2/14 | guarda de arranque | test_sec15_guarda_arranque.py::test_importar_main_con_produccion_sale_con_error | QA-11 |
| `tests/test_sec16_secretos_obligatorios.py` | CONSERVAR (parcial BORRAR) | 1/18 | JWT_SECRET obligatorio | test_sec16_secretos_obligatorios.py::test_api_index_en_la_nube_sin_jwt_secret_responde_503_startup_error | QA-11 |
| `tests/test_sec17_configuracion_nube.py` | CONSERVAR (parcial BORRAR) | 1/20 | configuración obligatoria | test_sec17_configuracion_nube.py::test_api_index_en_la_nube_sin_database_url_responde_503_startup_error | QA-11 |
| `tests/test_sec20_huella_cloudsql.py` | CONSERVAR (parcial BORRAR) | 1/15 | huella de la instancia de producción | test_sec20_huella_cloudsql.py::test_1_cada_variable_del_conector | QA-11 |
| `tests/test_sec23_copiloto_frontend.py` | BORRAR | 4/4 | el proxy del copiloto no fija tenant y reenvía identidad | NINGUNA — requiere prueba de comportamiento nueva (vitest de copilotProxy) | QA-11 |
| `tests/test_sec24_sin_tenant_por_defecto.py` | CONSERVAR (parcial BORRAR) | 1/4 | sin tenant por defecto | test_sec24_sin_tenant_por_defecto.py::test_headers_sin_cabecera_400 | QA-11 |
| `tests/test_seleccionar_pruebas.py` | CONSERVAR (parcial BORRAR) | 1/19 | nombre de la compuerta del CI | la protección de rama del propietario | QA-10 |
| `tests/test_servidor_humo.py` | CONSERVAR (parcial BORRAR) | 8/15 | humo como compuerta | NINGUNA — requiere prueba de comportamiento nueva | QA-10 |
| `tests/test_sin_codigo_huerfano.py` | CONSERVAR | 0/2 | sin componentes huérfanos | propia | — |
| `tests/test_sin_colores_fijos.py` | BORRAR | 1/1 | tema sin colores fijos | no aplica (estilo) | QA-10 |
| `tests/test_sin_rat_paralelo.py` | BORRAR | 1/1 | un único RAT | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_sin_respaldos_inventados.py` | BORRAR | 1/1 | la API no inventa datos | NINGUNA — requiere prueba de comportamiento nueva | QA-12 |
| `tests/test_sin_rol_antiguo.py` | FUSIONAR | 2/2 | rol antiguo rechazado | test_rol_coordinador.py::test_api_rechaza_rol_antiguo_encargado | QA-12 |
| `tests/test_sin_sql_interpolado.py` | CONSERVAR | 0/8 | sin SQL interpolado | propia | — |
| `tests/test_verificar_alcance_pr.py` | CONSERVAR (parcial BORRAR) | 1/30 | el árbitro de alcance corre en cada PR | el workflow del propietario | QA-10 |
| `tests/test_verificar_bom_huellas.py` | CONSERVAR (parcial BORRAR) | 2/11 | optimización del CI | no aplica | QA-10 |
| `tests/test_verificar_despliegue.py` | CONSERVAR | 0/11 | verificación tras desplegar | propia | — |
| `tests/test_verificar_especificaciones.py` | CONSERVAR | 0/8 | verificador de especificaciones | propia | — |
| `tests/test_vpa_map.py` | BORRAR | 3/3 | ninguna (prosa entre fichas y VPA_MAP) | no aplica | QA-10 |
