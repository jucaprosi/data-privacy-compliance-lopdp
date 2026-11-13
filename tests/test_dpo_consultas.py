# ¤dpo-cockpit ¤evidencias ¤arbitro
"""Árbitro de DPO-03: consultas de la organización al DPO con su historial como evidencia de asesoría.

Valida:
1. Cerrar asienta una OPINION_CONSULTIVA en la bitácora (cadena íntegra) y guarda la huella del hilo completo.
2. Solo el `dpo` cierra; admin, coordinador y autor reciben 403.
3. Visibilidad (R2): el autor ve la suya; dpo, admin y coordinador ven todas; otro autor y otra organización, nada.
4. RLS con `lopdp_app`: una organización no ve ni escribe en la otra; el hilo no admite UPDATE ni DELETE.
5. Tras el cierre, mensaje y cierre devuelven 409 CONSULTA_CERRADA; dos cierres simultáneos: uno 200 y otro 409.
6. El cierre es atómico: si la bitácora falla, la consulta sigue abierta y el hilo intacto.
7. Solo el mensaje del DPO deja la consulta «respondida»; el nombre del autor se resuelve al leer y no se guarda.
8. La huella del hilo es determinista y cualquier alteración de un mensaje la cambia.

Las pruebas de dominio puro no tocan la BD; las de integración necesitan TEST_DATABASE_URL (PostgreSQL 16 local
del arnés) y se omiten sin ella. Datos ficticios.

Pruebas de mutación (PostgreSQL 16 local):
- En `consultas_engine.cerrar_consulta` se eliminó la llamada a `registrar_dictamen` (cerrar sin bitácora):
  `pytest tests/test_dpo_consultas.py` falló en `test_cierre_bitacora_y_evidencia`.
- Quitar la guarda del dpo en las dos capas (`if rol != ROL_DPO` por `if False` en `consultas_engine.cerrar_consulta` y
  `require_role("dpo")` por `get_context` en el router): falló `test_solo_dpo_cierra`. Con una sola capa quitada la
  prueba sigue verde, porque la otra la sostiene (defensa en profundidad).
- En `domain.consulta.hilo_canonico` se sustituyó el orden por secuencia por el de llegada:
  falló `test_huella_del_hilo_es_determinista_y_detecta_alteraciones`.
Restauradas las líneas, la prueba vuelve a pasar (códigos de salida en el informe de entrega).
"""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from features.dpo_cockpit.domain.consulta import Consulta, MensajeConsulta, hilo_es_integro, huella_hilo
from main import app

client = TestClient(app)
BASE = "/api/v1/dpo/consultas"
ROLES = ("dpo", "admin_organizacion", "coordinador", "responsable_area", "implementador", "auditor")


# ---------------------------------------------------------------- dominio puro (sin BD)

def _mensajes(cid: str = "c1") -> list[MensajeConsulta]:
    t0 = datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc)
    return [
        MensajeConsulta(consulta_id=cid, autor_id="u1", autor_rol="responsable_area", texto="¿Puedo conservar los CV?",
                        secuencia=1, creado_en=t0),
        MensajeConsulta(consulta_id=cid, autor_id="d1", autor_rol="dpo", texto="Sí, por el plazo que defina el RAT.",
                        secuencia=2, creado_en=t0 + timedelta(minutes=5)),
    ]


def test_huella_del_hilo_es_determinista_y_detecta_alteraciones():
    ms = _mensajes()
    h = huella_hilo("c1", "Conservación de CV", ms)
    assert h == huella_hilo("c1", "Conservación de CV", list(reversed(ms))), "el orden de llegada no importa: manda la secuencia"
    assert len(h) == 64 and h == huella_hilo("c1", "Conservación de CV", _mensajes())
    alterados = _mensajes()
    alterados[1].texto = "No."
    assert huella_hilo("c1", "Conservación de CV", alterados) != h, "alterar un mensaje cambia la huella"
    assert huella_hilo("c1", "Otro asunto", ms) != h

    c = Consulta(tenant_id="t", asunto="Conservación de CV", creado_por="u1", id="c1", mensajes=ms, evidencia_sha256=h)
    assert hilo_es_integro(c) is True
    c.mensajes = alterados
    assert hilo_es_integro(c) is False, "la verificación falla si el hilo se altera"
    c.evidencia_sha256 = None
    assert hilo_es_integro(c) is False


