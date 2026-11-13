# ¤seguridad ¤rbac-tenant ¤arbitro
"""SEC-17 · Configuración mínima en la nube.

Contrato: `INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED`. «Nube» ≡ `K_SERVICE` definida (Cloud Run), como en
SEC-16. En la nube:
    DATABASE_URL = ∅ ∨ ¬postgresql ∨ usuario ≠ lopdp_app                         ⟹  no arranca;
    CORS_ORIGINS = ∅ ∨ ∃ origen : origen = ∅ ∨ '*' ∈ origen ∨ ¬https ∨ con ruta  ⟹  no arranca.
Fuera de la nube se conservan los valores de desarrollo.

Solo URL ficticias, generadas en la prueba: host `.invalid` (RFC 2606) y contraseñas aleatorias.

Mutación documentada: aceptar `*` en `CORS_ORIGINS` (quitar la comprobación `"*" in origen` de
`app_core/config.py#SEC-17`) hace fallar `test_en_la_nube_rechaza_el_comodin_en_cors`.
"""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from app_core.config import REGLA_CONFIGURACION, USUARIO_BD_APLICACION, exigir_configuracion_en_la_nube

RAIZ = Path(__file__).resolve().parent.parent
NUBE = {"K_SERVICE": "evydentia-backend"}
CORS_VALIDO = "https://app.ejemplo.invalid,https://admin.ejemplo.invalid"


def _url(usuario: str = USUARIO_BD_APLICACION, esquema: str = "postgresql+psycopg") -> tuple[str, str]:
    clave = secrets.token_urlsafe(24)
    return f"{esquema}://{usuario}:{clave}@db.ejemplo.invalid:5432/evydentia", clave


def _validos() -> dict:
    return {**NUBE, "DATABASE_URL": _url()[0], "CORS_ORIGINS": CORS_VALIDO}


def _rechaza(entorno: dict, variable: str) -> str:
    with pytest.raises(RuntimeError) as error:
        exigir_configuracion_en_la_nube(entorno)
    mensaje = str(error.value)
    assert REGLA_CONFIGURACION in mensaje and variable in mensaje
    url = entorno.get("DATABASE_URL")
    if url:
        assert url not in mensaje
        assert "db.ejemplo.invalid" not in mensaje
    return mensaje


# ----------------------------------------------------------------------------- DATABASE_URL

@pytest.mark.parametrize("valor", [None, "", "   "])
def test_en_la_nube_rechaza_database_url_ausente(valor):
    entorno = _validos()
    if valor is None:
        del entorno["DATABASE_URL"]
    else:
        entorno["DATABASE_URL"] = valor
    assert "falta DATABASE_URL" in _rechaza(entorno, "DATABASE_URL")


def test_en_la_nube_rechaza_sqlite():
    entorno = {**_validos(), "DATABASE_URL": "sqlite+aiosqlite:////tmp/test.db"}
    assert "PostgreSQL" in _rechaza(entorno, "DATABASE_URL")


@pytest.mark.parametrize("usuario", ["lopdp_beta_owner", "evydentia_app", "postgres", "lopdp_app_x"])
def test_en_la_nube_rechaza_otro_rol(usuario):
    url, clave = _url(usuario)
    mensaje = _rechaza({**_validos(), "DATABASE_URL": url}, "DATABASE_URL")
    assert USUARIO_BD_APLICACION in mensaje
    assert clave not in mensaje and usuario not in mensaje.replace(USUARIO_BD_APLICACION, "")


def test_en_la_nube_rechaza_url_sin_usuario():
    entorno = {**_validos(), "DATABASE_URL": "postgresql://db.ejemplo.invalid/evydentia"}
    _rechaza(entorno, "DATABASE_URL")


@pytest.mark.parametrize("esquema", ["postgresql", "postgresql+psycopg", "postgresql+asyncpg"])
def test_en_la_nube_con_lopdp_app_arranca(esquema):
    exigir_configuracion_en_la_nube({**_validos(), "DATABASE_URL": _url(esquema=esquema)[0]})


def test_el_mensaje_no_contiene_la_url_ni_la_contrasena():
    url, clave = _url("lopdp_beta_owner")
    mensaje = _rechaza({**NUBE, "DATABASE_URL": url}, "DATABASE_URL")
    assert url not in mensaje and clave not in mensaje


# ----------------------------------------------------------------------------- CORS_ORIGINS

@pytest.mark.parametrize("valor", [None, "", "  "])
def test_en_la_nube_rechaza_cors_ausente(valor):
    entorno = _validos()
    if valor is None:
        del entorno["CORS_ORIGINS"]
    else:
        entorno["CORS_ORIGINS"] = valor
    assert "falta CORS_ORIGINS" in _rechaza(entorno, "CORS_ORIGINS")


@pytest.mark.parametrize("valor", ["*", "https://app.ejemplo.invalid,*", "https://*.ejemplo.invalid"])
def test_en_la_nube_rechaza_el_comodin_en_cors(valor):
    assert "comodín" in _rechaza({**_validos(), "CORS_ORIGINS": valor}, "CORS_ORIGINS")


def test_en_la_nube_rechaza_http():
    entorno = {**_validos(), "CORS_ORIGINS": "https://app.ejemplo.invalid,http://app.ejemplo.invalid"}
    assert "https://" in _rechaza(entorno, "CORS_ORIGINS")


