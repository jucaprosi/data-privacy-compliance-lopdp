# SEC-23b · El asistente pasa la organización autenticada al tope de inferencia
`¤sdd` `¤seguridad-tenant`

## 1. Datos

Sin tablas ni migraciones. Cambia un argumento que hoy no se pasa:

- `api/routers/implementation_assistant.py` ya obtiene la organización autenticada con `obtener_tenant_id_actual` (SEC-23), pero la descarta (`_tenant_id`) y llama a `responder_implementacion(segura, guias, fuentes, CORPUS_VERSION)` sin organización.
- `responder_implementacion` y `enriquecer_implementacion` aceptan `org_id` opcional (IA-07). Sin él, el asistente usa el respaldo local y no llama a la compuerta de inferencia.

## 2. API

`POST /…/consulta` del asistente no cambia de contrato. Cambia su comportamiento con una organización autenticada: la consulta puede enriquecerse por la compuerta de inferencia y consume el tope de esa organización.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 401 o 403 | (dependencia de autenticación) | sin token, o sin membresía en la organización de la cabecera (SEC-23) |
| 429 | el del tope de la compuerta | la organización agotó su tope: el asistente responde con el respaldo local y un aviso neutro, no con un error |

## 3. Reglas

- **R1 · La organización es la autenticada.** El `org_id` que llega a la compuerta es el que devolvió `obtener_tenant_id_actual`, ya verificado contra el token y la membresía. Nunca sale del cuerpo ni de una cabecera sin verificar.
- **R2 · Cada organización gasta su tope.** Una consulta de la organización A consume el tope de A y ninguno de B.
- **R3 · Sin organización, respaldo local.** Si `org_id` falta, no se llama a la compuerta y no se consume ningún tope (comportamiento de IA-07, que no cambia).
- **R4 · Tope agotado o compuerta caída.** El asistente responde con el respaldo local y un aviso neutro que no nombra al proveedor ni el motivo técnico.
- **R5 · Nada más cambia.** El saneamiento de la consulta, las guías y las fuentes siguen igual.
- **R-ADPA · Ortogonalidad ZERAG (`SEC-23b`).** La compuerta de inferencia, por su pasillo.

## 4. Interfaz

No aplica: la pantalla del copiloto no cambia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una consulta autenticada de la organización A, **entonces** la compuerta recibe `org_id = A` y se consume una generación del tope de A. Mutación: pasar `org_id=None` con una organización autenticada hace fallar la prueba. | `test_consulta_consume_el_tope_de_su_organizacion` |
| **Dado** consultas de A y de B, **entonces** cada una consume solo su tope. | `test_topes_separados_por_organizacion` |
| **Dado** un cuerpo que trae otro identificador de organización, **entonces** se ignora: manda la organización autenticada. Mutación: tomarlo del cuerpo hace fallar la prueba. | `test_org_no_sale_del_cuerpo` |
| **Dado** el tope de A agotado, **entonces** la respuesta es 200 con el respaldo local y el aviso neutro. | `test_tope_agotado_respaldo_local` |

Todas en `tests/test_sec23b_asistente_org.py`, con el doble de la compuerta y del consumidor del tope, sin red y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/SEC-23b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Decisión del CTO (2026-11-13). Depende de SEC-23 e IA-07, las dos en curso.
- **Propiedad que falta en la ficha**, medida en `origin/main` 4eca5af2: `api/routers/implementation_assistant.py`. El cambio principal es en el router, que hoy posee SEC-23 (en curso): se añade a la propiedad de SEC-23b cuando SEC-23 esté fusionada. La ficha solo lista `implementation_assistant.py` de la sala, que ya acepta `org_id` y probablemente no necesita cambios.
- Falta también `tests/matriz/SEC-23b.py` solo si cambian los roles de la ruta; no cambian, así que no hace falta.
- **Bloqueo del árbitro:** `scripts/verificar_especificaciones.py` rechaza el sufijo «b».
