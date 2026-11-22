# REG-03 · Compuertas de vectores, caché y corpus citable de la sala regulacion_rag
`¤sdd` `¤adpa` `¤vertex-cache` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `features/regulacion_rag/regulacion_rag_service.py` | sección `REG-03` con `vectorizar_fragmentos`, `regenerar_cache_normativo`, `obtener_o_crear_cache_normativo` y `corpus_citable` |
| `features/regulacion_rag/services/vertex_context_cache.py` | el creador por defecto es `app_core.pasillo.inferencia.crear_cache_contenido` (IA-12); `configurar_creador` sigue siendo el puerto de las pruebas |
| `tests/test_reg03_compuertas_corpus.py` (nuevo) | casos de §5 |

Hecho medido en `origin/main` 60b8a5e0: `app_core/pasillo/regulacion_rag.py` llama a las cuatro funciones de la compuerta (secciones `NORM-03` y `VTX-01`) y la compuerta no define ninguna:
- con `getattr` (NORM-03), el pasillo lanza `NotImplementedError` y el análisis sigue sin vectores;
- sin `getattr` (VTX-01), `vertex_cached_rag_engine` y `orquestador_diez_dimensiones` reciben `AttributeError`; el orquestador lo convierte en «NO_DISPONIBLE».

## 2. API

Funciones de la compuerta (sin rutas):
- `async vectorizar_fragmentos(textos, modelo) -> list[list[float]]`: pasa a `app_core.pasillo.inferencia.vectorizar`.
- `obtener_o_crear_cache_normativo(modelo) -> VertexCorpusCacheDescriptor`: `vertex_context_cache.obtener_o_crear(modelo)` sobre `CORPUS_NORMATIVO_OFICIAL`.
- `regenerar_cache_normativo(corpus_sha256) -> None`: si el hash difiere de la caché vigente, vacía el registro para que la próxima llamada cree otra.
- `corpus_citable() -> dict[str, dict]`: `{clave: fundamento(clave)}` de cada unidad del corpus oficial.

## 3. Reglas

- **R1 · La sala no llama al SDK.** Los vectores y la caché van por el pasillo de inferencia (IA-08 R1), nunca por `google.genai`.
- **R2 · Falla cerrada.** Sin inferencia, `obtener_o_crear_cache_normativo` lanza `ErrorNegocio(VTX_CACHE_NO_DISPONIBLE)` como hoy, y `vectorizar_fragmentos` propaga el error para que el llamador de NORM-03 siga sin vectores.
- **R3 · Corpus único.** `corpus_citable` y la caché salen del mismo `CORPUS_NORMATIVO_OFICIAL`, y el `corpus_sha256` de la caché es el de `huella_corpus` de ese corpus.
- **R-ADPA · Ortogonalidad ZERAG (`REG-03`).** Solo la sala `regulacion_rag`; ningún import cruzado, salvo `app_core.pasillo.inferencia`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el pasillo `regulacion_rag`, **entonces** las cuatro funciones responden sin `NotImplementedError` ni `AttributeError` con la inferencia simulada. Mutación m1: quitar una de la compuerta hace fallar la prueba. | `test_cuatro_compuertas_presentes` |
| **Dado** dos llamadas con el mismo modelo, **entonces** la caché se crea una vez; tras `regenerar_cache_normativo` con otro hash, se crea otra. Mutación m2: no vaciar el registro deja la caché vieja. | `test_regenerar_cache_con_otro_hash` |
| **Dado** `corpus_citable()`, **entonces** tiene una clave por unidad del corpus oficial y su hash coincide con el `corpus_sha256` de la caché. Mutación m3: tomar otro corpus hace fallar la prueba. | `test_corpus_citable_y_cache_del_mismo_corpus` |
| **Dado** NORM-03 con vectores simulados, **entonces** el análisis cuenta los vectores y el pedido de caché devuelve `pedida=True`. | `tests/test_norm03_impacto_hitl.py` |

Sin red ni `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/REG-03.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Cierra los pendientes 2 de #831 (NORM-03) y las llamadas de VTX-01 y BOV-04. Depende de IA-12, que va antes, y de NORM-03 y VTX-01, hechas.
