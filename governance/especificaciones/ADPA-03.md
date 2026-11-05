# ADPA-03 · Retiro de deuda lateral ADPA lote 1 vía pasillo
`¤sdd` `¤adpa` `¤pasillo`

## 1. Datos

Sin tablas nuevas. Contratos tipados en `app_core/pasillo/{evidencias,organizacion,roadmap,niif18}.py`.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Pasillo tipado (ADR 0001).** `auditoria_capa`, `plataforma`, `rat` y `ai_copilot` consumen otras salas únicamente mediante `app_core/pasillo/<sala>.py`.
- **R2 · Deuda lateral cero en las 4 salas.** Los archivos `tests/deuda_adpa/{auditoria_capa,plataforma,rat,ai_copilot}.txt` quedan sin aristas.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el conjunto de salas `auditoria_capa`, `plataforma`, `rat` y `ai_copilot`, **cuando** corre `test_adpa_dependencias.py`, **entonces** ninguna tiene imports directos a otra sala y sus archivos en `tests/deuda_adpa/` están vacíos. | `test_salas_no_importan_otras_salas` |

## 6. Trazabilidad

- ADR 0001 (`docs/adr/0001-pasillo-central-entre-salas.md`) y PRD §7.1 Regla 1.
