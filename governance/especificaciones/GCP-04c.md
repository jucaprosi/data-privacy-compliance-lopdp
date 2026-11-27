# GCP-04c · Cloud Armor con sensibilidad 1 en SQLi y XSS
`¤sdd` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final de `governance/operaciones/cloud_load_balancer.yaml`, en `evydentia-waf`:
- regla 1000: `expresion: "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})"`, `accion: deny(403)`;
- regla 1001: `expresion: "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})"`, `accion: deny(403)`;
- la regla 2000 (límite por IP) y la regla por defecto no cambian.

Hecho medido por el CTO el 2026-11-27, en el registro del balanceador: la regla 1000, a sensibilidad 4, dio `body_denied_by_security_policy` 5 veces en `POST /api/v1/plataforma/organizaciones`, con la firma 942200. Fue la segunda firma de paranoia alta tras la 942421 (GCP-04b).

## 2. API

No aplica.

## 3. Reglas

- **R1 · Sensibilidad 1.** Las reglas 1000 y 1001 usan sensibilidad 1, sin `opt_out_rule_ids`, y bloquean con `deny(403)`. A sensibilidad 4 cualquier cuerpo JSON parece una inyección. La defensa de fondo contra la inyección es el SQL parametrizado y la RLS.
- **R2 · La nube manda en la expresión.** El YAML refleja las expresiones que el propietario aplicó con `PROPIETARIO_WAF_SENSIBILIDAD_1.md`. La ficha no se fusiona con una expresión distinta de la de la nube.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GCP-04c`).** Solo los archivos de la propiedad. Sin `import yaml`: se usa `tests/_lector_yaml.py`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la regla 1000, **entonces** es carácter a carácter la expresión de §1 con `deny(403)`. Mutación m1: volver a la sensibilidad 4 da rojo. | `tests/test_gcp04c_waf_sensibilidad.py` |
| **Dado** la regla 1001, **entonces** es la expresión de §1 con `deny(403)`. Mutación m2: quitar su sensibilidad da rojo. | ídem |
| **Dado** las reglas 1000 y 1001, **entonces** ninguna lleva `opt_out_rule_ids`. Mutación m3: añadir una firma da rojo. | ídem |
| **Dado** `servicios_backend`, **entonces** el registro sigue como en GCP-04b. | `tests/test_gcp04b_waf_y_registro.py` |

Comprobación del propietario: `gcloud compute security-policies rules describe 1000 --security-policy evydentia-waf --project evydentia` y lo mismo con la 1001 muestran las expresiones de §1.

## 6. Trazabilidad

- Decisión del CTO del 2026-11-27, base `origin/main` a70e0ecf. Brief al propietario: `PROPIETARIO_WAF_SENSIBILIDAD_1.md`.
- Sucede a la parte de Cloud Armor de GCP-04b.
