# GCP-02 · Test Impact Analysis (TIA) Determinista por Grafo ADPA
`¤sdd` `¤cloud-run-perf` `¤adpa` `¤arbitro`

## 1. Datos

Estructura `ImpactoPruebasADPA` en `app_core/cloud/tia_adpa_selector.py` (`salas_afectadas: list[str]`, `archivos_pytest: list[str]`, `requiere_frontend_build: bool`, `playwright_shards: int`).

## 2. API

- CLI y función pura `calcular_impacto_adpa(archivos_diff: Sequence[str]) -> ImpactoPruebasADPA`.

## 3. Reglas

- **R1 · Aislamiento backend vs. frontend.** Si ningún archivo del diff pertenece a `frontend/` ni a contratos consumidos por el cliente web, `requiere_frontend_build` es `False`.
- **R2 · Propagación por pasillo central.** Si un archivo modificado es `app_core/pasillo/<sala>.py#<ID>`, se seleccionan las pruebas de `<sala>` y de la sala dueña de `<ID>`.
- **R3 · Fallback seguro ante cambio transversal.** Si el diff toca `app_core/db/` o `alembic/`, se marca ejecución completa sin omisiones.

## 4. Interfaz

Sin interfaz gráfica; herramienta de aceleración de verificación local y CI para los 32 flujos paralelos de agentes.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un diff que modifica únicamente `features/conservacion/conservacion_service.py`, **cuando** se invoca `calcular_impacto_adpa`, **entonces** devuelve `tests/test_con01_conservacion.py` y `requiere_frontend_build = False`. | `test_tia_cambio_aislado_sala_omite_frontend` |
| **Dado** un diff que modifica `app_core/db/session.py`, **cuando** se invoca `calcular_impacto_adpa`, **entonces** activa el modo transversal completo. | `test_tia_cambio_nucleo_activa_suite_completa` |

## 6. Trazabilidad

- PRD §8.4 y `VPA_MAP.md` (`¤cloud-run-perf`, `¤arbitro`).
