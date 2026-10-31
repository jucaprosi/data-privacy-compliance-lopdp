# ¤¤qa-engineer
"""El selector de pruebas amplía y nunca reduce: salas tocadas, sus dependientes, zonas y el núcleo; lo compartido corre todo."""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("seleccionar_pruebas", RAIZ / "scripts" / "seleccionar_pruebas.py")
sp = importlib.util.module_from_spec(_spec)
sys.modules["seleccionar_pruebas"] = sp
_spec.loader.exec_module(sp)

SALAS = sp.salas_del_repositorio(RAIZ)
MAPA = sp.mapa_de_pruebas(RAIZ, SALAS)
POR_RUTA = {p.ruta: p for p in MAPA}


def test_las_salas_salen_del_disco():
    assert len(SALAS) >= 20 and {"rat", "roadmap", "organizacion"} <= set(SALAS)


def test_modulos_importados_ve_todas_las_formas():
    fuente = (
        "import features.rat.rat_service\n"
        "from features.roadmap import roadmap_service\n"
        "from features import evidencias\n"
        "from app_core.pasillo import organizacion\n"
        "def f():\n"
        "    from features.niif18.niif18_service import x\n"
    )
    assert sp.salas_de_modulos(sp.modulos_importados(fuente), SALAS) == {"rat", "roadmap", "evidencias", "organizacion", "niif18"}


def test_el_pasillo_cuenta_como_dependencia_de_la_sala():
    assert sp.salas_de_modulos({"app_core.pasillo.rat", "app_core.audit", "features.x.y"}, SALAS) == {"rat"}


@pytest.mark.parametrize("ruta, esperado", [
    ("features/rat/services/x.py", (("sala", "rat"),)),
    ("features/__init__.py", (("compartido", "features/__init__.py"),)),
    ("tests/test_incidentes.py", (("prueba", "tests/test_incidentes.py"),)),
    ("tests/conftest.py", (("compartido", "tests/conftest.py"),)),
    ("tests/matriz/RM-21.py", (("compartido", "tests/matriz/RM-21.py"),)),
    ("tests/deuda_adpa/roadmap.txt", (("sala", "roadmap"),)),
    ("frontend/src/components/X.tsx", (("zona", "frontend"),)),
    ("governance/tareas/RM-22.md", (("zona", "governance"),)),
    ("docs/adr/0001.md", (("zona", "docs/"),)),
    ("scripts/verificar_alcance_pr.py", (("zona", "verificar_alcance_pr"),)),
    ("verificadores/arnes_local.py", (("zona", "arnes_local"),)),
    ("README.md", (("zona", "README.md"),)),
    ("app_core/pasillo/rat.py", (("compartido", "app_core/pasillo/rat.py"),)),
    ("api/errores.py", (("compartido", "api/errores.py"),)),
    ("api/routers/__init__.py", (("compartido", "api/routers/__init__.py"),)),
    ("alembic/versions/20261101_x.py", (("compartido", "alembic/versions/20261101_x.py"),)),
    ("main.py", (("compartido", "main.py"),)),
    ("requirements.txt", (("compartido", "requirements.txt"),)),
    (".github/workflows/zero-regression-pipeline.yml", (("compartido", ".github/workflows/zero-regression-pipeline.yml"),)),
])
def test_clasificar_cada_archivo(ruta, esperado):
    assert tuple((o.tipo, o.nombre) for o in sp.clasificar(ruta, SALAS, RAIZ)) == esperado


def test_un_router_se_clasifica_por_las_salas_que_importa():
    assert {o.nombre for o in sp.clasificar("api/routers/rat.py", SALAS, RAIZ)} == {"rat"}
    assert {o.nombre for o in sp.clasificar("api/routers/roadmaps.py", SALAS, RAIZ)} >= {"roadmap"}
    assert sp.clasificar("api/routers/no_existe.py", SALAS, RAIZ)[0].tipo == "compartido"


def test_el_prefijo_http_asigna_sala_a_una_prueba_que_no_importa_la_sala():
    assert "incidentes" in POR_RUTA["tests/test_incidentes.py"].salas
    assert POR_RUTA["tests/test_api_integracion.py"].salas


def test_el_prefijo_respeta_su_limite():
    patron = sp.patron_prefijo("/rat")
    assert patron.search('client.get("/rat/eipd")') and patron.search("'/rat'")
    assert patron.search('"/rated"') is None and patron.search("/ratificar/") is None


def test_el_nucleo_son_las_pruebas_sin_sala_y_no_esta_vacio():
    nucleo = {p.ruta for p in MAPA if p.es_nucleo}
    assert {"tests/test_adpa_dependencias.py", "tests/test_adpa_bulkhead.py", "tests/test_alembic_una_cabeza.py"} <= nucleo
    # recorren todo el repositorio aunque importen una sala: el #265 borró un archivo del frontend y rompió la escala
    assert {"tests/test_escala_madurez.py", "tests/test_sin_rol_antiguo.py"} <= nucleo
    assert POR_RUTA["tests/test_escala_madurez.py"].salas and POR_RUTA["tests/test_escala_madurez.py"].arbitro_de_repositorio
    assert len(nucleo) < len(MAPA)


