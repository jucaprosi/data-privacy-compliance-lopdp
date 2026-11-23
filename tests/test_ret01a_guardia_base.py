# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""Pruebas unitarias y por AST de la guardia única de base local `exigir_base_de_pruebas`."""
import ast
from pathlib import Path

import pytest

from conftest import BaseNoDePruebas, HOSTS_DE_PRUEBAS, VARIABLES_DE_BASE, exigir_base_de_pruebas

CONFTEST_RUTA = Path(__file__).resolve().parent / "conftest.py"


def _limpiar_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for nombre in VARIABLES_DE_BASE:
        monkeypatch.delenv(nombre, raising=False)


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_hosts_locales_pasan(monkeypatch: pytest.MonkeyPatch, host: str) -> None:
    _limpiar_variables(monkeypatch)
    for nombre in VARIABLES_DE_BASE:
        monkeypatch.setenv(nombre, f"postgresql+psycopg://u:p@{host}:5432/lopdp")
    exigir_base_de_pruebas()


def test_host_no_local_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    _limpiar_variables(monkeypatch)
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql://u:p@base.ejemplo.test:5432/lopdp")
    with pytest.raises(BaseNoDePruebas) as exc:
        exigir_base_de_pruebas()
    assert exc.value.variables == ("TEST_DATABASE_URL",)
    assert "TEST_DATABASE_URL" in str(exc.value)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://u:p@/lopdp?host=/cloudsql/proyecto:region:instancia",
        "postgresql:///lopdp?host=/cloudsql/proyecto:region:instancia",
        "postgresql://localhost/lopdp?host=/cloudsql/proyecto:region:instancia",
    ],
)
def test_socket_de_la_nube_falla(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    _limpiar_variables(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(BaseNoDePruebas) as exc:
        exigir_base_de_pruebas()
    assert exc.value.variables == ("DATABASE_URL",)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql:///lopdp",
        "postgresql://:5432/lopdp",
        ":::invalida",
        "postgresql://[::1:5432/lopdp",
        "no-es-una-url",
        "http://127.0.0.1:5432/lopdp",
    ],
)
def test_url_dudosa_falla(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    _limpiar_variables(monkeypatch)
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    with pytest.raises(BaseNoDePruebas) as exc:
        exigir_base_de_pruebas()
    assert exc.value.variables == ("TEST_DATABASE_URL",)


def test_las_tres_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    _limpiar_variables(monkeypatch)
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/lopdp")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/lopdp")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://u:p@base.ejemplo.test:5432/lopdp")
    with pytest.raises(BaseNoDePruebas) as exc:
        exigir_base_de_pruebas()
    assert exc.value.variables == ("MIGRATION_DATABASE_URL",)


def test_sin_valores(monkeypatch: pytest.MonkeyPatch) -> None:
    _limpiar_variables(monkeypatch)
    secreto = "secreto-ultrasecreto-987"
    host = "privada.ejemplo.test"
    url = f"postgresql://usuaria_oculta:{secreto}@{host}:5432/lopdp"
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    with pytest.raises(BaseNoDePruebas) as exc:
        exigir_base_de_pruebas()
    representaciones = f"{exc.value!s} {exc.value!r}"
    assert "TEST_DATABASE_URL" in representaciones
    assert url not in representaciones
    assert host not in representaciones
    assert "usuaria_oculta" not in representaciones
    assert secreto not in representaciones


def test_falla_cerrada() -> None:
    arbol = ast.parse(CONFTEST_RUTA.read_text(encoding="utf-8"))
    funcion = next(
        n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "exigir_base_de_pruebas"
    )
    llamadas: list[str] = []
    for nodo in ast.walk(funcion):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            llamadas.append(nodo.func.attr)
        if isinstance(nodo, ast.Return) and nodo.value is not None:
            pytest.fail("exigir_base_de_pruebas no debe devolver valor")
    assert "skip" not in llamadas
    assert "xfail" not in llamadas


def test_una_sola_comprobacion() -> None:
    arbol = ast.parse(CONFTEST_RUTA.read_text(encoding="utf-8"))
    funciones = [n for n in ast.walk(arbol) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    lectoras_hosts = []
    for fn in funciones:
        for nodo in ast.walk(fn):
            if isinstance(nodo, ast.Name) and nodo.id == "HOSTS_DE_PRUEBAS":
                lectoras_hosts.append(fn.name)
                break
            if isinstance(nodo, ast.Constant) and nodo.value in HOSTS_DE_PRUEBAS:
                pytest.fail(f"Host literal {nodo.value!r} repetido en función {fn.name}")
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id in ("urlsplit", "urlparse"):
                if fn.name != "exigir_base_de_pruebas":
                    pytest.fail(f"Inspección de URL fuera de exigir_base_de_pruebas: {fn.name}")
    assert lectoras_hosts == ["exigir_base_de_pruebas"]
