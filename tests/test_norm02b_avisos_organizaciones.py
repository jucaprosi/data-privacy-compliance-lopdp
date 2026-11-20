# ¤inteligencia-normativa ¤vigilancia-spdp ¤seguridad-tenant ¤arbitro
"""NORM-02b: aviso a cada organización de las resoluciones nuevas o con versión nueva de una corrida.

PostgreSQL 16 local con las migraciones aplicadas (`alembic upgrade heads`). Los destinatarios se leen con
`lopdp_app` sin organización fijada, como el operador (ORG-09), y solo por `fn_destinatarios_normativos()`.
La corrida y el notificador son dobles; sin red real. Cada prueba documenta su mutación: el cambio en el código
o en la migración que la pondría en rojo.
"""
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import plataforma as pasillo_plataforma
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa.schemas import ResumenCorrida
from features.notificaciones import notificaciones_service as ns

pytestmark = pytest.mark.asyncio

PREFIJO = "n02b-"
CAMPOS = {"tenant_id", "correos_admin", "correos_dpo"}


# ---------------------------------------------------------------- entorno

@pytest_asyncio.fixture
async def fabrica(db_engine):
    f = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def limpiar():
        async with f() as s:
            await s.execute(text("TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
            await s.execute(text("DELETE FROM user_tenant_roles WHERE id LIKE :p"), {"p": f"{PREFIJO}%"})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"{PREFIJO}%"})
            await s.execute(text("DELETE FROM tenants WHERE id LIKE :p"), {"p": f"{PREFIJO}%"})
            await s.commit()

    await limpiar()
    svc.inyectar_dependencias_de_prueba(sesion_factory=f)

    @asynccontextmanager
    async def como_app():
        """Sesión con `lopdp_app` y sin organización fijada: el mecanismo del operador (ORG-09)."""
        async with f() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await s.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
            yield s

    svc.inyectar_destinatarios_de_prueba(como_app)
    f.como_app = como_app
    yield f
    svc.inyectar_dependencias_de_prueba()
    svc.inyectar_destinatarios_de_prueba()
    await limpiar()


class Notificador:
    """Doble del notificador: guarda cada sobre; falla para las organizaciones indicadas."""

    def __init__(self, fallan=()):
        self.enviados = []
        self.fallan = set(fallan)

    async def enviar_correo(self, correo):
        if correo.destinatario.tenant_id in self.fallan:
            raise RuntimeError("proveedor caído")
        self.enviados.append(correo)

        class R:
            estado = ns.EstadoEnvio.ENVIADO

        return R()

    def lotes(self, tenants):
        """{tenant_id: [(lote_id, sobres)]} de las organizaciones de la prueba (la base puede tener otras)."""
        por_lote = {}
        for c in self.enviados:
            por_lote.setdefault(c.lote_id, []).append(c)
        res = {}
        for lote, sobres in por_lote.items():
            dueños = {s.destinatario.tenant_id for s in sobres}
            if dueños & set(tenants):
                for d in dueños:
                    res.setdefault(d, []).append((lote, sobres))
        return res


@pytest.fixture
def notificador(monkeypatch):
    n = Notificador()
    monkeypatch.setattr(ns, "notificador_configurado", lambda: n)
    monkeypatch.setenv("APP_BASE_URL", "https://app.example.test")
    monkeypatch.delenv("NORMATIVA_AVISO_OPERADOR_EMAIL", raising=False)
    return n


async def _organizacion(f, *, activa=True, nombre=None):
    t = f"{PREFIJO}t-{uuid.uuid4().hex[:8]}"
    async with f() as s:
        await s.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, activo) "
                 "VALUES (:t, :n, :n, :ruc, :a)"),
            {"t": t, "n": nombre or f"Organización {t}", "ruc": f"17{uuid.uuid4().int % 10**10:010d}001", "a": activa},
        )
        await s.commit()
    return t


