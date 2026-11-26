# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""BIB-413: los scripts de la biblioteca reconocen la base de producción por proxy local (governance/especificaciones/BIB-413.md).

Sin base. Mutaciones (cada una hace fallar la prueba indicada):
  - m1: leer la URL local de producción como «local» -> test_m1_la_base_de_produccion_por_proxy_es_produccion;
  - m2: marcar toda URL local como producción -> test_m2_una_base_local_cualquiera_sigue_siendo_local_y_la_demo_demo;
  - m3: conectar sin confirmar -> test_m3_produccion_sin_confirmar_sale_2_sin_conectar_y_sin_imprimir_la_url.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
URL_PRODUCCION = "postgresql://dueno:secreto@127.0.0.1:5432/evydentia_prod"
URL_LOCAL = "postgresql://dueno:secreto@127.0.0.1:5432/lopdp_desarrollo"
URL_DEMO = "postgresql://dueno:secreto@127.0.0.1:5433/evydentia_demo"
SCRIPTS = ("cargar_plantillas_pmv", "capacidades_biblioteca")


def _script(nombre: str):
    especificacion = importlib.util.spec_from_file_location(f"{nombre}_b413", RAIZ / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


@pytest.mark.parametrize("nombre", SCRIPTS)
def test_m1_la_base_de_produccion_por_proxy_es_produccion(nombre):
    script = _script(nombre)
    assert script.entorno_de_url(URL_PRODUCCION) == "produccion"  # antes que «local», sin INSTANCE_CONNECTION_NAME
    assert script.entorno_de_url(URL_PRODUCCION.upper().replace("POSTGRESQL", "postgresql")) == "produccion"
    assert script.motivo_entorno(URL_PRODUCCION, "produccion", True) is None
    assert script.motivo_entorno(URL_PRODUCCION, "local", True) is not None


@pytest.mark.parametrize("nombre", SCRIPTS)
def test_m2_una_base_local_cualquiera_sigue_siendo_local_y_la_demo_demo(nombre):
    script = _script(nombre)
    assert script.entorno_de_url(URL_LOCAL) == "local"
    assert script.entorno_de_url("postgresql://u:p@localhost:5432/otra") == "local"
    assert script.entorno_de_url(URL_DEMO) == "demo"
    assert script.entorno_de_url("postgresql://u:p@evydentia-demo-db/otra") == "demo"
    assert script.motivo_entorno(URL_LOCAL, "produccion", True) is not None


def test_m3_produccion_sin_confirmar_sale_2_sin_conectar_y_sin_imprimir_la_url(monkeypatch, capsys):
    cargar = _script("cargar_plantillas_pmv")
    capacidades = _script("capacidades_biblioteca")
    conectado = []

    async def _no_conectar(*_a, **_k):
        conectado.append(True)
        return 0

    monkeypatch.setattr(cargar, "_cargar", _no_conectar)
    monkeypatch.setattr(capacidades, "_ejecutar", _no_conectar)
    monkeypatch.setenv("BIB109_DATABASE_URL", URL_PRODUCCION)
    monkeypatch.setenv("BIB_CAPACIDADES_DATABASE_URL", URL_PRODUCCION)
    assert cargar.main(["--cargar", "--actor", "u-1", "--entorno", "produccion"]) == 2
    assert capacidades.main(["--listar", "--entorno", "produccion"]) == 2
    salida = capsys.readouterr()
    assert conectado == []
    for texto in (salida.out, salida.err):
        assert "secreto" not in texto and "127.0.0.1" not in texto and "evydentia_prod" not in texto


# --- R3 y R4 · Guía ---------------------------------------------------------------------------------

def _guia() -> str:
    return (RAIZ / "docs" / "biblioteca-pmv.md").read_text(encoding="utf-8")


def _orden(texto: str, *marcas: str) -> None:
    posiciones = [texto.index(m) for m in marcas]
    assert posiciones == sorted(posiciones), marcas


def test_la_guia_de_produccion_va_de_operadores_a_capacidades_carga_y_publicacion():
    guia = _guia()
    bloque = guia[guia.index("### En producción"):guia.index("### En la demo (DEMO-12)")]
    _orden(bloque, "administrar_operadores alta", "administrar_operadores vincular", "/plataforma/capacidades",
           "cargar_plantillas_pmv.py --cargar", "/plataforma/biblioteca")
    assert "capacidades_biblioteca.py" not in bloque
    assert "--entorno produccion --confirmar-entorno" in bloque


def test_la_guia_dice_que_capacidades_biblioteca_es_para_local_y_pruebas():
    guia = _guia()
    assert "`scripts/capacidades_biblioteca.py` queda para local y pruebas" in guia


def test_los_pasos_1_a_3_de_la_demo_son_operadores_capacidades_en_la_web_y_carga():
    guia = _guia()
    bloque = guia[guia.index("### En la demo (DEMO-12)"):]
    _orden(bloque, "administrar_operadores alta", "administrar_operadores vincular", "/plataforma/capacidades",
           "cargar_plantillas_pmv.py --cargar", "/plataforma/biblioteca", "4. **Comprobación.**",
           "5. **Retiro de lo ficticio.**", "6. **Siembra.**")
    assert "capacidades_biblioteca.py" not in bloque
    assert "administrar_operadores listar" in bloque and "`--actor` es el `usuario_id`" in bloque
    assert "evydentia_demo" in bloque and "Antigravity" in bloque
    assert "entrada del equipo editorial" in bloque
    assert "cada una por otro operador" in bloque
    assert "una sola persona de las tres" in bloque and "distinta de quien la cargó" in bloque
    assert "postgresql://" not in bloque
