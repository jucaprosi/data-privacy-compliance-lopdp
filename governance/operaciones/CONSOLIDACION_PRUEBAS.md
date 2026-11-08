# Consolidación de pruebas · informe de TEST-05

Generado por `python scripts/medir_redundancia_pruebas.py informe`. Solo mide y propone: ninguna prueba se borró ni se editó. La consolidación se hace después, en una ficha por sala (TEST-05a, TEST-05b…).

## Criterio

- **Candidata:** sus líneas cubiertas están contenidas en las de otra prueba de su misma sala (la contenedora).
- **Retirar:** candidata con las mismas líneas que la contenedora y sin mutaciones exclusivas.
- **Fusionar:** candidata contenida estrictamente y sin mutaciones exclusivas.
- **Conservar:** alguna mutación exclusiva, o su docstring dice que nació por un error real, o es otra variante parametrizada de la misma función que la contenedora.
- **Pendiente de mutación:** no se le corrió mutación en esta medición; no se decide sin ella.

## Condiciones de la medición

Medición local del 2026-11-07 en Windows sin PostgreSQL 16: 1831 pruebas pasaron, 502 se saltaron y 147 fallaron o dieron error por no tener base (caen a SQLite sin archivo). Solo 499 pruebas dejan líneas Python medibles en app_core, features, api, scripts o verificadores; el resto revisa textos y archivos de gobernanza o del frontend, o corre scripts en subproceso, y no entra en la comparación por cobertura. Las salas con base se vuelven a medir con PostgreSQL 16 (entorno de CI-17) antes de cada ficha TEST-05x. Mutación: hasta 3 mutantes por candidata en todas las candidatas.

## pytest

Pruebas con cobertura medida: 499. Candidatas: 9.

### Sala `ai_copilot`

Pruebas de la sala: 13. Candidatas: 1.

| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas | Recomendación |
|---|---|---|---|---|---|
| `tests/test_implementation_assistant_provider.py::test_fallo_http_o_json_invalido_usa_respaldo_local[http]` | `tests/test_implementation_assistant_provider.py::test_deepseek_recibe_contexto_minimo_sanitizado_y_fusiona_salida` | 1/67 | 1 | ninguna | fusionar |

### Sala `api`

Pruebas de la sala: 37. Candidatas: 0.

### Sala `app_core`

Pruebas de la sala: 51. Candidatas: 0.

### Sala `auditoria_capa`

Pruebas de la sala: 5. Candidatas: 0.

### Sala `biblioteca`

Pruebas de la sala: 130. Candidatas: 1.

| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas | Recomendación |
|---|---|---|---|---|---|
| `tests/test_bib_105_editorial.py::test_maestros_reales_del_kit_pasan_validacion[AVI-01.docx]` | `tests/test_bib_105_editorial.py::test_xlsx_con_tipo_raiz_por_default_aceptado` | 2/31 | 0 | ninguna | conservar |

### Sala `derechos_arco`

Pruebas de la sala: 1. Candidatas: 0.

### Sala `diagnostico`

Pruebas de la sala: 20. Candidatas: 0.

### Sala `dpo_cockpit`

Pruebas de la sala: 6. Candidatas: 0.

### Sala `evidencias`

Pruebas de la sala: 5. Candidatas: 0.

### Sala `firma_electronica`

Pruebas de la sala: 12. Candidatas: 0.

### Sala `niif18`

Pruebas de la sala: 8. Candidatas: 0.

### Sala `notificaciones`

Pruebas de la sala: 9. Candidatas: 0.

### Sala `organizacion`

Pruebas de la sala: 9. Candidatas: 0.

### Sala `otros`

Pruebas de la sala: 2. Candidatas: 0.

### Sala `plataforma`

Pruebas de la sala: 2. Candidatas: 0.

### Sala `preanalisis`

Pruebas de la sala: 20. Candidatas: 1.

| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas | Recomendación |
|---|---|---|---|---|---|
| `tests/test_preanalisis.py::test_prompt_neutraliza_etiquetas_y_origen` | `tests/test_preanalisis.py::test_cita_verificada_conforme_e1` | 1/109 | 1 | ninguna | fusionar |

### Sala `rat`

Pruebas de la sala: 5. Candidatas: 0.

### Sala `regulacion_rag`

Pruebas de la sala: 6. Candidatas: 0.

### Sala `riesgos_mtge`

Pruebas de la sala: 10. Candidatas: 0.

### Sala `roadmap`

Pruebas de la sala: 22. Candidatas: 1.

| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas | Recomendación |
|---|---|---|---|---|---|
| `tests/test_roadmap_hallazgos.py::test_resultado_con_la_escala_nueva_usa_su_nivel_asignado` | `tests/test_roadmap_hallazgos.py::test_resultado_anterior_a_la_escala_registra_sus_hallazgos_criticos` | 1/36 | 0 | ninguna | pendiente de mutación |

