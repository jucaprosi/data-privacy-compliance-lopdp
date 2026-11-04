+++
id = "ADPA-09"
titulo = "Andamiar las salas faltantes del PRD §7.1 (features/formacion y features/conservacion) y sus pasillos"
ola = "C"
estado = "pendiente"
sala = "formacion, conservacion"
depende_de = ["ADPA-05", "ADPA-06"]
propiedad = ["features/formacion/__init__.py", "features/formacion/formacion_service.py#ADPA-09", "features/formacion/domain/__init__.py", "features/formacion/domain/errores.py#ADPA-09", "features/conservacion/__init__.py", "features/conservacion/conservacion_service.py#ADPA-09", "features/conservacion/domain/__init__.py", "features/conservacion/domain/errores.py#ADPA-09", "app_core/pasillo/formacion.py#ADPA-09", "app_core/pasillo/conservacion.py#ADPA-09", "tests/test_adpa09_salas_prd.py"]
arbitro = "pytest tests/test_adpa09_salas_prd.py tests/test_adpa_dependencias.py"
rastros = ["¤adpa", "¤implementacion", "¤conservacion"]
+++
# ADPA-09 · Andamiar las salas faltantes del PRD §7.1 (`features/formacion` y `features/conservacion`) y sus pasillos

## Entrega
- Crear `features/formacion/` (`formacion_service.py` y `domain/errores.py` con sección `#FOR-01`) y `app_core/pasillo/formacion.py` (`#FOR-01`, `#DPO-03`).
- Crear `features/conservacion/` (`conservacion_service.py` y `domain/errores.py` con sección `#CON-01`) y `app_core/pasillo/conservacion.py` (`#CON-01`, `#DPO-03`).
- Crear `tests/test_adpa09_salas_prd.py` que verifica que las 22 salas del catálogo del PRD §7.1 existen físicamente en `features/` con su compuerta canónica.

## Pruebas
- `pytest tests/test_adpa09_salas_prd.py` comprueba la correspondencia 1:1 entre `PRD.md` §7.1 y `features/<sala>/`.