# ---------------------------------------------------------------- integración (PostgreSQL 16 local)

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de DPO-03 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    url = _async_url()
    assert "ep-late-hall" not in url, "Nunca producción"
    engine = create_async_engine(url, pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


async def _como_app(s: AsyncSession, tenant: str, usuario: str = "") -> None:
    from app_core.db.session import fijar_contexto_rls

    await s.execute(text("SET LOCAL ROLE lopdp_app"))
    await fijar_contexto_rls(s, tenant, usuario)


@pytest_asyncio.fixture
async def env(factory):
    from app_core.db.session import fijar_contexto_rls

    sfx = uuid.uuid4().hex[:8]
    ta, tb = f"dpo3a-{sfx}", f"dpo3b-{sfx}"
    ua = {rol: f"dpo3-ua-{rol[:5]}-{sfx}" for rol in ROLES}
    ua["otro"] = f"dpo3-ua-otro-{sfx}"  # segundo responsable de área: ni autor ni DPO
    ub = {"dpo": f"dpo3-ub-dpo-{sfx}", "responsable_area": f"dpo3-ub-resp-{sfx}"}
    usuarios = (*ua.values(), *ub.values())

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                                 "VALUES (:t, :t, :t, :t)"), {"t": t})
        for u in usuarios:
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                            {"u": u, "e": f"{u}@example.test", "n": f"Persona {u[-12:]}"})
        for tenant, mapa in ((ta, ua), (tb, ub)):
            for rol, u in mapa.items():
                rol_real = "responsable_area" if rol == "otro" else rol
                await fijar_contexto_rls(s, tenant, u)
                await s.execute(
                    text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                    {"i": str(uuid.uuid4()), "u": u, "t": tenant, "r": rol_real})
        await s.commit()

    yield {"ta": ta, "tb": tb, "ua": ua, "ub": ub}

    async with factory() as s:
        await s.execute(text("SET session_replication_role = replica"))  # el hilo es de solo alta: limpieza como dueño
        for t in (ta, tb):
            await fijar_contexto_rls(s, t)
            for sql in ("DELETE FROM audit_events WHERE tenant_id = :t",
                        "DELETE FROM dpo_consultas_mensajes WHERE tenant_id = :t",
                        "DELETE FROM dpo_consultas WHERE tenant_id = :t",
                        "DELETE FROM dpo_dictamenes WHERE tenant_id = :t",
                        "DELETE FROM user_tenant_roles WHERE tenant_id = :t"):
                await s.execute(text(sql), {"t": t})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
        for u in usuarios:
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": u})
        await s.commit()


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


def _abrir(env, asunto="Conservación de CV", texto="¿Hasta cuándo conservo los CV?") -> dict:
    r = client.post(BASE, headers=_cab(env["ta"], env["ua"]["responsable_area"], "responsable_area"),
                    json={"asunto": asunto, "texto": texto})
    assert r.status_code == 201, r.text
    return r.json()


def _dpo(env) -> dict[str, str]:
    return _cab(env["ta"], env["ua"]["dpo"], "dpo")


