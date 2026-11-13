# ¤evidencias ¤rbac-tenant ¤arbitro
"""EVI-03: el auditor lee todas las evidencias de su organización y no define atributos, contra PostgreSQL 16.

Sin TEST_DATABASE_URL se omite. Todo SQL es texto literal con parámetros enlazados.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- m1 `vigencia.ROLES_VEN_TODO` sin "auditor" -> test_el_auditor_lista_y_descarga_un_documento_solo_para_el_dpo.
- m2 `definir_atributos` con `Depends(_consulta)` en lugar de `_definir` -> test_el_auditor_no_puede_definir_atributos.
- m3 `ROLES_VISIBILIDAD_POSIBLES = tuple(ROLES_CONSULTA_DOCUMENTOS)` -> test_los_atributos_por_defecto_no_incluyen_al_auditor.
- m4 `listar_atributos` sin `fijar_contexto_rls` -> test_el_auditor_de_una_organizacion_no_ve_las_de_otra.
- m5 `armar_paquete` filtrando por `visible_para` también para el auditor -> test_el_paquete_del_auditor_es_el_mismo_que_el_del_dpo.
"""
import io
import uuid
import zipfile

import pytest
import pytest_asyncio
from sqlalchemy import text

from tests.test_evidencias_vigencia import (  # noqa: F401  (fixture y ayudas de EVI-02)
    BASE,
    _TEST_URL,
    _atributos,
    _como,
    _h,
    _pdf,
    _subir,
    ctx,
)


@pytest_asyncio.fixture
async def ctx_auditor(ctx):
    from app_core.db.session import fijar_contexto_rls

    sufijo = ctx["a"].split("-")[-1]
    auditores = {
        "aud": (f"evi2-aud-{sufijo}", ctx["a"], "auditor"),
        "aud_b": (f"evi2-audb-{sufijo}", ctx["b"], "auditor"),
    }
    async with ctx["factory"]() as s:
        for uid, tenant, rol in auditores.values():
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
    ctx["u"].update(auditores)
    return ctx


def _aud(ctx, clave="aud"):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _documento_solo_dpo(ctx, nombre="solo-dpo.pdf"):
    doc = await _subir(ctx, nombre, _pdf(nombre))
    assert (await _atributos(ctx, doc["id"], visible_para=["dpo"])).status_code == 200
    return doc


@pytest.mark.asyncio
async def test_el_auditor_lista_y_descarga_un_documento_solo_para_el_dpo(ctx_auditor):
    ctx = ctx_auditor
    doc = await _documento_solo_dpo(ctx)
    # Aserción positiva previa: el rol sin visibilidad sí queda fuera.
    assert (await ctx["client"].get(f"{BASE}/documentos/{doc['id']}/archivo", headers=_como(ctx, "coord"))).status_code in (403, 404)
    lista = await ctx["client"].get(f"{BASE}/atributos", headers=_aud(ctx))
    assert lista.status_code == 200, lista.text
    assert doc["id"] in [d["documento_id"] for d in lista.json()["documentos"]]
    bajada = await ctx["client"].get(f"{BASE}/documentos/{doc['id']}/archivo", headers=_aud(ctx))
    assert bajada.status_code == 200, bajada.text
    assert bajada.content == _pdf("solo-dpo.pdf")


@pytest.mark.asyncio
async def test_el_auditor_no_puede_definir_atributos(ctx_auditor):
    ctx = ctx_auditor
    doc = await _subir(ctx, "atributos.pdf", _pdf("atributos.pdf"))
    r = await _atributos(ctx, doc["id"], visible_para=["dpo"], quien="aud")
    assert r.status_code == 403, r.text
    # El DPO sí puede: la ruta no quedó cerrada para todos.
    assert (await _atributos(ctx, doc["id"], visible_para=["dpo"])).status_code == 200


@pytest.mark.asyncio
async def test_los_atributos_por_defecto_no_incluyen_al_auditor(ctx_auditor):
    from features.evidencias.domain.vigencia import ROLES_VISIBILIDAD_POSIBLES

    ctx = ctx_auditor
    assert "auditor" not in ROLES_VISIBILIDAD_POSIBLES
    doc = await _subir(ctx, "por-defecto.pdf", _pdf("por-defecto.pdf"))
    # Fijar atributos sin lista usa el valor por omisión: el INSERT debe pasar el CHECK de la base.
    assert (await _atributos(ctx, doc["id"])).status_code == 200
    lista = await ctx["client"].get(f"{BASE}/atributos", headers=_aud(ctx))
    fila = next(d for d in lista.json()["documentos"] if d["documento_id"] == doc["id"])
    assert "auditor" not in fila["visible_para"] and "dpo" in fila["visible_para"]


@pytest.mark.asyncio
async def test_el_auditor_de_una_organizacion_no_ve_las_de_otra(ctx_auditor):
    ctx = ctx_auditor
    doc = await _subir(ctx, "de-a.pdf", _pdf("de-a.pdf"))
    propia = await ctx["client"].get(f"{BASE}/atributos", headers=_aud(ctx))
    assert doc["id"] in [d["documento_id"] for d in propia.json()["documentos"]]
    ajena = await ctx["client"].get(f"{BASE}/atributos", headers=_aud(ctx, "aud_b"))
    assert ajena.status_code == 200, ajena.text
    assert ajena.json()["documentos"] == []
    assert (await ctx["client"].get(f"{BASE}/documentos/{doc['id']}/archivo", headers=_aud(ctx, "aud_b"))).status_code in (403, 404)


@pytest.mark.asyncio
async def test_el_paquete_del_auditor_es_el_mismo_que_el_del_dpo(ctx_auditor):
    ctx = ctx_auditor
    await _documento_solo_dpo(ctx, "reservado.pdf")
    await _subir(ctx, "abierto.pdf", _pdf("abierto.pdf"))

    def nombres(r):
        assert r.status_code == 200, r.text
        return sorted(zipfile.ZipFile(io.BytesIO(r.content)).namelist())

    del_dpo = nombres(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_como(ctx, "dpo")))
    del_auditor = nombres(await ctx["client"].get(f"{BASE}/paquete-inspeccion", headers=_aud(ctx)))
    assert del_auditor == del_dpo and len(del_auditor) >= 4
