# ¤evidencias ¤arbitro
"""EVI-04: subida de servidor en el almacén y custodia de documentos generados, contra PostgreSQL 16.

Sin TEST_DATABASE_URL se omite. Las sesiones de la función corren como `lopdp_app` (RLS efectiva);
la preparación y las lecturas de comprobación, como propietario. El almacén es un doble: sin red.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- m1 `AlmacenGcs.subir` sin `if_generation_match=0` -> test_m1_la_subida_es_de_escritura_unica_en_gcs.
- m2 la clave y el registro con un hash distinto al del contenido (`hashlib.sha256(b"x")`) -> test_feliz_sube_retiene_registra_y_vincula,
  test_m2_el_hash_registrado_es_el_del_contenido y las dos del huérfano.
- m3 `_vincular` sin efecto -> test_m3_sin_controles_no_se_registra_y_con_ellos_queda_vinculado y test_feliz_sube_retiene_registra_y_vincula.
- m4 `almacen_de_evidencias` devolviendo un almacén simulado fuera de la nube -> test_m4_fuera_de_la_nube_falla_cerrado.
"""
import hashlib
import os
import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from google.api_core.exceptions import PreconditionFailed
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.errors import ErrorNegocio
from app_core.storage import gcs, r2

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
PDF = b"%PDF-1.7\nconstancia de capacitacion\n"


class AlmacenDoble:
    def __init__(self, falla_retencion: bool = False) -> None:
        self.objetos: dict[str, bytes] = {}
        self.subidas = 0
        self.retenciones: dict[str, object] = {}
        self._falla_retencion = falla_retencion

    def firmar_subida(self, clave, tipo_mime):  # pragma: no cover - no se usa aquí
        raise AssertionError

    def subir(self, clave, contenido, tipo_mime):
        if clave in self.objetos:
            raise gcs.ObjetoYaExiste(clave)
        self.objetos[clave] = contenido
        self.subidas += 1

    def descargar(self, clave, maximo_bytes):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave, retener_hasta):
        if self._falla_retencion:
            raise RuntimeError("sin retención")
        self.retenciones[clave] = retener_hasta


def _pdf(texto: str) -> bytes:
    return b"%PDF-1.7\n" + texto.encode("utf-8") + b"\n"


@pytest_asyncio.fixture
async def ctx():
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    from app_core.db.session import fijar_contexto_rls

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"evi4-{x}-{sufijo}" for x in "ab")
    usuarios = {a: f"evi4-ua-{sufijo}", b: f"evi4-ub-{sufijo}"}
    async with factory() as s:
        for tenant, uid in usuarios.items():
            await s.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                    "VALUES (:t, :t, :t, :t, 'mediana')"
                ),
                {"t": tenant},
            )
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                {"u": uid, "e": f"{uid}@ejemplo.invalid"},
            )
        await s.commit()

    async def como_app(tenant):
        sesion = factory()
        await sesion.__aenter__()
        await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(sesion, tenant, usuarios[tenant])
        return sesion

    try:
        yield {"factory": factory, "a": a, "b": b, "u": usuarios, "como_app": como_app}
    finally:
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM evidencias_vinculos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM users WHERE id = :u",
                    "DELETE FROM tenants WHERE id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t, "u": usuarios[t]})
            await s.commit()
        await engine.dispose()


async def _custodiar(ctx, tenant, almacen, contenido=PDF, **cambios):
    from features.evidencias import evidencias_service as svc

    datos = dict(
        contenido=contenido, tipo_mime="application/pdf", tipo_evidencia="capacitacion",
        control_refs=["P73"], nombre="constancia.pdf", almacen=almacen,
    )
    datos.update(cambios)
    sesion = await ctx["como_app"](tenant)
    try:
        resultado = await svc.custodiar_documento_generado(sesion, tenant, ctx["u"][tenant], **datos)
        await sesion.commit()
        return resultado
    except BaseException:
        await sesion.rollback()
        raise
    finally:
        await sesion.__aexit__(None, None, None)


async def _leer(ctx, tenant, sentencia, **params):
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        return (await s.execute(text(sentencia), {"t": tenant, **params})).all()


@pytest.mark.asyncio
async def test_feliz_sube_retiene_registra_y_vincula(ctx):
    almacen = AlmacenDoble()
    r = await _custodiar(ctx, ctx["a"], almacen)
    huella = hashlib.sha256(PDF).hexdigest()
    assert r == {"evidencia_id": r["evidencia_id"], "sha256": huella, "tipo_evidencia": "capacitacion"}
    clave = f"{ctx['a']}/{huella}"
    assert almacen.objetos == {clave: PDF}
    assert almacen.retenciones[clave] is not None
    docs = await _leer(ctx, ctx["a"], "SELECT id, sha256, clave_almacen, retencion_dias, subido_por FROM evidencias_documentos WHERE tenant_id = :t")
    assert [tuple(d) for d in docs] == [(r["evidencia_id"], huella, clave, 1825, ctx["u"][ctx["a"]])]
    vinculos = await _leer(ctx, ctx["a"], "SELECT control_id FROM evidencias_vinculos WHERE tenant_id = :t AND documento_id = :d", d=r["evidencia_id"])
    assert [v[0] for v in vinculos] == [73]
    eventos = await _leer(
        ctx, ctx["a"],
        "SELECT user_id, payload->>'tipo_evidencia' FROM audit_events WHERE tenant_id = :t AND action = 'custodiar'",
    )
    assert [tuple(e) for e in eventos] == [(ctx["u"][ctx["a"]], "capacitacion")]


