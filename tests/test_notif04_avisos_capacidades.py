# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤arbitro
"""NOTIF-04: avisos de concesiones y retiros de capacidades editoriales. Textos sin base; envío con base.

Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from tests.test_norm05_privilegios_backend import como_app, propietario  # noqa: F401 - fixtures de NORM-05

try:  # sin DATABASE_URL la sala no se puede importar: las pruebas de base se saltan
    from features.notificaciones.services import avisos_capacidades as srv

    HAY_BASE = True
except RuntimeError:
    HAY_BASE = False

con_base = pytest.mark.skipif(not HAY_BASE, reason="necesita PostgreSQL (DATABASE_URL)")
PROHIBIDAS = ["undefined", "null", "None", "{", "}", ", ,", "  ", "conforme", "cumple", "garantiza", "certificado", "legal"]


def _limpio(t: str) -> None:
    for p in PROHIBIDAS:
        assert p not in t, (p, t)


def _t(**k):
    base = dict(accion="concedida", capacidad="editor", por="Ana", a_quien="Luis", para_el_afectado=False, motivo=None)
    return srv.texto_del_aviso(**{**base, **k})


def test_titulos():
    assert srv.titulo("concedida") == "Capacidad editorial concedida"
    assert srv.titulo("retirada") == "Capacidad editorial retirada"
    assert srv.ENLACE_TEXTO == "Ver capacidades editoriales" and srv.ENLACE == "/plataforma/capacidades"


@pytest.mark.parametrize("kw,esperado", [
    (dict(para_el_afectado=True), "Ana te concedió la capacidad Editor."),
    (dict(accion="retirada", capacidad="revisor_tecnico", para_el_afectado=True), "Ana te retiró la capacidad Revisor técnico."),
    (dict(), "Ana concedió a Luis la capacidad Editor."),
    (dict(accion="retirada", capacidad="publicador"), "Ana retiró a Luis la capacidad Publicador."),
])
def test_textos_segun_quien_lo_lee(kw, esperado):
    t = _t(**kw)
    assert t == esperado
    _limpio(t)


def test_el_motivo_va_para_todos_y_sin_motivo_no_hay_hueco():
    """Mutación m2: no incluir el motivo da rojo."""
    assert _t(accion="retirada", motivo="Cambió de área") == "Ana retiró a Luis la capacidad Editor. Motivo: «Cambió de área»."
    assert _t(para_el_afectado=True, motivo="Por cobertura") == "Ana te concedió la capacidad Editor. Motivo: «Por cobertura»."
    for vacio in (None, "", "  "):
        assert _t(motivo=vacio) == "Ana concedió a Luis la capacidad Editor."


def test_motivo_largo_se_corta_a_200_y_es_texto_plano():
    t = _t(motivo="x" * 300)
    assert t.endswith("Motivo: «" + "x" * 200 + "…».")
    p = _t(motivo="**a** [b](http://c.d)\n# e")
    assert "**" not in p and "](" not in p and "\n" not in p and "  " not in p


def test_sin_nombres_no_deja_huecos():
    t = _t(por=None, a_quien=None)
    assert t == "Un operador concedió a otra persona la capacidad Editor."
    _limpio(t)


def test_el_servicio_no_programa_recordatorios():
    """Mutación m3: escribir `proximo_recordatorio` en el INSERT da rojo."""
    import inspect

    fuente = inspect.getsource(srv)
    assert "proximo_recordatorio" not in fuente and "recordatorios_hechos" not in fuente


# ------------------------------------------------------------ con base
async def _usuario(propietario) -> str:  # noqa: F811
    u = f"u-n04-{uuid.uuid4().hex[:10]}"
    async with propietario() as s:
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'Prueba')"),
                        {"id": u, "e": f"{u}@prueba.invalid"})
        await s.commit()
    return u


@pytest.fixture
def pasillos(monkeypatch):
    from app_core.pasillo import biblioteca, plataforma

    def poner(cambios, operadores):
        async def _c(session, desde):
            return [dict(c) for c in cambios]

        async def _o(session):
            return [dict(o) for o in operadores]

        monkeypatch.setattr(biblioteca, "cambios_de_capacidades", _c)
        monkeypatch.setattr(plataforma, "listar_operadores_activos", _o)
    return poner


async def _avisos(como_app, usuario):  # noqa: F811
    async with como_app() as s:
        await s.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": usuario})
        return [dict(f) for f in (await s.execute(text(
            "SELECT titulo, texto, enlace, proximo_recordatorio, recordatorios_hechos FROM avisos_plataforma "
            "WHERE usuario_id=:u AND tipo='capacidad_editorial'"), {"u": usuario})).mappings().all()]


@con_base
@pytest.mark.asyncio
async def test_db_tres_operadores_una_concesion_tres_avisos_y_repetir_no_crea_mas(propietario, como_app, pasillos):  # noqa: F811
    """Mutación m1: avisar solo a quien la recibe da rojo."""
    a, b, c = [await _usuario(propietario) for _ in range(3)]
    cambio = {"id": uuid.uuid4().hex, "usuario_id": b, "capacidad": "editor", "accion": "concedida", "por": a,
              "motivo": "Cubre vacaciones", "en": datetime.now(timezone.utc)}
    pasillos([cambio], [{"usuario_id": u, "nombre": n} for u, n in ((a, "Ana"), (b, "Beto"), (c, "Carla"))])
    async with como_app() as s:
        assert (await srv.sincronizar(s))["creados"] == 3
        await s.commit()
    async with como_app() as s:
        assert (await srv.sincronizar(s))["creados"] == 0
        await s.commit()
    de_b, de_c = (await _avisos(como_app, b))[0], (await _avisos(como_app, c))[0]
    assert de_b["texto"] == "Ana te concedió la capacidad Editor. Motivo: «Cubre vacaciones»."
    assert de_c["texto"] == "Ana concedió a Beto la capacidad Editor. Motivo: «Cubre vacaciones»."
    assert de_b["titulo"] == "Capacidad editorial concedida" and de_b["enlace"] == "/plataforma/capacidades"
    assert de_b["proximo_recordatorio"] is None and de_b["recordatorios_hechos"] == 0
