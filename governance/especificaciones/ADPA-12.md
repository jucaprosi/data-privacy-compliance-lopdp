# ADPA-12 · Compuerta y Pasillo Modular por Ficha (Sala Piloto: `roadmap`)
`¤sdd` `¤adpa` `¤arbitro`

## 1. Datos
Sin tablas ni migraciones nuevas.

## 2. API
Sin rutas nuevas.

## 3. Reglas

- **R1 · Carga determinista por módulo de ficha.** La compuerta canónica `features/roadmap/roadmap_service.py` conserva su historial intacto y descubre automáticamente en tiempo de importación los módulos en `features/roadmap/compuerta/<ID>.py` en orden alfabético.
- **R2 · Contrato estricto de exportación (`__all__`).** Todo submódulo de compuerta debe definir `__all__` no vacío con cadenas válidas. La ausencia o vacuidad de `__all__` detiene la importación (`ValueError`).
- **R3 · Protección contra colisiones y reemplazo explícito (`REEMPLAZA`).** Si dos fichas exportan el mismo identificador con objetos distintos, la compuerta lanza `ValueError`, a menos que el submódulo declare `REEMPLAZA = ("<nombre>",)` y su ficha declare `depende_de` hacia la ficha dueña original.
- **R4 · Delegación modular en Pasillo Central.** `app_core/pasillo/roadmap.py` carga análogamente `app_core/pasillo/roadmap_fichas/<ID>.py`. Ningún archivo en `roadmap_fichas/` puede tener `import features...` en el nivel superior (debe ser importación local dentro de cada función, según invariante ADPA §3 / ADPA-06).

## 4. Interfaz
Sin interfaz gráfica.

## 5. Aceptación y Mutaciones

| Escenario | Prueba |
| :--- | :--- |
| **Dado** submódulos válidos en `features/roadmap/compuerta/`, **cuando** se importa `roadmap_service`, **entonces** todos sus símbolos públicos están disponibles en el módulo y en `__all__`. | `test_adpa12_compuerta_modular.py::test_carga_nominal_submodulos` |
| **Dado** un submódulo sin `__all__`, **cuando** se carga la compuerta, **entonces** lanza `ValueError` (M1). | `test_adpa12_compuerta_modular.py::test_mutacion_sin_all_falla` |
| **Dado** dos submódulos que exportan el mismo símbolo sin `REEMPLAZA`, **cuando** se carga la compuerta, **entonces** lanza `ValueError` por colisión (M2). | `test_adpa12_compuerta_modular.py::test_mutacion_colision_accidental_falla` |
| **Dado** un submódulo con `REEMPLAZA`, **cuando** sustituye un símbolo existente, **entonces** se aplica y conserva la cadena de invocación (M3). | `test_adpa12_compuerta_modular.py::test_reemplazo_explicito_valido` |
| **Dado** cualquier archivo en `app_core/pasillo/roadmap_fichas/`, **cuando** corre el linter AST, **entonces** ninguno importa `features` en el nivel superior (M4). | `test_adpa12_compuerta_modular.py::test_pasillo_cero_imports_top_level_features` |

## 6. Trazabilidad
- Pilar Constitucional ADPA (Mamparos Estancos y Ortogonalidad de Tareas).
- ADR 0001 (`docs/adr/0001-pasillo-central-entre-salas.md`).
