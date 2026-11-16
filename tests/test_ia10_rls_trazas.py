# ¤gemini-vertex ¤seguridad-tenant ¤arbitro
"""IA-10: trazas_ia aislada por organización con RLS forzada, y escrita en la transacción del llamador."""
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import inferencia
from features.inferencia.domain.traza import Traza


def _traza(tenant: str) -> Traza:
    return Traza("roadmap", tenant, "gemini-2.5-flash-002", "gemini-2.5-flash", "roadmap.redaccion", 1, None)


@pytest_asyncio.fixture
async def dos_organizaciones(db_engine):
    ids = [f"t-ia10-{uuid.uuid4().hex[:8]}" for _ in range(2)]
    fabrica = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with fabrica() as s:
        for t in ids:
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:t, :t, :t, :ruc)"),
                {"t": t, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
            )
        await s.commit()
    yield ids, fabrica
    async with fabrica() as s:
        await s.execute(text("DELETE FROM trazas_ia WHERE tenant_id = ANY(:ids)"), {"ids": ids})
        await s.execute(text("DELETE FROM tenants WHERE id = ANY(:ids)"), {"ids": ids})
        await s.commit()


async def _contar(sesion, tenant: str | None = None) -> int:
    consulta = "SELECT count(*) FROM trazas_ia" + (" WHERE tenant_id = :t" if tenant else "")
    return (await sesion.execute(text(consulta), {"t": tenant} if tenant else {})).scalar()


@pytest.mark.asyncio
async def test_trazas_ia_tiene_rls_habilitada_y_forzada(db_engine):
    async with db_engine.connect() as c:
        fila = (await c.execute(text(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE relname = 'trazas_ia' AND relnamespace = 'public'::regnamespace"
        ))).first()
    assert fila is not None, "falta la tabla trazas_ia"
    assert fila.relrowsecurity is True and fila.relforcerowsecurity is True


@pytest.mark.asyncio
async def test_cada_organizacion_ve_solo_sus_trazas(dos_organizaciones):
    (a, b), fabrica = dos_organizaciones
    for t in (a, b):
        async with fabrica() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, t)
            await inferencia.registrar_traza(s, _traza(t), "roadmaps", f"rm-{t}")
            await s.commit()
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, a)
        assert await _contar(s) == 1
        assert await _contar(s, b) == 0
        await s.rollback()
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        assert await _contar(s) == 0  # sin tenant fijado no se ve nada
        await s.rollback()


@pytest.mark.asyncio
async def test_no_se_puede_escribir_una_traza_de_otra_organizacion(dos_organizaciones):
    (a, b), fabrica = dos_organizaciones
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, a)
        with pytest.raises(Exception, match="row-level security"):
            await inferencia.registrar_traza(s, _traza(b), "roadmaps", "rm-ajeno")
        await s.rollback()


@pytest.mark.asyncio
async def test_la_aplicacion_no_puede_modificar_ni_borrar_trazas(dos_organizaciones):
    (a, _), fabrica = dos_organizaciones
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, a)
        await inferencia.registrar_traza(s, _traza(a), "roadmaps", "rm-1")
        for sentencia in ("UPDATE trazas_ia SET sala = 'x'", "DELETE FROM trazas_ia"):
            with pytest.raises(Exception, match="permission denied"):
                async with s.begin_nested():
                    await s.execute(text(sentencia))
        await s.rollback()


@pytest.mark.asyncio
async def test_un_rollback_del_llamador_se_lleva_la_traza(dos_organizaciones):
    """registrar_traza no hace commit: si el llamador revierte, la traza desaparece con el resultado."""
    (a, _), fabrica = dos_organizaciones
    traza = _traza(a)
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, a)
        await inferencia.registrar_traza(s, traza, "roadmaps", "rm-1")
        await s.rollback()
    async with fabrica() as s:
        total = (await s.execute(text("SELECT count(*) FROM trazas_ia WHERE id = :i"), {"i": traza.id})).scalar()
    assert total == 0