def test_un_arbitro_de_repositorio_es_nucleo_aunque_tenga_sala():
    con_sala = sp.Prueba("tests/test_x.py", frozenset({"rat"}), "import features.rat", arbitro_de_repositorio=True)
    sin_arbitro = sp.Prueba("tests/test_y.py", frozenset({"rat"}), "import features.rat")
    assert con_sala.es_nucleo and not sin_arbitro.es_nucleo
    for texto in ("git ls-files", '["git", "ls-files", "-z"]', "RAIZ.rglob(\"*.py\")", "os.walk(RAIZ)", 'RAIZ / "scripts" / "verificar_x.py"', "scripts/verificar_x.py"):
        assert sp.ARBITRO_DE_REPOSITORIO.search(texto), texto
    assert not sp.ARBITRO_DE_REPOSITORIO.search("from features.rat import rat_service")


def test_un_cambio_en_una_sala_corre_sus_pruebas_sus_dependientes_y_el_nucleo():
    seleccion = sp.seleccionar(["features/rat/services/eipd_engine.py"], RAIZ, MAPA)
    assert seleccion.modo == "salas" and "rat" in seleccion.salas and "roadmap" in seleccion.salas
    assert {"tests/test_rat_eipd.py", "tests/test_roadmap_contexto_real.py", "tests/test_adpa_dependencias.py"} <= set(seleccion.pruebas)
    assert "tests/test_incidentes.py" not in seleccion.pruebas
    assert len(seleccion.pruebas) < len(MAPA)
    assert seleccion.etiqueta.startswith("salas: ")


@pytest.mark.parametrize("archivos", [
    [], ["app_core/audit.py"], ["alembic/versions/x.py"], ["tests/conftest.py"], ["main.py"],
    [".github/workflows/zero-regression-pipeline.yml"], ["features/rat/x.py", "api/dependencies.py"],
])
def test_lo_compartido_o_lo_desconocido_corre_todo(archivos):
    seleccion = sp.seleccionar(archivos, RAIZ, MAPA)
    assert seleccion.modo == "completo" and seleccion.etiqueta == "completo" and seleccion.pruebas == []


def test_una_prueba_tocada_corre_aunque_no_tenga_sala_tocada():
    seleccion = sp.seleccionar(["tests/test_incidentes.py"], RAIZ, MAPA)
    assert seleccion.modo == "salas" and "tests/test_incidentes.py" in seleccion.pruebas and seleccion.salas == []


def test_una_prueba_borrada_no_se_pide():
    seleccion = sp.seleccionar(["tests/test_que_ya_no_existe.py"], RAIZ, MAPA)
    assert seleccion.modo == "salas" and "tests/test_que_ya_no_existe.py" not in seleccion.pruebas


def test_la_zona_frontend_corre_el_nucleo_y_lo_que_la_nombra():
    seleccion = sp.seleccionar(["frontend/src/app/page.tsx"], RAIZ, MAPA)
    assert seleccion.modo == "salas" and seleccion.zonas == ["frontend"]
    assert "tests/test_rutas_cliente_frontend.py" in seleccion.pruebas


def test_node_solo_cuando_una_prueba_elegida_lo_invoca():
    assert sp.seleccionar(["features/diagnostico/services/engine.py"], RAIZ, MAPA).necesita_node is True
    assert sp.seleccionar(["features/incidentes/domain/models.py"], RAIZ, MAPA).necesita_node is False


def test_un_cambio_en_un_script_corre_las_pruebas_que_lo_nombran():
    seleccion = sp.seleccionar(["scripts/verificar_revision_alembic.py"], RAIZ, MAPA)
    assert "tests/test_verificar_revision_alembic.py" in seleccion.pruebas


def test_la_salida_para_github(tmp_path):
    seleccion = sp.Seleccion("salas", [], ["rat"], ["frontend"], ["tests/test_a.py", "tests/test_b.py"], necesita_node=False)
    sp.escribir_salida_github(seleccion, str(tmp_path / "out"))
    assert (tmp_path / "out").read_text(encoding="utf-8").splitlines() == [
        "modo=salas", "etiqueta=salas: rat; zonas: frontend", "pruebas=tests/test_a.py tests/test_b.py", "frontend=true", "node=false",
    ]


def test_sin_base_un_push_corre_todo(capsys):
    assert sp.main(["--base", "", "--cabeza", ""]) == 0
    assert "ALCANCE: completo" in capsys.readouterr().out


def test_el_ci_tiene_dos_arneses_y_una_compuerta_con_el_nombre_obligatorio():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert "scripts/seleccionar_pruebas.py" in flujo and "--salida-github" in flujo
    assert "name: Arnés por salas" in flujo and "name: Arnés completo" in flujo
    assert "needs.alcance.outputs.modo == 'salas'" in flujo and "needs.alcance.outputs.modo == 'completo'" in flujo
    assert "pytest $PRUEBAS -v" in flujo and "pytest tests/ -v" in flujo
    assert "name: Arnés Físico Determinista" in flujo and "needs: [alcance, arnes-salas, arnes-completo]" in flujo
    assert "if: always()" in flujo
    assert flujo.count("&base_de_pruebas") == 1 and flujo.count("*base_de_pruebas") == 1
