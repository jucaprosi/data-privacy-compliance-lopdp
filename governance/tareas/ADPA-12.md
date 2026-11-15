+++
id = "ADPA-12"
titulo = "Compuerta pública y pasillo modular por ficha en la sala roadmap"
ola = "indep"
estado = "pendiente"
sala = "roadmap"
depende_de = ["RM-01", "RET-03"]
propiedad = [
    "governance/especificaciones/ADPA-12.md",
    "features/roadmap/roadmap_service.py#ADPA-12",
    "features/roadmap/compuerta/**",
    "app_core/pasillo/roadmap.py#ADPA-12",
    "app_core/pasillo/roadmap_fichas/**",
    "tests/test_adpa_bulkhead.py",
    "tests/test_adpa12_compuerta_modular.py",
]
crea = []
arbitro = "python -m pytest tests/test_adpa12_compuerta_modular.py tests/test_adpa_bulkhead.py tests/test_adpa_bulkheads.py tests/test_adpa_dependencias.py tests/test_adpa06_pasillos_secciones.py; mutaciones M1 a M4 documentadas"
rastros = ["¤adpa", "¤arbitro"]
+++

# ADPA-12 · Compuerta pública y pasillo modular por ficha (Sala `roadmap`)

Especificación del Arquitecto ADPA en `governance/especificaciones/ADPA-12.md` (manda sobre esta ficha).

## Entrega
1. Crear el paquete `features/roadmap/compuerta/` y `app_core/pasillo/roadmap_fichas/`.
2. Añadir en `features/roadmap/roadmap_service.py#ADPA-12` la función `cargar_extensiones_compuerta()` para fusionar dinámicamente submódulos por ficha (`features/roadmap/compuerta/<ficha>.py`).
3. Añadir en `app_core/pasillo/roadmap.py#ADPA-12` el cargador de capacidades del pasillo por ficha.
4. Excluir `.claude` y `.gemini` en `CARPETAS_EXCLUIDAS` de `tests/test_adpa_bulkhead.py` para evitar escaneo ocioso de worktrees.
5. Crear el árbitro de mutación `tests/test_adpa12_compuerta_modular.py` (M1 a M4).

## Orden y dependencias
- Depende de `RM-01` y `RET-03` para garantizar la ortogonalidad y evitar choques de propiedad en `roadmap_service.py`.
