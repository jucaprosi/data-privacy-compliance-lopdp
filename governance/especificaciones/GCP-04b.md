# GCP-04b · Registro permanente del balanceador
`¤sdd` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `governance/operaciones/cloud_load_balancer.yaml` | `evydentia-backend-bs` y `evydentia-web-bs` llevan `registro: {habilitado: true, muestreo: 1}` |
| `tests/test_gcp04b_waf_y_registro.py` (nuevo) | casos de §5 |

Hecho medido el 2026-11-22. Fuentes: el registro del balanceador, leído por el CTO con el paso 1 del brief, y `origin/main` f34d1dc1.
- Los servicios de backend no declaraban registro. En la nube, `logConfig` estaba vacío, así que un bloqueo de Cloud Armor no dejaba rastro.
- El propietario activó el registro en los dos servicios, con muestreo 1.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Reglas del WAF.** Las reglas de `evydentia-waf` son las de GCP-04c.
- **R3 · Registro permanente.** Todo servicio de `servicios_backend` lleva `registro.habilitado: true` y `registro.muestreo: 1`, para que un bloqueo de Cloud Armor quede en el registro del balanceador.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-04b`).** Solo el YAML y la prueba nueva. Sin `import yaml`: se usa el lector común `tests/_lector_yaml.py`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `servicios_backend`, **entonces** los dos tienen `registro.habilitado: true` y `muestreo: 1`. Mutación m4: quitar el registro de uno da rojo. | `test_registro_en_todos_los_servicios` |

Comprobación del propietario, tras aplicar el cambio: `gcloud compute backend-services describe <bs> --global --format="value(logConfig)"` muestra `enable=True` y `sampleRate=1.0` en los dos servicios.

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-04b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Incidente del 2026-11-22, brief `governance/operaciones/BRIEF_PROPIETARIO_WAF_403_LOGIN.md` (#939). Pedido del CTO. Depende de GCP-04 y GCP-09, hechas.