@pytest.mark.asyncio
async def test_cierre_bitacora_y_evidencia(factory, env):
    c = _abrir(env)
    r = client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": "Por el plazo del RAT."})
    assert r.status_code == 200, r.text
    cerrada = r.json()
    assert cerrada["estado"] == "cerrada" and cerrada["dictamen_id"] and len(cerrada["evidencia_sha256"]) == 64

    async with factory() as s:
        await _como_app(s, env["ta"], env["ua"]["dpo"])
        dictamenes = (await s.execute(
            text("SELECT id, tipo, asunto, cuerpo, dpo_id, es_vinculante FROM dpo_dictamenes "
                 "WHERE id = :d AND tenant_id = :t"),
            {"d": cerrada["dictamen_id"], "t": env["ta"]})).mappings().all()
        assert len(dictamenes) == 1, "hay una entrada en la bitácora con el dictamen_id de la consulta"
        d = dictamenes[0]
        assert (d["tipo"], d["asunto"], d["cuerpo"]) == ("OPINION_CONSULTIVA", "Conservación de CV", "Por el plazo del RAT.")
        assert d["dpo_id"] == env["ua"]["dpo"] and d["es_vinculante"] is False

        from features.dpo_cockpit.services.bitacora_service import verificar_cadena_organizacion

        assert await verificar_cadena_organizacion(s, env["ta"]) is None, "la cadena de DPO-01 sigue íntegra"

        filas = (await s.execute(
            text("SELECT id, consulta_id, secuencia, autor_id, autor_rol, texto, creado_en "
                 "FROM dpo_consultas_mensajes WHERE consulta_id = :c ORDER BY secuencia"), {"c": c["id"]})).mappings().all()
        ms = [MensajeConsulta(consulta_id=f["consulta_id"], autor_id=f["autor_id"], autor_rol=f["autor_rol"],
                              texto=f["texto"], secuencia=f["secuencia"], creado_en=f["creado_en"]) for f in filas]
        assert [m.autor_rol for m in ms] == ["responsable_area", "dpo"], "el hilo incluye la respuesta final"
        assert huella_hilo(c["id"], "Conservación de CV", ms) == cerrada["evidencia_sha256"]

    # El autor ve la respuesta; la huella llega a la interfaz.
    vista = client.get(BASE, headers=_cab(env["ta"], env["ua"]["responsable_area"], "responsable_area")).json()["consultas"]
    assert vista[0]["estado"] == "cerrada" and vista[0]["huella_hilo"] == cerrada["evidencia_sha256"]
    assert [m["autor_rol"] for m in vista[0]["mensajes"]] == ["responsable_area", "dpo"]


@pytest.mark.asyncio
async def test_solo_dpo_cierra(env):
    c = _abrir(env)
    for rol in ("coordinador", "admin_organizacion", "responsable_area", "implementador", "auditor"):
        r = client.post(f"{BASE}/{c['id']}/cerrar", headers=_cab(env["ta"], env["ua"][rol], rol), json={"respuesta": "Cierro."})
        assert r.status_code == 403, rol
    assert client.get(BASE, headers=_dpo(env)).json()["consultas"][0]["estado"] == "abierta"


@pytest.mark.asyncio
async def test_visibilidad_r2_autor_dpo_admin_coordinador(env):
    c = _abrir(env)
    for rol in ("responsable_area", "dpo", "admin_organizacion", "coordinador"):
        h = _cab(env["ta"], env["ua"][rol], rol)
        assert [x["id"] for x in client.get(BASE, headers=h).json()["consultas"]] == [c["id"]], rol
    for rol in ("otro", "implementador", "auditor"):
        h = _cab(env["ta"], env["ua"][rol], "responsable_area" if rol == "otro" else rol)
        assert client.get(BASE, headers=h).json()["consultas"] == [], f"{rol} no es autor ni DPO: no la ve"
        r = client.post(f"{BASE}/{c['id']}/mensajes", headers=h, json={"texto": "Intruso"})
        assert r.status_code == 404 and r.json()["code"] == "CONSULTA_NO_ENCONTRADA", rol
    # Otra organización: ni siquiera el DPO de B la ve ni escribe en ella.
    hb = _cab(env["tb"], env["ub"]["dpo"], "dpo")
    assert client.get(BASE, headers=hb).json()["consultas"] == []
    assert client.post(f"{BASE}/{c['id']}/mensajes", headers=hb, json={"texto": "x"}).status_code == 404
    assert client.post(f"{BASE}/{c['id']}/cerrar", headers=hb, json={"respuesta": "x"}).status_code == 404
    # Admin y coordinador la ven pero no escriben en el hilo ajeno.
    for rol in ("admin_organizacion", "coordinador"):
        r = client.post(f"{BASE}/{c['id']}/mensajes", headers=_cab(env["ta"], env["ua"][rol], rol), json={"texto": "Yo opino"})
        assert r.status_code == 403, rol


