+++
id = "GEN-08"
titulo = "Los comentarios del modelo de diagnóstico sin marca y el contrato OpenAPI regenerado encima de GEN-05"
ola = "backlog"
estado = "en_curso"
tanda = 102
sala = "plataforma"
depende_de = ["GEN-02", "GEN-05", "CI-38"]
propiedad = ["features/diagnostico/domain/models.py", "governance/contratos/hoja_de_ruta.openapi.json"]
crea = []
arbitro = "python scripts/exportar_contrato_hoja_ruta.py; pytest tests/test_contrato_hoja_ruta.py tests/test_diagnostico_escala_1_5.py tests/test_diagnostico_resultados.py tests/test_diagnostico_respuestas.py; git grep -i -n smartcidi -- features/diagnostico/domain/models.py governance/contratos/hoja_de_ruta.openapi.json (vacío)."
rastros = ["¤adpa", "¤arbitro"]
+++

# GEN-08 · Los comentarios del modelo de diagnóstico sin marca

**Contrato:** `governance/especificaciones/GEN-08.md` (manda sobre esta ficha).

**Origen.** Pedido del Tech Lead con autorización del propietario (2026-11-24). GEN-02 dejó la marca en tres comentarios de `features/diagnostico/domain/models.py` (líneas 15, 27 y 159), y el contrato regenerado de GEN-05 (#1036) la hereda en una `description`.

## Entrega
- Las tres líneas de `models.py` con el vocabulario de GEN-02: «escala de madurez de 1 a 5» y, para la anterior, «escala anterior».
- `hoja_de_ruta.openapi.json` regenerado con `scripts/exportar_contrato_hoja_ruta.py` encima de GEN-05.

## Límites
- Solo comentarios y docstrings: no cambia el comportamiento, los valores ni la forma del esquema. En el contrato solo cambia el texto de la `description` que sale de ese docstring.
- El contrato no se edita a mano. GEN-05 se fusiona primero.
