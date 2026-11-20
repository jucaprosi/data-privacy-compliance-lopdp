# -*- coding: utf-8 -*-
# ¤arbitro ¤seguridad
"""El arrancador de humo vive solo en pruebas y se detiene ante un despliegue o ante producción.

El humo es compuerta: el guion del check obligatorio del CI se ejecuta aquí con cada desenlace de sus jobs.
"""
import ast
import importlib.util
import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app_core import security

RAIZ = Path(__file__).resolve().parents[1]
RUTA_ARRANCADOR = RAIZ / "tests" / "humo" / "servidor_humo.py"
CARPETAS_DESPLEGADAS = ("api", "app_core", "features", "alembic", "scripts")
ARCHIVOS_DE_DESPLIEGUE = ("backend.Dockerfile", "docker-compose.yml", "iniciar_backend.bat")
FLUJO_DEL_CI = RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml"
PASO_DE_LA_COMPUERTA = "Un arnes corrio y paso"


# ¤seguridad
def cargar_arrancador():
    spec = importlib.util.spec_from_file_location("servidor_humo", RUTA_ARRANCADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ENTORNO_VALIDO = {
    "HUMO_E2E": "1",
    "DATABASE_URL": "postgresql://localhost:5432/lopdp",
    "GOOGLE_CLIENT_ID": "humo-ci",
    "HUMO_CLAVE_PRIVADA": "clave.pem",
}


# ¤seguridad
def test_arranca_solo_con_el_entorno_completo_de_humo():
    assert cargar_arrancador().rechazo_de_entorno(ENTORNO_VALIDO) is None


# ¤seguridad
@pytest.mark.parametrize("cambio, motivo", [
    ({"K_SERVICE": "evydentia-api"}, "Cloud Run"),
    ({"CLOUD_RUN_SERVICE": "evydentia-api"}, "Cloud Run"),
    ({"APP_ENV": "production"}, "producción"),
    ({"DATABASE_URL": "postgresql://bd.remota.ejemplo/lopdp"}, "local"),
    ({"TEST_DATABASE_URL": "postgresql://bd.remota.ejemplo/lopdp"}, "local"),
    ({"MIGRATION_DATABASE_URL": "postgresql://bd.remota.ejemplo/lopdp"}, "local"),
    ({"DATABASE_URL": "postgresql:///lopdp?host=/cloudsql/proyecto:region:instancia"}, "producción"),
    ({"HUMO_E2E": "0"}, "HUMO_E2E"),
    ({"DATABASE_URL": ""}, "DATABASE_URL"),
    ({"GOOGLE_CLIENT_ID": ""}, "GOOGLE_CLIENT_ID"),
    ({"HUMO_CLAVE_PRIVADA": ""}, "HUMO_CLAVE_PRIVADA"),
])
def test_se_detiene_ante_un_despliegue_produccion_o_entorno_incompleto(cambio, motivo):
    assert motivo in cargar_arrancador().rechazo_de_entorno({**ENTORNO_VALIDO, **cambio})


# ¤seguridad
def test_en_cloud_run_el_proceso_termina_sin_generar_clave(monkeypatch, tmp_path, capsys):
    arrancador = cargar_arrancador()
    clave = tmp_path / "clave.pem"
    for nombre, valor in {**ENTORNO_VALIDO, "HUMO_CLAVE_PRIVADA": str(clave), "K_SERVICE": "evydentia-api"}.items():
        monkeypatch.setenv(nombre, valor)
    assert arrancador.main() == 1
    assert not clave.exists()
    assert "Cloud Run" in capsys.readouterr().err


# ¤seguridad
def test_importarlo_no_toca_la_verificacion_de_google():
    original = security._clave_de_firma
    cargar_arrancador()
    assert security._clave_de_firma is original


# ¤seguridad
def test_ningun_codigo_desplegado_lo_nombra():
    fuentes = [RAIZ / "main.py", *(p for c in CARPETAS_DESPLEGADAS for p in (RAIZ / c).rglob("*.py"))]
    fuentes += [RAIZ / nombre for nombre in ARCHIVOS_DE_DESPLIEGUE if (RAIZ / nombre).exists()]
    nombrado = [str(f.relative_to(RAIZ)) for f in fuentes if "servidor_humo" in f.read_text(encoding="utf-8")]
    assert nombrado == []


# ¤seguridad
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


# ¤seguridad
def test_la_aplicacion_sigue_sin_interruptor_de_claves():
    """La clave solo sale de Google: ninguna variable de entorno cambia la fuente ni el emisor."""
    fuente = inspect.getsource(security._clave_de_firma)
    assert "URL_CLAVES_GOOGLE" in fuente and "environ" not in fuente
    assert security.URL_CLAVES_GOOGLE == "https://www.googleapis.com/oauth2/v3/certs"
    assert security.EMISORES_GOOGLE == ("https://accounts.google.com", "accounts.google.com")


# ¤arbitro
def guion_de_la_compuerta(flujo: Path = FLUJO_DEL_CI) -> str:
    """El bloque `run: |` del paso que decide el check obligatorio, tal como lo ejecuta el runner."""
    lineas = flujo.read_text(encoding="utf-8").splitlines()
    paso = next(i for i, linea in enumerate(lineas) if linea.strip() == f"- name: {PASO_DE_LA_COMPUERTA}")
    inicio = next(i for i in range(paso, len(lineas)) if lineas[i].strip() == "run: |")
    sangria = len(lineas[inicio]) - len(lineas[inicio].lstrip())
    cuerpo = []
    for linea in lineas[inicio + 1:]:
        if linea.strip() and len(linea) - len(linea.lstrip()) <= sangria:
            break
        cuerpo.append(linea)
    return "\n".join(cuerpo) + "\n"


# ¤arbitro
def _bash() -> str | None:
    """El bash del runner; en Windows, el de Git (el `bash.exe` de System32 lanza WSL, que puede no estar)."""
    if sys.platform != "win32":
        return shutil.which("bash")
    git = shutil.which("git")
    candidatos = [raiz / "bin" / "bash.exe" for raiz in Path(git).resolve().parents[1:3]] if git else []
    return next((str(c) for c in candidatos if c.is_file()), None)


# ¤arbitro
def ejecutar_compuerta(resultados: dict[str, str], flujo: Path = FLUJO_DEL_CI) -> subprocess.CompletedProcess:
    """Corre el guion de la compuerta como GitHub: `bash -e` y los resultados de los jobs en variables."""
    entorno = {**os.environ, "ALCANCE": "success", "ETIQUETA": "prueba", "CUBIERTA": "", "HACIA_MAIN": "false",
               "MODO": "salas", "HUMO": "success", "SALAS": "skipped", "COMPLETO": "skipped", **resultados}
    return subprocess.run([_bash(), "-e", "-c", guion_de_la_compuerta(flujo)], env=entorno,
                          capture_output=True, text=True, encoding="utf-8")


sin_bash = pytest.mark.skipif(_bash() is None, reason="hace falta bash para ejecutar el guion del runner")


# ¤arbitro
@sin_bash
@pytest.mark.parametrize("resultados", [
    {"MODO": "salas", "HUMO": "success", "SALAS": "success"},
    {"MODO": "completo", "HUMO": "success", "COMPLETO": "success"},
    # El push a main no corre el humo: ya fue compuerta en el PR. El arnés completo sigue siendo obligatorio.
    {"MODO": "completo", "HACIA_MAIN": "true", "HUMO": "skipped", "COMPLETO": "success"},
    # El PR cubierto por la corrida del push no repite nada: todos sus jobs se omiten.
    {"MODO": "salas", "CUBIERTA": "10", "HUMO": "skipped"},
], ids=["pr-por-salas", "pr-completo", "push-a-main", "pr-cubierto"])
def test_la_compuerta_pasa_cuando_el_humo_y_el_arnes_obligatorio_pasaron(resultados):
    res = ejecutar_compuerta(resultados)
    assert res.returncode == 0, res.stdout + res.stderr


# ¤arbitro
@sin_bash
@pytest.mark.parametrize("resultados, motivo", [
    # Con el humo en rojo los arneses no arrancan (quedan omitidos) y el check obligatorio falla.
    ({"MODO": "salas", "HUMO": "failure"}, "no paso"),
    ({"MODO": "completo", "HUMO": "failure"}, "no paso"),
    ({"MODO": "", "HUMO": "failure"}, "El humo fallo"),
    ({"MODO": "", "HUMO": "cancelled"}, "cancelado"),
    ({"MODO": "salas", "HUMO": "success", "SALAS": "failure"}, "no paso"),
    ({"MODO": "completo", "HUMO": "success", "COMPLETO": "cancelled"}, "no paso"),
    ({"MODO": "completo", "HACIA_MAIN": "true", "HUMO": "skipped", "COMPLETO": "skipped"}, "no paso"),
    ({"MODO": "", "HUMO": "success"}, "Ningun arnes corrio"),
    ({"ALCANCE": "failure", "MODO": "", "HUMO": "skipped"}, "alcance"),
], ids=["humo-rojo-salas", "humo-rojo-completo", "humo-rojo-sin-modo", "humo-cancelado", "salas-rojo",
        "completo-cancelado", "main-sin-arnes", "ningun-arnes", "alcance-rojo"])
def test_la_compuerta_falla_si_el_humo_o_el_arnes_obligatorio_no_pasaron(resultados, motivo):
    res = ejecutar_compuerta(resultados)
    assert res.returncode == 1, res.stdout + res.stderr
    assert motivo in res.stdout