@pytest.mark.asyncio
async def test_rls_consultas(factory, env):
    c = _abrir(env)
    async with factory() as s:
        await _como_app(s, env["tb"], env["ub"]["dpo"])
        for tabla in ("dpo_consultas", "dpo_consultas_mensajes"):
            n = (await s.execute(text(f"SELECT count(*) FROM {tabla} WHERE tenant_id = :t"), {"t": env["ta"]})).scalar_one()
            assert n == 0, f"B no ve {tabla} de A"
        await s.rollback()
    async with factory() as s:
        await _como_app(s, env["ta"], env["ua"]["dpo"])
        assert (await s.execute(text("SELECT count(*) FROM dpo_consultas WHERE id = :i"), {"i": c["id"]})).scalar_one() == 1
        await s.rollback()
    async with factory() as s:  # A no puede escribir con el tenant de B (WITH CHECK)
        await _como_app(s, env["ta"], env["ua"]["dpo"])
        with pytest.raises(DBAPIError):
            await s.execute(text("INSERT INTO dpo_consultas (id, tenant_id, asunto, estado, creado_por, creado_en) "
                                 "VALUES (:i, :t, 'x', 'abierta', 'u', now())"), {"i": str(uuid.uuid4()), "t": env["tb"]})
        await s.rollback()


@pytest.mark.asyncio
async def test_el_hilo_es_de_solo_alta_y_la_consulta_no_cambia_su_contenido(factory, env):
    c = _abrir(env)
    async with factory() as s:
        await _como_app(s, env["ta"], env["ua"]["dpo"])
        for sql in ("UPDATE dpo_consultas_mensajes SET texto = 'Reescrito' WHERE consulta_id = :c",
                    "DELETE FROM dpo_consultas_mensajes WHERE consulta_id = :c",
                    "UPDATE dpo_consultas SET asunto = 'Reescrito' WHERE id = :c",
                    "DELETE FROM dpo_consultas WHERE id = :c"):
            with pytest.raises(DBAPIError) as exc:
                await s.execute(text(sql), {"c": c["id"]})
            assert getattr(exc.value.orig, "sqlstate", None) == "42501", sql
            await s.rollback()
            await _como_app(s, env["ta"], env["ua"]["dpo"])
    async with factory() as s:  # ni el dueño: el trigger protege el hilo
        with pytest.raises(DBAPIError):
            await s.execute(text("UPDATE dpo_consultas_mensajes SET texto = 'Reescrito' WHERE consulta_id = :c"), {"c": c["id"]})
        await s.rollback()


@pytest.mark.asyncio
async def test_tras_el_cierre_el_mensaje_y_otro_cierre_dan_409(env):
    c = _abrir(env)
    assert client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": "Listo."}).status_code == 200
    for rol, uid in (("responsable_area", env["ua"]["responsable_area"]), ("dpo", env["ua"]["dpo"])):
        r = client.post(f"{BASE}/{c['id']}/mensajes", headers=_cab(env["ta"], uid, rol), json={"texto": "Una más"})
        assert r.status_code == 409 and r.json()["code"] == "CONSULTA_CERRADA", rol
    r = client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": "Otra vez."})
    assert r.status_code == 409 and r.json()["code"] == "CONSULTA_CERRADA"
    hilo = client.get(BASE, headers=_dpo(env)).json()["consultas"][0]["mensajes"]
    assert len(hilo) == 2, "el hilo cerrado no cambió"


