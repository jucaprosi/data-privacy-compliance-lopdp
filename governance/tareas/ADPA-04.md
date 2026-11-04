+++
id = "ADPA-04"
titulo = "Retirar deuda lateral ADPA lote 2 (riesgos_mtge, roadmap) y sellar DEUDA_LATERAL = 0"
ola = "C"
estado = "pendiente"
sala = "riesgos_mtge, roadmap"
depende_de = ["ADPA-03", "DIAG-08"]
propiedad = ["app_core/pasillo/rat.py#ADPA-04", "app_core/pasillo/organizacion.py#ADPA-04", "features/riesgos_mtge/riesgos_mtge_service.py#ADPA-04", "features/roadmap/generador_service.py#ADPA-04", "features/roadmap/recalculo_service.py#ADPA-04", "features/roadmap/roadmap_service.py#ADPA-04", "tests/deuda_adpa/riesgos_mtge.txt", "tests/deuda_adpa/roadmap.txt", "tests/test_adpa_dependencias.py#ADPA-04"]
arbitro = "pytest tests/test_adpa_dependencias.py + suite completa"
rastros = ["¤adpa"]
+++
# ADPA-04 · Retirar deuda lateral ADPA lote 2 (`riesgos_mtge`, `roadmap`) y sellar `DEUDA_LATERAL = 0`

## Entrega
- Crear `app_core/pasillo/rat.py` y completar `app_core/pasillo/organizacion.py#ADPA-04`.
- Redirigir los imports laterales de `riesgos_mtge` y `roadmap` hacia `app_core/pasillo/{diagnostico,organizacion,rat}.py`.
- Vaciar `tests/deuda_adpa/{riesgos_mtge,roadmap}.txt` y sellar `DEUDA_LATERAL == 0` en `tests/test_adpa_dependencias.py#ADPA-04`.

## Pruebas
- `pytest tests/test_adpa_dependencias.py` verifica que las 22 salas tienen 0 aristas laterales (`ImportsCruzados = ∅`).
