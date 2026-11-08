# ¤seguridad ¤arbitro
"""SEC-16 · Secretos obligatorios en la nube.

Contrato: `INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD`. Predicado, con S = {JWT_SECRET, SESSION_SECRET}:
    nube ∧ (∃ s ∈ S : s = ∅ ∨ s ∈ CLAVES_POR_DEFECTO ∨ |s| < 32  ∨  JWT_SECRET = SESSION_SECRET)
    ⟹  no arranca.
«nube» ≡ K_SERVICE definida (Cloud Run; decisión del CTO, PR #445). VERCEL no cuenta.
Fuera de la nube no cambia nada.

Solo valores generados en la propia prueba (`secrets.token_urlsafe`): ningún secreto real.

Mutación documentada: quitar la comprobación `valor in CLAVES_POR_DEFECTO` en
`app_core/config.py#SEC-16` hace fallar `test_en_la_nube_rechaza_la_clave_por_defecto` (las dos claves
por defecto miden 32 caracteres o más y ya no las para nada).
"""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import jwt
import pytest

from app_core.config import (
    CLAVES_POR_DEFECTO, LONGITUD_MINIMA_SECRETO, REGLA_SECRETOS, SECRETOS_OBLIGATORIOS,
    corre_en_cloud_run, exigir_secretos_en_la_nube,
)
from features.biblioteca.services import archivos

RAIZ = Path(__file__).resolve().parent.parent
VARIABLES_DE_NUBE = ("VERCEL", "K_SERVICE")


def _secreto() -> str:
    return secrets.token_urlsafe(32)  # 43 caracteres


def _validos() -> dict:
    return {"K_SERVICE": "evydentia-backend", "JWT_SECRET": _secreto(), "SESSION_SECRET": _secreto()}


def _rechaza(entorno: dict, variable: str) -> str:
    with pytest.raises(RuntimeError) as error:
        exigir_secretos_en_la_nube(entorno)
    mensaje = str(error.value)
    assert REGLA_SECRETOS in mensaje and variable in mensaje
    for nombre in SECRETOS_OBLIGATORIOS:
        valor = entorno.get(nombre)
        if valor:
            assert valor not in mensaje, f"el mensaje contiene el valor de {nombre}"
    return mensaje


# ----------------------------------------------------------------------------- guarda de config

def test_los_dos_secretos_son_obligatorios_y_el_minimo_es_32():
    assert SECRETOS_OBLIGATORIOS == ("JWT_SECRET", "SESSION_SECRET")
    assert LONGITUD_MINIMA_SECRETO == 32


@pytest.mark.parametrize("variable", SECRETOS_OBLIGATORIOS)
@pytest.mark.parametrize("valor", [None, "", "   "])
def test_en_la_nube_rechaza_el_secreto_ausente(variable, valor):
    entorno = _validos()
    if valor is None:
        del entorno[variable]
    else:
        entorno[variable] = valor
    assert "falta" in _rechaza(entorno, variable)


@pytest.mark.parametrize("variable", SECRETOS_OBLIGATORIOS)
@pytest.mark.parametrize("clave", sorted(CLAVES_POR_DEFECTO))
def test_en_la_nube_rechaza_la_clave_por_defecto(variable, clave):
    assert len(clave) >= LONGITUD_MINIMA_SECRETO  # la mutación depende de esto
    entorno = {**_validos(), variable: clave}
    assert "clave por defecto" in _rechaza(entorno, variable)


@pytest.mark.parametrize("variable", SECRETOS_OBLIGATORIOS)
def test_en_la_nube_rechaza_un_secreto_de_20_caracteres(variable):
    entorno = {**_validos(), variable: _secreto()[:20]}
    assert "menos de 32" in _rechaza(entorno, variable)


def test_en_la_nube_rechaza_los_dos_secretos_iguales():
    comun = _secreto()
    entorno = {"K_SERVICE": "evydentia-backend", "JWT_SECRET": comun, "SESSION_SECRET": comun}
    assert "iguales" in _rechaza(entorno, "JWT_SECRET")


@pytest.mark.parametrize("valor", ["evydentia-backend", ""])
def test_en_la_nube_con_dos_secretos_validos_arranca(valor):
    exigir_secretos_en_la_nube({"JWT_SECRET": _secreto(), "SESSION_SECRET": _secreto(), "K_SERVICE": valor})


@pytest.mark.parametrize("valor", ["evydentia-backend", ""])
def test_k_service_definida_aunque_vacia_es_la_nube(valor):
    assert corre_en_cloud_run({"K_SERVICE": valor})
    _rechaza({"K_SERVICE": valor}, "JWT_SECRET")


def test_vercel_sin_k_service_no_es_la_nube_para_sec16():
    """El PMV en Vercel está congelado: SEC-16 no cambia su arranque."""
    assert not corre_en_cloud_run({"VERCEL": "1"})
    exigir_secretos_en_la_nube({"VERCEL": "1"})


def test_fuera_de_la_nube_sin_secretos_arranca():
    exigir_secretos_en_la_nube({})
    exigir_secretos_en_la_nube({"JWT_SECRET": "corto", "SESSION_SECRET": "corto"})