@pytest.mark.asyncio
async def test_dos_cierres_simultaneos_uno_200_y_otro_409(env):
    c = _abrir(env)

    def cerrar(i: int):
        return client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": f"Respuesta {i}"})

    with ThreadPoolExecutor(2) as pool:
        codigos = sorted(r.status_code for r in pool.map(cerrar, (1, 2)))
    assert codigos == [200, 409]
    assert len(client.get(BASE, headers=_dpo(env)).json()["consultas"][0]["mensajes"]) == 2


@pytest.mark.asyncio
async def test_el_cierre_es_atomico_si_falla_la_bitacora(env, monkeypatch):
    from features.dpo_cockpit.services import consultas_engine

    async def falla(*_a, **_k):
        raise RuntimeError("bitácora caída")

    monkeypatch.setattr(consultas_engine, "registrar_dictamen", falla)
    c = _abrir(env)
    r = client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": "No debería quedar."})
    assert r.status_code == 500, "la falla de la bitácora aborta el cierre"
    monkeypatch.undo()
    vista = client.get(BASE, headers=_dpo(env)).json()["consultas"][0]
    assert vista["estado"] == "abierta" and vista["huella_hilo"] is None
    assert [m["autor_rol"] for m in vista["mensajes"]] == ["responsable_area"], "la respuesta no quedó en el hilo"


@pytest.mark.asyncio
async def test_solo_el_mensaje_del_dpo_deja_respondida_y_el_nombre_no_se_guarda(factory, env):
    c = _abrir(env)
    autor = _cab(env["ta"], env["ua"]["responsable_area"], "responsable_area")
    assert client.post(f"{BASE}/{c['id']}/mensajes", headers=autor, json={"texto": "Aclaro mi duda."}).status_code == 201
    assert client.get(BASE, headers=autor).json()["consultas"][0]["estado"] == "abierta", "el autor no cambia el estado"
    assert client.post(f"{BASE}/{c['id']}/mensajes", headers=_dpo(env), json={"texto": "Te respondo."}).status_code == 201
    vista = client.get(BASE, headers=autor, params={"estado": "respondida"}).json()["consultas"]
    assert [x["id"] for x in vista] == [c["id"]]
    assert client.get(BASE, headers=autor, params={"estado": "abierta"}).json()["consultas"] == []

    msgs = vista[0]["mensajes"]
    assert [m["es_mio"] for m in msgs] == [True, True, False]
    assert msgs[2]["autor_rol"] == "dpo" and msgs[2]["autor_nombre"].startswith("Persona ")
    assert all(k not in msgs[0] for k in ("autor_id", "id")), "la interfaz no recibe ids"

    async with factory() as s:
        cols = {r[0] for r in (await s.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'dpo_consultas_mensajes'"))).all()}
    assert not {"autor_nombre", "nombre", "email"} & cols, "el nombre es un dato personal: no se duplica"


@pytest.mark.asyncio
async def test_validaciones_y_la_organizacion_del_cuerpo_se_ignora(env):
    h = _cab(env["ta"], env["ua"]["responsable_area"], "responsable_area")
    for cuerpo in ({"asunto": "  ", "texto": "x"}, {"asunto": "x", "texto": "  "}, {"asunto": "a" * 121, "texto": "x"}):
        r = client.post(BASE, headers=h, json=cuerpo)
        assert r.status_code == 422 and r.json()["code"] == "CONSULTA_INVALIDA", cuerpo
    r = client.post(BASE, headers=h, json={"asunto": "a" * 120, "texto": "ok", "tenant_id": env["tb"], "creado_por": "otro"})
    assert r.status_code == 201
    assert client.get(BASE, headers=_cab(env["tb"], env["ub"]["dpo"], "dpo")).json()["consultas"] == []
    assert client.get(BASE, headers=h, params={"estado": "inventado"}).status_code == 422
    c = _abrir(env)
    r = client.post(f"{BASE}/{c['id']}/cerrar", headers=_dpo(env), json={"respuesta": "  "})
    assert r.status_code == 422 and r.json()["code"] == "CONSULTA_INVALIDA"
