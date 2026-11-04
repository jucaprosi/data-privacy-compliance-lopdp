# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Conservación de documentos privados sin asumir un plazo universal.

La ausencia de una política aprobada es una denegación, no un plazo implícito. El bloqueo legal
prevalece incluso cuando una fecha de retención ya venció.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.biblioteca.services.documentos_consulta import contexto, obtener_documento


class ContratoConservacion(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CambiarConservacion(ContratoConservacion):
    retenido_hasta: datetime | None = None
    bloqueo_legal: bool
    motivo: str = Field(min_length=1, max_length=1000)
    politica_id: str | None = Field(default=None, min_length=1, max_length=120)
    politica_aprobada: bool = False


class ConservacionDocumento(ContratoConservacion):
    documento_id: str
    retenido_hasta: datetime | None
    bloqueo_legal: bool
    motivo: str | None
    politica_id: str | None
    politica_aprobada: bool
    actualizado_por: str | None
    actualizado_en: datetime | None


async def obtener_conservacion(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str,
) -> ConservacionDocumento:
    await obtener_documento(session, tenant_id, actor, documento_id)
    fila = (await session.execute(text(
        "SELECT documento_id, retenido_hasta, bloqueo_legal, motivo, politica_id, politica_aprobada, "
        "actualizado_por, actualizado_en FROM biblioteca_conservacion "
        "WHERE tenant_id=:t AND documento_id=:d"
    ), {"t": tenant_id, "d": documento_id})).mappings().first()
    if fila is None:
        return ConservacionDocumento(documento_id=documento_id, retenido_hasta=None, bloqueo_legal=False,
                                     motivo=None, politica_id=None, politica_aprobada=False,
                                     actualizado_por=None, actualizado_en=None)
    return ConservacionDocumento(**fila)


async def cambiar_conservacion(
    session: AsyncSession, tenant_id: str, actor: str, documento_id: str, cambio: CambiarConservacion,
) -> ConservacionDocumento:
    await contexto(session, tenant_id, actor)
    await obtener_documento(session, tenant_id, actor, documento_id)
    await session.execute(text(
        "INSERT INTO biblioteca_conservacion(tenant_id, documento_id, retenido_hasta, bloqueo_legal, motivo, "
        "politica_id, politica_aprobada, actualizado_por) VALUES (:t,:d,:r,:b,:m,:p,:a,:u) "
        "ON CONFLICT (documento_id) DO UPDATE SET retenido_hasta=EXCLUDED.retenido_hasta, "
        "bloqueo_legal=EXCLUDED.bloqueo_legal, motivo=EXCLUDED.motivo, politica_id=EXCLUDED.politica_id, "
        "politica_aprobada=EXCLUDED.politica_aprobada, actualizado_por=EXCLUDED.actualizado_por, actualizado_en=now()"
    ), {"t": tenant_id, "d": documento_id, "r": cambio.retenido_hasta, "b": cambio.bloqueo_legal,
        "m": cambio.motivo, "p": cambio.politica_id, "a": cambio.politica_aprobada, "u": actor})
    return await obtener_conservacion(session, tenant_id, actor, documento_id)


def exigir_eliminable(conservacion: ConservacionDocumento, ahora: datetime | None = None) -> None:
    """Compuerta para cualquier futuro borrado físico; BIB-306 no ejecuta el borrado."""
    instante = ahora or datetime.now(timezone.utc)
    if conservacion.bloqueo_legal:
        raise ErrorNegocio("BIB_BLOQUEO_LEGAL_ACTIVO")
    if not conservacion.politica_aprobada or not conservacion.politica_id:
        raise ErrorNegocio("BIB_POLITICA_CONSERVACION_PENDIENTE")
    if conservacion.retenido_hasta is None or conservacion.retenido_hasta > instante:
        raise ErrorNegocio("BIB_RETENCION_ACTIVA")
