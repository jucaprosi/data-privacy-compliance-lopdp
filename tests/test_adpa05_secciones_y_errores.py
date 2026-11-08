# ¤adpa
"""ADPA-05: cada sala tiene su domain/errores.py con registrar() y las secciones reservadas sembradas."""
from __future__ import annotations

import importlib
import re
import tomllib
from pathlib import Path

import pytest

from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio

RAIZ = Path(__file__).resolve().parent.parent
FICHA = RAIZ / "governance" / "tareas" / "ADPA-05.md"


def _ficha() -> dict:
    texto = FICHA.read_text(encoding="utf-8")
    return tomllib.loads(texto.split("+++")[1])


def _secciones(texto: str) -> list[str]:
    return re.findall(r"(?m)^# === ([A-Za-z0-9-]+) ===$", texto)


def test_cada_marca_sembrada_existe_y_cierra():
    for entrada in _ficha()["siembra"] + [p for p in _ficha()["propiedad"] if p.endswith("#ADPA-05")]:
        ruta, ident = entrada.split("#")
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        assert texto.count(f"# === {ident} ===") == 1, entrada
        assert texto.count(f"# === fin {ident} ===") == 1, entrada
        assert texto.index(f"# === {ident} ===") < texto.index(f"# === fin {ident} ==="), entrada


def test_secciones_no_se_anidan():
    for ruta in {e.split("#")[0] for e in _ficha()["propiedad"]}:
        abierta = None
        for linea in (RAIZ / ruta).read_text(encoding="utf-8").splitlines():
            if m := re.fullmatch(r"# === fin ([A-Za-z0-9-]+) ===", linea):
                assert abierta == m.group(1), (ruta, linea)
                abierta = None
            elif m := re.fullmatch(r"# === ([A-Za-z0-9-]+) ===", linea):
                assert abierta is None, (ruta, linea)
                abierta = m.group(1)
        assert abierta is None, ruta


SALAS = sorted({p.split("/")[1] for p in _ficha()["propiedad"] if p.endswith("domain/errores.py") or "errores.py#" in p})


@pytest.mark.parametrize("sala", SALAS)
def test_registrar_por_sala(sala):
    modulo = importlib.import_module(f"features.{sala}.domain.errores")
    codigo = CodigoErrorNegocio(f"PRUEBA_ADPA05_{sala.upper()}", 400, "Prueba.")
    try:
        modulo.registrar(codigo)
        modulo.registrar(codigo)  # idempotente
        assert CATALOGO_ERRORES[codigo.codigo] is codigo
        with pytest.raises(ValueError):
            modulo.registrar(CodigoErrorNegocio(codigo.codigo, 409, "Otro."))
    finally:
        CATALOGO_ERRORES.pop(codigo.codigo, None)


@pytest.mark.parametrize("compuerta", [p.split("#")[0] for p in _ficha()["propiedad"] if p.endswith("_service.py#ADPA-05")])
def test_compuerta_importa_y_carga_errores(compuerta):
    sala = compuerta.split("/")[1]
    importlib.import_module(compuerta[:-3].replace("/", "."))
    assert importlib.import_module(f"features.{sala}.domain.errores")