@pytest.mark.asyncio
async def test_m2_el_hash_registrado_es_el_del_contenido(ctx):
    r = await _custodiar(ctx, ctx["a"], AlmacenDoble(), contenido=_pdf("otro"))
    assert r["sha256"] == hashlib.sha256(_pdf("otro")).hexdigest() != hashlib.sha256(PDF).hexdigest()
    fila = await _leer(ctx, ctx["a"], "SELECT sha256, tamano_bytes FROM evidencias_documentos WHERE tenant_id = :t")
    assert [tuple(f) for f in fila] == [(r["sha256"], len(_pdf("otro")))]


@pytest.mark.asyncio
async def test_el_mismo_contenido_en_dos_organizaciones_da_dos_objetos_y_dos_registros(ctx):
    almacen = AlmacenDoble()
    ra = await _custodiar(ctx, ctx["a"], almacen)
    rb = await _custodiar(ctx, ctx["b"], almacen)
    assert ra["sha256"] == rb["sha256"] and ra["evidencia_id"] != rb["evidencia_id"]
    assert sorted(almacen.objetos) == sorted([f"{ctx['a']}/{ra['sha256']}", f"{ctx['b']}/{ra['sha256']}"])
    # La RLS: cada organización ve solo el suyo.
    sesion = await ctx["como_app"](ctx["a"])
    try:
        vistos = (await sesion.execute(text("SELECT tenant_id FROM evidencias_documentos"))).scalars().all()
    finally:
        await sesion.rollback()
        await sesion.__aexit__(None, None, None)
    assert vistos == [ctx["a"]]