def test_en_la_nube_rechaza_un_origen_vacio():
    entorno = {**_validos(), "CORS_ORIGINS": "https://app.ejemplo.invalid,,https://admin.ejemplo.invalid"}
    assert "vacío" in _rechaza(entorno, "CORS_ORIGINS")


@pytest.mark.parametrize("valor", ["https://app.ejemplo.invalid/panel", "https://app.ejemplo.invalid?x=1"])
def test_en_la_nube_rechaza_un_origen_con_ruta(valor):
    assert "ruta" in _rechaza({**_validos(), "CORS_ORIGINS": valor}, "CORS_ORIGINS")


@pytest.mark.parametrize("valor", [CORS_VALIDO, "https://app.ejemplo.invalid", "https://app.ejemplo.invalid:8443/"])
def test_en_la_nube_con_origenes_https_validos_arranca(valor):
    exigir_configuracion_en_la_nube({**_validos(), "CORS_ORIGINS": valor})


def test_en_la_nube_nombra_los_dos_motivos_a_la_vez():
    mensaje = _rechaza(dict(NUBE), "DATABASE_URL")
    assert "falta CORS_ORIGINS" in mensaje


# ----------------------------------------------------------------------------- fuera de la nube

def test_fuera_de_la_nube_sin_variables_arranca():
    exigir_configuracion_en_la_nube({})
    exigir_configuracion_en_la_nube({"DATABASE_URL": "sqlite+aiosqlite:////tmp/test.db", "CORS_ORIGINS": "*"})


def test_vercel_sin_k_service_no_es_la_nube_para_sec17():
    """El PMV en Vercel está congelado: SEC-17 no cambia su arranque."""
    exigir_configuracion_en_la_nube({"VERCEL": "1", "VERCEL_ENV": "production"})


# ----------------------------------------------------------------------------- arranque real

def _python(codigo: str, **variables) -> subprocess.CompletedProcess:
    quitar = ("VERCEL", "VERCEL_ENV", "K_SERVICE", "DATABASE_URL", "CORS_ORIGINS",
              "JWT_SECRET", "SESSION_SECRET", "SECRET_KEY")
    env = {k: v for k, v in os.environ.items() if k not in quitar}
    env.update(AUTH_MODE="oidc", PYTHONIOENCODING="utf-8")
    if "K_SERVICE" in variables:
        # app_core.config carga el `.env` del checkout sin pisar lo definido. Para que una variable
        # ausente en la prueba no la rellene ese archivo, se define vacía: la guarda la trata como ausente.
        for nombre in ("DATABASE_URL", "CORS_ORIGINS"):
            env[nombre] = ""
    env.update(variables)
    return subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


SALUD = (
    "import json; from fastapi.testclient import TestClient; from api.index import app; "
    "r = TestClient(app).get('/health'); print('SALUD=' + json.dumps([r.status_code, r.json().get('status')]))"
)


def _secretos() -> dict:
    return {"JWT_SECRET": secrets.token_urlsafe(32), "SESSION_SECRET": secrets.token_urlsafe(32)}


def _salud(resultado: subprocess.CompletedProcess) -> list:
    linea = [l for l in resultado.stdout.splitlines() if l.startswith("SALUD=")]
    assert linea, resultado.stderr[-2000:]
    return json.loads(linea[-1][len("SALUD="):])


def test_api_index_en_la_nube_sin_database_url_responde_503_startup_error():
    resultado = _python(SALUD, CORS_ORIGINS=CORS_VALIDO, **NUBE, **_secretos())
    assert _salud(resultado) == [503, "STARTUP_ERROR"]
    assert REGLA_CONFIGURACION in resultado.stderr and "DATABASE_URL" in resultado.stderr


def test_api_index_en_la_nube_con_cors_comodin_responde_503_startup_error():
    resultado = _python(SALUD, DATABASE_URL=_url()[0], CORS_ORIGINS="*", **NUBE, **_secretos())
    assert _salud(resultado) == [503, "STARTUP_ERROR"]
    assert REGLA_CONFIGURACION in resultado.stderr and "CORS_ORIGINS" in resultado.stderr


def test_api_index_en_la_nube_con_configuracion_valida_no_es_startup_error():
    """Control: los 503 anteriores se deben a la guarda. La base ficticia no responde, pero importar sí."""
    resultado = _python(SALUD, DATABASE_URL=_url()[0], CORS_ORIGINS=CORS_VALIDO, PROXIES_CONFIABLES="1", **NUBE, **_secretos())  # SEC-21
    assert REGLA_CONFIGURACION not in resultado.stderr, resultado.stderr[-2000:]
    assert _salud(resultado)[1] != "STARTUP_ERROR", resultado.stderr[-2000:]


def test_fuera_de_la_nube_sin_variables_la_configuracion_carga_como_hoy():
    resultado = _python("from app_core.config import config; print('CARGA=' + str(bool(config.database_url)))")
    assert resultado.returncode == 0, resultado.stderr[-2000:]
    assert "CARGA=True" in resultado.stdout


def test_api_index_ya_no_pone_ningun_valor_por_defecto():
    texto = (RAIZ / "api" / "index.py").read_text(encoding="utf-8")
    assert "setdefault(" not in texto
