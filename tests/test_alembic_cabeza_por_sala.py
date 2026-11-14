# ¤arbitro ¤adpa
"""CI-28: una rama de Alembic por sala (sustituye a test_alembic_una_cabeza.py).

Las reglas viven en `tests/_alembic_salas.py` y se comprueban sobre el grafo real y sobre grafos
armados en un directorio temporal (nunca en `alembic/versions/`). Sin `import yaml`.
"""
import importlib.util
import os
import re
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from tests import _alembic_salas as AS
from tests._alembic_salas import escribir_migracion, guion_de

RAIZ = AS.RAIZ
BASE = "base0"
TABLAS = {"diagnostico_respuestas": "diagnostico", "roadmaps": "roadmap"}


@pytest.fixture
def grafo(tmp_path):
    """Directorio de migraciones temporal con una base común y dos carpetas de sala."""
    versiones = tmp_path / "versions"
    escribir_migracion(versiones, BASE, None)
    features = tmp_path / "features"
    for sala in ("roadmap", "diagnostico"):
        (features / sala).mkdir(parents=True)
    return versiones, features, tmp_path


def _fallos(grafo_):
    versiones, features, raiz = grafo_
    return AS.fallos_del_grafo(guion_de(raiz), BASE, TABLAS, features)


def _dos_ramas(versiones):
    escribir_migracion(versiones, "rm1", BASE, labels=("roadmap",))
    escribir_migracion(versiones, "dg1", BASE, labels=("diagnostico",))


# ---- El grafo real ---------------------------------------------------------------------------

def test_grafo_real_cumple_las_reglas():
    salas = AS.cargar_salas()
    assert AS.fallos_del_grafo(AS.guion_del_repositorio(), salas.BASE_COMUN, salas.TABLAS_POR_SALA) == []


def test_base_comun_es_una_revision_del_grafo_y_la_historia_no_cambia_de_forma():
    salas = AS.cargar_salas()
    guion = AS.guion_del_repositorio()
    assert guion.get_revision(salas.BASE_COMUN) is not None
    # Sin etiquetas aún, la cabeza de cualquier sala es la base común.
    assert AS.cabeza_de_sala("biblioteca") == salas.BASE_COMUN


def test_toda_tabla_del_mapa_tiene_sala_de_features():
    salas = AS.cargar_salas()
    carpetas = {p.name for p in AS.FEATURES.iterdir() if p.is_dir()}
    assert set(salas.TABLAS_POR_SALA.values()) <= carpetas


# ---- Escenarios de la especificación --------------------------------------------------------

def test_una_cabeza_por_etiqueta(grafo):
    versiones, _, _ = grafo
    _dos_ramas(versiones)
    assert _fallos(grafo) == []
    # Mutación: dos migraciones de roadmap que cuelgan de la misma revisión.
    escribir_migracion(versiones, "rm2", "rm1")
    escribir_migracion(versiones, "rm2b", "rm1")
    fallos = _fallos(grafo)
    assert any("«roadmap» tiene 2 cabezas" in f for f in fallos)
    with pytest.raises(AssertionError, match="2 cabezas"):
        AS.cabeza_de_sala("roadmap", guion_de(grafo[2]), BASE)


def test_cabeza_de_sala_con_y_sin_rama_propia(grafo):
    versiones, _, raiz = grafo
    _dos_ramas(versiones)
    escribir_migracion(versiones, "rm2", "rm1")
    guion = guion_de(raiz)
    assert AS.cabeza_de_sala("roadmap", guion, BASE) == "rm2"
    assert AS.cabeza_de_sala("diagnostico", guion, BASE) == "dg1"
    assert AS.cabeza_de_sala("sala_sin_migraciones", guion, BASE) == BASE


def test_toda_migracion_nueva_con_sala(grafo):
    versiones, _, _ = grafo
    escribir_migracion(versiones, "rm1", BASE, labels=("roadmap",))
    assert _fallos(grafo) == []
    # Mutación: una migración que cuelga de BASE_COMUN sin branch_labels.
    escribir_migracion(versiones, "suelta", BASE)
    fallos = _fallos(grafo)
    assert any("suelta" in f and "branch_labels" in f for f in fallos)


def test_etiquetas_son_salas(grafo):
    versiones, _, _ = grafo
    escribir_migracion(versiones, "x1", BASE, labels=("no_es_una_sala",))
    assert any("no_es_una_sala" in f and "features/" in f for f in _fallos(grafo))


def test_dependencia_entre_salas_declarada(grafo):
    versiones, _, _ = grafo
    _dos_ramas(versiones)
    fk = 'op.create_table("tarea_x", sa.Column("r", sa.Integer, sa.ForeignKey("diagnostico_respuestas.id")))'
    # Mutación: la FK a una tabla de otra sala sin depends_on.
    escribir_migracion(versiones, "rm2", "rm1", cuerpo=fk)
    fallos = _fallos(grafo)
    assert any("rm2" in f and "«diagnostico»" in f and "depends_on" in f for f in fallos)
    # Con depends_on hacia la revisión de esa sala, pasa.
    escribir_migracion(versiones, "rm2", "rm1", depends_on="dg1", cuerpo=fk)
    assert _fallos(grafo) == []


