"""Fixtures compartidos. Fuerza tests contra el branch test de Neon.

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

import pytest


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


_FALTAN = _paquetes_que_faltan()
HOST_PRODUCCION = "ep-late-hall"


def _worktree_sin_env() -> bool:
    """Un worktree tiene `.git` como archivo. Sin `.env` propio no hereda el de la carpeta principal, que trae producción."""
    raiz = Path(__file__).resolve().parent.parent
    return (raiz / ".git").is_file() and not (raiz / ".env").exists()


# ¤arbitro
# ¤¤qa-engineer
# Justificación: la suite escribe en la base. Se comprueban las dos variables de las que salen sus conexiones, ya con
#   TEST_DATABASE_URL aplicada sobre DATABASE_URL. Nunca se imprime el valor: solo el nombre de la variable.
def _variables_con_produccion() -> list[str]:
    nombres = ("TEST_DATABASE_URL", "DATABASE_URL")
    return [n for n in nombres if HOST_PRODUCCION in os.environ.get(n, "").lower()]


_WORKTREE_SIN_ENV = _worktree_sin_env()


def pytest_configure(config):
    if _WORKTREE_SIN_ENV:
        pytest.exit(
            "[ENTORNO] Este worktree no tiene .env propio y la suite no usa el de la carpeta principal porque apunta a "
            "produccion. Cree aqui un .env con TEST_DATABASE_URL de su rama de pruebas (test-<persona>).",
            returncode=3,
        )
    prohibidas = _variables_con_produccion()
    if prohibidas:
        pytest.exit(
            f"[ENTORNO] {', '.join(prohibidas)} apunta a produccion. La suite se detiene sin conectarse.",
            returncode=3,
        )
    if _FALTAN:
        pytest.exit(
            f"[ENTORNO] El interprete {sys.executable} (Python {sys.version.split()[0]}) no tiene: "
            f"{', '.join(_FALTAN)}. Ejecute las pruebas con el entorno virtual del proyecto (carpeta .venv) o "
            "resuelva el interprete con scripts\\entorno.bat.",
            returncode=3,
        )
    if _paralelo_sobre_neon(config):
        pytest.exit(
            "[ENTORNO] Pytest en paralelo clona la base y cierra sus conexiones: solo vale con PostgreSQL local o de "
            "contenedor, no con una rama Neon compartida. Ejecute sin -n.",
            returncode=3,
        )
    if hasattr(config, "workerinput"):
        _preparar_trabajador(config)


def pytest_collection_modifyitems(config, items):
    if hasattr(config, "workerinput"):
        _ordenar_parametros(items)


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

# ---- FIX Windows + psycopg async ----
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)

# SEC-03: la API arranca en modo `oidc` por defecto. La suite usa identidad por cabeceras de forma
# explícita; las pruebas de test_autenticacion.py cambian a `oidc` con monkeypatch.
os.environ["AUTH_MODE"] = "headers"

# Forzar DATABASE_URL al branch test (session.py lo lee al importar)
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

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
VARIABLES_DE_BASE = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL")
INTENTOS_DE_CLONADO = 10


def _ordenar_parametros(items: list) -> None:
    """xdist aborta si dos trabajadores recogen listas distintas, y un parametrize sobre un set cambia de orden en cada
    proceso. Se conserva el orden de definición y solo se ordenan los parámetros de cada prueba."""
    posiciones: dict[str, int] = {}
    for item in items:
        posiciones.setdefault(item.nodeid.split("[")[0], len(posiciones))
    items.sort(key=lambda item: (posiciones[item.nodeid.split("[")[0]], item.nodeid))


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


def _paralelo_sobre_neon(config) -> bool:
    return bool(config.getoption("numprocesses", None)) and "neon" in os.environ.get("TEST_DATABASE_URL", "").lower()


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


class _RedisEnMemoria:
    """Doble mínimo de Upstash para entornos sin UPSTASH_REDIS_URL (CI)."""

    def __init__(self):
        self.hashes, self.listas = {}, {}

    def hset(self, key, mapping):
        self.hashes.setdefault(key, {}).update({k: str(v) for k, v in mapping.items()})

    def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    def expire(self, key, seconds):
        return True

    def rpush(self, key, value):
        self.listas.setdefault(key, []).append(value)

    def lpop(self, key):
        lista = self.listas.get(key)
        return lista.pop(0) if lista else None


class _R2Firmador:
    """Doble de boto3 para entornos sin credenciales R2 (CI): firma sin red."""

    def generate_presigned_url(self, operation, Params, ExpiresIn=None):
        return f"https://r2.test/{Params.get('Key')}?op={operation}"

    def delete_object(self, Bucket, Key):
        return None


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


@pytest.fixture(autouse=True)
def servicios_externos_sin_credenciales(monkeypatch):
    """Sin credenciales de Redis o R2, sustituye esos clientes por dobles locales."""
    if not os.environ.get("UPSTASH_REDIS_URL"):
        from app_core.queue import redis_client
        monkeypatch.setattr(redis_client, "_client", _RedisEnMemoria())
    if not os.environ.get("R2_ACCESS_KEY_ID"):
        from app_core.storage import r2
        monkeypatch.setattr(r2, "_client", _R2Firmador())


@pytest_asyncio.fixture
async def db_engine():
    """Engine async apuntando al branch test."""
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
