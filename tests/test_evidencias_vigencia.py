# ¤evidencias ¤evidencias-vigencia ¤rbac-tenant ¤arbitro
"""EVI-02: vigencia, visibilidad y paquete para inspección, contra PostgreSQL 16 (almacén simulado).

Sin TEST_DATABASE_URL se omite. Todo SQL es texto literal con parámetros enlazados.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- `paquete_inspeccion_engine.armar_paquete`: no filtrar por `d.vigente(hoy)` -> test_un_documento_vencido_no_entra_en_el_paquete.
- `vigencia_engine.controles_con_documento_vigente`: quitar `a.vence_en >= :hoy` -> test_un_vencido_no_respalda_ningun_requisito.
- `vigencia_engine.listar_atributos`: no comprobar `puede_ver` -> test_un_rol_sin_visibilidad_no_ve_ni_descarga_el_documento.
"""
import csv
import hashlib
import io
import os
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone

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
from app_core.zona_negocio import hoy_negocio  # noqa: E402

BASE = "/api/v1/evidencias"


def _pdf(texto: str) -> bytes:
    return b"%PDF-1.7\n" + texto.encode("utf-8") + b"\n"


class AlmacenSimulado:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def firmar_subida(self, clave: str, tipo_mime: str) -> FirmaSubida:
        return FirmaSubida(
            clave=clave, url=f"https://almacen.invalid/{clave}", cabeceras={CABECERA_ESCRITURA_UNICA: "0"}
        )

    def descargar(self, clave: str, maximo_bytes: int):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave: str, retener_hasta) -> None:
        return None


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
    from api.routers import evidencias_inspeccion as router_inspeccion
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"evi2-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "dpo": (f"evi2-dpo-{sufijo}", a, "dpo"),
        "coord": (f"evi2-coord-{sufijo}", a, "coordinador"),
        "impl": (f"evi2-impl-{sufijo}", a, "implementador"),
        "resp": (f"evi2-resp-{sufijo}", a, "responsable_area"),
        "dpo_b": (f"evi2-dpob-{sufijo}", b, "dpo"),
    }
    async with factory() as s:
        for tenant in (a, b):
            await s.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                    "VALUES (:t, :t, :t, :t, 'mediana')"
                ),
                {"t": tenant},
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
    app.dependency_overrides[router_inspeccion._almacen] = lambda: almacen
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios, "almacen": almacen}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM evidencias_atributos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_vinculos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"evi2-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _subir(ctx, nombre: str, contenido: bytes, quien: str = "dpo") -> dict:
    """Sube y confirma un documento por las rutas de EVI-01 y devuelve el documento registrado."""
    cliente, almacen = ctx["client"], ctx["almacen"]
    pedir = await cliente.post(
        f"{BASE}/subidas", headers=_como(ctx, quien),
        json={"nombre_archivo": nombre, "tipo_mime": "application/pdf", "tamano_bytes": len(contenido)},
    )
    assert pedir.status_code == 200, pedir.text
    clave = pedir.json()["clave"]
    almacen.objetos[clave] = contenido
    r = await cliente.post(
        f"{BASE}/subidas/confirmar", headers=_como(ctx, quien),
        json={"clave": clave, "sha256_hash": hashlib.sha256(contenido).hexdigest(), "nombre_archivo": nombre,
              "tipo_mime": "application/pdf"},
    )
    assert r.status_code == 200, r.text
    return r.json()["documento"]


async def _atributos(ctx, documento_id: str, vence_en=None, visible_para=None, quien: str = "dpo"):
    cuerpo: dict = {"vence_en": vence_en.isoformat() if vence_en else None}
    if visible_para is not None:
        cuerpo["visible_para"] = visible_para
    return await ctx["client"].put(f"{BASE}/documentos/{documento_id}/atributos", headers=_como(ctx, quien), json=cuerpo)


async def _vincular(ctx, documento_id: str, control: int) -> None:
    r = await ctx["client"].put(f"{BASE}/documentos/{documento_id}/vinculos/{control}", headers=_como(ctx, "dpo"))
    assert r.status_code == 200, r.text


def _hoy() -> date:
    return hoy_negocio()


def _zip(respuesta) -> zipfile.ZipFile:
    assert respuesta.status_code == 200, respuesta.text
    return zipfile.ZipFile(io.BytesIO(respuesta.content))