def test_dependencia_hacia_una_tabla_creada_por_la_rama_de_otra_sala(grafo):
    versiones, _, _ = grafo
    escribir_migracion(versiones, "dg1", BASE, labels=("diagnostico",),
                       cuerpo='op.create_table("diagnostico_nueva", sa.Column("id", sa.Integer))')
    escribir_migracion(versiones, "rm1", BASE, labels=("roadmap",),
                       cuerpo='op.add_column("diagnostico_nueva", sa.Column("x", sa.Integer))')
    assert any("rm1" in f and "depends_on" in f for f in _fallos(grafo))


def test_sql_en_texto_entre_salas(grafo):
    versiones, _, _ = grafo
    _dos_ramas(versiones)
    sql = 'op.execute("UPDATE diagnostico_respuestas SET puntaje = 0 WHERE puntaje IS NULL")'
    escribir_migracion(versiones, "rm2", "rm1", cuerpo=sql)
    assert any("rm2" in f and "«diagnostico»" in f for f in _fallos(grafo))
    escribir_migracion(versiones, "rm2", "rm1", depends_on="dg1", cuerpo=sql)
    assert _fallos(grafo) == []


def test_tablas_de_la_propia_sala_o_del_texto_libre_no_exigen_depends_on(grafo):
    versiones, _, _ = grafo
    _dos_ramas(versiones)
    escribir_migracion(versiones, "rm2", "rm1", cuerpo='op.execute("UPDATE roadmaps SET x = 1")')
    escribir_migracion(versiones, "rm3", "rm2", cuerpo='op.execute("SELECT 1")  # diagnostico_respuestas en un comentario')
    assert _fallos(grafo) == []


def test_sin_merges_entre_salas(grafo):
    versiones, _, _ = grafo
    _dos_ramas(versiones)
    assert _fallos(grafo) == []
    escribir_migracion(versiones, "union", ("rm1", "dg1"))
    assert any("union" in f and "depends_on" in f for f in _fallos(grafo))


def test_merges_historicos_anteriores_a_la_base_comun_no_cuentan(grafo):
    versiones, _, _ = grafo
    escribir_migracion(versiones, "viejo_a", BASE)
    escribir_migracion(versiones, "viejo_b", BASE)
    escribir_migracion(versiones, "fusion", ("viejo_a", "viejo_b"))
    guion = guion_de(grafo[2])
    assert AS.fallos_sin_merges_entre_salas(guion, "fusion") == []


# ---- upgrade heads contra el PostgreSQL 16 local -----------------------------------------------

def _url_local() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("MIGRATION_DATABASE_URL") or ""
    if not url:
        pytest.skip("sin TEST_DATABASE_URL: esta prueba exige el PostgreSQL 16 local del arnés")
    if (urlsplit(url).hostname or "") not in ("localhost", "127.0.0.1", "::1"):
        pytest.skip("la URL no es local: una URL remota no habilita pruebas con base")
    return url


def test_upgrade_heads_local(tmp_path):
    """`upgrade heads` aplica las dos ramas y deja `current == heads`.

    Corre en un esquema propio y desechable (nombre único por prueba) dentro de la base que el arnés da a este
    trabajador de xdist: no abre conexiones a otra base ni crea ni borra bases, que es lo que el resto de
    trabajadores tocan (clonado de la plantilla con `pg_terminate_backend`). Cada paso usa su conexión.
    """
    import psycopg
    from psycopg import sql
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    url = _url_local().replace("postgresql+psycopg://", "postgresql://", 1)
    partes = urlsplit(url)
    esquema = "ci28_" + uuid.uuid4().hex[:10]
    versiones = tmp_path / "versions"
    escribir_migracion(versiones, BASE, None, cuerpo='op.execute("CREATE TABLE ci28_base (id int)")')
    escribir_migracion(versiones, "rm1", BASE, labels=("roadmap",), cuerpo='op.execute("CREATE TABLE ci28_rm (id int)")')
    escribir_migracion(versiones, "dg1", BASE, labels=("diagnostico",), cuerpo='op.execute("CREATE TABLE ci28_dg (id int)")')
    (tmp_path / "env.py").write_text(
        "import os\nfrom alembic import context\nfrom sqlalchemy import create_engine\n"
        "motor = create_engine(os.environ['CI28_URL'])\n"
        "with motor.connect() as c:\n    context.configure(connection=c)\n    with context.begin_transaction():\n"
        "        context.run_migrations()\n    c.commit()\nmotor.dispose()\n", encoding="utf-8")
    (tmp_path / "script.py.mako").write_text("", encoding="utf-8")
    crear = sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(esquema))
    with psycopg.connect(url, autocommit=True) as con:
        con.execute(crear)
    try:
        destino = partes._replace(scheme="postgresql+psycopg", query="options=-csearch_path%3D" + esquema).geturl()
        os.environ["CI28_URL"] = destino
        config = Config()
        config.set_main_option("script_location", str(tmp_path))
        command.upgrade(config, "heads")
        motor = create_engine(destino)
        try:
            with motor.connect() as c:
                actuales = set(MigrationContext.configure(c).get_current_heads())
            with motor.connect() as c:
                tablas = {r[0] for r in c.exec_driver_sql(
                    "select tablename from pg_tables where schemaname = current_schema()")}
        finally:
            motor.dispose()
        assert actuales == set(guion_de(tmp_path).get_heads()) == {"rm1", "dg1"}
        assert {"ci28_base", "ci28_rm", "ci28_dg"} <= tablas
    finally:
        os.environ.pop("CI28_URL", None)
        borrar = sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(esquema))
        with psycopg.connect(url, autocommit=True) as con:
            con.execute(borrar)


