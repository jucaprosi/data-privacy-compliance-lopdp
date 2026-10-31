# ¤¤qa-engineer
"""Pasillo central entre salas (ADR 0001): sin ciclos al cargar y sin tipos internos en la salida."""
import ast
import subprocess
import sys
from pathlib import Path

import pytest

from app_core.pasillo import diagnostico, evidencias, niif18
from app_core.sod import RbacError, SoDViolation, check_four_eyes

RAIZ = Path(__file__).resolve().parent.parent
PASILLO = RAIZ / "app_core" / "pasillo"


def test_cargar_el_pasillo_no_carga_ninguna_sala():
    codigo = (
        "import sys\n"
        "from app_core.pasillo import diagnostico, evidencias, niif18, organizacion, rat, roadmap\n"
        "print([m for m in sys.modules if m.startswith('features')])\n"
    )
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True, check=True)
    assert salida.stdout.strip() == "[]"


@pytest.mark.parametrize("ruta", sorted(PASILLO.glob("*.py")), ids=lambda r: r.name)
def test_el_pasillo_solo_importa_salas_dentro_de_funciones(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.ImportFrom):
            assert not (nodo.module or "").startswith("features"), f"{ruta.name}: import de sala al cargar"


def test_la_sala_organizacion_conserva_los_nombres_de_sus_errores():
    from features.organizacion import organizacion_service

    assert organizacion_service.RbacError is RbacError
    assert organizacion_service.SoDViolation is SoDViolation
    assert organizacion_service.check_four_eyes is check_four_eyes
    assert SoDViolation("x").code == 409


def test_cuatro_ojos():
    assert check_four_eyes("ana", "ana") == "Quien sube una evidencia no puede validarla"
    assert check_four_eyes("ana", "luis") is None
    assert check_four_eyes(None, "luis") is None


def test_huella_invalida_o_inexistente_es_none():
    assert evidencias.huella_registrada("tenant-sin-evidencias", "no-es-un-hash") is None
    assert evidencias.huella_registrada("tenant-sin-evidencias", "a" * 64) is None


def test_catalogo_de_controles_tiene_codigo_y_control():
    assert all(c["codigo"] and c["control"] for c in diagnostico.catalogo_de_controles())


def test_contexto_doctrinal_es_texto():
    assert isinstance(niif18.contexto_doctrinal(), str)


def test_sanitizar_textos_usa_un_solo_sanitizador():
    primero, segundo = diagnostico.sanitizar_textos(["Dr. Juan Perez", "Dr. Juan Perez"])
    assert primero == segundo