@pytest.mark.asyncio
async def test_un_documento_vencido_no_entra_en_el_paquete(ctx):
    vigente = await _subir(ctx, "vigente.pdf", _pdf("vigente"))
    vencido = await _subir(ctx, "vencido.pdf", _pdf("vencido"))
    assert (await _atributos(ctx, vencido["id"], _hoy() - timedelta(days=1))).status_code == 200
    paquete = _zip(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo")))
    indice = paquete.read("indice.csv").decode("utf-8")
    assert vigente["codigo"] in indice and vencido["codigo"] not in indice
    assert [n for n in paquete.namelist() if n.startswith("documentos/")] == [f"documentos/{vigente['codigo']}_vigente.pdf"]


@pytest.mark.asyncio
async def test_el_dia_del_vencimiento_el_documento_sigue_vigente(ctx):
    doc = await _subir(ctx, "hoy.pdf", _pdf("hoy"))
    await _atributos(ctx, doc["id"], _hoy())
    paquete = _zip(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo")))
    assert doc["codigo"] in paquete.read("indice.csv").decode("utf-8")


@pytest.mark.asyncio
async def test_sin_documentos_vigentes_el_paquete_es_un_409(ctx):
    doc = await _subir(ctx, "viejo.pdf", _pdf("viejo"))
    await _atributos(ctx, doc["id"], _hoy() - timedelta(days=30))
    r = await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo"))
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_el_paquete_va_ordenado_por_requisito_con_huellas_y_fechas(ctx):
    a = await _subir(ctx, "a.pdf", _pdf("a"))
    b = await _subir(ctx, "b.pdf", _pdf("b"))
    c = await _subir(ctx, "c.pdf", _pdf("c"))
    await _vincular(ctx, a["id"], 5)
    await _vincular(ctx, b["id"], 2)
    await _vincular(ctx, b["id"], 5)
    paquete = _zip(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo")))
    filas = list(csv.reader(io.StringIO(paquete.read("indice.csv").decode("utf-8"))))
    assert filas[0][:5] == ["requisito", "control", "codigo", "archivo", "sha256"]
    orden = [(f[1], f[2]) for f in filas[1:]]
    assert orden == [("2", b["codigo"]), ("5", a["codigo"]), ("5", b["codigo"]), ("", c["codigo"])]
    assert filas[-1][0] == "Sin requisito vinculado"
    esperada = hashlib.sha256(_pdf("a")).hexdigest()
    assert any(f[4] == esperada and f[2] == a["codigo"] and f[6] and f[0].startswith("P5") for f in filas[1:])
    assert "LEEME.txt" in paquete.namelist()
    # Cada archivo del paquete es el que se registró.
    assert hashlib.sha256(paquete.read(f"documentos/{a['codigo']}_a.pdf")).hexdigest() == esperada


@pytest.mark.asyncio
async def test_un_rol_sin_visibilidad_no_ve_ni_descarga_el_documento(ctx):
    visible = await _subir(ctx, "publico.pdf", _pdf("publico"))
    reservado = await _subir(ctx, "reservado.pdf", _pdf("reservado"))
    assert (await _atributos(ctx, reservado["id"], None, ["dpo"])).status_code == 200

    lista = await ctx["client"].get(f"{BASE}/atributos", headers=_como(ctx, "coord"))
    assert [d["codigo"] for d in lista.json()["documentos"]] == [visible["codigo"]]
    descarga = await ctx["client"].get(f"{BASE}/documentos/{reservado['id']}/archivo", headers=_como(ctx, "coord"))
    assert descarga.status_code == 403
    paquete = _zip(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "coord")))
    assert reservado["codigo"] not in paquete.read("indice.csv").decode("utf-8")

    # El DPO sí lo ve y lo descarga, y quien tiene visibilidad recibe el archivo íntegro.
    propia = await ctx["client"].get(f"{BASE}/documentos/{reservado['id']}/archivo", headers=_como(ctx, "dpo"))
    assert propia.status_code == 200 and propia.content == _pdf("reservado")
    abierta = await ctx["client"].get(f"{BASE}/documentos/{visible['id']}/archivo", headers=_como(ctx, "impl"))
    assert abierta.status_code == 200 and abierta.content == _pdf("publico")


@pytest.mark.asyncio
async def test_solo_el_dpo_define_vigencia_y_visibilidad_y_el_dpo_siempre_ve(ctx):
    doc = await _subir(ctx, "doc.pdf", _pdf("doc"))
    assert (await _atributos(ctx, doc["id"], None, ["coordinador"], quien="coord")).status_code == 403
    assert (await _atributos(ctx, doc["id"], None, ["responsable_area"])).status_code == 422
    assert (await _atributos(ctx, doc["id"], None, ["coordinador"])).status_code == 200
    lista = await ctx["client"].get(f"{BASE}/atributos", headers=_como(ctx, "dpo"))
    assert lista.json()["documentos"][0]["visible_para"] == ["coordinador", "dpo"]
    assert (await _atributos(ctx, "no-existe", None)).status_code == 404


@pytest.mark.asyncio
async def test_quien_no_consulta_evidencias_recibe_403(ctx):
    for ruta in ("/atributos", "/paquete-inspeccion"):
        assert (await ctx["client"].get(f"{BASE}{ruta}", headers=_como(ctx, "resp"))).status_code == 403


@pytest.mark.asyncio
async def test_un_vencido_no_respalda_ningun_requisito(ctx):
    from features.evidencias import evidencias_service as sala

    viva = await _subir(ctx, "viva.pdf", _pdf("viva"))
    muerta = await _subir(ctx, "muerta.pdf", _pdf("muerta"))
    await _vincular(ctx, viva["id"], 3)
    await _vincular(ctx, muerta["id"], 4)
    await _atributos(ctx, muerta["id"], _hoy() - timedelta(days=1))
    async with ctx["factory"]() as s:
        assert await sala.controles_con_documento_vigente(s, ctx["a"], _hoy()) == {3}
        assert await sala.controles_con_documento_vigente(s, ctx["a"], _hoy() - timedelta(days=2)) == {3, 4}


@pytest.mark.asyncio
async def test_un_archivo_alterado_en_el_almacen_no_entra_en_el_paquete(ctx):
    doc = await _subir(ctx, "integro.pdf", _pdf("integro"))
    clave = next(iter(ctx["almacen"].objetos))
    ctx["almacen"].objetos[clave] = _pdf("otro contenido")
    r = await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo"))
    assert r.status_code == 502, r.text
    assert doc["id"]


@pytest.mark.asyncio
async def test_con_la_bandera_apagada_las_rutas_nuevas_dan_404(ctx, monkeypatch):
    monkeypatch.delenv("EVIDENCIAS_SUBIDA_FIRMADA", raising=False)
    for metodo, ruta in (
        ("get", "/atributos"), ("get", "/paquete-inspeccion"), ("get", "/documentos/x/archivo"),
        ("put", "/documentos/x/atributos"),
    ):
        r = await getattr(ctx["client"], metodo)(
            f"{BASE}{ruta}", headers=_como(ctx, "dpo"), **({"json": {}} if metodo == "put" else {})
        )
        assert r.status_code == 404, f"{metodo} {ruta} -> {r.status_code}"


@pytest.mark.asyncio
async def test_lopdp_app_no_borra_atributos_y_rls_los_aisla(ctx):
    doc = await _subir(ctx, "aislado.pdf", _pdf("aislado"))
    await _atributos(ctx, doc["id"], _hoy() + timedelta(days=30))
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ctx["a"]})
        assert (await s.execute(text("SELECT count(*) FROM evidencias_atributos"))).scalar_one() == 1
        with pytest.raises(DBAPIError) as info:
            await s.execute(text("DELETE FROM evidencias_atributos WHERE tenant_id = :t"), {"t": ctx["a"]})
        assert info.value.orig.sqlstate == "42501"
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ctx["b"]})
        assert (await s.execute(text("SELECT count(*) FROM evidencias_atributos"))).scalar_one() == 0