async def _persona(f, tenant, rol, *, vence=None, activo=True, borrado=False):
    u = f"{PREFIJO}u-{uuid.uuid4().hex[:8]}"
    correo = f"{u}@example.test"
    async with f() as s:
        await s.execute(
            text("INSERT INTO users (id, email, nombre, activo, deleted_at) VALUES (:u, :e, :n, :a, :d)"),
            {"u": u, "e": correo, "n": f"Persona {u}", "a": activo,
             "d": datetime.now(timezone.utc) if borrado else None},
        )
        await s.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, valid_to) VALUES (:i, :u, :t, :r, :v)"),
            {"i": f"{PREFIJO}r-{uuid.uuid4().hex[:8]}", "u": u, "t": tenant, "r": rol, "v": vence},
        )
        await s.commit()
    return correo


async def _org_con_admin_y_dpo(f, **kw):
    t = await _organizacion(f, **kw)
    return t, await _persona(f, t, "admin_organizacion"), await _persona(f, t, "dpo")


def corrida_doble(f, *, estado="ok", nuevas=1, inserta=True):
    """Corrida que registra `nuevas` resoluciones (si `inserta`) y su fila en la bitácora."""

    async def corrida(origen):
        ahora = datetime.now(timezone.utc)
        async with f() as s:
            if inserta:
                for _ in range(nuevas):
                    n = f"SPDP-{uuid.uuid4().hex[:6]}"
                    await s.execute(
                        text("INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, url_fuente, "
                             "seccion_fuente, archivo_sha256, ruta_original, tamano_bytes) "
                             "VALUES (:n, 2026, :t, 'https://spdp.example.test/a.pdf', 'resoluciones', :h, 'spdp/a.pdf', 10)"),
                        {"n": n, "t": f"Resolución {n}", "h": uuid.uuid4().hex * 2},
                    )
            id_ = (await s.execute(
                text("INSERT INTO normativa_monitoreo_logs (inicio, fin, origen, estado, nuevos) "
                     "VALUES (:i, :i, 'manual', :e, :n) RETURNING id::text"),
                {"i": ahora, "e": estado, "n": nuevas},
            )).scalar_one()
            await s.commit()
        return ResumenCorrida(id=id_, origen="manual", estado=estado, inicio=ahora, fin=ahora, nuevos=nuevas)

    return corrida


async def _bitacora(f, id_corrida):
    async with f() as s:
        return (await s.execute(
            text("SELECT codigos_error FROM normativa_monitoreo_logs WHERE id = CAST(:i AS uuid)"), {"i": id_corrida}
        )).scalar_one()


# ---------------------------------------------------------------- escenarios

async def test_un_aviso_por_organizacion(fabrica, notificador, monkeypatch):
    """Mutación: un solo lote con los destinatarios de todas las organizaciones rompe la prueba."""
    a, a_admin, a_dpo = await _org_con_admin_y_dpo(fabrica)
    b, b_admin, b_dpo = await _org_con_admin_y_dpo(fabrica)
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica))

    resumen = await svc.disparar_monitoreo()

    assert resumen.estado == "ok"
    lotes = notificador.lotes({a, b})
    assert len(lotes[a]) == 1 and len(lotes[b]) == 1
    (lote_a, sobres_a), (lote_b, sobres_b) = lotes[a][0], lotes[b][0]
    assert lote_a != lote_b
    assert sorted(s.destinatario.email for s in sobres_a) == sorted([a_admin, a_dpo])
    assert sorted(s.destinatario.email for s in sobres_b) == sorted([b_admin, b_dpo])
    assert "SPDP-" in sobres_a[0].cuerpo_texto and "https://app.example.test/normativa" in sobres_a[0].cuerpo_texto


