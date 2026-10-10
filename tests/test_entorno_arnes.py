"""El entorno de ejecucion de los .bat se resuelve en un unico sitio y se comprueba.

Estas pruebas impiden volver a dos defectos: que cada .bat decida el interprete por su cuenta
(con rutas de una maquina concreta) y que se ejecute con un interprete sin las dependencias.
"""
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_entorno", RAIZ / "scripts" / "verificar_entorno.py")
ve = importlib.util.module_from_spec(_spec)
sys.modules["verificar_entorno"] = ve  # se registra antes de ejecutar el modulo (ver Aporte 95)
_spec.loader.exec_module(ve)

BATS = sorted(p for p in RAIZ.glob("*.bat")) + [RAIZ / "scripts" / "entorno.bat"]
USAN_INTERPRETE = re.compile(r"%PYTHON_BIN%|%NODE_BIN%|^\s*python\s", re.IGNORECASE | re.MULTILINE)


# ----------------------------------------------------------------- lectura de requirements.txt

def test_nombres_requeridos_ignora_extras_versiones_marcadores_y_comentarios():
    texto = (
        "# Web\n"
        "fastapi>=0.111.0\n"
        "sqlalchemy[asyncio]>=2.0.30  # con extras\n"
        "psycopg[binary]>=3.2.3\n"
        "\n"
        "-r otro.txt\n"
        "pywin32>=300 ; sys_platform == 'win32'\n"
        "pytest-asyncio>=0.24.0\r\n"
    )
    assert ve.nombres_requeridos(texto) == ["fastapi", "sqlalchemy", "psycopg", "pywin32", "pytest-asyncio"]


def test_faltantes_normaliza_los_nombres():
    texto = "pytest-asyncio>=0.24\nPyYAML>=6\npydantic_settings>=2\nboto3>=1.35\n"
    instalados = ["pytest_asyncio", "pyyaml", "pydantic-settings"]
    assert ve.faltantes(texto, instalados) == ["boto3"]


def test_faltantes_vacio_cuando_estan_todos():
    assert ve.faltantes("fastapi>=1\nhttpx>=0.27\n", ["FastAPI", "httpx"]) == []


def test_el_interprete_de_las_pruebas_cumple_requirements_txt():
    texto = (RAIZ / "requirements.txt").read_text(encoding="utf-8-sig")
    assert ve.faltantes(texto, ve.instalados_ahora()) == []


# ----------------------------------------------------------------- los .bat

@pytest.mark.parametrize("bat", BATS, ids=lambda p: p.name)
def test_ningun_bat_lleva_rutas_de_usuario_de_una_maquina(bat):
    texto = bat.read_text(encoding="utf-8", errors="replace")
    assert not re.search(r"[A-Za-z]:\\Users\\", texto), f"{bat.name} lleva una ruta de usuario fija"


@pytest.mark.parametrize("bat", [b for b in BATS if b.name != "entorno.bat"], ids=lambda p: p.name)
def test_los_bat_que_usan_un_interprete_lo_resuelven_con_entorno_bat(bat):
    texto = bat.read_text(encoding="utf-8", errors="replace")
    if USAN_INTERPRETE.search(texto):
        assert r"scripts\entorno.bat" in texto, f"{bat.name} usa un interprete sin pasar por scripts\\entorno.bat"


@pytest.mark.skipif(sys.platform != "win32", reason="los .bat solo se ejecutan en Windows")
def test_entorno_bat_resuelve_y_valida_el_interprete_por_defecto():
    entorno = {k: v for k, v in os.environ.items() if k != "PYTHON_BIN"}
    res = subprocess.run(["cmd", "/c", r"scripts\entorno.bat", "--sin-node"], cwd=RAIZ, env=entorno,
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "[ENTORNO] OK" in res.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="los .bat solo se ejecutan en Windows")
def test_entorno_bat_rechaza_un_interprete_inexistente_con_mensaje_claro():
    entorno = dict(os.environ, PYTHON_BIN=r"C:\no\existe\python.exe")
    res = subprocess.run(["cmd", "/c", r"scripts\entorno.bat", "--sin-node"], cwd=RAIZ, env=entorno,
                         capture_output=True, text=True)
    assert res.returncode == 1
    assert "No se puede ejecutar el interprete de Python" in res.stdout
