# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤seguridad ¤arbitro
"""FE-29 §5 (backend): los 403 de identidad llevan un código estable y el `detail` de siempre.

La sesión de base es un doble que devuelve las filas pedidas: así se ejercitan `usuario_de_identidad` y
`verificar_operador` reales sin abrir la base. Los tokens se firman con una clave RSA generada aquí.
"""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app_core import security
from app_core.db.session import get_session
from features.boveda_cloud import boveda_cloud_service
from main import app

pytestmark = pytest.mark.asyncio

CLIENT_ID = "cliente-fe29.apps.googleusercontent.com"
CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
RUTA_ORGANIZACIONES = "/api/v1/organizacion/mis-organizaciones"
RUTA_OPERADOR = "/api/v1/plataforma/organizaciones"


def bearer(sub="sub-fe29", email="fe29@empresa.test") -> dict:
    ahora = int(time.time())
    claims = {"iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": sub, "email": email,
              "email_verified": True, "iat": ahora, "exp": ahora + 3600}
    return {"Authorization": f"Bearer {jwt.encode(claims, CLAVE, algorithm='RS256')}"}


class _Resultado:
    def __init__(self, fila):
        self._fila = fila

    def first(self):
        return self._fila

    def mappings(self):
        return self


class SesionDoble:
    """Devuelve, en orden, una fila por cada `execute`; None si no quedan."""

    def __init__(self, *filas):
        self.filas = list(filas)

    async def execute(self, *_args, **_kwargs):
        return _Resultado(self.filas.pop(0) if self.filas else None)


@pytest.fixture
def con_sesion(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(security, "_clave_de_firma", lambda _token: CLAVE.public_key())
    anteriores = dict(app.dependency_overrides)

    def usar(sesion):
        app.dependency_overrides[get_session] = lambda: sesion

    yield usar
    app.dependency_overrides.clear()
    app.dependency_overrides.update(anteriores)


async def get(ruta):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return await c.get(ruta, headers=bearer())


async def test_no_registrado_con_codigo(con_sesion):
    # m1: volver a HTTPException deja el cuerpo sin `code` y esta prueba da rojo.
    con_sesion(SesionDoble(None, None))  # ni por sub ni por correo
    r = await get(RUTA_ORGANIZACIONES)
    assert r.status_code == 403
    assert r.json() == {"detail": "Usuario no registrado en la plataforma.", "code": "USUARIO_NO_REGISTRADO",
                        "action_required": None}


async def test_vinculada_y_operador_con_codigo(con_sesion):
    con_sesion(SesionDoble(None, ("usuario-1", "sub-de-otra-cuenta")))
    r = await get(RUTA_ORGANIZACIONES)
    assert r.status_code == 403
    assert r.json()["code"] == "CUENTA_VINCULADA_OTRA_IDENTIDAD"
    assert r.json()["detail"] == "La cuenta está vinculada a otra identidad de Google."

    con_sesion(SesionDoble(None))  # no está en operadores_plataforma
    r = await get(RUTA_OPERADOR)
    assert r.status_code == 403
    assert r.json() == {"detail": "Acceso restringido: no tiene permisos de operador de la plataforma.",
                        "code": "OPERADOR_NO_AUTORIZADO", "action_required": None}


async def test_los_que_capturan_httpexception_siguen_igual():
    # La bóveda y los paquetes normativos capturan el 403 de operador como HTTPException: sigue siéndolo.
    assert await boveda_cloud_service.operador_activo(SesionDoble(None), "x@empresa.test", "sub-x") is None
    with pytest.raises(HTTPException) as e:
        await security.usuario_de_identidad(SesionDoble(None, None),
                                            security.IdentidadVerificada(sub="s", email="nadie@empresa.test"))
    assert e.value.status_code == 403 and e.value.detail == "Usuario no registrado en la plataforma."
