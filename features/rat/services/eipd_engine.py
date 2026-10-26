"""Persistencia PostgreSQL de EIPD y cálculo reproducible de riesgo."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import MetaData, Table, Column, String, Text, Integer, DateTime, select, insert, update
from sqlalchemy.dialects.postgresql import JSONB

# La LOPDP (art. 42) exige la EIPD cuando el tratamiento entraña alto riesgo, pero no fija escalas
# ni bandas numéricas. Las de abajo son una decisión operativa del producto (matriz 5×5 de
# probabilidad por impacto, la de la matriz de trabajo SALUDATA), pendiente de validación por el
# DPO o un profesional legal; no se presentan como norma. Ver governance/tareas/RAT-03.md.
MAXIMA_ESCALA = 5  # probabilidad e impacto de 1 a 5
MAXIMO_BAJO = 4  # P×I 1..4
MAXIMO_MEDIO = 9  # P×I 5..9
MAXIMO_ALTO = 16  # P×I 10..16; desde 17, crítico

metadata = MetaData()
rat_eipd = Table("rat_eipd", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String), Column("rat_id", String),
    Column("estado", String), Column("descripcion", Text), Column("volumen_titulares_aprobacion", Integer),
    Column("categorias_datos_aprobacion", JSONB),
    Column("version", Integer), Column("aprobada_por", String), Column("aprobada_en", DateTime(timezone=True)),
    Column("creada_en", DateTime(timezone=True)), Column("actualizada_en", DateTime(timezone=True)))
rat_eipd_riesgos = Table("rat_eipd_riesgos", metadata,
    Column("id", String, primary_key=True), Column("tenant_id", String), Column("eipd_id", String),
    Column("descripcion", Text), Column("probabilidad", Integer), Column("impacto", Integer),
    Column("puntuacion", Integer), Column("nivel", String), Column("medida", Text))


def nivel_riesgo(probabilidad: int, impacto: int) -> tuple[int, str]:
    if not 1 <= probabilidad <= MAXIMA_ESCALA or not 1 <= impacto <= MAXIMA_ESCALA:
        raise ValueError("Probabilidad e impacto deben estar entre 1 y 5")
    puntuacion = probabilidad * impacto
    nivel = "BAJO" if puntuacion <= MAXIMO_BAJO else "MEDIO" if puntuacion <= MAXIMO_MEDIO else "ALTO" if puntuacion <= MAXIMO_ALTO else "CRITICO"
    return puntuacion, nivel


@dataclass
class RiesgoEIPD:
    descripcion: str
    probabilidad: int
    impacto: int
    medida: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))


async def obtener_eipd(session, tenant_id: str, eipd_id: str, bloquear=False):
    consulta = select(rat_eipd).where(rat_eipd.c.id == eipd_id, rat_eipd.c.tenant_id == tenant_id)
    fila = (await session.execute(consulta.with_for_update() if bloquear else consulta)).mappings().first()
    if not fila:
        return None
    riesgos = (await session.execute(select(rat_eipd_riesgos).where(
        rat_eipd_riesgos.c.eipd_id == eipd_id, rat_eipd_riesgos.c.tenant_id == tenant_id,
    ).order_by(rat_eipd_riesgos.c.id))).mappings().all()
    resultado = dict(fila); resultado["riesgos"] = [dict(r) for r in riesgos]
    return resultado


async def crear_eipd(session, tenant_id, rat_id, descripcion, volumen, riesgos):
    ahora, eipd_id = datetime.now(timezone.utc), str(uuid4())
    await session.execute(insert(rat_eipd).values(id=eipd_id, tenant_id=tenant_id, rat_id=rat_id,
        estado="BORRADOR", descripcion=descripcion, volumen_titulares_aprobacion=volumen,
        version=1, aprobada_por=None, aprobada_en=None, creada_en=ahora, actualizada_en=ahora))
    for riesgo in riesgos:
        puntuacion, nivel = nivel_riesgo(riesgo.probabilidad, riesgo.impacto)
        await session.execute(insert(rat_eipd_riesgos).values(id=riesgo.id, tenant_id=tenant_id,
            eipd_id=eipd_id, descripcion=riesgo.descripcion, probabilidad=riesgo.probabilidad,
            impacto=riesgo.impacto, puntuacion=puntuacion, nivel=nivel, medida=riesgo.medida))
    return await obtener_eipd(session, tenant_id, eipd_id)


async def editar_eipd(session, tenant_id, eipd_id, descripcion):
    actual = await obtener_eipd(session, tenant_id, eipd_id, True)
    if not actual:
        return None
    await session.execute(update(rat_eipd).where(rat_eipd.c.id == eipd_id,
        rat_eipd.c.tenant_id == tenant_id).values(descripcion=descripcion,
        version=actual["version"] + 1, estado="BORRADOR", actualizada_en=datetime.now(timezone.utc)))
    return await obtener_eipd(session, tenant_id, eipd_id)


async def aprobar_eipd(session, tenant_id, eipd_id, user_id, volumen, categorias_datos):
    actual = await obtener_eipd(session, tenant_id, eipd_id, True)
    if not actual:
        return None
    ahora = datetime.now(timezone.utc)
    await session.execute(update(rat_eipd).where(rat_eipd.c.id == eipd_id,
        rat_eipd.c.tenant_id == tenant_id).values(estado="APROBADA", aprobada_por=user_id,
        aprobada_en=ahora, volumen_titulares_aprobacion=volumen,
        categorias_datos_aprobacion=list(categorias_datos), version=actual["version"] + 1,
        actualizada_en=ahora))
    return await obtener_eipd(session, tenant_id, eipd_id)
