# ¤arbitro ¤seguridad
"""RET-01 · Configuración solo por variables de entorno del proceso y guardia única de base local.

Cubre los criterios de aceptación de `governance/especificaciones/RET-01.md`:
- Un `.env` en el directorio de trabajo se ignora (`app_core/config.py` solo lee `os.environ`).
- La suite, `AUTH_MODE=headers`, Alembic, `pre-push` y scripts solo aceptan PostgreSQL local
  (`localhost`, `127.0.0.1`, `::1`); `/cloudsql/` y hosts remotos fallan cerrado sin filtrar URLs.
- El arranque de Cloud Run (`K_SERVICE` + `AUTH_MODE=oidc` + `/cloudsql/...`) no activa la guardia local.
- Configuración exclusiva mediante `os.environ`, `VARIABLES_DE_NUBE == ("K_SERVICE",)` y `HOSTS_LOCALES`.
"""
from __future__ import annotations

import ast
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import conftest
from app_core.huellas_produccion import (
    HOSTS_LOCALES, INSTANCIA_CLOUD_SQL_PRODUCCION, VARIABLES_DE_NUBE, BaseNoLocal, es_base_local,
    exigir_base_local,
)
from app_core.security import REGLA_ARRANQUE, exigir_arranque_seguro

RAIZ = Path(__file__).resolve().parent.parent


def test_env_en_carpeta_se_ignora(tmp_path: Path) -> None:
    """Un `.env` presente en el cwd no altera `os.environ` ni `app_core.config`."""
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://u:secreto-env@db.env.invalid:5432/prod\n"
        "MIGRATION_DATABASE_URL=postgresql://u:secreto-env@db.env.invalid:5432/prod\n"
        "CORS_ORIGINS=https://env.invalid\n"
        "JWT_SECRET=clave-secreta-del-archivo-local-debe-ignorarse\n",
        encoding="utf-8",
    )
    quitar = {"DATABASE_URL", "MIGRATION_DATABASE_URL", "TEST_DATABASE_URL", "CORS_ORIGINS", "JWT_SECRET", "K_SERVICE"}
    env = {k: v for k, v in os.environ.items() if k not in quitar}
    env["PYTHONPATH"] = str(RAIZ)
    env["PYTHONIOENCODING"] = "utf-8"
    codigo = (
        "import json, os; "
        "from app_core.config import CLAVE_JWT_DESARROLLO, CORS_ORIGINS_DESARROLLO, DATABASE_URL_DESARROLLO, config; "
        "print(json.dumps({"
        "'db': config.database_url, 'env_db': os.environ.get('DATABASE_URL'), "
        "'cors': config.cors_origins, 'jwt_default': config.jwt_secret == CLAVE_JWT_DESARROLLO, "
        "'esperado_db': DATABASE_URL_DESARROLLO, 'esperado_cors': CORS_ORIGINS_DESARROLLO}))"
    )
    res = subprocess.run([sys.executable, "-c", codigo], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    assert "db.env.invalid" not in res.stdout and "secreto-env" not in res.stdout
    import json
    datos = json.loads(res.stdout.strip().splitlines()[-1])
    assert datos["db"] == datos["esperado_db"]
    assert datos["env_db"] == datos["esperado_db"]
    assert datos["cors"] == datos["esperado_cors"]
    assert datos["jwt_default"] is True


@pytest.mark.parametrize("variable", ["TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL"])
@pytest.mark.parametrize("url_no_local", [
    "postgresql://usuario:secreto-suite@db.remota.invalid:5432/lopdp",
    "postgresql://usuario:secreto-suite@/lopdp?host=/cloudsql/evydentia-pruebas:us-central1:evydentia-pruebas",
])
def test_suite_solo_con_base_local(tmp_path: Path, variable: str, url_no_local: str) -> None:
    """La suite falla cerrado (código 3) antes de correr pruebas si alguna URL no es local."""
    (tmp_path / "tests").mkdir()
    shutil.copy(RAIZ / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k and k != "PYTEST_ADDOPTS"}
    env[variable] = url_no_local
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
    )
    salida = res.stdout + res.stderr
    assert res.returncode == 3
    assert variable in salida
    assert "secreto-suite" not in salida and "db.remota.invalid" not in salida and "passed" not in salida


