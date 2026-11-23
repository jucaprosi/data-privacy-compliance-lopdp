+++
id = "LEG-06"
titulo = "Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = ["CI-19", "CI-22", "CI-23", "CI-25", "CI-26", "CI-29", "CI-31", "CI-36", "GCP-07", "PRD-01", "PRD-03", "QA-11", "RET-05", "RET-09"]
propiedad = ["LICENSE", "frontend/package.json", "scripts/poner_aviso_de_autor.py", "scripts/verificar_alcance_pr.py", "tests/test_verificar_alcance_pr.py", "tests/test_leg06_aviso_de_autor.py"]
crea = ["LICENSE", "scripts/poner_aviso_de_autor.py", "tests/test_leg06_aviso_de_autor.py"]
transversal = "aviso-de-autor"
arbitro = "pytest tests/test_leg06_aviso_de_autor.py tests/test_verificar_alcance_pr.py; python -m compileall -q .; npx tsc --noEmit y npm run lint en frontend; arnés completo; verificar_alcance_pr, reparto, índice y especificaciones con código 0; mutaciones m1 a m5."
rastros = ["¤ip", "¤arbitro"]
+++

# LEG-06 · Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado

**Contrato:** `governance/especificaciones/LEG-06.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO, aprobado por el propietario el 2026-11-22. El repositorio es público y no tiene `LICENSE`. De 2.506 archivos, solo `AGENTS.md` lleva aviso de autor.

## Entrega
- `LICENSE` propietario en la raíz y `"license": "UNLICENSED"` en `frontend/package.json`.
- La línea de aviso al inicio de cada archivo de código versionado, puesta por un script y vigilada por una prueba.
- Una regla de alcance transversal: el PR toca archivos fuera de la propiedad solo para añadir esa línea.

## Límites
- `.github/` queda fuera: los workflows son del propietario y CI-37 está sobre ese archivo.
- Se lanza sola, al final de una tanda (R6).
