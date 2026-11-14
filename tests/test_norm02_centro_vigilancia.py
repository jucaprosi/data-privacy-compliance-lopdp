# ¤inteligencia-normativa ¤vigilancia-spdp ¤arbitro
"""NORM-02: catálogo, filtros, revisión humana del operador, original por el backend, bitácora y aviso técnico.

PostgreSQL local con las migraciones aplicadas; lector de originales y aviso, dobles. Sin red real.
Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import notificaciones as pasillo_notificaciones
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa.schemas import ResumenCorrida

pytestmark = pytest.mark.asyncio

PDF = b"%PDF-1.7\nel original\n%%EOF"
NOTA = "Cotejada con el Registro Oficial."


class LectorEnMemoria:
    def __init__(self, objetos):
        self.objetos = objetos

    def leer(self, clave):
        return self.objetos.get(clave)


@pytest_asyncio.fixture
async def fabrica(db_engine):
    f = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def limpiar():
        async with f() as s:
            await s.execute(text("TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
            await s.execute(text("DELETE FROM operadores_plataforma WHERE id LIKE 'n02-%'"))
            await s.commit()

    await limpiar()
    svc.inyectar_dependencias_de_prueba(sesion_factory=f)
    svc.inyectar_lector_de_prueba(LectorEnMemoria({"spdp/a.pdf": PDF}))
    yield f
    svc.inyectar_dependencias_de_prueba()
    svc.inyectar_lector_de_prueba()
    await limpiar()


@pytest_asyncio.fixture
async def cliente(fabrica):
    from app_core.db.session import get_session
    from main import app

    async def _sesion():
        async with fabrica() as s:
            yield s

    app.dependency_overrides[get_session] = _sesion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def operador(fabrica):
    correo = f"op-{uuid.uuid4().hex[:6]}@example.test"
    async with fabrica() as s:
        await s.execute(
            text("INSERT INTO operadores_plataforma (id, email, nombre, activo, created_at, updated_at) "
                 "VALUES (:i, :e, 'Operador', TRUE, NOW(), NOW())"),
            {"i": f"n02-{uuid.uuid4().hex[:8]}", "e": correo},
        )
        await s.commit()
    return {"X-User-Email": correo, "X-User-ID": f"sub-{uuid.uuid4().hex[:6]}"}


@pytest_asyncio.fixture
async def miembro(seed_tenants):
    """Rol de organización (implementador); nunca es operador."""
    return {"X-User-ID": seed_tenants["user_a"], "X-Tenant-ID": seed_tenants["tenant_a"], "X-Role": "implementador"}


async def _sembrar(fabrica, numero, anio, titulo="Resolución", organo="SPDP", materia="General",
                   estado="pendiente_revision", ruta="spdp/a.pdf") -> str:
    async with fabrica() as s:
        i = (await s.execute(
            text("INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, organo_emisor, materia, "
                 "url_fuente, seccion_fuente, archivo_sha256, ruta_original, tamano_bytes, estado) "
                 "VALUES (:n, :a, :t, :o, :m, 'https://x.invalid/a.pdf', 'resoluciones', :h, :r, 10, :e) "
                 "RETURNING id::text"),
            {"n": numero, "a": anio, "t": titulo, "o": organo, "m": materia,
             "h": uuid.uuid4().hex + uuid.uuid4().hex, "r": ruta, "e": estado})).scalar_one()
        await s.commit()
    return i


def _numeros(r):
    return sorted(x["numero_resolucion"] for x in r.json()["items"])


# ---------------------------------------------------------------- catálogo

async def test_filtro_por_anio(fabrica, cliente, miembro):
    """Mutación: quitar `anio_emision = :a` de `_DONDE` en services/revision.py devuelve las tres resoluciones."""
    for n, a in (("SPDP-2024-1", 2024), ("SPDP-2025-1", 2025), ("SPDP-2026-1", 2026)):
        await _sembrar(fabrica, n, a)
    r = await cliente.get("/api/v1/normativa/resoluciones", params={"anio": 2026}, headers=miembro)
    assert r.status_code == 200 and _numeros(r) == ["SPDP-2026-1"] and r.json()["total"] == 1


async def test_filtros_combinados_y_paginacion(fabrica, cliente, miembro):
    """Mutación: usar OR en lugar de AND entre filtros, o ignorar `OFFSET`, rompe las aserciones."""
    await _sembrar(fabrica, "A-1", 2026, "Datos biométricos", "SPDP", "Biometría", "vigente")
    await _sembrar(fabrica, "A-2", 2026, "Cámaras", "SPDP", "Videovigilancia", "pendiente_revision")
    await _sembrar(fabrica, "B-1", 2025, "Cámaras antiguas", "Otro órgano", "Videovigilancia", "vigente")

    def g(**p):
        return cliente.get("/api/v1/normativa/resoluciones", params=p, headers=miembro)

    assert _numeros(await g(q="cámaras")) == ["A-2", "B-1"]
    assert _numeros(await g(numero="A-")) == ["A-1", "A-2"]
    assert _numeros(await g(organo="otro")) == ["B-1"]
    assert _numeros(await g(materia="biometr")) == ["A-1"]
    assert _numeros(await g(estado="vigente", materia="video")) == ["B-1"]
    p2 = await g(por_pagina=1, pagina=2)
    assert p2.json()["total"] == 3 and len(p2.json()["items"]) == 1


async def test_el_comodin_del_filtro_no_es_comodin(fabrica, cliente, miembro):
    """Mutación: no escapar `%` en `_like` hace que `q=%` devuelva todo el catálogo."""
    await _sembrar(fabrica, "A-1", 2026, "Uno")
    r = await cliente.get("/api/v1/normativa/resoluciones", params={"q": "%"}, headers=miembro)
    assert r.json()["total"] == 0


async def test_detalle_con_versiones_sin_ruta_interna(fabrica, cliente, miembro):
    """Mutación: devolver `ruta_original` en el detalle filtra la clave del almacén."""
    i = await _sembrar(fabrica, "A-1", 2026)
    r = await cliente.get(f"/api/v1/normativa/resoluciones/{i}", headers=miembro)
    assert r.status_code == 200 and "ruta_original" not in r.text and r.json()["versiones"] == []
    assert (await cliente.get(f"/api/v1/normativa/resoluciones/{uuid.uuid4()}", headers=miembro)).status_code == 404


async def test_lectura_exige_identidad(fabrica, cliente):
    """Mutación: quitar la dependencia `lector_del_corpus` de `listar` deja leer sin identidad."""
    assert (await cliente.get("/api/v1/normativa/resoluciones")).status_code in (401, 403, 422)


# ---------------------------------------------------------------- original

async def test_original_por_el_backend_sin_cache(fabrica, cliente, miembro):
    """Mutación: quitar `Cache-Control: no-store` o servir otro contenido rompe la prueba."""
    i = await _sembrar(fabrica, "A-1", 2026)
    r = await cliente.get(f"/api/v1/normativa/resoluciones/{i}/original", headers=miembro)
    assert r.status_code == 200 and r.content == PDF and r.headers["cache-control"] == "no-store"
    assert r.headers["content-type"] == "application/pdf"


async def test_original_falla_cerrado_sin_lector_real(fabrica, cliente, miembro):
    """Mutación: devolver bytes vacíos cuando el lector falla, en lugar de 503, abre el original sin custodia."""
    svc.inyectar_lector_de_prueba()  # el adaptador real llega con EVI-04
    i = await _sembrar(fabrica, "A-1", 2026)
    r = await cliente.get(f"/api/v1/normativa/resoluciones/{i}/original", headers=miembro)
    assert r.status_code == 503 and r.json()["detail"] == {"codigo": "NORMATIVA_ORIGINAL_NO_DISPONIBLE"}


async def test_original_ausente_en_el_almacen(fabrica, cliente, miembro):
    """Mutación: tratar `None` del lector como contenido devuelve 200 con cuerpo vacío."""
    i = await _sembrar(fabrica, "A-1", 2026, ruta="spdp/no-esta.pdf")
    r = await cliente.get(f"/api/v1/normativa/resoluciones/{i}/original", headers=miembro)
    assert r.status_code == 503


# ---------------------------------------------------------------- revisión

async def test_revision_por_operador_con_traza(fabrica, cliente, operador, miembro):
    """Mutación: no guardar `revisada_por`, `revisada_en` o la nota deja el detalle sin traza."""
    i = await _sembrar(fabrica, "A-1", 2026)
    r = await cliente.post(f"/api/v1/normativa/resoluciones/{i}/revision",
                           json={"estado": "vigente", "nota": NOTA}, headers=operador)
    assert r.status_code == 200 and r.json()["estado"] == "vigente"
    d = (await cliente.get(f"/api/v1/normativa/resoluciones/{i}", headers=miembro)).json()
    assert d["estado"] == "vigente" and d["nota_revision"] == NOTA and d["revisada_por"] and d["revisada_en"]


async def test_organizacion_no_homologa(fabrica, cliente, miembro):
    """Mutación: aceptar `lector_del_corpus` en `revisar` deja que una organización cambie el estado global."""
    i = await _sembrar(fabrica, "A-1", 2026)
    r = await cliente.post(f"/api/v1/normativa/resoluciones/{i}/revision",
                           json={"estado": "vigente", "nota": NOTA}, headers=miembro)
    assert r.status_code == 403
    assert (await cliente.post("/api/v1/normativa/monitoreo", headers=miembro)).status_code == 403
    async with fabrica() as s:
        assert (await s.execute(text("SELECT estado FROM normativa_resoluciones"))).scalar_one() == "pendiente_revision"


async def test_nota_obligatoria_y_estado_permitido(fabrica, cliente, operador):
    """Mutación: quitar la comprobación de nota o permitir `pendiente_revision` como destino rompe los 422."""
    i = await _sembrar(fabrica, "A-1", 2026)
    url = f"/api/v1/normativa/resoluciones/{i}/revision"
    for nota in ("", "   ", "corta"):
        r = await cliente.post(url, json={"estado": "vigente", "nota": nota}, headers=operador)
        assert r.status_code == 422 and r.json()["detail"] == {"codigo": "NORMATIVA_NOTA_OBLIGATORIA"}
    r = await cliente.post(url, json={"estado": "pendiente_revision", "nota": NOTA}, headers=operador)
    assert r.status_code == 422 and r.json()["detail"] == {"codigo": "NORMATIVA_ESTADO_NO_PERMITIDO"}
    r = await cliente.post(f"/api/v1/normativa/resoluciones/{uuid.uuid4()}/revision",
                           json={"estado": "vigente", "nota": NOTA}, headers=operador)
    assert r.status_code == 404


async def test_la_base_exige_la_nota(fabrica):
    """Mutación: quitar `ck_normativa_nota_revision` deja revisar sin nota por SQL directo."""
    i = await _sembrar(fabrica, "A-1", 2026)
    async with fabrica() as s:
        with pytest.raises(DBAPIError):
            await s.execute(text("UPDATE normativa_resoluciones SET revisada_en = now(), estado = 'vigente' "
                                 "WHERE id = CAST(:i AS uuid)"), {"i": i})


# ---------------------------------------------------------------- bitácora y disparo

async def test_bitacora_y_disparo_manual(fabrica, cliente, operador, miembro, monkeypatch):
    """Mutación: devolver 200 en lugar de 202, o no lanzar la corrida, rompe la prueba."""
    lanzadas = []

    async def corrida(origen):
        lanzadas.append(origen)
        ahora = datetime.now(timezone.utc)
        return ResumenCorrida(id="x", origen="manual", estado="ok", inicio=ahora, fin=ahora)

    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida)
    r = await cliente.post("/api/v1/normativa/monitoreo", headers=operador)
    assert r.status_code == 202 and lanzadas == ["manual"]
    async with fabrica() as s:
        await s.execute(text("INSERT INTO normativa_monitoreo_logs (inicio, fin, origen, estado, nuevos) "
                             "VALUES (now(), now(), 'manual', 'ok', 2)"))
        await s.commit()
    b = await cliente.get("/api/v1/normativa/monitoreo", headers=miembro)
    assert b.status_code == 200 and b.json()[0]["nuevos"] == 2 and "codigos_error" not in b.json()[0]


# ---------------------------------------------------------------- aviso al operador

def _resumen(estado):
    ahora = datetime.now(timezone.utc)
    return ResumenCorrida(id="x", origen="manual", estado=estado, inicio=ahora, fin=ahora,
                          codigos_error=["NORMATIVA_FUENTE_BLOQUEADA"])


async def test_aviso_al_operador_solo_si_la_corrida_falla(fabrica, monkeypatch):
    """Mutación: avisar también cuando `estado == 'ok'`, o no avisar si es 'fallida', rompe la prueba."""
    monkeypatch.setenv("NORMATIVA_AVISO_OPERADOR_EMAIL", "op@example.test, otro@example.test")
    avisos = []

    async def avisador(**kw):
        avisos.append(kw)

    svc.inyectar_lector_de_prueba(avisador=avisador)
    estados = iter(["ok", "fallida"])

    async def corrida(origen):
        return _resumen(next(estados))

    monkeypatch.setattr(svc, "ejecutar_monitoreo", corrida)
    await svc.disparar_monitoreo()
    assert avisos == []
    await svc.disparar_monitoreo()
    assert avisos[0]["correos"] == ["op@example.test", "otro@example.test"]
    assert avisos[0]["codigos"] == ["NORMATIVA_FUENTE_BLOQUEADA"]


async def test_aviso_del_pasillo_sin_datos_de_resoluciones(monkeypatch):
    """Mutación: incluir títulos o datos de la fuente en el cuerpo, o no enviar a cada correo, rompe la prueba."""
    from features.notificaciones import notificaciones_service as ns

    enviados = []

    class Falso:
        async def enviar_correo(self, correo):
            enviados.append(correo)

            class R:
                estado = ns.EstadoEnvio.ENVIADO

            return R()

    monkeypatch.setattr(ns, "notificador_configurado", lambda: Falso())
    n = await pasillo_notificaciones.avisar_corrida_normativa_fallida(
        correos=["a@example.test", "b@example.test"], origen="manual", codigos=["NORMATIVA_FUENTE_BLOQUEADA"],
        app_base_url="https://app.example.test")
    assert n == 2 and [c.destinatario.email for c in enviados] == ["a@example.test", "b@example.test"]
    assert "NORMATIVA_FUENTE_BLOQUEADA" in enviados[0].cuerpo_texto
    assert "https://app.example.test/normativa" in enviados[0].cuerpo_texto