async def test_ningun_aviso_cruza_organizaciones(fabrica, notificador, monkeypatch):
    """Mutación: añadir al lote de una organización los correos (en copia) de la otra rompe la prueba."""
    a, *correos_a = await _org_con_admin_y_dpo(fabrica, nombre="Alfa Privada S.A.")
    b, *correos_b = await _org_con_admin_y_dpo(fabrica, nombre="Beta Reservada S.A.")
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica))

    await svc.disparar_monitoreo()

    lotes = notificador.lotes({a, b})
    for propia, ajena, ajenos, nombre_ajeno in ((a, b, correos_b, "Beta Reservada"), (b, a, correos_a, "Alfa Privada")):
        assert len(lotes[propia]) == 1
        for sobre in lotes[propia][0][1]:
            assert sobre.destinatario.tenant_id == propia
            contenido = " ".join([sobre.asunto, sobre.cuerpo_texto, sobre.cuerpo_html, sobre.destinatario.email,
                                  sobre.destinatario.nombre, sobre.destinatario.user_id])
            assert ajena not in contenido
            assert nombre_ajeno not in contenido and "Alfa Privada" not in sobre.cuerpo_texto
            assert not any(c in contenido for c in ajenos)


async def test_destinatarios_solo_lo_minimo(fabrica):
    """Mutaciones: añadir el nombre de la organización al pasillo, o una columna a la función, rompe la prueba."""
    a, a_admin, a_dpo = await _org_con_admin_y_dpo(fabrica, nombre="Gamma Confidencial S.A.")

    async with fabrica.como_app() as s:
        destinatarios = await pasillo_plataforma.destinatarios_normativos(s)
        columnas = list((await s.execute(text("SELECT * FROM fn_destinatarios_normativos() LIMIT 0"))).keys())

    assert columnas == ["tenant_id", "correos_admin", "correos_dpo"]
    assert destinatarios and all(set(d) == CAMPOS for d in destinatarios)
    propio = next(d for d in destinatarios if d["tenant_id"] == a)
    assert propio == {"tenant_id": a, "correos_admin": [a_admin], "correos_dpo": [a_dpo]}
    assert "Gamma Confidencial" not in repr(destinatarios)


async def test_solo_activas_y_roles_vigentes(fabrica, notificador, monkeypatch):
    """Mutación: avisar a organizaciones inactivas o incluir roles vencidos rompe la prueba."""
    a, a_admin, a_dpo = await _org_con_admin_y_dpo(fabrica)
    vencido = await _persona(fabrica, a, "admin_organizacion", vence=datetime.now(timezone.utc) - timedelta(days=1))
    inactiva, *_ = await _org_con_admin_y_dpo(fabrica, activa=False)
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica))

    await svc.disparar_monitoreo()

    lotes = notificador.lotes({a, inactiva})
    assert inactiva not in lotes
    assert sorted(s.destinatario.email for s in lotes[a][0][1]) == sorted([a_admin, a_dpo])
    assert vencido not in {c.destinatario.email for c in notificador.enviados}


async def test_funcion_excluye_inactivas_y_vencidas(fabrica):
    """Mutación: quitar `valid_to IS NULL OR valid_to > now()` de la función rompe la prueba."""
    ahora = datetime.now(timezone.utc)
    a = await _organizacion(fabrica)
    vigente = await _persona(fabrica, a, "admin_organizacion")
    futuro = await _persona(fabrica, a, "dpo", vence=ahora + timedelta(days=30))
    vencido = await _persona(fabrica, a, "admin_organizacion", vence=ahora - timedelta(minutes=1))
    vencido_dpo = await _persona(fabrica, a, "dpo", vence=ahora - timedelta(days=1))
    inactivo = await _persona(fabrica, a, "admin_organizacion", activo=False)
    borrado = await _persona(fabrica, a, "dpo", borrado=True)
    otro_rol = await _persona(fabrica, a, "coordinador")
    inactiva = await _organizacion(fabrica, activa=False)
    await _persona(fabrica, inactiva, "admin_organizacion")
    sin_vigentes = await _organizacion(fabrica)
    await _persona(fabrica, sin_vigentes, "admin_organizacion", vence=ahora - timedelta(days=1))

    async with fabrica.como_app() as s:
        filas = {f.tenant_id: f for f in (await s.execute(
            text("SELECT tenant_id, correos_admin, correos_dpo FROM fn_destinatarios_normativos()"))).all()}

    assert inactiva not in filas and sin_vigentes not in filas
    assert filas[a].correos_admin == [vigente] and filas[a].correos_dpo == [futuro]
    for excluido in (vencido, vencido_dpo, inactivo, borrado, otro_rol):
        assert excluido not in filas[a].correos_admin + filas[a].correos_dpo


