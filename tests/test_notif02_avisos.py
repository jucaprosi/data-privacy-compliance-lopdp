# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤arbitro
"""NOTIF-02: avisos y recordatorios de versiones por revisar. Textos (R2, R3) y calendario sin base de datos.

Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from features.notificaciones.domain import avisos as av

PROHIBIDAS = ["undefined", "null", "None", "{", "}", ", ,", "  ", "conforme", "cumple", "garantiza", "certificado", "legal"]


def _limpio(texto: str) -> None:
    for p in PROHIBIDAS:
        assert p not in texto, (p, texto)


def test_fecha_larga_en_espanol_sin_cero():
    assert av.fecha_larga(date(2026, 12, 5)) == "5 de diciembre de 2026"
    assert av.fecha_larga(date(2027, 1, 31)) == "31 de enero de 2027"


def test_hoy_se_calcula_en_hora_de_ecuador():
    # 03:00 UTC del 6 es todavía el 5 a las 22:00 en Ecuador (UTC-5).
    assert av.hoy_ecuador(datetime(2026, 12, 6, 3, 0, tzinfo=timezone.utc)) == date(2026, 12, 5)


def test_titulo():
    assert av.titulo("Política de privacidad") == "Versión por revisar: Política de privacidad"
    assert av.ENLACE_TEXTO == "Revisar la versión"


HOY = date(2026, 11, 25)


@pytest.mark.parametrize("vigencia,esperado", [
    (date(2026, 12, 5), "Motivo del cambio: Resolución 1, artículo 4, que entra en vigencia el 5 de diciembre de 2026."),
    (HOY, "Motivo del cambio: Resolución 1, artículo 4, que entra en vigencia hoy."),
    (date(2026, 11, 1), "Motivo del cambio: Resolución 1, artículo 4, que entró en vigencia el 1 de noviembre de 2026."),
    (None, "Motivo del cambio: Resolución 1, artículo 4. La norma no indica fecha de vigencia."),
])
def test_motivo_por_resolucion(vigencia, esperado):
    t = av.motivo(origen="resolucion", norma="Resolución 1", articulo="artículo 4", vigencia=vigencia, hoy=HOY)
    assert t == esperado
    _limpio(t)


def test_sin_articulo_se_quita_la_coma_entera():
    """Mutación m5: dejar «, ,» al faltar el artículo da rojo."""
    for articulo in (None, "", "  "):
        t = av.motivo(origen="resolucion", norma="Resolución 1", articulo=articulo, vigencia=date(2026, 12, 5), hoy=HOY)
        assert t == "Motivo del cambio: Resolución 1, que entra en vigencia el 5 de diciembre de 2026."
        _limpio(t)
    t = av.motivo(origen="resolucion", norma="Resolución 1", articulo=None, vigencia=None, hoy=HOY)
    assert t == "Motivo del cambio: Resolución 1. La norma no indica fecha de vigencia."


def test_peticion_con_y_sin_texto():
    assert av.motivo(origen="peticion", nombre="Ana", texto="Actualizar el plazo", hoy=HOY) == \
        "Motivo del cambio: petición de Ana: «Actualizar el plazo»."
    for vacio in (None, "", "   "):
        assert av.motivo(origen="peticion", nombre="Ana", texto=vacio, hoy=HOY) == "Motivo del cambio: petición de Ana."


def test_peticion_larga_se_corta_a_200_y_va_como_texto_plano():
    """Mutación m7: una petición de 300 caracteres sin cortar da rojo."""
    t = av.motivo(origen="peticion", nombre="Ana", texto="x" * 300, hoy=HOY)
    assert t == "Motivo del cambio: petición de Ana: «" + "x" * 200 + "…»."
    justo = av.motivo(origen="peticion", nombre="Ana", texto="y" * 200, hoy=HOY)
    assert "…" not in justo


def test_peticion_texto_plano_sin_formato_ni_enlaces():
    t = av.motivo(origen="peticion", nombre="Ana", texto="**negrita** [x](http://a.b)\n# t", hoy=HOY)
    assert "**" not in t and "](" not in t and "\n" not in t and "  " not in t


# ------------------------------------------------------------ R3
def test_recordatorios_con_fecha_futura():
    assert av.programa(date(2026, 11, 25), date(2026, 12, 5)) == [date(2026, 11, 28), date(2026, 12, 4)]
    assert av.programa(date(2026, 11, 25), date(2026, 11, 30)) == [date(2026, 11, 29)]


def test_recordatorios_sin_fecha_pasada_o_peticion_a_5_y_10_dias():
    """Mutación m2: un tercer recordatorio sin fecha da rojo."""
    esperado = [date(2026, 11, 30), date(2026, 12, 5)]
    assert av.programa(date(2026, 11, 25), None) == esperado
    assert av.programa(date(2026, 11, 25), date(2026, 11, 1)) == esperado
    assert len(av.programa(date(2026, 11, 25), None)) == 2


@pytest.mark.parametrize("hoy,esperado", [
    (date(2026, 11, 25), "La norma que motiva el cambio entra en vigencia el 2 de diciembre de 2026 (faltan 7 días)."),
    (date(2026, 12, 1), "La norma que motiva el cambio entra en vigencia el 2 de diciembre de 2026 (falta 1 día)."),
])
def test_texto_recordatorio_por_vigencia(hoy, esperado):
    """Mutación m6: «faltan 1 días» da rojo."""
    t = av.recordatorio(vigencia=date(2026, 12, 2), hoy=hoy)
    assert t == esperado
    _limpio(t)


def test_texto_recordatorio_el_dia_de_la_vigencia():
    assert av.recordatorio(vigencia=HOY, hoy=HOY) == "La norma que motiva el cambio entra en vigencia hoy."


@pytest.mark.parametrize("n,esperado", [
    (5, "Sigue sin revisión técnica desde hace 5 días."), (1, "Sigue sin revisión técnica desde hace 1 día."),
])
def test_texto_recordatorio_sin_vigencia(n, esperado):
    assert av.recordatorio(vigencia=None, hoy=date(2026, 11, 25), creado=date(2026, 11, 25 - n)) == esperado


def test_fin_del_aviso():
    assert av.TEXTO_FIN == "Ya no está pendiente"


def test_las_palabras_prohibidas_no_estan_en_los_textos_fijos():
    for t in (av.ENLACE_TEXTO, av.TEXTO_FIN, av.titulo("Plantilla")):
        _limpio(t)


def test_peticion_sin_nombre_no_deja_huecos():
    t = av.motivo(origen="peticion", nombre=None, texto=None, hoy=HOY)
    assert t == "Motivo del cambio: petición."
    _limpio(t)


# ------------------------------------------------------------ con base (PostgreSQL): UNIQUE, RLS, sincronizar, R4
import uuid  # noqa: E402

import pytest_asyncio  # noqa: E402,F401
from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from tests.test_norm05_privilegios_backend import como_app, propietario  # noqa: E402,F401 - fixtures de NORM-05

try:  # sin DATABASE_URL la sala no se puede importar: las pruebas de base se saltan
    from features.notificaciones.services import avisos_plataforma as srv

    HAY_BASE = True
except RuntimeError:
    HAY_BASE = False

con_base = pytest.mark.skipif(not HAY_BASE, reason="necesita PostgreSQL (DATABASE_URL)")


async def _usuario(propietario) -> str:  # noqa: F811
    u = f"u-n02-{uuid.uuid4().hex[:10]}"
    async with propietario() as s:
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'Prueba')"),
                        {"id": u, "e": f"{u}@prueba.invalid"})
        await s.commit()
    return u


class Pasillos:
    """Dobles de los pasillos de biblioteca y normativo: ninguna prueba toca esas salas."""

    def __init__(self, versiones, revisores, vigencia=None):
        self.versiones, self.revisores, self.vigencia = versiones, revisores, vigencia

    async def versiones_en_revision(self, session):
        return [dict(v) for v in self.versiones]

    async def revisores_tecnicos(self, session):
        return list(self.revisores)

    async def obtener_resolucion(self, i):
        return type("R", (), {"titulo": "Resolución 1"})()

    async def fecha_vigencia_de(self, i):
        return self.vigencia


def _version(i=None, origen="resolucion"):
    return {"id": i or f"v-{uuid.uuid4().hex[:8]}", "codigo": "POL-1", "titulo": "Política", "redactada_por": "ia",
            "origen_ia": origen, "id_resolucion": "r1", "creada_en": datetime.now(timezone.utc)}


@pytest.fixture
def pasillos(monkeypatch):
    from app_core.pasillo import biblioteca, inteligencia_normativa

    def poner(p: Pasillos):
        monkeypatch.setattr(biblioteca, "versiones_en_revision", p.versiones_en_revision)
        monkeypatch.setattr(biblioteca, "revisores_tecnicos", p.revisores_tecnicos)
        monkeypatch.setattr(inteligencia_normativa, "obtener_resolucion", p.obtener_resolucion)
        monkeypatch.setattr(inteligencia_normativa, "fecha_vigencia_de", p.fecha_vigencia_de)
    return poner


async def _avisos(como_app, usuario):  # noqa: F811
    async with como_app() as s:
        return (await srv.listar(s, usuario, "todos"))["avisos"]


@con_base
@pytest.mark.asyncio
async def test_db_dos_revisores_dos_avisos_y_repetir_no_crea_mas(propietario, como_app, pasillos):  # noqa: F811
    """Mutación m1: quitar el UNIQUE (o su ON CONFLICT) da rojo."""
    a, b = await _usuario(propietario), await _usuario(propietario)
    pasillos(Pasillos([_version("v-uno")], [a, b]))
    async with como_app() as s:
        assert (await srv.sincronizar(s))["creados"] == 2
        await s.commit()
    async with como_app() as s:
        assert (await srv.sincronizar(s))["creados"] == 0
        await s.commit()
    assert len(await _avisos(como_app, a)) == 1 and len(await _avisos(como_app, b)) == 1


@con_base
@pytest.mark.asyncio
async def test_db_el_unique_lo_impone_la_base(propietario, como_app):  # noqa: F811
    """Mutación m1: sin el UNIQUE, la segunda inserción pasa y esta prueba da rojo."""
    u = await _usuario(propietario)
    sql = text("INSERT INTO avisos_plataforma (id, usuario_id, tipo, referencia, titulo, texto) "
               "VALUES (:id, :u, 'version_por_revisar', 'v-x', 't', 'x')")
    async with propietario() as s:
        await s.execute(sql, {"id": str(uuid.uuid4()), "u": u})
        with pytest.raises(IntegrityError):
            await s.execute(sql, {"id": str(uuid.uuid4()), "u": u})


@con_base
@pytest.mark.asyncio
async def test_db_cada_persona_ve_y_marca_solo_lo_suyo(propietario, como_app, pasillos):  # noqa: F811
    """Mutación m4: quitar la política de lectura (o de cambio) da rojo."""
    a, b = await _usuario(propietario), await _usuario(propietario)
    pasillos(Pasillos([_version("v-rls")], [a]))
    async with como_app() as s:
        await srv.sincronizar(s)
        await s.commit()
    propio = (await _avisos(como_app, a))[0]
    assert await _avisos(como_app, b) == []
    async with como_app() as s:
        assert await srv.marcar_leido(s, b, propio["id"]) is False
        await s.commit()
    async with como_app() as s:
        await s.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": b})
        assert (await s.execute(text("SELECT count(*) FROM avisos_plataforma"))).scalar_one() == 0
    async with como_app() as s:
        assert await srv.marcar_leido(s, a, propio["id"]) is True
        await s.commit()
    assert (await _avisos(como_app, a))[0]["leido"] is True


@con_base
@pytest.mark.asyncio
async def test_db_al_dejar_de_estar_en_revision_el_aviso_queda_cerrado(propietario, como_app, pasillos):  # noqa: F811
    """Mutación m3: dejar el enlace da rojo."""
    a = await _usuario(propietario)
    pasillos(Pasillos([_version("v-fin")], [a]))
    async with como_app() as s:
        await srv.sincronizar(s)
        await s.commit()
    pasillos(Pasillos([], [a]))
    async with como_app() as s:
        assert (await srv.sincronizar(s))["cerrados"] == 1
        await s.commit()
    aviso = (await _avisos(como_app, a))[0]
    assert aviso["pendiente"] is False and aviso["enlace"] is None and av.TEXTO_FIN in aviso["texto"]


@con_base
@pytest.mark.asyncio
async def test_db_recordatorio_sin_fecha_actualiza_el_mismo_aviso_y_lo_deja_sin_leer(propietario, como_app, pasillos):  # noqa: F811
    a = await _usuario(propietario)
    v = _version("v-rec")
    pasillos(Pasillos([v], [a]))
    async with como_app() as s:
        await srv.sincronizar(s)
        await srv.marcar_leido(s, a, (await srv.listar(s, a, "todos"))["avisos"][0]["id"])
        await s.commit()
    for dias, esperado in ((4, 0), (5, 1), (10, 1), (30, 0)):
        async with como_app() as s:
            r = await srv.sincronizar(s, datetime.now(timezone.utc) + timedelta(days=dias, hours=1))
            await s.commit()
        assert r["recordatorios"] == esperado, dias
    lista = await _avisos(como_app, a)
    assert len(lista) == 1 and lista[0]["leido"] is False
    assert "Sigue sin revisión técnica desde hace 5 días." in lista[0]["texto"]
    assert "desde hace 10 días" in lista[0]["texto"]