def test_la_clave_fija_de_descargas_figura_entre_las_claves_por_defecto():
    assert archivos.CLAVE_FIRMA_DESARROLLO in CLAVES_POR_DEFECTO


# ----------------------------------------------------------------------------- arranque real

def _python(codigo: str, **variables) -> subprocess.CompletedProcess:
    quitar = (*VARIABLES_DE_NUBE, *SECRETOS_OBLIGATORIOS, "SECRET_KEY")
    env = {k: v for k, v in os.environ.items() if k not in quitar}
    env.update(AUTH_MODE="oidc", DATABASE_URL="sqlite+aiosqlite:///:memory:", PYTHONIOENCODING="utf-8")
    env.update(variables)
    return subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


SALUD = (
    "import json; from fastapi.testclient import TestClient; from api.index import app; "
    "r = TestClient(app).get('/health'); print('SALUD=' + json.dumps([r.status_code, r.json().get('status')]))"
)


def _salud(resultado: subprocess.CompletedProcess) -> list:
    linea = [l for l in resultado.stdout.splitlines() if l.startswith("SALUD=")]
    assert linea, resultado.stderr[-2000:]
    return json.loads(linea[-1][len("SALUD="):])


def test_api_index_en_la_nube_sin_jwt_secret_responde_503_startup_error():
    resultado = _python(SALUD, K_SERVICE="evydentia-backend", SESSION_SECRET=_secreto())
    assert _salud(resultado) == [503, "STARTUP_ERROR"]
    assert REGLA_SECRETOS in resultado.stderr and "JWT_SECRET" in resultado.stderr


def test_api_index_en_la_nube_con_secretos_validos_no_es_startup_error():
    """Control: el 503 anterior se debe a la guarda, no a otra cosa del entorno."""
    resultado = _python(SALUD, K_SERVICE="evydentia-backend", JWT_SECRET=_secreto(), SESSION_SECRET=_secreto())
    assert _salud(resultado)[1] != "STARTUP_ERROR", resultado.stderr[-2000:]


def test_fuera_de_la_nube_sin_secretos_la_configuracion_carga_como_hoy():
    resultado = _python("from app_core.config import config, CLAVE_JWT_DESARROLLO; "
                        "print(config.jwt_secret == CLAVE_JWT_DESARROLLO)")
    assert resultado.returncode == 0, resultado.stderr[-2000:]
    assert resultado.stdout.strip().endswith("True")


def test_api_index_ya_no_pone_jwt_secret_por_defecto():
    texto = (RAIZ / "api" / "index.py").read_text(encoding="utf-8")
    assert 'setdefault("JWT_SECRET"' not in texto
    # DATABASE_URL y CORS_ORIGINS son de SEC-17: siguen igual.
    assert 'setdefault("DATABASE_URL"' in texto and 'setdefault("CORS_ORIGINS"' in texto


# ----------------------------------------------------------------------------- biblioteca

@pytest.fixture
def sin_nube(monkeypatch):
    for nombre in (*VARIABLES_DE_NUBE, "SESSION_SECRET", "SECRET_KEY"):
        monkeypatch.delenv(nombre, raising=False)
    return monkeypatch


def _firmar() -> str:
    return archivos.generar_token_descarga("tenant-1", "usuario-1", "plantilla-1", "1.0")


def test_biblioteca_en_la_nube_sin_session_secret_no_firma_enlaces(sin_nube):
    sin_nube.setenv("K_SERVICE", "evydentia-backend")
    sin_nube.setenv("SECRET_KEY", _secreto())  # el alias no vale en la nube
    with pytest.raises(RuntimeError) as error:
        _firmar()
    assert REGLA_SECRETOS in str(error.value) and "SESSION_SECRET" in str(error.value)
    with pytest.raises(RuntimeError):
        archivos.verificar_token_descarga("cualquier.token.firmado")


def test_biblioteca_firma_con_session_secret_leido_al_usarlo(sin_nube):
    sin_nube.setenv("K_SERVICE", "evydentia-backend")
    primero = _secreto()
    sin_nube.setenv("SESSION_SECRET", primero)
    token = _firmar()
    assert archivos.verificar_token_descarga(token)["pid"] == "plantilla-1"
    jwt.decode(token, primero, algorithms=["HS256"], audience=archivos.AUDIENCIA_TOKEN)
    sin_nube.setenv("SESSION_SECRET", _secreto())  # rotación: el token anterior deja de valer
    with pytest.raises(Exception):
        archivos.verificar_token_descarga(token)


def test_biblioteca_fuera_de_la_nube_usa_el_alias_y_luego_la_clave_fija(sin_nube):
    assert archivos.secreto_firma_descargas() == archivos.CLAVE_FIRMA_DESARROLLO
    alias = _secreto()
    sin_nube.setenv("SECRET_KEY", alias)
    assert archivos.secreto_firma_descargas() == alias
    assert archivos.verificar_token_descarga(_firmar())["sub"] == "usuario-1"


def test_biblioteca_no_lee_la_clave_al_importar():
    assert not hasattr(archivos, "SECRETO_TOKEN")