async def test_sin_novedades_no_avisa(fabrica, notificador, monkeypatch):
    """Mutación: avisar en una corrida sin novedades, fallida o con resoluciones ya conocidas rompe la prueba."""
    a, *_ = await _org_con_admin_y_dpo(fabrica)

    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica, nuevas=0))
    await svc.disparar_monitoreo()
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica, estado="fallida"))
    await svc.disparar_monitoreo()
    assert a not in notificador.lotes({a})

    # R5: la resolución que trajo la corrida fallida ya es conocida; otra corrida que la cuenta no la repite.
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica, nuevas=1, inserta=False))
    await svc.disparar_monitoreo()
    assert a not in notificador.lotes({a})


async def test_fallo_de_envio_no_rompe_la_corrida(fabrica, notificador, monkeypatch):
    """Mutación: dejar que la excepción del notificador suba, o guardar correos en la bitácora, rompe la prueba."""
    a, *correos_a = await _org_con_admin_y_dpo(fabrica)
    b, *correos_b = await _org_con_admin_y_dpo(fabrica)
    notificador.fallan = {b}
    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida_doble(fabrica))

    resumen = await svc.disparar_monitoreo()

    assert resumen.estado == "ok"
    assert sorted(s.destinatario.email for s in notificador.lotes({a})[a][0][1]) == sorted(correos_a)
    async with fabrica.como_app() as s:
        total = len(await pasillo_plataforma.destinatarios_normativos(s))
        activas = await pasillo_plataforma.contar_organizaciones_activas(s)
    codigos = await _bitacora(fabrica, resumen.id)
    assert f"NORMATIVA_AVISOS_ENVIADOS={total - 1}" in codigos
    assert "NORMATIVA_AVISOS_FALLIDOS=1" in codigos
    assert f"NORMATIVA_ORGANIZACIONES_SIN_DESTINATARIOS={activas - total}" in codigos
    assert "@" not in repr(codigos)


async def test_lectura_solo_por_el_pasillo(fabrica):
    """Mutación: `GRANT EXECUTE ON FUNCTION fn_destinatarios_normativos() TO PUBLIC` rompe la prueba."""
    a, *_ = await _org_con_admin_y_dpo(fabrica)

    async with fabrica.como_app() as s:
        directos = (await s.execute(
            text("SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :t"), {"t": a})).scalar_one()
        por_pasillo = [d["tenant_id"] for d in await pasillo_plataforma.destinatarios_normativos(s)]
    assert directos == 0
    assert a in por_pasillo

    async with fabrica() as s:
        definer, config = (await s.execute(text(
            "SELECT prosecdef, proconfig FROM pg_proc WHERE oid = 'fn_destinatarios_normativos()'::regprocedure"
        ))).one()
        publico = (await s.execute(text(
            "SELECT count(*) FROM pg_proc p, aclexplode(p.proacl) x "
            "WHERE p.oid = 'fn_destinatarios_normativos()'::regprocedure AND x.grantee = 0 "
            "AND x.privilege_type = 'EXECUTE'"
        ))).scalar_one()
        acl_nula = (await s.execute(text(
            "SELECT proacl IS NULL FROM pg_proc WHERE oid = 'fn_destinatarios_normativos()'::regprocedure"
        ))).scalar_one()
        app = (await s.execute(text(
            "SELECT has_function_privilege('lopdp_app', 'fn_destinatarios_normativos()', 'EXECUTE')"))).scalar_one()
        normativa = (await s.execute(text(
            "SELECT has_function_privilege('lopdp_normativa', 'fn_destinatarios_normativos()', 'EXECUTE')"))).scalar_one()
    assert definer is True
    assert config == ["search_path=pg_catalog, public"]
    assert acl_nula is False and publico == 0  # ACL nula equivale a EXECUTE para PUBLIC
    assert app is True and normativa is False
