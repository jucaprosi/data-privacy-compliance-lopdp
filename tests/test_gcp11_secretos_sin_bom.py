"""GCP-11 · El árbitro de secretos sin BOM, con secretos simulados (no toca Google Cloud).

`¤versionado-despliegue` `¤arbitro`

Mutación documentada: quitar la comparación con el BOM en `estado` (devolver siempre «sin BOM» para
tres bytes) hace fallar `test_un_secreto_con_bom_da_codigo_1_y_lo_nombra`.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import verificar_secretos_sin_bom as v  # noqa: E402

VALOR_SIMULADO = b"postgresql://lopdp_app:clave-simulada@host.invalid/db"


def _lector(tabla):
    return lambda proyecto, nombre, version: tabla[nombre]


def test_sin_bom_da_codigo_0(capsys):
    tabla = {"DATABASE_URL_APP": VALOR_SIMULADO[:3], "JWT_SECRET": b"abc"}
    assert v.main(["--proyecto", "p.invalid", "DATABASE_URL_APP", "JWT_SECRET"], _lector(tabla)) == 0
    assert capsys.readouterr().out.splitlines() == ["DATABASE_URL_APP: sin BOM", "JWT_SECRET: sin BOM"]


def test_un_secreto_con_bom_da_codigo_1_y_lo_nombra(capsys):
    tabla = {"DATABASE_URL_APP": v.BOM_UTF8, "JWT_SECRET": b"abc"}
    assert v.main(["--proyecto", "p.invalid", "DATABASE_URL_APP", "JWT_SECRET"], _lector(tabla)) == 1
    salida = capsys.readouterr().out
    assert "DATABASE_URL_APP: CON BOM" in salida and "JWT_SECRET: sin BOM" in salida


def test_vacio_y_no_leido_no_pasan(capsys):
    assert v.main(["--proyecto", "p.invalid", "A", "B"], _lector({"A": b"", "B": None})) == 1
    assert capsys.readouterr().out.splitlines() == ["A: vacío", "B: no se pudo leer"]


def test_nunca_imprime_el_valor(capsys):
    v.main(["--proyecto", "p.invalid", "X"], _lector({"X": v.BOM_UTF8 + VALOR_SIMULADO}))
    salida = capsys.readouterr().out
    assert "clave-simulada" not in salida and "postgresql" not in salida


def test_el_lector_real_conserva_solo_tres_bytes(monkeypatch):
    class Corrida:
        returncode = 0
        stdout = v.BOM_UTF8 + VALOR_SIMULADO

    monkeypatch.setattr(v.subprocess, "run", lambda *a, **k: Corrida())
    assert v.leer_tres_bytes("p.invalid", "X", "latest") == v.BOM_UTF8


def test_el_lector_real_devuelve_none_si_gcloud_falla(monkeypatch):
    class Corrida:
        returncode = 1
        stdout = b"nunca se usa"

    monkeypatch.setattr(v.subprocess, "run", lambda *a, **k: Corrida())
    assert v.leer_tres_bytes("p.invalid", "X", "latest") is None
