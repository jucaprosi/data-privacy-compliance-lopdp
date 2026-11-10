# ¤evidencias ¤diagnostico ¤rbac-tenant ¤arbitro
"""EVI-01: documentos guardados y comprobados por el servidor, contra PostgreSQL 16 (almacén simulado).

Sin TEST_DATABASE_URL se omite. Todo SQL es texto literal con parámetros enlazados.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- engine `confirmar_subida`: usar `esperada` (la huella del navegador) en vez de calcularla del archivo
  -> test_si_la_huella_del_navegador_no_coincide_nada_se_registra.
- engine `exigir_puede_vincular`: anular la rama `if real_sellado` -> test_sellado_el_real_nadie_vincula_ni_desvincula.
- models `puede_subir`: anular la rama `if real_sellado` (comprobación del sello del real)
  -> test_sellado_el_real_suben_el_responsable_de_area_y_el_coordinador.
"""
import hashlib
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from app_core.storage.gcs import CABECERA_ESCRITURA_UNICA, FirmaSubida  # noqa: E402

BASE = "/api/v1/evidencias"
PDF = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"


class AlmacenSimulado:
    """Almacén en memoria: respeta la escritura única y no sabe borrar."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}
        self.retenciones: dict[str, object] = {}
        self.falla_retencion = False

    def firmar_subida(self, clave: str, tipo_mime: str) -> FirmaSubida:
        return FirmaSubida(
            clave=clave, url=f"https://almacen.invalid/{clave}",
            cabeceras={CABECERA_ESCRITURA_UNICA: "0", "Content-Type": tipo_mime},
        )

    def subir(self, clave: str, cabeceras: dict, contenido: bytes) -> None:
        """Lo que haría el navegador con la URL firmada."""
        if cabeceras.get(CABECERA_ESCRITURA_UNICA) == "0" and clave in self.objetos:
            raise FileExistsError("412 Precondition Failed")
        self.objetos[clave] = contenido

    def descargar(self, clave: str, maximo_bytes: int):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave: str, retener_hasta) -> None:
        if self.falla_retencion:
            raise RuntimeError("sin permiso")
        self.retenciones[clave] = retener_hasta


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    monkeypatch.setenv("EVIDENCIAS_SUBIDA_FIRMADA", "1")
    from api.routers import evidencias as router_evidencias
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"evi1-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "dpo": (f"evi1-dpo-{sufijo}", a, "dpo"),
        "resp": (f"evi1-resp-{sufijo}", a, "responsable_area"),
        "coord": (f"evi1-coord-{sufijo}", a, "coordinador"),
        "impl": (f"evi1-impl-{sufijo}", a, "implementador"),
        "admin": (f"evi1-admin-{sufijo}", a, "admin_organizacion"),
        "dpo_b": (f"evi1-dpob-{sufijo}", b, "dpo"),
    }
    async with factory() as s:
        for tenant, tamano in ((a, "mediana"), (b, "mediana")):
            await s.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                    "VALUES (:t, :t, :t, :t, :tamano)"
                ),
                {"t": tenant, "tamano": tamano},
            )
        for uid, tenant, rol in usuarios.values():
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                {"u": uid, "e": f"{uid}@ejemplo.invalid"},
            )
            await fijar_contexto_rls(s, tenant, uid)
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol},
            )
        await s.commit()

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    almacen = AlmacenSimulado()
    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[router_evidencias._almacen] = lambda: almacen
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios, "almacen": almacen}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM evidencias_vinculos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"evi1-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


def _con_real_sellado(monkeypatch, sellado: bool) -> None:
    from app_core.pasillo import diagnostico as pasillo

    async def _real(session, tenant_id, user_id=None):
        return sellado

    monkeypatch.setattr(pasillo, "diagnostico_real_sellado", _real)


async def _subir(ctx, quien="dpo", contenido=PDF, nombre="politica.pdf", tipo="application/pdf", huella=None,
                 normativa="LOPDP"):
    """Los tres pasos; devuelve la respuesta de confirmar."""
    cliente, almacen = ctx["client"], ctx["almacen"]
    pedir = await cliente.post(
        f"{BASE}/subidas", headers=_como(ctx, quien),
        json={"nombre_archivo": nombre, "tipo_mime": tipo, "tamano_bytes": len(contenido)},
    )
    assert pedir.status_code == 200, pedir.text
    firma = pedir.json()
    almacen.subir(firma["clave"], firma["cabeceras"], contenido)
    return await cliente.post(
        f"{BASE}/subidas/confirmar", headers=_como(ctx, quien),
        json={
            "clave": firma["clave"], "sha256_hash": huella or hashlib.sha256(contenido).hexdigest(),
            "nombre_archivo": nombre, "tipo_mime": tipo, "normativa": normativa,
        },
    )


async def _contar_documentos(ctx, tenant: str) -> int:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        return (
            await s.execute(text("SELECT count(*) FROM evidencias_documentos WHERE tenant_id = :t"), {"t": tenant})
        ).scalar_one()


@pytest.mark.asyncio
async def test_la_huella_la_calcula_el_servidor(ctx):
    r = await _subir(ctx)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["duplicada"] is False
    assert cuerpo["documento"]["sha256_hash"] == hashlib.sha256(PDF).hexdigest()
    assert cuerpo["documento"]["tamano_bytes"] == len(PDF)
    assert cuerpo["documento"]["codigo"].startswith("EVD-")


@pytest.mark.asyncio
async def test_el_registro_sobrevive_a_una_sesion_nueva(ctx):
    documento = (await _subir(ctx)).json()["documento"]
    r = await ctx["client"].get(f"{BASE}/documentos", headers=_como(ctx, "dpo"))
    assert r.status_code == 200
    assert [d["id"] for d in r.json()["documentos"]] == [documento["id"]]
    assert await _contar_documentos(ctx, ctx["a"]) == 1


@pytest.mark.asyncio
async def test_si_la_huella_del_navegador_no_coincide_nada_se_registra(ctx):
    r = await _subir(ctx, huella="0" * 64)
    assert r.status_code == 422, r.text
    assert await _contar_documentos(ctx, ctx["a"]) == 0


@pytest.mark.asyncio
async def test_una_clave_de_otra_organizacion_no_se_confirma(ctx):
    pedir = await ctx["client"].post(
        f"{BASE}/subidas", headers=_como(ctx, "dpo"),
        json={"nombre_archivo": "a.pdf", "tipo_mime": "application/pdf", "tamano_bytes": len(PDF)},
    )
    firma = pedir.json()
    assert firma["clave"].startswith(f"{ctx['a']}/")
    ctx["almacen"].subir(firma["clave"], firma["cabeceras"], PDF)
    r = await ctx["client"].post(
        f"{BASE}/subidas/confirmar", headers=_como(ctx, "dpo_b"),
        json={"clave": firma["clave"], "sha256_hash": hashlib.sha256(PDF).hexdigest(),
              "nombre_archivo": "a.pdf", "tipo_mime": "application/pdf"},
    )
    assert r.status_code in (403, 404)
    assert await _contar_documentos(ctx, ctx["b"]) == 0


@pytest.mark.asyncio
async def test_una_firma_de_formato_que_no_corresponde_se_rechaza(ctx):
    r = await _subir(ctx, contenido=b"esto no es un pdf", nombre="falso.pdf")
    assert r.status_code == 422, r.text
    assert await _contar_documentos(ctx, ctx["a"]) == 0


@pytest.mark.asyncio
async def test_el_mismo_archivo_se_deduplica_por_organizacion_huella_y_normativa(ctx):
    primero = (await _subir(ctx)).json()
    segundo = (await _subir(ctx)).json()
    assert segundo["duplicada"] is True
    assert segundo["documento"]["id"] == primero["documento"]["id"]
    assert await _contar_documentos(ctx, ctx["a"]) == 1
    otra_normativa = (await _subir(ctx, normativa="ISO27001")).json()
    assert otra_normativa["duplicada"] is False
    assert await _contar_documentos(ctx, ctx["a"]) == 2


@pytest.mark.parametrize("quien", ["admin", "impl", "coord", "resp"])
@pytest.mark.asyncio
async def test_antes_del_sello_del_real_solo_el_dpo_sube(ctx, monkeypatch, quien):
    _con_real_sellado(monkeypatch, False)
    r = await ctx["client"].post(
        f"{BASE}/subidas", headers=_como(ctx, quien),
        json={"nombre_archivo": "a.pdf", "tipo_mime": "application/pdf", "tamano_bytes": 10},
    )
    assert r.status_code == 403, r.text
    assert (await _subir(ctx, "dpo")).status_code == 200


@pytest.mark.parametrize("quien", ["admin", "impl", "coord", "resp"])
@pytest.mark.asyncio
async def test_antes_del_sello_del_real_solo_el_dpo_vincula(ctx, monkeypatch, quien):
    _con_real_sellado(monkeypatch, False)
    documento = (await _subir(ctx, "dpo")).json()["documento"]
    r = await ctx["client"].put(f"{BASE}/documentos/{documento['id']}/vinculos/3", headers=_como(ctx, quien))
    assert r.status_code == 403, r.text
    ok = await ctx["client"].put(f"{BASE}/documentos/{documento['id']}/vinculos/3", headers=_como(ctx, "dpo"))
    assert ok.status_code == 200 and ok.json()["vinculado"] is True


@pytest.mark.parametrize("quien,esperado", [("dpo", 403), ("impl", 403), ("admin", 403), ("resp", 200), ("coord", 200)])
@pytest.mark.asyncio
async def test_sellado_el_real_suben_el_responsable_de_area_y_el_coordinador(ctx, monkeypatch, quien, esperado):
    _con_real_sellado(monkeypatch, True)
    pedir = await ctx["client"].post(
        f"{BASE}/subidas", headers=_como(ctx, quien),
        json={"nombre_archivo": "a.pdf", "tipo_mime": "application/pdf", "tamano_bytes": len(PDF)},
    )
    assert pedir.status_code == esperado, pedir.text


@pytest.mark.parametrize("quien", ["dpo", "coord", "resp", "impl", "admin"])
@pytest.mark.asyncio
async def test_sellado_el_real_nadie_vincula_ni_desvincula(ctx, monkeypatch, quien):
    _con_real_sellado(monkeypatch, False)
    documento = (await _subir(ctx, "dpo")).json()["documento"]
    vinculo = await ctx["client"].put(f"{BASE}/documentos/{documento['id']}/vinculos/5", headers=_como(ctx, "dpo"))
    assert vinculo.status_code == 200
    _con_real_sellado(monkeypatch, True)
    url = f"{BASE}/documentos/{documento['id']}/vinculos/5"
    assert (await ctx["client"].put(url, headers=_como(ctx, quien))).status_code == 409
    assert (await ctx["client"].delete(url, headers=_como(ctx, quien))).status_code == 409


@pytest.mark.parametrize("quien,esperado", [("dpo", 200), ("coord", 200), ("impl", 200), ("admin", 200), ("resp", 403)])
@pytest.mark.asyncio
async def test_quien_consulta_los_documentos(ctx, quien, esperado):
    r = await ctx["client"].get(f"{BASE}/documentos", headers=_como(ctx, quien))
    assert r.status_code == esperado, r.text


@pytest.mark.asyncio
async def test_cada_alta_y_baja_de_un_vinculo_deja_un_evento(ctx):
    documento = (await _subir(ctx)).json()["documento"]
    url = f"{BASE}/documentos/{documento['id']}/vinculos/7"
    assert (await ctx["client"].put(url, headers=_como(ctx, "dpo"))).json()["vinculado"] is True
    assert (await ctx["client"].put(url, headers=_como(ctx, "dpo"))).json()["vinculado"] is False
    assert (await ctx["client"].delete(url, headers=_como(ctx, "dpo"))).json()["desvinculado"] is True
    assert (await ctx["client"].delete(url, headers=_como(ctx, "dpo"))).json()["desvinculado"] is False
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        acciones = (
            await s.execute(
                text(
                    "SELECT action FROM audit_events WHERE tenant_id = :t AND entity_type = 'evidencia_vinculo' "
                    "ORDER BY timestamp"
                ),
                {"t": ctx["a"]},
            )
        ).scalars().all()
    assert acciones == ["vincular", "desvincular"]


@pytest.mark.asyncio
async def test_lopdp_app_no_actualiza_ni_borra_un_documento_registrado(ctx):
    await _subir(ctx)
    for sentencia in (
        "UPDATE evidencias_documentos SET nombre_archivo = 'otro' WHERE tenant_id = :t",
        "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
    ):
        async with ctx["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ctx["a"]})
            with pytest.raises(DBAPIError) as info:
                await s.execute(text(sentencia), {"t": ctx["a"]})
            assert info.value.orig.sqlstate == "42501"


@pytest.mark.asyncio
async def test_rls_aisla_documentos_y_vinculos_entre_organizaciones(ctx):
    documento = (await _subir(ctx)).json()["documento"]
    await ctx["client"].put(f"{BASE}/documentos/{documento['id']}/vinculos/9", headers=_como(ctx, "dpo"))
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ctx["b"]})
        for tabla_sql in (
            "SELECT count(*) FROM evidencias_documentos",
            "SELECT count(*) FROM evidencias_vinculos",
        ):
            assert (await s.execute(text(tabla_sql))).scalar_one() == 0
        with pytest.raises(DBAPIError):
            await s.execute(
                text(
                    "INSERT INTO evidencias_documentos (id, tenant_id, codigo, nombre_archivo, tipo_mime, "
                    "tamano_bytes, sha256, normativa, clave_almacen, subido_por, retencion_dias) "
                    "VALUES (:i, :t, 'EVD-1', 'x', 'text/plain', 1, :h, 'LOPDP', :k, :u, 1)"
                ),
                {"i": str(uuid.uuid4()), "t": ctx["a"], "h": "a" * 64, "k": f"{ctx['a']}/{uuid.uuid4().hex}",
                 "u": ctx["u"]["dpo"][0]},
            )


@pytest.mark.asyncio
async def test_el_estado_dice_subida_firmada_con_la_bandera_encendida(ctx):
    r = await ctx["client"].get(f"{BASE}/estado", headers=_como(ctx, "dpo"))
    assert r.status_code == 200 and r.json() == {"subida_firmada": True}


@pytest.mark.asyncio
async def test_diag03_un_control_con_documento_vinculado_se_sella_con_su_nivel_y_sin_documento_como_e0(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    cliente = ctx["client"]
    respuesta = {
        "pregunta_id": 1, "control": "Control del banco", "dimension": "D01", "nivel_asignado": 4,
        "nivel_evidencia": 3, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
    }

    async def sellar_y_leer():
        r = await cliente.put(
            "/api/v1/diagnostico/respuestas", headers=_como(ctx, "dpo"), json={"respuestas": [respuesta]}
        )
        assert r.status_code == 200, r.text
        sello = await cliente.post("/api/v1/diagnostico/resultados", headers=_como(ctx, "dpo"), json={"perfil": {}})
        assert sello.status_code == 201, sello.text
        return next(x for x in sello.json()["respuestas"] if x["pregunta_id"] == 1)

    sin_documento = await sellar_y_leer()
    assert (sin_documento["nivel_declarado"], sin_documento["nivel_sellado"]) == (3, 0)

    documento = (await _subir(ctx)).json()["documento"]
    assert (await cliente.put(f"{BASE}/documentos/{documento['id']}/vinculos/1", headers=_como(ctx, "dpo"))).status_code == 200
    con_documento = await sellar_y_leer()
    assert (con_documento["nivel_declarado"], con_documento["nivel_sellado"]) == (3, 3)
