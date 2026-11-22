# GCP-04b · Exclusión de la firma 942421 en Cloud Armor y registro permanente del balanceador
`¤sdd` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `governance/operaciones/cloud_load_balancer.yaml` | la regla 1000 lleva `expresion: evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 4, 'opt_out_rule_ids': ['owasp-crs-v030301-id942421-sqli']})`, y la 1001 no cambia. `evydentia-backend-bs` y `evydentia-web-bs` llevan `registro: {habilitado: true, muestreo: 1}` |
| `tests/test_gcp04b_waf_y_registro.py` (nuevo) | casos de §5 |

Hecho medido el 2026-11-22. Fuentes: el registro del balanceador, leído por el CTO con el paso 1 del brief, y `origin/main` f34d1dc1.
- A las 15:55:01 UTC, la regla 1000 (`sqli-v33-stable`) dio DENY 403 en `/api/v1/organizacion/mis-organizaciones` y en `/api/v1/plataforma/organizaciones`. La firma fue `owasp-crs-v030301-id942421-sqli`, de anomalía de caracteres SQL restringidos y nivel 4 de paranoia. Las páginas pasaron con ACCEPT; solo se bloquean las llamadas que llevan el token de Google.
- `governance/operaciones/cloud_load_balancer.yaml:12` tenía `evaluatePreconfiguredWaf('sqli-v33-stable')` sin `sensitivity`, y los servicios de backend no declaraban registro. En la nube, `logConfig` estaba vacío, así que el bloqueo no dejó rastro.
- **La firma llega por dos vías.** A las 15:55 llegó por la cabecera `Authorization: Bearer <token de Google>` de las llamadas a la API. Entre las 16:04:56 y las 16:05:01 UTC, antes de que el cambio se propagara, dio DENY en `/login` y `/favicon.ico`, en peticiones que solo llevaban cookies: la causa era la cookie de Google Identity. Por eso se excluye la firma y no se excluye la cabecera `Authorization`.
- **Expresión aplicada.** Confirmada en la nube con `rules describe 1000` y aplicada por el propietario: la de §1. Desde las 16:05:05 UTC hubo 30 ACCEPT, 0 DENY y ningún 403.
- El propietario activó el registro en los dos servicios, con muestreo 1.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Excluir la firma, no la regla.** La regla 1000 conserva la sensibilidad 4 y excluye solo `owasp-crs-v030301-id942421-sqli`. La acción sigue siendo `deny(403)`. La regla 1001 (`xss-v33-stable`) no cambia.
- **R2 · Cada exclusión tiene su evidencia.** Toda firma en `opt_out_rule_ids` aparece en §1 con la fecha, la ruta y el registro que la justifican. Una exclusión sin evidencia en esta especificación da rojo.
- **R3 · Registro permanente.** Todo servicio de `servicios_backend` lleva `registro.habilitado: true` y `registro.muestreo: 1`, para que un bloqueo de Cloud Armor quede en el registro del balanceador.
- **R4 · La nube manda en la expresión.** Si el propietario aplicó otra corrección, `governance/operaciones/cloud_load_balancer.yaml` y §1 reflejan la que aplicó. Por ejemplo, la sensibilidad 3 si salta otra firma de paranoia 4. La ficha no se fusiona con una expresión distinta de la de la nube.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-04b`).** Solo el YAML y la prueba nueva. Sin `import yaml`: se usa el lector común `tests/_lector_yaml.py`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `governance/operaciones/cloud_load_balancer.yaml`, **entonces** la regla 1000 tiene la sensibilidad 4, `opt_out_rule_ids` igual a `['owasp-crs-v030301-id942421-sqli']` y `deny(403)`. Mutación m1: volver a la expresión sin opciones da rojo. Mutación m2: añadir otra firma da rojo. | `test_regla_1000_excluye_solo_942421` |
| **Dado** la regla 1001, **entonces** sigue siendo `evaluatePreconfiguredWaf('xss-v33-stable')` con `deny(403)`. | `test_regla_1001_sin_cambios` |
| **Dado** cada firma excluida, **entonces** su id aparece en §1 de esta especificación. Mutación m3: una firma excluida sin evidencia da rojo. | `test_exclusiones_con_evidencia` |
| **Dado** `servicios_backend`, **entonces** los dos tienen `registro.habilitado: true` y `muestreo: 1`. Mutación m4: quitar el registro de uno da rojo. | `test_registro_en_todos_los_servicios` |

Comprobación del propietario, tras aplicar el cambio: `gcloud compute security-policies rules describe 1000 --security-policy evydentia-waf` muestra la misma expresión. `gcloud compute backend-services describe <bs> --global --format="value(logConfig)"` muestra `enable=True` y `sampleRate=1.0` en los dos servicios.

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-04b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Incidente del 2026-11-22, brief `governance/operaciones/BRIEF_PROPIETARIO_WAF_403_LOGIN.md` (#939). Pedido del CTO. Depende de GCP-04 y GCP-09, hechas.
