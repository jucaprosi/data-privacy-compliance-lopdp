# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤arbitro
"""CI-39: el job `playwright` corre en 4 shards y `playwright-resultado` resume el estado (lee el workflow como texto)."""
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml"


def _job(nombre: str) -> str:
    """Texto del job de primer nivel `nombre`, hasta el siguiente job o el final."""
    texto = WORKFLOW.read_bytes().decode("utf-8")
    m = re.search(rf"^  {re.escape(nombre)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", texto, re.S | re.M)
    assert m, f"no existe el job {nombre}"
    return m.group(1)


def test_r1_matriz_de_cuatro_shards():
    job = _job("playwright")
    assert re.search(r"fail-fast:\s*false", job)
    assert re.search(r"shard:\s*\[\s*1\s*,\s*2\s*,\s*3\s*,\s*4\s*\]", job)
    assert "npx playwright test $SPECS --shard=${{ matrix.shard }}/4" in job


def test_r2_informe_por_shard():
    job = _job("playwright")
    assert "name: playwright-report-${{ matrix.shard }}" in job


def test_r4_resultado_depende_de_playwright_y_falla_si_un_shard_falla():
    job = _job("playwright-resultado")
    assert re.search(r"^    needs:\s*playwright\s*$", job, re.M)
    assert re.search(r"^    if:\s*always\(\)\s*$", job, re.M)
    assert "needs.playwright.result" in job
    assert 'test "$RESULTADO" = "success"' in job and "exit 1" in job
