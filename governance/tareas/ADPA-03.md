+++
id = "ADPA-03"
titulo = "Retirar deuda lateral ADPA lote 1 (auditoria_capa, plataforma, rat, ai_copilot) vía pasillo"
ola = "C"
estado = "hecha"
sala = "auditoria_capa, plataforma, rat, ai_copilot"
depende_de = ["ADPA-02"]
propiedad = [
  "app_core/pasillo/evidencias.py#ADPA-03",
  "app_core/pasillo/organizacion.py#ADPA-03",
  "app_core/pasillo/roadmap.py#ADPA-03",
  "app_core/pasillo/niif18.py#ADPA-03",
  "features/ai_copilot/services/inference_engine.py#ADPA-03",
  "features/auditoria_capa/services/controles_engine.py#ADPA-03",
  "features/plataforma/services/operador_engine.py#ADPA-03",
  "features/rat/services/plantilla_engine.py#ADPA-03",
  "tests/deuda_adpa/auditoria_capa.txt",
  "tests/deuda_adpa/plataforma.txt",
  "tests/deuda_adpa/rat.txt",
  "tests/deuda_adpa/ai_copilot.txt",
  "tests/test_adpa_dependencias.py#ADPA-03"
]
arbitro = "pytest tests/test_adpa_dependencias.py + suite completa"
rastros = ["¤adpa", "¤pasillo"]
+++
# ADPA-03 · Retirar deuda lateral ADPA lote 1 (`auditoria_capa`, `plataforma`, `rat`, `ai_copilot`) vía pasillo

## Entrega
- Crear los módulos de pasillo tipados `app_core/pasillo/{evidencias,organizacion,roadmap,niif18}.py` conforme a ADR 0001.
- Redirigir los imports laterales de `auditoria_capa`, `plataforma`, `rat` y `ai_copilot` hacia `app_core/pasillo/`.
- Vaciar `tests/deuda_adpa/{auditoria_capa,plataforma,rat,ai_copilot}.txt`.

## Pruebas
- `pytest tests/test_adpa_dependencias.py` con 0 aristas en las 4 salas.