# ---- Comprobación 5 de verificar_cloudsql_conexion.py ---------------------------------------------

def _verificador():
    spec = importlib.util.spec_from_file_location("verificar_cloudsql_conexion_ci28", RAIZ / "scripts" / "verificar_cloudsql_conexion.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo  # los dataclasses lo exigen
    spec.loader.exec_module(modulo)
    return modulo


def test_comprobacion_5_por_conjuntos():
    vc = _verificador()
    cabezas = {"rm1", "dg1"}
    assert vc.motivo_revision_por_conjuntos({"rm1", "dg1"}, cabezas) is None
    assert vc.motivo_revision_por_conjuntos(["dg1", "rm1"], cabezas) is None
    assert "atrasada" in vc.motivo_revision_por_conjuntos({"rm1"}, cabezas)
    assert "dg1" in vc.motivo_revision_por_conjuntos({"rm1"}, cabezas)
    assert "otra rama" in vc.motivo_revision_por_conjuntos({"rm1", "dg1", "zz"}, cabezas)
    assert "falta alembic_version" in vc.motivo_revision_por_conjuntos(None, cabezas)
    assert vc.motivo_revision_por_conjuntos({"unica"}, {"unica"}) is None


# ---- El despliegue usa todas las cabezas -----------------------------------------------------------

BRIEFS_DE_DESPLIEGUE = (
    "governance/operaciones/BRIEF_PROPIETARIO_BOV-01.md",
    "governance/apoyo/BRIEF_PROPIETARIO_DER04.md",
    "governance/operaciones/PRUEBAS_EN_FISICO.md",
    "governance/operaciones/entornos/produccion/MIGRAR_PRODUCCION.md",
)


def _archivos_de_despliegue() -> list[Path]:
    flujos = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
    scripts = [p for p in sorted((RAIZ / "scripts").rglob("*")) if p.suffix in (".ps1", ".sh", ".bat")]
    dockerfiles = sorted(p for p in RAIZ.glob("*") if p.is_file() and (p.name == "Dockerfile" or p.name.endswith(".Dockerfile")))
    return flujos + scripts + dockerfiles + [RAIZ / b for b in BRIEFS_DE_DESPLIEGUE]


SIN_S = re.compile(r"\balembic(?:\.exe)?\s+upgrade\s+head(?!s)\b")


def fallos_de_despliegue(textos: dict[str, str]) -> list[str]:
    return [f"{nombre} usa «alembic upgrade head»; debe ser «upgrade heads»"
            for nombre, texto in textos.items() if SIN_S.search(texto)]


def test_despliegue_usa_heads():
    archivos = _archivos_de_despliegue()
    faltan = [p.relative_to(RAIZ).as_posix() for p in archivos if not p.is_file()]
    assert not faltan, f"archivos de despliegue que ya no existen (actualice la lista): {faltan}"
    textos = {p.relative_to(RAIZ).as_posix(): p.read_text(encoding="utf-8") for p in archivos}
    assert any(n.startswith(".github/workflows/") for n in textos) and any(n.endswith(".ps1") for n in textos)
    assert any(n.endswith("Dockerfile") for n in textos) and all(b in textos for b in BRIEFS_DE_DESPLIEGUE)
    assert fallos_de_despliegue(textos) == []


def test_despliegue_usa_heads_detecta_la_forma_antigua_en_cada_tipo():
    antiguas = {
        "flujo.yml": "run: python -m alembic upgrade head",
        "a.ps1": "python -m alembic upgrade head *> $null",
        "backend.Dockerfile": 'CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app"]',
        "BRIEF.md": r".\.venv\Scripts\alembic.exe upgrade head",
        "tabla.md": "| Comando | `alembic upgrade head` |",
    }
    for nombre, texto in antiguas.items():
        assert fallos_de_despliegue({nombre: texto}), nombre
        assert not fallos_de_despliegue({nombre: texto.replace("upgrade head", "upgrade heads")}), nombre
    assert not fallos_de_despliegue({"nota.md": "el comando antiguo era upgrade head (ya no se usa)"})