@pytest.mark.asyncio
async def test_el_mismo_contenido_no_se_sube_dos_veces_y_suma_vinculos(ctx):
    almacen = AlmacenDoble()
    r1 = await _custodiar(ctx, ctx["a"], almacen)
    r2 = await _custodiar(ctx, ctx["a"], almacen, control_refs=["P73", "P74"])
    assert r1["evidencia_id"] == r2["evidencia_id"] and almacen.subidas == 1
    assert len(await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_documentos WHERE tenant_id = :t")) == 1
    vinculos = await _leer(ctx, ctx["a"], "SELECT control_id FROM evidencias_vinculos WHERE tenant_id = :t ORDER BY 1")
    assert [v[0] for v in vinculos] == [73, 74]


@pytest.mark.asyncio
async def test_si_falla_no_queda_registro_y_el_huerfano_se_reutiliza_en_el_reintento(ctx):
    almacen = AlmacenDoble()
    from features.evidencias import evidencias_service as svc

    sesion = await ctx["como_app"](ctx["a"])
    try:
        await svc.custodiar_documento_generado(
            sesion, ctx["a"], ctx["u"][ctx["a"]], contenido=PDF, tipo_mime="application/pdf",
            tipo_evidencia="capacitacion", control_refs=["P73"], nombre="constancia.pdf", almacen=almacen,
        )
    finally:
        await sesion.rollback()  # el llamador falla después y deshace
        await sesion.__aexit__(None, None, None)
    assert almacen.subidas == 1  # el objeto quedó huérfano en el almacén
    assert await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_documentos WHERE tenant_id = :t") == []
    assert await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_vinculos WHERE tenant_id = :t") == []
    r = await _custodiar(ctx, ctx["a"], almacen)  # el reintento termina bien
    assert almacen.subidas == 1
    assert len(await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_documentos WHERE tenant_id = :t")) == 1
    assert r["sha256"] == hashlib.sha256(PDF).hexdigest()


@pytest.mark.asyncio
async def test_m1_un_objeto_huerfano_con_otro_contenido_no_se_acepta(ctx):
    almacen = AlmacenDoble()
    almacen.objetos[f"{ctx['a']}/{hashlib.sha256(PDF).hexdigest()}"] = b"%PDF-1.7\nOTRO\n"
    with pytest.raises(ErrorNegocio):
        await _custodiar(ctx, ctx["a"], almacen)
    assert await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_documentos WHERE tenant_id = :t") == []
    assert almacen.objetos[f"{ctx['a']}/{hashlib.sha256(PDF).hexdigest()}"] == b"%PDF-1.7\nOTRO\n"


@pytest.mark.asyncio
async def test_si_no_se_fija_la_retencion_no_queda_registro(ctx):
    with pytest.raises(ErrorNegocio):
        await _custodiar(ctx, ctx["a"], AlmacenDoble(falla_retencion=True))
    assert await _leer(ctx, ctx["a"], "SELECT 1 FROM evidencias_documentos WHERE tenant_id = :t") == []


@pytest.mark.asyncio
async def test_m3_sin_controles_no_se_registra_y_con_ellos_queda_vinculado(ctx):
    from features.evidencias import evidencias_service as svc

    almacen = AlmacenDoble()
    for refs in ([], ["73"], ["P0"], ["P99999"], "P73"):
        with pytest.raises(svc.EvidenciaError):
            await _custodiar(ctx, ctx["a"], almacen, control_refs=refs)
    assert almacen.subidas == 0
    r = await _custodiar(ctx, ctx["a"], almacen)
    vinculos = await _leer(ctx, ctx["a"], "SELECT control_id FROM evidencias_vinculos WHERE tenant_id = :t AND documento_id = :d", d=r["evidencia_id"])
    assert [v[0] for v in vinculos] == [73]


@pytest.mark.asyncio
@pytest.mark.parametrize("cambio", [{"tipo_evidencia": "otro"}, {"tipo_evidencia": ""}])
async def test_tipo_de_evidencia_fuera_de_la_lista_cerrada_falla_antes_de_subir(ctx, cambio):
    from features.evidencias import evidencias_service as svc

    almacen = AlmacenDoble()
    with pytest.raises(svc.CustodiaInvalida):
        await _custodiar(ctx, ctx["a"], almacen, **cambio)
    assert almacen.subidas == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("tenant,usuario", [("", "u"), (None, "u"), ("t", ""), ("t", None), ("t", "  ")])
async def test_sin_organizacion_o_actor_falla_antes_de_subir(ctx, tenant, usuario):
    from features.evidencias import evidencias_service as svc

    almacen = AlmacenDoble()
    with pytest.raises(svc.CustodiaInvalida):
        await svc.custodiar_documento_generado(
            MagicMock(), tenant, usuario, contenido=PDF, tipo_mime="application/pdf",
            tipo_evidencia="capacitacion", control_refs=["P73"], nombre="c.pdf", almacen=almacen,
        )
    assert almacen.subidas == 0


@pytest.mark.asyncio
async def test_contenido_que_no_es_del_tipo_declarado_se_rechaza(ctx):
    almacen = AlmacenDoble()
    with pytest.raises(ErrorNegocio):
        await _custodiar(ctx, ctx["a"], almacen, contenido=b"no es un pdf")
    with pytest.raises(ErrorNegocio):
        await _custodiar(ctx, ctx["a"], almacen, nombre="constancia.png")
    assert almacen.subidas == 0


@pytest.mark.asyncio
async def test_m4_fuera_de_la_nube_falla_cerrado(monkeypatch):
    from unittest.mock import AsyncMock

    from features.evidencias import evidencias_service as svc
    from features.evidencias.services import custodia_generados_engine as motor

    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv(gcs.VARIABLE_BUCKET, raising=False)
    with pytest.raises(gcs.AlmacenNoDisponible):
        gcs.almacen_por_defecto()
    monkeypatch.setattr(motor._motor, "_fijar_rls", AsyncMock())
    monkeypatch.setattr(motor._motor, "_documento_existente", AsyncMock(return_value=None))
    sesion = MagicMock()
    sesion.execute = AsyncMock(side_effect=AssertionError("no debe registrar sin almacén"))
    with pytest.raises(ErrorNegocio) as info:
        await svc.custodiar_documento_generado(
            sesion, "t", "u", contenido=PDF, tipo_mime="application/pdf",
            tipo_evidencia="capacitacion", control_refs=["P73"], nombre="c.pdf",
        )
    assert info.value.code == "EVI_ALMACEN_NO_DISPONIBLE"


def test_r2_no_sube_desde_el_servidor():
    with pytest.raises(NotImplementedError):
        r2.subir("clave", b"x", "application/pdf")


class _Blob:
    def __init__(self, bucket, clave):
        self.bucket, self.clave = bucket, clave

    def upload_from_string(self, contenido, content_type=None, if_generation_match=None):
        self.bucket.llamadas.append((self.clave, contenido, content_type, if_generation_match))
        if if_generation_match == 0 and self.clave in self.bucket.existentes:
            raise PreconditionFailed("412")


class _Bucket:
    def __init__(self, nombre):
        self.nombre, self.llamadas, self.existentes = nombre, [], set()

    def blob(self, clave):
        return _Blob(self, clave)


class _Cliente:
    def __init__(self):
        self.buckets = {}

    def bucket(self, nombre):
        return self.buckets.setdefault(nombre, _Bucket(nombre))


def test_m1_la_subida_es_de_escritura_unica_en_gcs():
    cliente = _Cliente()
    almacen = gcs.AlmacenGcs(cliente, "evydentia-corpus-normativo", credenciales=None)
    almacen.subir("t/abc", b"x", "application/pdf")
    bucket = cliente.buckets["evydentia-corpus-normativo"]  # el bucket viene del constructor
    assert bucket.llamadas == [("t/abc", b"x", "application/pdf", 0)]
    bucket.existentes.add("t/abc")
    with pytest.raises(gcs.ObjetoYaExiste):
        almacen.subir("t/abc", b"otro", "application/pdf")