### Sala `scripts`

Pruebas de la sala: 117. Candidatas: 5.

| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas | Recomendación |
|---|---|---|---|---|---|
| `tests/test_bib_108_importacion.py::test_script_importar_exige_rama_de_desarrollo_explicita[postgresql://x@rama-dev/db-args1]` | `tests/test_bib_108_importacion.py::test_script_importar_exige_rama_de_desarrollo_explicita[-args0]` | 31/31 | 3 | ninguna | conservar (variante parametrizada) |
| `tests/test_bib_108_importacion.py::test_script_importar_exige_rama_de_desarrollo_explicita[postgresql://x@rama-dev/db-args2]` | `tests/test_bib_108_importacion.py::test_script_importar_exige_rama_de_desarrollo_explicita[-args0]` | 31/31 | 3 | ninguna | conservar (variante parametrizada) |
| `tests/test_crear_organizacion_dev.py::test_sanitizar_host_oculta_credenciales` | `tests/test_sec15_guarda_arranque.py::test_crear_organizacion_dev_usa_la_huella_del_modulo` | 4/57 | 0 | ninguna | conservar |
| `tests/test_crear_organizacion_dev.py::test_validar_entorno_acepta_configuracion_correcta` | `tests/test_sec15_guarda_arranque.py::test_crear_organizacion_dev_usa_la_huella_del_modulo` | 1/57 | 0 | ninguna | conservar |
| `tests/test_medir_variacion_ci.py::test_una_prueba_que_no_llega_a_neon_no_cuenta_como_consulta` | `tests/test_medir_variacion_ci.py::test_el_registro_da_region_mediana_y_control_sin_base` | 1/15 | 0 | ninguna | pendiente de mutación |

### Sala `transferencias`

Pruebas de la sala: 1. Candidatas: 0.

### Sala `verificadores`

Pruebas de la sala: 8. Candidatas: 0.

## Playwright

Fuente de duraciones: registro del job Playwright Frontend de la corrida 42422811800 de main (2026-11-07, reporter list). Specs: 87. Duración sumada de las pruebas: 1579.3 s (suma por prueba; la corrida en paralelo tarda menos).

En Playwright no se corre mutación: basta la duración y el solapamiento de rutas.

### Sala `api`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/api/sin-respaldos.spec.ts` | 3 | 10.1 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `arco`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/arco/arco.spec.ts` | 2 | 20.2 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `asistente`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/asistente/flujo.spec.ts` | 5 | 6.4 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `auth`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/auth/identidad.spec.ts` | 12 | 56.5 | `/`, `/dashboard`, `/login` | — |
| `tests/auth/organizaciones.spec.ts` | 5 | 44.8 | `/login` | grupo 1 |
| `tests/auth/datos-por-usuario.spec.ts` | 4 | 41.7 | `/login` | grupo 1 |
| `tests/auth/operador-sin-organizacion-activa.spec.ts` | 5 | 17.9 | `/login`, `/plataforma` | — |
| `tests/auth/modo.spec.ts` | 10 | 0.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `biblioteca`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/biblioteca/documentos.spec.ts` | 7 | 51.3 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/acceso.spec.ts` | 10 | 44.1 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/catalogo.spec.ts` | 5 | 43.1 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/formularios.spec.ts` | 6 | 42.9 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/ficha.spec.ts` | 4 | 31.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/aplicabilidad.spec.ts` | 3 | 27.1 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/registro.spec.ts` | 3 | 21.3 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/tablas.spec.ts` | 3 | 20.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/vinculos.spec.ts` | 3 | 20.3 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/fichas-iniciales.spec.ts` | 2 | 16.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/concurrencia.spec.ts` | 2 | 15.8 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/descarga.spec.ts` | 2 | 14.8 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/verificacion.spec.ts` | 2 | 14.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/indicadores.spec.ts` | 3 | 13.2 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/identidad.spec.ts` | 4 | 9.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/procedencia.spec.ts` | 2 | 8.7 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/generacion.spec.ts` | 1 | 8.2 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/conservacion.spec.ts` | 1 | 7.8 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/preview.spec.ts` | 1 | 7.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/enlaces.spec.ts` | 1 | 7.0 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/impacto.spec.ts` | 1 | 4.6 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/editorial.spec.ts` | 5 | 4.1 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/biblioteca/revision.spec.ts` | 1 | 0.3 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `capa`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/capa/capa.spec.ts` | 3 | 10.2 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `conocimiento`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/conocimiento/conocimiento.spec.ts` | 3 | 11.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/conocimiento/ayuda.spec.ts` | 2 | 6.6 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `controles`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/controles/controles.spec.ts` | 4 | 13.6 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `designaciones`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/designaciones/designaciones.spec.ts` | 6 | 45.3 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `diagnostico`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/diagnostico/escala.spec.ts` | 6 | 23.5 | `/` | grupo 2 |
| `tests/diagnostico/sellado.spec.ts` | 3 | 14.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/diagnostico/persistencia.spec.ts` | 2 | 8.9 | `/` | grupo 2 |
| `tests/diagnostico/escala-activa.spec.ts` | 1 | 7.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/diagnostico/paridad.spec.ts` | 5 | 0.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `dpo`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/dpo/informe-anual.spec.ts` | 4 | 13.7 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/dpo/bitacora.spec.ts` | 3 | 10.6 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `entorno`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/entorno/aviso.spec.ts` | 12 | 9.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `ergonomia`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/ergonomia/colores-diagnostico-activa.spec.ts` | 4 | 25.2 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/ergonomia/colores-modulos.spec.ts` | 4 | 20.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/ergonomia/colores-diagnostico.spec.ts` | 6 | 19.7 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/ergonomia/dashboard-ficha.spec.ts` | 2 | 6.9 | `/` | grupo 2 |
| `tests/ergonomia/persistencia.spec.ts` | 3 | 6.9 | `/` | grupo 2 |
| `tests/ergonomia/ficha-lateral.spec.ts` | 1 | 3.9 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `estructura`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/estructura/estructura.spec.ts` | 7 | 56.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `firma`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/firma/aceptacion.spec.ts` | 6 | 15.2 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `incidentes`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/incidentes/bitacora.spec.ts` | 4 | 18.2 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `legal`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/legal/citas.spec.ts` | 4 | 7.2 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `mtge`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/mtge/calculadora.spec.ts` | 3 | 13.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/mtge/obligaciones.spec.ts` | 3 | 11.3 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `navegacion`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/navegacion/menus.spec.ts` | 3 | 14.0 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/navegacion/paleta.spec.ts` | 2 | 7.9 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/navegacion/niif.spec.ts` | 1 | 4.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `organizacion`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/organizacion/alta.spec.ts` | 6 | 28.8 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/organizacion/datos-documentales.spec.ts` | 6 | 22.0 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `plataforma`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/plataforma/plataforma.spec.ts` | 13 | 12.3 | `/invitacion`, `/plataforma` | — |

