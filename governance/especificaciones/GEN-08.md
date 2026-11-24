# GEN-08 · Los comentarios del modelo de diagnóstico sin marca
`¤sdd` `¤adpa` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hecho medido en `origin/main` 6c5726e9:
- `features/diagnostico/domain/models.py:15`: el docstring de `NivelEvidencia` nombra la marca. Pasa al contrato como `description` del esquema (`hoja_de_ruta.openapi.json`, regenerado por GEN-05 en #1036).
- `models.py:27`: el comentario de `NIVELES_ASIGNADOS` nombra la marca.
- `models.py:159`: el comentario de `_NIVEL_ASIGNADO_ANTERIOR` nombra la marca para referirse a la escala anterior.

## 2. API

Ninguna ruta ni esquema cambia de forma. En el contrato solo cambia el texto de la `description` de `NivelEvidencia`: «Nivel de evidencia 0 a 4 de la escala de madurez de 1 a 5 (DIAG-08).»

## 3. Reglas

- **R1 · El vocabulario de GEN-02.** Las tres líneas dicen «escala de madurez de 1 a 5» (GEN-02 R2). La 159 habla de un resultado sellado antes de esa escala: dice «antes de la escala de madurez de 1 a 5».
- **R2 · Sin cambio de comportamiento.** Solo cambian comentarios y docstrings. Los valores de `NivelEvidencia`, `NIVELES_ASIGNADOS`, `_NIVEL_ASIGNADO_ANTERIOR` y `ESCALA_SELLADA` no cambian.
- **R3 · Contrato regenerado, no editado.** `hoja_de_ruta.openapi.json` sale de `scripts/exportar_contrato_hoja_ruta.py`, sobre main con GEN-05 ya fusionada.
- **R4 · Sin marca.** `git grep -i smartcidi` no encuentra nada en los dos archivos de la propiedad.
- **R5 · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GEN-08`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el contrato regenerado, **entonces** coincide con la aplicación. | `tests/test_contrato_hoja_ruta.py` |
| **Dado** el diagnóstico, **entonces** la escala, los resultados y las respuestas se comportan igual. | `tests/test_diagnostico_escala_1_5.py`, `tests/test_diagnostico_resultados.py`, `tests/test_diagnostico_respuestas.py` |
| **Dado** los dos archivos, **entonces** no contienen la marca. | `git grep -i -n smartcidi -- features/diagnostico/domain/models.py governance/contratos/hoja_de_ruta.openapi.json` (vacío) |

## 6. Trazabilidad

- **PRD:** ninguna decisión nueva; cierra el residuo de GEN-02 (programa GEN-01 §0).
- Pedido del Tech Lead con autorización del propietario (2026-11-24); depende de GEN-02 y GEN-05 (#1036).
