# ¤ci-cd
# ¤arbitro
# ¤¤qa-engineer
"""Cuenta lo que cada prueba envía a la base. Se activa con `-p plugin_contar_consultas --consultas-json salida.json`.

Las sentencias no son los únicos viajes de red: abrir una conexión, BEGIN, COMMIT, ROLLBACK y el pre_ping de cada
checkout también pagan la latencia y no pasan por before_cursor_execute. Por eso se cuentan aparte. Solo se guardan
contadores: ni texto de sentencias ni parámetros, que pueden llevar datos. Debe correr en serie: con xdist cada proceso
vería solo sus pruebas. No se ve lo que use psycopg directamente ni lo que ocurra en subprocesos.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

CONTADORES = ("consultas", "conexiones", "checkouts", "begin", "commit", "rollback")
FASES = ("setup", "call", "teardown")
_ACTIVO: list["Contador"] = []  # pytest_runtest_logreport no recibe la configuración


class Contador:
    """Reparte cada evento entre la prueba y la fase en curso; lo que ocurre fuera de una prueba no se atribuye."""

    def __init__(self) -> None:
        self.por_prueba: dict[str, dict[str, Counter]] = defaultdict(lambda: {fase: Counter() for fase in FASES})
        self.segundos: Counter = Counter()
        self.actual: tuple[str, str] | None = None
        self._escuchas = [
            (Engine, "before_cursor_execute", self._al_ejecutar),
            (Engine, "begin", lambda *_: self._sumar("begin")),
            (Engine, "commit", lambda *_: self._sumar("commit")),
            (Engine, "rollback", lambda *_: self._sumar("rollback")),
            (Pool, "connect", lambda *_: self._sumar("conexiones")),
            (Pool, "checkout", lambda *_: self._sumar("checkouts")),
        ]

    def _sumar(self, contador: str) -> None:
        if self.actual:
            nodeid, fase = self.actual
            self.por_prueba[nodeid][fase][contador] += 1

    def _al_ejecutar(self, conn, cursor, statement, parameters, context, executemany) -> None:
        self._sumar("consultas")

    def instalar(self) -> None:
        for objetivo, nombre, funcion in self._escuchas:
            event.listen(objetivo, nombre, funcion)

    def retirar(self) -> None:
        for objetivo, nombre, funcion in self._escuchas:
            event.remove(objetivo, nombre, funcion)

    def filas(self) -> list[dict]:
        filas = []
        for nodeid, fases in sorted(self.por_prueba.items()):
            fila = {"nodeid": nodeid, "segundos": round(self.segundos[nodeid], 3)}
            for contador in CONTADORES:
                fila[contador] = sum(fases[fase][contador] for fase in FASES)
            fila["consultas_en_fixtures"] = fases["setup"]["consultas"] + fases["teardown"]["consultas"]
            filas.append(fila)
        return filas


def pytest_addoption(parser):
    parser.addoption("--consultas-json", default=None, help="archivo donde escribir los contadores por prueba")


def pytest_configure(config):
    if config.getoption("--consultas-json"):
        if config.getoption("numprocesses", None):
            raise pytest.UsageError("plugin_contar_consultas debe correr en serie, sin -n.")
        config._contador_consultas = Contador()
        config._contador_consultas.instalar()
        _ACTIVO.append(config._contador_consultas)


def pytest_unconfigure(config):
    contador = getattr(config, "_contador_consultas", None)
    if contador:
        contador.retirar()
        _ACTIVO.remove(contador)
        Path(config.getoption("--consultas-json")).write_text(json.dumps(contador.filas(), indent=1), encoding="utf-8")


def _en_fase(item, fase: str):
    contador = getattr(item.config, "_contador_consultas", None)
    if contador:
        contador.actual = (item.nodeid, fase)
        contador.por_prueba[item.nodeid]  # una prueba sin consultas también cuenta como prueba
    yield
    if contador:
        contador.actual = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    yield from _en_fase(item, "setup")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    yield from _en_fase(item, "call")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    yield from _en_fase(item, "teardown")


def pytest_runtest_logreport(report):
    if _ACTIVO:
        _ACTIVO[0].segundos[report.nodeid] += report.duration