### Sala `pmv`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/pmv/sin-subida-activa.spec.ts` | 3 | 24.3 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/pmv/sin-subida.spec.ts` | 5 | 13.7 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `purga`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/purga/purga-normativa-activa.spec.ts` | 2 | 21.2 | `/` | grupo 2 |

### Sala `raiz`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/assessmentDashboard.spec.ts` | 5 | 21.9 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/commandPalette.spec.ts` | 2 | 6.8 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `rat`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/rat/validaciones.spec.ts` | 3 | 15.9 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/rat/exportacion.spec.ts` | 3 | 12.8 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/rat/plantilla.spec.ts` | 2 | 8.3 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `roadmap`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/roadmap/integracion.spec.ts` | 13 | 45.7 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/integracion-activa.spec.ts` | 7 | 45.0 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/admin.spec.ts` | 23 | 43.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/evidencia.spec.ts` | 18 | 35.1 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/olas.spec.ts` | 17 | 30.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/planeacion.spec.ts` | 8 | 23.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/e2e/criterio12_roles-activa.spec.ts` | 2 | 18.2 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/admin-colores.spec.ts` | 8 | 17.4 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/colores-hoja-de-ruta.spec.ts` | 6 | 15.3 | `/harness-roadmap/evidencia`, `/harness-roadmap/olas`, `/harness-roadmap/planeacion` | — |
| `tests/roadmap/vistas.spec.ts` | 7 | 12.5 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/e2e/criterio12_roles.spec.ts` | 1 | 6.0 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/tarjeta-colores.spec.ts` | 4 | 5.9 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/roadmap/informe.spec.ts` | 1 | 3.9 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `seguridad`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/seguridad/cabeceras.spec.ts` | 8 | 10.8 | `/` | grupo 2 |

### Sala `tableros`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/tableros/tablero.spec.ts` | 5 | 18.1 | sin `page.goto` propio (usa ayudantes) | — |

### Sala `tamano`

| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |
|---|---|---|---|---|
| `tests/tamano/ficha.spec.ts` | 8 | 22.7 | sin `page.goto` propio (usa ayudantes) | — |
| `tests/tamano/mapeo.spec.ts` | 29 | 0.1 | sin `page.goto` propio (usa ayudantes) | — |

### Specs que repiten el mismo recorrido

- Grupo 1: `tests/auth/datos-por-usuario.spec.ts`, `tests/auth/organizaciones.spec.ts` → /login
- Grupo 2: `tests/diagnostico/escala.spec.ts`, `tests/diagnostico/persistencia.spec.ts`, `tests/ergonomia/dashboard-ficha.spec.ts`, `tests/ergonomia/persistencia.spec.ts`, `tests/purga/purga-normativa-activa.spec.ts`, `tests/seguridad/cabeceras.spec.ts` → /

