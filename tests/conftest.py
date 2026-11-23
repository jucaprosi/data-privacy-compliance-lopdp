# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Fixtures compartidos. Fuerza las pruebas contra una base local (contenedor PostgreSQL 16 del arnés).

IMPORTANTE: en Windows, psycopg async requiere SelectorEventLoop,
no ProactorEventLoop. La policy se fija AL INICIO, antes de cualquier
import que toque asyncio.
"""
import asyncio
import os
import sys
import time
import uuid
import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

_DATABASE_URL_INICIAL = os.environ.get("DATABASE_URL")
_DATABASE_URL_DESARROLLO = "sqlite+aiosqlite:////tmp/test.db"


def _limpiar_sqlite_de_desarrollo() -> None:
    if (
        _DATABASE_URL_INICIAL is None
        and not os.environ.get("TEST_DATABASE_URL")
        and os.environ.get("DATABASE_URL") == _DATABASE_URL_DESARROLLO
    ):
        os.environ.pop("DATABASE_URL", None)


# ¤arbitro
# ¤¤qa-engineer
# Justificación: con un intérprete al que le faltan paquetes la suite falla lejos de la causa (un router que no
#   carga y un /health en 503). Se comprueba antes de importar nada más y se detiene con un único mensaje.
def _paquetes_que_faltan() -> list[str]:
    raiz = Path(__file__).resolve().parent.parent
    ruta, requisitos = raiz / "scripts" / "verificar_entorno.py", raiz / "requirements.txt"
    if not (ruta.exists() and requisitos.exists()):
        return []
    spec = importlib.util.spec_from_file_location("verificar_entorno_guardia", ruta)
    ve = importlib.util.module_from_spec(spec)
    sys.modules["verificar_entorno_guardia"] = ve
    spec.loader.exec_module(ve)
    return ve.faltantes(requisitos.read_text(encoding="utf-8-sig"), ve.instalados_ahora())


VARIABLES_DE_BASE: tuple[str, ...] = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL")
HOSTS_DE_PRUEBAS: tuple[str, ...] = ("localhost", "127.0.0.1", "::1")


class BaseNoDePruebas(RuntimeError):
    """Se lanza cuando alguna variable de base apunta fuera de los hosts locales permitidos."""

    def __init__(self, variables: tuple[str, ...]) -> None:
        self.variables: tuple[str, ...] = tuple(variables)
        nombres = ", ".join(self.variables)
        super().__init__(
            f"[ENTORNO] {nombres} debe apuntar a una base local. "
            "La suite se detiene sin conectarse."
        )


# ¤arbitro
# ¤¤qa-engineer
# Justificación: lista blanca única para toda la suite. Falla cerrada antes de abrir conexión alguna y nunca
#   imprime URLs, hosts ni credenciales: solo los nombres de las variables rechazadas.
def exigir_base_de_pruebas() -> None:
    """Verifica en os.environ que ninguna variable de base apunte fuera de HOSTS_DE_PRUEBAS."""
    rechazadas: list[str] = []
    for nombre in VARIABLES_DE_BASE:
        valor = os.environ.get(nombre)
        if not valor:
            continue
        try:
            partes = urlsplit(valor)
            _ = partes.port
        except ValueError:
            rechazadas.append(nombre)
            continue
        esquema = (partes.scheme or "").lower()
        hosts_query = [h.lower() for h in parse_qs(partes.query).get("host", [])]
        host = (partes.hostname or "").lower()
        query_invalida = any(h not in HOSTS_DE_PRUEBAS for h in hosts_query)
        esquema_valido = esquema == "postgres" or esquema.startswith("postgresql")
        if not esquema_valido or query_invalida or host not in HOSTS_DE_PRUEBAS:
            rechazadas.append(nombre)
    if rechazadas:
        raise BaseNoDePruebas(tuple(rechazadas))


def pytest_configure(config):
    try:
        exigir_base_de_pruebas()
    except BaseNoDePruebas as exc:
        pytest.exit(str(exc), returncode=3)
    if os.environ.get("TEST_DATABASE_URL"):
        os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    faltan = _paquetes_que_faltan()
    if faltan:
        pytest.exit(
            f"[ENTORNO] El interprete {sys.executable} (Python {sys.version.split()[0]}) no tiene: "
            f"{', '.join(faltan)}. Ejecute las pruebas con el entorno virtual del proyecto (carpeta .venv) o "
            "resuelva el interprete con scripts\\entorno.bat.",
            returncode=3,
        )
    if hasattr(config, "workerinput"):
        _preparar_trabajador(config)
    _respetar_orden_por_duracion(config)


def pytest_collection_modifyitems(config, items):
    if hasattr(config, "workerinput"):
        _ordenar_parametros(items)
        _ordenar_por_duracion(items)


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(collector):
    if not (hasattr(collector.config, "workerinput") and isinstance(collector, pytest.Module)):
        return (yield)
    antes = dict(_overrides_de_la_api())
    reporte = yield
    _OVERRIDES_POR_ARCHIVO[collector.nodeid] = _overrides_nuevos(antes, _overrides_de_la_api())
    return reporte


def pytest_unconfigure(config):
    if getattr(config, "_base_de_trabajador", None):
        _borrar_base_de_trabajador(*config._base_de_trabajador)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    _limpiar_sqlite_de_desarrollo()

# ---- FIX Windows + psycopg async ----
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# SEC-03: la API arranca en modo `oidc` por defecto. La suite usa identidad por cabeceras de forma
# explícita; las pruebas de test_autenticacion.py cambian a `oidc` con monkeypatch.
os.environ["AUTH_MODE"] = "headers"

import psycopg
import pytest_asyncio
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# ¤ci-cd
# ¤arbitro
# ¤¤qa-engineer
# Justificación: las pruebas hacen commit reales y por eso no pueden compartir base entre procesos. Cada trabajador de
#   xdist clona la suya de TEST_DATABASE_URL, ya migrada por quien lo lanza. El trabajador se reconoce por
#   config.workerinput y no por PYTEST_XDIST_WORKER: esa variable la heredan los pytest que las pruebas lanzan en
#   subprocesos, y sin -n nada de esto se ejecuta. Los pytest hijos tampoco deben heredar el -n de PYTEST_ADDOPTS.
INTENTOS_DE_CLONADO = 10


def _ordenar_parametros(items: list) -> None:
    """xdist aborta si dos trabajadores recogen listas distintas, y un parametrize sobre un set cambia de orden en cada
    proceso. Se conserva el orden de definición y solo se ordenan los parámetros de cada prueba."""
    posiciones: dict[str, int] = {}
    for item in items:
        posiciones.setdefault(item.nodeid.split("[")[0], len(posiciones))
    items.sort(key=lambda item: (posiciones[item.nodeid.split("[")[0]], item.nodeid))


# ¤ci-cd
# ¤arbitro
# ¤¤qa-engineer
# Justificación: solo se ordena en los trabajadores: en serie, que es como corre una base remota, el orden no acorta nada y cambiarlo
#   arriesga dependencias de orden. xdist reordena por número de pruebas con --dist loadfile y anularía esto sin avisar.
#   El import va dentro porque tests/test_conftest_guardias.py ejecuta una copia de este archivo a solas.
_DURACIONES = Path(__file__).with_name("duraciones.json")


def _respetar_orden_por_duracion(config) -> None:
    if _DURACIONES.exists():
        config.option.loadscopereorder = False


def _ordenar_por_duracion(items: list) -> None:
    from orden_por_duracion import cargar, ordenar

    ordenar(items, cargar(_DURACIONES))


# ¤ci-cd
# Justificación: dos archivos de prueba instalan dependency_overrides al importarse y otros los borran con clear(). En
#   serie el orden alfabético lo oculta; en paralelo el reparto cambia entre corridas. Cada trabajador empieza cada
#   archivo solo con los overrides que ese archivo instaló, y el resultado deja de depender del reparto.
_OVERRIDES_POR_ARCHIVO: dict[str, dict] = {}


def _overrides_de_la_api() -> dict:
    principal = sys.modules.get("main")
    return principal.app.dependency_overrides if hasattr(principal, "app") else {}


def _overrides_nuevos(antes: dict, ahora: dict) -> dict:
    return {clave: valor for clave, valor in ahora.items() if antes.get(clave) is not valor}


def _restablecer_overrides(archivo: str) -> None:
    overrides = _overrides_de_la_api()
    overrides.clear()
    overrides.update(_OVERRIDES_POR_ARCHIVO.get(archivo, {}))


def _nombre_de_clon(plantilla: str, trabajador: str, corrida: str) -> str:
    return f"{plantilla}_{trabajador}_{corrida[:8]}".lower()


def _conectar_a_mantenimiento(url: URL):
    destino = url.set(drivername="postgresql", database="postgres")
    return psycopg.connect(destino.render_as_string(hide_password=False), autocommit=True)


def _clonar_plantilla(conexion, plantilla: str, clon: str) -> None:
    """PostgreSQL rechaza clonar una base con sesiones abiertas: se cierran todas justo antes de cada intento."""
    crear = sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(clon), sql.Identifier(plantilla))
    for intento in range(1, INTENTOS_DE_CLONADO + 1):
        conexion.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
            (plantilla,),
        )
        try:
            conexion.execute(crear)
            return
        except psycopg.errors.ObjectInUse:
            if intento == INTENTOS_DE_CLONADO:
                raise
            time.sleep(0.2 * intento)


def _preparar_trabajador(config) -> None:
    os.environ.pop("PYTEST_ADDOPTS", None)
    original = os.environ.get("TEST_DATABASE_URL")
    if not original:
        return
    url = make_url(original)
    entrada = config.workerinput
    clon = _nombre_de_clon(url.database, entrada["workerid"], entrada["testrunuid"])
    with _conectar_a_mantenimiento(url) as conexion:
        _clonar_plantilla(conexion, url.database, clon)
    config._base_de_trabajador = (url, clon)
    propia = url.set(database=clon).render_as_string(hide_password=False)
    for nombre in VARIABLES_DE_BASE:
        if os.environ.get(nombre) == original:
            os.environ[nombre] = propia


def _borrar_base_de_trabajador(url: URL, clon: str) -> None:
    borrar = sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(clon))
    with _conectar_a_mantenimiento(url) as conexion:
        conexion.execute(borrar)


@pytest.fixture(autouse=True, scope="module")
def overrides_de_cada_archivo(request):
    if hasattr(request.config, "workerinput"):
        _restablecer_overrides(request.node.nodeid)
    yield


@pytest.fixture(autouse=True)
def sustituciones_de_dependencias_restauradas():
    """Cada prueba deja `app.dependency_overrides` como lo encontró. `app` es compartida por todo el
    proceso: una sustitución olvidada alcanza a las pruebas siguientes y el fallo depende del orden."""
    modulo = sys.modules.get("main")
    antes = dict(modulo.app.dependency_overrides) if modulo else {}
    yield
    modulo = sys.modules.get("main")
    if modulo:
        modulo.app.dependency_overrides.clear()
        modulo.app.dependency_overrides.update(antes)


@pytest_asyncio.fixture
async def db_engine():
    """Engine async apuntando a la base de pruebas local."""
    _limpiar_sqlite_de_desarrollo()
    exigir_base_de_pruebas()
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Sesión async con cleanup automático."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def seed_tenants(db_session):
    """Crea 2 tenants + 2 users + roles. Cleanup al final."""
    ta = f"test-ta-{uuid.uuid4().hex[:8]}"
    tb = f"test-tb-{uuid.uuid4().hex[:8]}"
    ua = f"test-ua-{uuid.uuid4().hex[:8]}"
    ub = f"test-ub-{uuid.uuid4().hex[:8]}"

    for tid in (ta, tb):
        await db_session.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                 "VALUES (:id, :n, :r, :ruc)"),
            {"id": tid, "n": f"Test {tid}", "r": f"Test {tid} SA", "ruc": f"RUC{tid[:20]}"},
        )

    for uid in (ua, ub):
        await db_session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
            {"id": uid, "e": f"{uid}@test.local", "n": f"User {uid}"},
        )

    await db_session.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
             "VALUES (:id, :uid, :tid, 'implementador')"),
        {"id": f"role-a-{uuid.uuid4().hex[:8]}", "uid": ua, "tid": ta},
    )
    await db_session.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
             "VALUES (:id, :uid, :tid, 'implementador')"),
        {"id": f"role-b-{uuid.uuid4().hex[:8]}", "uid": ub, "tid": tb},
    )
    await db_session.commit()

    yield {"tenant_a": ta, "tenant_b": tb, "user_a": ua, "user_b": ub}

    # Cleanup
    try:
        await db_session.execute(
            text("DELETE FROM task_audit_log WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM task_evidence WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM task_dependencies WHERE task_id IN "
                 "(SELECT id FROM roadmap_tasks WHERE tenant_id IN (:a, :b))"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmap_tasks WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmap_waves WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmaps WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM users WHERE id IN (:a, :b)"),
            {"a": ua, "b": ub},
        )
        await db_session.execute(
            text("DELETE FROM tenants WHERE id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.commit()
    except Exception:
        await db_session.rollback()
