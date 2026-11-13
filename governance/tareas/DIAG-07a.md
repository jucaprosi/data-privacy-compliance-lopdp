+++
id = "DIAG-07a"
titulo = "El administrador puede guardar respuestas del diagnóstico (escritura transitoria)"
ola = "D"
estado = "en_curso"
sala = "diagnostico"
depende_de = ["ADPA-05", "DIAG-01", "DIAG-03", "DIAG-05", "DIAG-08"]
propiedad = ["api/routers/diagnostico_respuestas.py", "tests/test_diagnostico_escritura_transitoria.py", "tests/test_diagnostico_resultados.py"]
crea = ["tests/test_diagnostico_escritura_transitoria.py"]
arbitro = "pytest tests/test_diagnostico_escritura_transitoria.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite de diagnóstico y vigilantes; mutación documentada: quitar admin_organizacion del gate hace fallar la primera prueba y quitar dpo, la segunda"
rastros = ["¤diagnostico"]
+++

# DIAG-07a · El administrador puede guardar respuestas del diagnóstico (escritura transitoria)

Partida el 2026-11-11 por el Arquitecto ADPA de DIAG-07 en expandir y contraer; orden: DIAG-07a → (DIAG-07b y DIAG-07c, en paralelo) → DIAG-07 → NEON-02. Borrador completo en la conversación del Arquitecto; lo que sigue es la entrega medida sobre origin/main d13d3bd6 por lectura.

## Entrega
- `_escritura = require_role("dpo", "admin_organizacion")` en `api/routers/diagnostico_respuestas.py`, con un comentario que dice que es transitorio y que lo estrecha DIAG-07. Nada más cambia en el handler. Es el paso «expandir».
- Esta ficha es dueña entera de `api/routers/diagnostico_respuestas.py` (la única ficha viva que lo posee); DIAG-07 lo toma después.

## Pruebas
- El administrador guarda y el dpo sigue guardando; el implementador y el coordinador reciben 403.
- Mutación: quitar `admin_organizacion` del gate hace fallar la primera prueba; quitar `dpo`, la segunda.
- **Una línea de una prueba ajena (propiedad ampliada por el Tech Lead, 2026-11-12, a petición de la sesión):** `tests/test_diagnostico_resultados.py:174` (`test_solo_el_dpo_responde[admin]`) fija `admin_organizacion` = 403 en `PUT /diagnostico/respuestas` y falla con la expansión de esta ficha. DIAG-07a quita `admin` de esa parametrización (una línea) y deja en el código el motivo y la referencia a DIAG-07, que reescribe esas pruebas con la regla definitiva (no se toca nada más del archivo; las demás pruebas de quién puede responder siguen para DIAG-07).