# --- El sello futuro exige un documento vigente en el día de negocio de Guayaquil ------------------------------------
#
# Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
# - `vigencia_engine.controles_para_sellar`: `vigentes = registrados` (volver a contar los vencidos) -> test_un_documento_vencido_ayer_no_respalda_el_sello.
# - `controles_con_documento_vigente`: `a.vence_en >= :hoy` por `a.vence_en > :hoy` -> test_vence_hoy_o_sin_fecha_si_respalda_el_sello.
# - `controles_para_sellar`: el rechazo usa el mensaje genérico (`mensaje_defecto`) -> test_el_rechazo_nombra_el_documento_vencido.
# - `_controles_documentados`: `hoy_negocio()` por la fecha UTC del mismo reloj (`zona_negocio.datetime.now(timezone.utc).date()`) -> test_el_dia_de_negocio_es_el_de_guayaquil_no_el_utc.

RESPUESTA = {
    "pregunta_id": 1, "control": "Control del banco", "dimension": "D01", "nivel_asignado": 4,
    "nivel_evidencia": 3, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
}


async def _guardar_respuesta(ctx):
    r = await ctx["client"].put(
        "/api/v1/diagnostico/respuestas", headers=_como(ctx, "dpo"), json={"respuestas": [RESPUESTA]}
    )
    assert r.status_code == 200, r.text


