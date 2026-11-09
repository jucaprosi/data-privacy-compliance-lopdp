+++
id = "ADPA-09"
titulo = "Andamiar las salas faltantes del PRD §7.1 (features/formacion y features/conservacion) y sus pasillos"
ola = "C"
estado = "en_curso"
sala = "formacion, conservacion"
depende_de = ["ADPA-05", "ADPA-06"]
propiedad = ["features/formacion/__init__.py", "features/formacion/formacion_service.py", "features/formacion/domain/__init__.py", "features/formacion/domain/errores.py", "features/conservacion/__init__.py", "features/conservacion/conservacion_service.py", "features/conservacion/domain/__init__.py", "features/conservacion/domain/errores.py", "app_core/pasillo/formacion.py", "app_core/pasillo/conservacion.py", "tests/test_adpa09_salas_prd.py"]
crea = ["features/formacion/__init__.py", "features/formacion/formacion_service.py", "features/formacion/domain/__init__.py", "features/formacion/domain/errores.py", "features/conservacion/__init__.py", "features/conservacion/domain/__init__.py", "tests/test_adpa09_salas_prd.py", "features/conservacion/conservacion_service.py", "features/conservacion/domain/errores.py", "app_core/pasillo/formacion.py", "app_core/pasillo/conservacion.py"]
siembra = ["features/conservacion/conservacion_service.py#CON-01", "features/conservacion/domain/errores.py#CON-01", "app_core/pasillo/conservacion.py#CON-01", "app_core/pasillo/conservacion.py#DPO-03", "app_core/pasillo/conservacion.py#GOVW-01", "app_core/pasillo/formacion.py#DPO-03", "app_core/pasillo/formacion.py#FOR-01"]
arbitro = "pytest tests/test_adpa09_salas_prd.py tests/test_adpa_dependencias.py"
rastros = ["¤adpa", "¤implementacion", "¤conservacion"]
+++
# ADPA-09 · Andamiar las salas faltantes del PRD §7.1 (`features/formacion` y `features/conservacion`) y sus pasillos

## Entrega
- **Dueña del archivo entero (Tech Lead, 2026-11-07, regla: quien crea un archivo es dueña de todo el archivo y siembra las marcas de las fichas posteriores):** andamia la sala `features/formacion/` y es dueña de `__init__.py`, `formacion_service.py` y `domain/errores.py`. Deja sembrado el par vacío `# === FOR-01 ===` / `# === fin FOR-01 ===` en `formacion_service.py` y en `domain/errores.py`.
- Crear `features/formacion/` (`formacion_service.py` y `domain/errores.py` con sección `#FOR-01`) y `app_core/pasillo/formacion.py` (`#FOR-01`, `#DPO-03`).
- Crear `features/conservacion/` (`conservacion_service.py` y `domain/errores.py` con sección `#CON-01`) y `app_core/pasillo/conservacion.py` (`#CON-01`, `#DPO-03`).
- Crear `tests/test_adpa09_salas_prd.py` que verifica que las 22 salas del catálogo del PRD §7.1 existen físicamente en `features/` con su compuerta canónica.

## Pruebas
- `pytest tests/test_adpa09_salas_prd.py` comprueba la correspondencia 1:1 entre `PRD.md` §7.1 y `features/<sala>/`.

**Creación y siembra (Tech Lead, 2026-11-09, a pedido del ingeniero).** `conservacion_service.py`, `conservacion/domain/errores.py`, `app_core/pasillo/formacion.py` y `app_core/pasillo/conservacion.py` no existen en main. ADPA-09 los crea con su sección `#ADPA-09` y siembra las secciones vacías de CON-01, DPO-03, FOR-01 y GOVW-01, que dependen de ella.
