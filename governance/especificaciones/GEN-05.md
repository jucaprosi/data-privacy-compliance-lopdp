# GEN-05 · Contrato OpenAPI regenerado tras la escala y la Biblioteca sin marca
`¤sdd` `¤adpa` `¤arbitro`

## 1. Datos

Programa: GEN-01 §0. Hecho medido en `origin/main` ea6d26bf: `hoja_de_ruta.openapi.json` contiene el nombre de la marca en tres `description` (`:36782`, `:38977` y `:39147`) y en un `enum` (`:37833`, la fuente de plantillas). `tests/test_contrato_hoja_ruta.py` no compara `enum` ni `description`, así que no detecta la diferencia: por eso la regeneración es una ficha y no un efecto del CI.

## 2. API

Sin cambios: el archivo refleja la API que dejan GEN-02 y GEN-03.

## 3. Reglas

- **R1 · Se regenera, no se edita.** `python scripts/exportar_contrato_hoja_ruta.py`, sobre `origin/main` con GEN-02 y GEN-03 fusionadas. El diff solo contiene lo que cambiaron esas dos fichas y lo que otras fichas añadieron desde la última regeneración. Las adiciones de otras fichas se anotan en el PR.
- **R2 · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GEN-05`).** Solo el contrato.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el contrato regenerado, **entonces** `tests/test_contrato_hoja_ruta.py` pasa y el `enum` de la fuente es `["catalogo", "organizacion"]`. Mutación m1: editar el `enum` a mano con otro valor y volver a ejecutar el exportador lo restaura. | `tests/test_contrato_hoja_ruta.py` |

## 6. Trazabilidad

- Programa GEN-01 §0. Depende de GEN-02 y GEN-03, y de MARCA-01, la última ficha que regeneró el contrato.
