# ¤evidencias ¤arbitro
"""EVI-01: la retención por objeto sale de un solo lugar y, si no se fija, el documento no se registra.

La parte de base corre contra PostgreSQL (sin TEST_DATABASE_URL se omite); el almacén se simula.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- Escribir `1825` en otro archivo de features/, api/ o app_core/ -> test_ningun_literal_1825_fuera_de_retencion_dias.
- En `confirmar_subida`, omitir el bloque `almacen.fijar_retencion(...)`
  -> test_sin_retencion_fijada_el_documento_no_se_registra y test_la_retencion_se_fija_con_los_dias_de_retencion_dias.
"""
import ast
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from app_core.errors import ErrorNegocio  # noqa: E402
from features.evidencias.domain.retencion import retencion_dias  # noqa: E402
from features.evidencias.services import evidencias_engine as motor  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CARPETAS = ("features", "api", "app_core")
PDF = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"


def _literales_1825(ruta: Path) -> list[int]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
    return [
        n.lineno for n in ast.walk(arbol) if isinstance(n, ast.Constant) and n.value in (1825, "1825")
    ]


def test_retencion_dias_devuelve_1825_para_toda_organizacion_mientras_no_exista_bov01():
    assert retencion_dias("cualquier-organizacion") == 1825
    assert retencion_dias("otra") == 1825


def test_ningun_literal_1825_fuera_de_retencion_dias():
    propio = RAIZ / "features" / "evidencias" / "domain" / "retencion.py"
    hallazgos = {}
    for carpeta in CARPETAS:
        for ruta in (RAIZ / carpeta).rglob("*.py"):
            if ruta == propio:
                continue
            lineas = _literales_1825(ruta)
            if lineas:
                hallazgos[str(ruta.relative_to(RAIZ))] = lineas
    assert hallazgos == {}, f"El 1825 solo puede estar en retencion_dias: {hallazgos}"
    assert len(_literales_1825(propio)) == 1


class AlmacenConRetencion:
    def __init__(self, falla: bool = False) -> None:
        self.objetos: dict[str, bytes] = {}
        self.retenciones: dict[str, datetime] = {}
        self.falla = falla

    def descargar(self, clave: str, maximo_bytes: int):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave: str, retener_hasta: datetime) -> None:
        if self.falla:
            raise RuntimeError("el almacén no dejó fijar la retención")
        self.retenciones[clave] = retener_hasta


@pytest_asyncio.fixture
async def sesion():
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant, usuario = f"evi1r-t-{sufijo}", f"evi1r-u-{sufijo}"
    from app_core.db.session import fijar_contexto_rls

    async with factory() as s:
        await s.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, :t, :t, :t)"
            ),
            {"t": tenant},
        )
        await s.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
            {"u": usuario, "e": f"{usuario}@ejemplo.invalid"},
        )
        await s.commit()
    async with factory() as s:
        yield s, tenant, usuario
        await s.rollback()
    async with factory() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM evidencias_documentos WHERE tenant_id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": usuario})
        await s.commit()
    await engine.dispose()


async def _contar(session, tenant: str) -> int:
    return (
        await session.execute(text("SELECT count(*) FROM evidencias_documentos WHERE tenant_id = :t"), {"t": tenant})
    ).scalar_one()


@pytest.mark.asyncio
async def test_la_retencion_se_fija_con_los_dias_de_retencion_dias(sesion):
    s, tenant, usuario = sesion
    almacen = AlmacenConRetencion()
    clave = f"{tenant}/{uuid.uuid4().hex}"
    almacen.objetos[clave] = PDF
    antes = datetime.now(timezone.utc)
    documento, duplicada = await motor.confirmar_subida(
        s, almacen, tenant, usuario, "dpo", False, clave, hashlib.sha256(PDF).hexdigest(), "p.pdf",
        "application/pdf",
    )
    assert duplicada is False
    assert documento.retencion_dias == retencion_dias(tenant)
    hasta = almacen.retenciones[clave]
    esperado = antes + timedelta(days=retencion_dias(tenant))
    assert abs((hasta - esperado).total_seconds()) < 60


@pytest.mark.asyncio
async def test_sin_retencion_fijada_el_documento_no_se_registra(sesion):
    s, tenant, usuario = sesion
    almacen = AlmacenConRetencion(falla=True)
    clave = f"{tenant}/{uuid.uuid4().hex}"
    almacen.objetos[clave] = PDF
    with pytest.raises(ErrorNegocio) as info:
        await motor.confirmar_subida(
            s, almacen, tenant, usuario, "dpo", False, clave, hashlib.sha256(PDF).hexdigest(), "p.pdf",
            "application/pdf",
        )
    assert info.value.code == "EVI_RETENCION_NO_FIJADA" and info.value.status_code == 502
    assert await _contar(s, tenant) == 0
