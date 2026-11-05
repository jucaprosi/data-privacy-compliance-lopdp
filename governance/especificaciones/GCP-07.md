# GCP-07 · Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract)
`¤sdd` `¤versionado-despliegue` `¤grado-productivo` `¤cloud-run-perf` `¤ci-cd`

## 1. Datos

Escalón `EscalonTrafico` (`porcentaje: int`, `observacion_min: int`). Política `PoliticaReversion` (`metrica: disponibilidad | tasa_5xx`, `umbral: float`). Hallazgo `HallazgoMigracion` (`migracion: str`, `operacion: str`, `objeto: str`).

## 2. API

- Sin rutas: el verificador se ejecuta como `python scripts/verificar_migracion_compatible.py [--base origin/main]` con código 1 si hay operaciones incompatibles.

## 3. Reglas

- **R1 · Escalones crecientes.** Los porcentajes de tráfico son estrictamente crecientes y el último es 100.
- **R2 · Reversión por SLO (`INV_PROGRESSIVE_DELIVERY_EXPAND_CONTRACT`).** Si un escalón incumple el SLO de disponibilidad o de 5xx, el tráfico vuelve a la revisión anterior sin intervención manual.
- **R3 · Migraciones compatibles.** Una migración no borra ni renombra en el mismo paso un objeto que la revisión anterior usa; primero se añade, luego se migra y al final se retira.

## 4. Interfaz

Sin cambios visibles: las publicaciones dejan de interrumpir a los usuarios.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el manifiesto `despliegue_progresivo.yaml`, **cuando** se valida, **entonces** cada servicio tiene escalones crecientes hasta 100 % y una condición de reversión. | `test_escalones_y_reversion_definidos` |
| **Dado** una migración de ejemplo que borra una columna en uso, **cuando** se ejecuta el verificador, **entonces** devuelve código 1 con el hallazgo de la operación destructiva. | `test_rechaza_migracion_destructiva` |
| **Dado** una migración de ejemplo que solo añade una columna anulable, **cuando** se ejecuta el verificador, **entonces** no hay hallazgos. | `test_acepta_migracion_aditiva` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §5.4 pilar 3 y criterio 31; invariante `INV_PROGRESSIVE_DELIVERY_EXPAND_CONTRACT`.