async def _sellar(ctx):
    await _guardar_respuesta(ctx)
    return await ctx["client"].post("/api/v1/diagnostico/resultados", headers=_como(ctx, "dpo"), json={"perfil": {}})


def _control_1(sello_json) -> dict:
    return next(x for x in sello_json["respuestas"] if x["pregunta_id"] == 1)


async def _documento_para_control_1(ctx, vence_en, nombre="sello.pdf"):
    doc = await _subir(ctx, nombre, _pdf(nombre))
    await _vincular(ctx, doc["id"], 1)
    if vence_en is not None:
        assert (await _atributos(ctx, doc["id"], vence_en)).status_code == 200
    return doc


@pytest.mark.asyncio
async def test_un_documento_vencido_ayer_no_respalda_el_sello(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    await _documento_para_control_1(ctx, _hoy() - timedelta(days=1))
    r = await _sellar(ctx)
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "EVI_SELLO_CON_DOCUMENTOS_VENCIDOS"


@pytest.mark.parametrize("vence", ["hoy", "sin_fecha"])
@pytest.mark.asyncio
async def test_vence_hoy_o_sin_fecha_si_respalda_el_sello(ctx, monkeypatch, vence):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    await _documento_para_control_1(ctx, _hoy() if vence == "hoy" else None)
    r = await _sellar(ctx)
    assert r.status_code == 201, r.text
    control = _control_1(r.json())
    assert (control["nivel_declarado"], control["nivel_sellado"]) == (3, 3)


@pytest.mark.asyncio
async def test_el_rechazo_nombra_el_documento_vencido(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    doc = await _documento_para_control_1(ctx, date(2020, 3, 5), nombre="politica-vencida.pdf")
    r = await _sellar(ctx)
    assert r.status_code == 409, r.text
    detalle = r.json()["detail"]
    assert "politica-vencida.pdf" in detalle and doc["codigo"] in detalle
    assert "05/03/2020" in detalle and "P1" in detalle


@pytest.mark.asyncio
async def test_un_control_con_un_documento_vigente_y_otro_vencido_sigue_respaldado(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    await _documento_para_control_1(ctx, _hoy() - timedelta(days=1), nombre="viejo.pdf")
    await _documento_para_control_1(ctx, None, nombre="nuevo.pdf")
    r = await _sellar(ctx)
    assert r.status_code == 201, r.text
    assert _control_1(r.json())["nivel_sellado"] == 3


@pytest.mark.asyncio
async def test_el_dia_de_negocio_es_el_de_guayaquil_no_el_utc(ctx, monkeypatch):
    """A las 23:30 en Guayaquil ya son las 04:30 UTC del día siguiente: un documento que vence ese día local sigue vigente."""
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    from app_core import zona_negocio

    utc = datetime(2030, 6, 11, 4, 30, tzinfo=timezone.utc)  # = 2030-06-10 23:30 en Guayaquil
    assert hoy_negocio(utc) == date(2030, 6, 10) and utc.date() == date(2030, 6, 11)

    class RelojCongelado(datetime):
        @classmethod
        def now(cls, tz=None):
            return utc if tz is None else utc.astimezone(tz)

    # El reloj de la zona de negocio queda fijo a esa hora: todo lo que lea el día de negocio la ve así.
    monkeypatch.setattr(zona_negocio, "datetime", RelojCongelado)
    assert zona_negocio.hoy_negocio() == date(2030, 6, 10)
    await _documento_para_control_1(ctx, date(2030, 6, 10))
    r = await _sellar(ctx)
    assert r.status_code == 201, r.text
    assert _control_1(r.json())["nivel_sellado"] == 3


@pytest.mark.asyncio
async def test_un_sello_ya_hecho_conserva_su_huella_aunque_el_documento_venza_despues(ctx, monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    doc = await _documento_para_control_1(ctx, None)
    r = await _sellar(ctx)
    assert r.status_code == 201, r.text
    sellado = r.json()
    assert _control_1(sellado)["nivel_sellado"] == 3
    assert (await _atributos(ctx, doc["id"], _hoy() - timedelta(days=1))).status_code == 200
    historial = await ctx["client"].get("/api/v1/diagnostico/resultados", headers=_como(ctx, "dpo"))
    guardado = next(x for x in historial.json()["resultados"] if x["id"] == sellado["id"])
    assert guardado["huella"] == sellado["huella"]
    assert _control_1(guardado)["nivel_sellado"] == 3
    assert historial.json()["cadena_integra"] is True
    # El sello siguiente sí exige el documento vigente.
    assert (await _sellar(ctx)).status_code == 409
