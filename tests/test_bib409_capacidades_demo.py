# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤arbitro
"""BIB-409: capacidades editoriales en la demo y guía de la demo por Antigravity (governance/especificaciones/BIB-409.md).

Pruebas sin base. Mutaciones (cada una hace fallar la prueba indicada):
  - m1: quitar `demo` de `ENTORNOS` -> test_m1_el_script_admite_demo y test_demo_con_url_de_pruebas_sale_2_sin_conectar;
  - m2: no exigir la confirmación -> test_m2_demo_sin_confirmar_sale_2_sin_conectar;
  - m3: poner las capacidades después de la carga en la guía -> test_m3_la_guia_pone_las_capacidades_antes_de_la_carga.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
URL_DEMO = "postgresql://u:p@127.0.0.1:5433/evydentia_demo"
URL_PRUEBAS = "postgresql://u:p@host/evydentia-pruebas"


def _script():
    especificacion = importlib.util.spec_from_file_location("capacidades_biblioteca_b409", RAIZ / "scripts" / "capacidades_biblioteca.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _bloque_demo() -> str:
    texto = (RAIZ / "docs" / "biblioteca-pmv.md").read_text(encoding="utf-8")
    inicio = texto.index("### En la demo (DEMO-12)")
    return texto[inicio:]


def _argv(confirmar: bool) -> list[str]:
    base = ["--conceder", "--usuario", "u-1", "--capacidad", "editor", "--otorgante", "u-2", "--motivo", "m", "--entorno", "demo"]
    return base + (["--confirmar-entorno"] if confirmar else [])


def test_m1_el_script_admite_demo():
    script = _script()
    assert "demo" in script.ENTORNOS
    assert script.entorno_de_url(URL_DEMO) == "demo"  # antes que «local»
    assert script.entorno_de_url("postgresql://u:p@evydentia-demo-db/otra") == "demo"
    assert script.entorno_de_url(URL_PRUEBAS) == "pruebas"
    assert script.motivo_entorno(URL_DEMO, "demo", True) is None


def test_demo_con_url_de_pruebas_sale_2_sin_conectar(monkeypatch):
    script = _script()
    conectado = []

    async def _no_conectar(*_a, **_k):
        conectado.append(True)
        return 0

    monkeypatch.setattr(script, "_ejecutar", _no_conectar)
    monkeypatch.setenv(script.VARIABLE_URL, URL_PRUEBAS)
    assert script.main(_argv(True)) == 2
    assert conectado == []


def test_m2_demo_sin_confirmar_sale_2_sin_conectar(monkeypatch):
    script = _script()
    conectado = []

    async def _no_conectar(*_a, **_k):
        conectado.append(True)
        return 0

    monkeypatch.setattr(script, "_ejecutar", _no_conectar)
    monkeypatch.setenv(script.VARIABLE_URL, URL_DEMO)
    assert script.main(_argv(False)) == 2
    assert conectado == []
    assert script.motivo_entorno(URL_DEMO, "demo", False) is not None


def test_la_guia_nombra_antigravity_y_la_siembra():
    bloque = _bloque_demo()
    assert "Antigravity" in bloque
    assert "scripts/demo/sembrar_plantilla.py" in bloque
    assert "--entorno demo --confirmar-entorno" in bloque
    assert "<URL" in bloque and "postgresql://" not in bloque  # sin valores de secretos


def test_m3_la_guia_pone_las_capacidades_antes_de_la_carga():
    bloque = _bloque_demo()
    capacidades = bloque.index("/plataforma/capacidades")  # BIB-413 R4: la concesión es en la web de la demo
    carga = bloque.index("scripts/cargar_plantillas_pmv.py --cargar")
    siembra = bloque.index("scripts/demo/sembrar_plantilla.py")
    assert capacidades < carga < siembra
    for capacidad in ("editor", "revisor_tecnico", "publicador"):
        assert capacidad in bloque[:carga]


def test_la_guia_dice_quien_aprueba():
    bloque = _bloque_demo()
    assert "BIB-406 R4" in bloque and "una sola persona de las tres" in bloque
    assert "BIB-403 R4" in bloque and "distinta de quien la cargó" in bloque


def test_la_guia_no_deja_variables_de_entorno_puestas():
    import re
    bloque = _bloque_demo()
    puestas = set(re.findall(r"\$env:(\w+)\s*=", bloque))
    quitadas = set(re.findall(r"Remove-Item Env:(\w+)", bloque))
    assert {"APP_ENV", "MIGRATION_DATABASE_URL", "BIB109_DATABASE_URL"} <= puestas  # BIB-413 R4: sin BIB_CAPACIDADES_DATABASE_URL
    assert puestas <= quitadas
