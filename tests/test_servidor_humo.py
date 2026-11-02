# -*- coding: utf-8 -*-
# ¤arbitro ¤seguridad
"""El arrancador de humo vive solo en pruebas y se detiene ante un despliegue o ante producción."""
import ast
import importlib.util
import inspect
import re
from pathlib import Path

import pytest

from app_core import security

RAIZ = Path(__file__).resolve().parents[1]
RUTA_ARRANCADOR = RAIZ / "tests" / "humo" / "servidor_humo.py"
CARPETAS_DESPLEGADAS = ("api", "app_core", "features", "alembic", "scripts")
ARCHIVOS_DE_DESPLIEGUE = ("vercel.json", "backend.Dockerfile", "docker-compose.yml", "iniciar_backend.bat")


def cargar_arrancador():
    spec = importlib.util.spec_from_file_location("servidor_humo", RUTA_ARRANCADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ENTORNO_VALIDO = {
    "HUMO_E2E": "1",
    "DATABASE_URL": "postgresql://rama-de-prueba/lopdp",
    "GOOGLE_CLIENT_ID": "humo-ci",
    "HUMO_CLAVE_PRIVADA": "clave.pem",
}


def test_arranca_solo_con_el_entorno_completo_de_humo():
    assert cargar_arrancador().rechazo_de_entorno(ENTORNO_VALIDO) is None


@pytest.mark.parametrize("cambio, motivo", [
    ({"VERCEL": "1"}, "Vercel"),
    ({"VERCEL_ENV": "production"}, "Vercel"),
    ({"DATABASE_URL": "postgresql://ep-late-hall-b50bpbk5/lopdp"}, "producción"),
    ({"TEST_DATABASE_URL": "postgresql://ep-late-hall-b50bpbk5/lopdp"}, "producción"),
    ({"MIGRATION_DATABASE_URL": "postgresql://ep-late-hall-b50bpbk5/lopdp"}, "producción"),
    ({"HUMO_E2E": "0"}, "HUMO_E2E"),
    ({"DATABASE_URL": ""}, "DATABASE_URL"),
    ({"GOOGLE_CLIENT_ID": ""}, "GOOGLE_CLIENT_ID"),
    ({"HUMO_CLAVE_PRIVADA": ""}, "HUMO_CLAVE_PRIVADA"),
])
def test_se_detiene_ante_un_despliegue_produccion_o_entorno_incompleto(cambio, motivo):
    assert motivo in cargar_arrancador().rechazo_de_entorno({**ENTORNO_VALIDO, **cambio})


def test_en_vercel_el_proceso_termina_sin_generar_clave(monkeypatch, tmp_path, capsys):
    arrancador = cargar_arrancador()
    clave = tmp_path / "clave.pem"
    for nombre, valor in {**ENTORNO_VALIDO, "HUMO_CLAVE_PRIVADA": str(clave), "VERCEL": "1"}.items():
        monkeypatch.setenv(nombre, valor)
    assert arrancador.main() == 1
    assert not clave.exists()
    assert "Vercel" in capsys.readouterr().err


def test_importarlo_no_toca_la_verificacion_de_google():
    original = security._clave_de_firma
    cargar_arrancador()
    assert security._clave_de_firma is original


def test_ningun_codigo_desplegado_lo_nombra():
    fuentes = [RAIZ / "main.py", *(p for c in CARPETAS_DESPLEGADAS for p in (RAIZ / c).rglob("*.py"))]
    fuentes += [RAIZ / nombre for nombre in ARCHIVOS_DE_DESPLIEGUE if (RAIZ / nombre).exists()]
    nombrado = [str(f.relative_to(RAIZ)) for f in fuentes if "servidor_humo" in f.read_text(encoding="utf-8")]
    assert nombrado == []


def test_ningun_codigo_desplegado_importa_de_tests():
    fuentes = [RAIZ / "main.py", *(p for c in ("api", "app_core", "features") for p in (RAIZ / c).rglob("*.py"))]
    culpables = []
    for fuente in fuentes:
        for nodo in ast.walk(ast.parse(fuente.read_text(encoding="utf-8"))):
            nombres = []
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                nombres = [nodo.module]
            if any(n == "tests" or n.startswith("tests.") for n in nombres):
                culpables.append(str(fuente.relative_to(RAIZ)))
    assert culpables == []


def test_la_aplicacion_sigue_sin_interruptor_de_claves():
    """La clave solo sale de Google: ninguna variable de entorno cambia la fuente ni el emisor."""
    fuente = inspect.getsource(security._clave_de_firma)
    assert "URL_CLAVES_GOOGLE" in fuente and "environ" not in fuente
    assert security.URL_CLAVES_GOOGLE == "https://www.googleapis.com/oauth2/v3/certs"
    assert security.EMISORES_GOOGLE == ("https://accounts.google.com", "accounts.google.com")


def test_el_humo_es_compuerta_de_los_arneses_y_de_playwright():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    for nombre, necesita in (
        ("Humo de extremo a extremo", "alcance"),
        ("Arnés por salas", "[alcance, humo]"),
        ("Arnés completo", "[alcance, humo]"),
        ("Playwright Frontend", "[alcance, humo]"),
    ):
        assert f"name: {nombre}\n    needs: {necesita}\n" in flujo, nombre
    assert "needs: [alcance, humo, arnes-salas, arnes-completo]" in flujo
    assert "npx playwright test -c playwright.humo.config.ts" in flujo
    assert flujo.index("Flujos de humo") < flujo.index("pytest $PRUEBAS -v")
    assert flujo.count("if: always()") == 1  # solo la compuerta: un arnés con always() ignoraría el humo


def test_el_job_de_humo_no_define_auth_mode():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert "AUTH_MODE" not in flujo


def test_los_limites_de_la_metodologia_se_cumplen():
    """governance/operaciones/PRUEBAS_DE_HUMO.md §4: pocos casos, sin simulación y sin reintentos."""
    carpeta = RAIZ / "frontend" / "tests" / "humo"
    especificaciones = sorted(carpeta.glob("*.spec.ts"))
    textos = [p.read_text(encoding="utf-8") for p in especificaciones]
    assert especificaciones and all(p.name[:2].isdigit() for p in especificaciones)  # el prefijo fija el orden
    assert sum(len(re.findall(r"^\s+test\(", t, re.M)) for t in textos) <= 8
    assert not any("page.route" in t or "context.route" in t or "test.skip" in t or "test.only" in t for t in textos)
    configuracion = (RAIZ / "frontend" / "playwright.humo.config.ts").read_text(encoding="utf-8")
    assert "retries: 0" in configuracion and "maxFailures: 1" in configuracion and "workers: 1" in configuracion
    assert "ep-late-hall" in configuracion and "AUTH_MODE" not in configuracion


def test_la_metodologia_existe_y_los_arneses_normales_no_recogen_el_humo():
    assert (RAIZ / "governance" / "operaciones" / "PRUEBAS_DE_HUMO.md").is_file()
    assert '"**/humo/**"' in (RAIZ / "frontend" / "playwright.config.ts").read_text(encoding="utf-8")


def test_el_humo_corre_en_las_ramas_de_los_colaboradores_y_no_hacia_main():
    """PRUEBAS_DE_HUMO.md «Dónde corre»: compuerta en dev/** y tarea/**; hacia main se omite y el arnés completo es obligatorio."""
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    hacia_main = "(github.event_name == 'push' && github.ref_name == 'main') || (github.event_name == 'pull_request' && github.base_ref == 'main')"
    assert hacia_main in flujo and "hacia_main: ${{ steps.destino.outputs.hacia_main }}" in flujo
    assert "if: needs.alcance.outputs.cubierta == '' && needs.alcance.outputs.hacia_main != 'true'\n" in flujo
    # Hacia main el modo se fuerza a completo, toque lo que toque el diff.
    assert 'if [ "$HACIA_MAIN" = "true" ]; then\n            MODO=completo' in flujo
    assert "modo: ${{ steps.destino.outputs.modo }}" in flujo
    # Los arneses arrancan con el humo en verde u omitido, nunca si falló o fue cancelado.
    arranque = "!cancelled() && (needs.humo.result == 'success' || needs.humo.result == 'skipped')"
    assert flujo.count(arranque) == 3  # los dos arneses y Playwright
    assert 'Hacia main el arnes completo es obligatorio y no paso.' in flujo


def test_las_ramas_usan_el_contenedor_y_hacia_main_todo_sigue_contra_neon():
    """PRUEBAS_DE_HUMO.md «Dónde corre»: lo dudoso cae en Neon, nunca en el contenedor."""
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert flujo.count("&postgres_de_las_ramas") == 1 and flujo.count("*postgres_de_las_ramas") == 2
    assert "image: ${{ needs.alcance.outputs.hacia_main == 'false' && 'pgvector/pgvector:pg16' || '' }}" in flujo
    assert "TEST_DATABASE_URL: ${{ (needs.alcance.outputs.hacia_main == 'false' && 'postgresql://" in flujo
    assert "|| secrets.TEST_DATABASE_URL }}" in flujo  # hacia main, la rama Neon
    # El turno y la comparación de Alembic son solo de Neon; la guarda de migrar está en test_verificar_revision_alembic.py.
    assert flujo.count("if: needs.alcance.outputs.hacia_main == 'true'\n        env:\n          GH_TOKEN") == 2
    assert flujo.count("if: needs.alcance.outputs.hacia_main == 'true'\n        run: python scripts/verificar_revision_alembic.py") == 2
    assert "testcontainers" not in flujo.lower()


def test_pytest_va_en_paralelo_contra_el_contenedor_y_en_serie_hacia_neon():
    """METODOLOGIAS.md §14: en Neon no hay plantilla que clonar; lo dudoso cae en serie, como cae en Neon."""
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    paralelo = "PARALELO: ${{ needs.alcance.outputs.hacia_main == 'false' && '-n auto' || '' }}\n"
    assert flujo.count(paralelo) == 2 and flujo.count("-n auto") == 2
    instalar = "- &instalar_xdist\n        name: Instalar pytest-xdist\n        if: needs.alcance.outputs.hacia_main == 'false'\n"
    assert flujo.count(instalar) == 1 and flujo.count("*instalar_xdist") == 1
    for trabajo, siguiente, pytest_del_trabajo in (("arnes-salas:", "arnes-completo:", "pytest $PRUEBAS -v $PARALELO\n"),
                                                   ("arnes-completo:", "zero-regression:", "run: pytest tests/ -v $PARALELO\n")):
        cuerpo = flujo[flujo.index(f"  {trabajo}"):flujo.index(f"  {siguiente}")]
        assert cuerpo.index("instalar_xdist") < cuerpo.index(pytest_del_trabajo)
    assert "PYTEST_ADDOPTS" not in flujo  # los pytest que lanzan las pruebas no heredan el -n


def test_playwright_no_se_repite_sobre_una_corrida_cubierta():
    """METODOLOGIAS.md §14: el PR cubierto omite Playwright; la compuerta obligatoria no depende de ese job."""
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    trabajo = flujo[flujo.index("  playwright:\n"):]
    assert "needs: [alcance, humo]\n" in trabajo and "&& needs.alcance.outputs.cubierta == '' }}\n" in trabajo
    compuerta = flujo[flujo.index("  zero-regression:\n"):flujo.index("  playwright:\n")]
    assert "needs: [alcance, humo, arnes-salas, arnes-completo]\n" in compuerta and "needs.playwright" not in compuerta
    assert 'if [ -n "$CUBIERTA" ]' in compuerta
    assert 'PLAYWRIGHT = "Playwright Frontend"' in (RAIZ / "scripts" / "corrida_cubierta.py").read_text(encoding="utf-8")
