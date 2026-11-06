# ADPA-02 · Reubicación de `ErrorNegocio` en `app_core/errors.py` y prohibición `features -> api`
`¤sdd` `¤adpa` `¤errores`

## 1. Datos

Sin tablas nuevas. Contrato transversal en `app_core/errors.py`.

## 2. API

Sin endpoints nuevos. `api/errores.py` reexporta `ErrorNegocio` desde `app_core.errors` y mantiene intacto el formato HTTP de respuesta de error.

## 3. Reglas

- **R1 · Definición en cimiento (`app_core/errors.py`).** `ErrorNegocio` vive en `app_core/errors.py` junto a `CodigoErrorNegocio` y `CATALOGO_ERRORES`.
- **R2 · Prohibición de inversión de capas (`features/ -> api/`).** Ningún módulo de `features/<sala>/**` puede importar `api` ni `api.*`.

## 4. Interfaz

Sin cambios visuales en el Frontend.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol de `features/`, **cuando** el verificador AST inspecciona todos los imports de las salas, **entonces** ningún archivo importa `api` ni `api.*` y `ErrorNegocio` proviene de `app_core.errors`. | `test_ninguna_sala_importa_capa_api` |

## 6. Trazabilidad

- PRD §7.1 Regla 3 (`api/ -> features/<sala>/ -> app_core/ -> db/`).
