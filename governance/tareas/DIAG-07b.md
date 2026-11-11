+++
id = "DIAG-07b"
titulo = "Las pruebas de pytest siembran las respuestas del diagnóstico como administrador"
ola = "D"
estado = "pendiente"
sala = "pruebas"
depende_de = ["DIAG-07a", "DIAG-01", "DIAG-03", "DIAG-05", "DIAG-06", "DIAG-08", "DIAG-11", "DIAG-13", "EVI-01", "RM-21"]
propiedad = ["tests/test_diag11_prueba_y_real.py", "tests/test_diag13_evidencia_declarada.py", "tests/test_diagnostico_comparativo.py", "tests/test_diagnostico_escala_smartcidi.py", "tests/test_diagnostico_no_aplica.py", "tests/test_diagnostico_respuestas.py", "tests/test_diagnostico_resultados.py", "tests/test_evidencias_persistencia.py", "tests/test_roadmap_hallazgos.py", "tests/test_diag07b_siembra_como_admin.py"]
crea = ["tests/test_diag07b_siembra_como_admin.py"]
arbitro = "pytest de los nueve archivos contra PostgreSQL 16 local + tests/test_diag07b_siembra_como_admin.py, que recorre esos archivos y falla si un PUT a la ruta de respuestas usa el rol dpo fuera de la lista de excepciones (solo puede decrecer); mutación documentada: volver a poner dpo en un PUT de siembra hace fallar la guardia"
rastros = ["¤diagnostico"]
+++

# DIAG-07b · Las pruebas de pytest siembran las respuestas del diagnóstico como administrador

Partida el 2026-11-11 por el Arquitecto ADPA de DIAG-07 en expandir y contraer; orden: DIAG-07a → (DIAG-07b y DIAG-07c, en paralelo) → DIAG-07 → NEON-02. Borrador completo en la conversación del Arquitecto; lo que sigue es la entrega medida sobre origin/main d13d3bd6 por lectura.

## Entrega
- En cada archivo, los `PUT /diagnostico/respuestas` que solo SIEMBRAN datos pasan a `admin_organizacion`. Cambio mecánico.
- No toca los tests cuyo asunto es quién puede responder (por ejemplo `test_solo_el_dpo_responde` en `test_diagnostico_resultados.py` y el parametrizado de `test_diagnostico_respuestas.py` que comprueba 403 para otros roles): los reescribe DIAG-07. La lista de esos tests se escribe en esta ficha al empezar y es la excepción cerrada.
- Guardia propia: sin ella el cambio de rol de siembra no fallaría nunca, porque el gate transitorio de DIAG-07a todavía deja pasar al dpo.
- Dueñas previas: cinco archivos los posee NEON-02 entero (diag13, escala, respuestas, resultados y roadmap_hallazgos); NEON-02 pasa a depender de esta ficha. Mide la lista de nuevo al empezar: `tests/test_roadmap_hallazgos.py` no mostró PUT de respuestas en la lectura del Arquitecto.