@pytest.mark.parametrize("url_cloudsql", [
    f"postgresql+asyncpg://lopdp_app:secreto@/evydentia?host=/cloudsql/{INSTANCIA_CLOUD_SQL_PRODUCCION}",
    "postgresql+psycopg://lopdp_app:secreto@/lopdp?host=/cloudsql/evydentia-pruebas:us-central1:evydentia-pruebas",
    "postgresql://lopdp_app:secreto@/lopdp?unix_sock=/cloudsql/proyecto:region:instancia/.s.PGSQL.5432",
    "postgresql://lopdp_app:secreto@localhost/lopdp?host=/cloudsql/proyecto:region:instancia",
    "postgresql://lopdp_app:secreto@/lopdp?host=%2Fcloudsql%2Fproyecto%3Aregion%3Ainstancia",
    "postgresql://lopdp_app:secreto@/lopdp?host=%252Fcloudsql%252Fproyecto%253Aregion%253Ainstancia",
])
def test_cloudsql_no_es_local(monkeypatch: pytest.MonkeyPatch, url_cloudsql: str) -> None:
    """Un socket `/cloudsql/...` nunca es local, ni para herramientas ni para `AUTH_MODE=headers`."""
    assert es_base_local(url_cloudsql, {}) is False
    for nombre in ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setenv("AUTH_MODE", "headers")
    monkeypatch.setenv("DATABASE_URL", url_cloudsql)
    with pytest.raises(BaseNoLocal):
        exigir_base_local()
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    assert REGLA_ARRANQUE in str(error.value) and "DATABASE_URL" in str(error.value)


def test_guardia_no_rige_el_arranque_de_produccion() -> None:
    """Cloud Run (`K_SERVICE` + `AUTH_MODE=oidc` + `/cloudsql/<prod>`) arranca sin activar la guardia local."""
    env = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    env.update(
        K_SERVICE="evydentia-backend",
        APP_ENV="production",
        ENVIRONMENT="production",
        AUTH_MODE="oidc",
        DATABASE_URL=f"postgresql+asyncpg://lopdp_app:secreto-prod@/evydentia?host=/cloudsql/{INSTANCIA_CLOUD_SQL_PRODUCCION}",
        CLOUD_SQL_INSTANCE=INSTANCIA_CLOUD_SQL_PRODUCCION,
        CORS_ORIGINS="https://app.evydentia.com",
        JWT_SECRET=secrets.token_urlsafe(32),
        SESSION_SECRET=secrets.token_urlsafe(32),
        PROXIES_CONFIABLES="1",
        PYTHONIOENCODING="utf-8",
    )
    res = subprocess.run(
        [sys.executable, "-c", "from main import app; print(app.title)"],
        cwd=RAIZ, env=env, capture_output=True, text=True, timeout=180,
    )
    assert res.returncode == 0, res.stderr[-2000:]
    assert "EVYDENTIA" in res.stdout


def test_sec15_guarda_arranque(monkeypatch: pytest.MonkeyPatch) -> None:
    """Con `AUTH_MODE=headers`, solo hosts locales pasan y cualquier no-local o nube falla cerrado."""
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("CLOUD_SQL_INSTANCE", raising=False)
    monkeypatch.setenv("AUTH_MODE", "headers")
    for nombre in ("DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT"):
        monkeypatch.setenv(nombre, "postgresql+psycopg://u:secreto@127.0.0.1:5432/lopdp")
    exigir_arranque_seguro()

    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+psycopg://u:secreto-2@db.externa.invalid:5432/lopdp")
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    assert REGLA_ARRANQUE in str(error.value) and "MIGRATION_DATABASE_URL" in str(error.value)
    assert "secreto-2" not in str(error.value) and "db.externa.invalid" not in str(error.value)


