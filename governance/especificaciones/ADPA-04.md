# ADPA-04 · Retiro de deuda lateral ADPA lote 2 y cierre de `DEUDA_LATERAL = 0`
`¤sdd` `¤adpa` `¤pasillo`

## 1. Datos

Sin tablas nuevas.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Retiro total de deuda lateral.** `riesgos_mtge` y `roadmap` dejan de importar `features.diagnostico`, `features.organizacion` y `features.rat` directamente y usan `app_core/pasillo/`.
- **R2 · Invariante `DEUDA_LATERAL == 0`.** `tests/test_adpa_dependencias.py` exige que `sum(len(v) for v in DEUDA_LATERAL.values()) == 0`.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el repositorio completo, **cuando** corre `test_adpa_dependencias.py`, **entonces** `DEUDA_LATERAL` es un conjunto vacío en todas las salas y no existen imports cruzados entre salas de `features/`. | `test_deuda_lateral_total_es_cero` |

## 6. Trazabilidad

- ADR 0001 (`docs/adr/0001-pasillo-central-entre-salas.md`) y PRD §7.1 Regla 1 (`ImportsCruzados = ∅`).