def test_puntos_de_entrada_misma_guardia() -> None:
    """Todos los puntos de entrada comparten la lista blanca de hosts locales y rechazan hosts no locales."""
    assert VARIABLES_DE_NUBE == ("K_SERVICE",)
    assert HOSTS_LOCALES == conftest.HOSTS_DE_PRUEBAS == ("localhost", "127.0.0.1", "::1")

    for relativa in (
        "app_core/security.py",
        "alembic/env.py",
        "scripts/capacidades_biblioteca.py",
        "scripts/crear_organizacion_dev.py",
        "scripts/demo/sembrar_plantilla.py",
        "scripts/sembrar_entorno_pruebas.py",
        "scripts/importar_catalogo_biblioteca.py",
    ):
        arbol = ast.parse((RAIZ / relativa).read_text(encoding="utf-8"))
        modulos = {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module}
        assert "app_core.huellas_produccion" in modulos, relativa

    hook = (RAIZ / ".githooks" / "pre-push").read_text(encoding="utf-8")
    assert "app_core.huellas_produccion" in hook and "exigir_base_local" in hook

    # Verificar fallo cerrado real de alembic/env.py antes de abrir conexión
    env_alembic = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    env_alembic["MIGRATION_DATABASE_URL"] = "postgresql://u:secreto-alembic@db.remota.invalid/lopdp"
    env_alembic["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=RAIZ, env=env_alembic, capture_output=True, text=True, timeout=60,
    )
    assert res.returncode != 0
    assert "MIGRATION_DATABASE_URL" in res.stderr
    assert "secreto-alembic" not in res.stderr and "db.remota.invalid" not in res.stderr


def test_sin_dotenv() -> None:
    """La configuración lee solo `os.environ` y las herramientas usan `entorno_local.ps1` y `K_SERVICE`."""
    assert VARIABLES_DE_NUBE == ("K_SERVICE",)
    assert HOSTS_LOCALES == ("localhost", "127.0.0.1", "::1")
    requisitos = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pydantic-settings" in requisitos
    assert "google-cloud-storage" in requisitos
    assert "google-genai" in requisitos
    assert (RAIZ / "scripts" / "entorno_local.ps1").is_file()

    doc = (RAIZ / "governance" / "operaciones" / "ENTORNO_LOCAL.md").read_text(encoding="utf-8")
    for esperado in ("entorno_local.ps1", "DATABASE_URL", "MIGRATION_DATABASE_URL", "TEST_DATABASE_URL",
                     "APP_ENV", "AUTH_MODE", "CORS_ORIGINS", "JWT_SECRET", "SESSION_SECRET", "K_SERVICE",
                     "HUELLA_PROYECTO_PRODUCCION"):
        assert esperado in doc, esperado

    config_src = (RAIZ / "app_core" / "config.py").read_text(encoding="utf-8")
    assert "os.environ" in config_src
    assert 'SettingsConfigDict(extra="ignore")' in config_src

    for relativa in (
        "app_core/config.py",
        "app_core/huellas_produccion.py",
        "app_core/security.py",
        "app_core/entorno/guardias.py",
        "alembic/env.py",
        ".githooks/pre-push",
        "scripts/capacidades_biblioteca.py",
        "scripts/crear_organizacion_dev.py",
        "scripts/demo/sembrar_plantilla.py",
        "scripts/sembrar_entorno_pruebas.py",
        "scripts/importar_catalogo_biblioteca.py",
    ):
        ruta = RAIZ / relativa
        assert ruta.is_file(), relativa
        texto = ruta.read_text(encoding="utf-8")
        if ruta.suffix == ".py":
            ast.parse(texto, filename=str(ruta))
        else:
            assert "exigir_base_local" in texto, relativa
