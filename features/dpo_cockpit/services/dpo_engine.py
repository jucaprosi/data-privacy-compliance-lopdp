"""Lógica de negocio e independencia del DPD/DPO (Invariante INV_LOPDP_DPO_INDEPENDENCE)."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from features.dpo_cockpit.domain.models import DictamenDPO
from features.dpo_cockpit.services.bitacora_service import (
    AcuseYaRegistradoError,
    GENESIS_HASH,
    acusar_recibo_alta_direccion,
    calcular_hash_dictamen,
    obtener_bitacora_tenant,
    registrar_dictamen,
    verificar_cadena_organizacion,
)


def emitir_dictamen_consultivo(dictamen: DictamenDPO, prev_hash: str = GENESIS_HASH) -> DictamenDPO:
    """Sella un dictamen técnico no vinculante en el dominio sin almacenamiento en memoria."""
    dictamen.es_vinculante = False
    dictamen.acuse_recibo_alta_direccion = False
    dictamen.prev_hash = prev_hash
    dictamen.sha256_hash = calcular_hash_dictamen(dictamen, prev_hash)
    return dictamen


def registrar_acuse_gerencial(dictamen_id: str, acuse_por: str = "alta_direccion") -> DictamenDPO:
    """Representa la constancia de recepción del dictamen por la Alta Dirección en pruebas de dominio."""
    return DictamenDPO(
        id=dictamen_id,
        es_vinculante=False,
        acuse_recibo_alta_direccion=True,
        acuse_por=acuse_por,
        fecha_acuse=datetime.now(timezone.utc),
    )


async def emitir_dictamen_persistido(
    session: AsyncSession, dictamen: DictamenDPO
) -> DictamenDPO:
    """Emite y persiste un dictamen en PostgreSQL dentro de la sesión activa."""
    return await registrar_dictamen(session, dictamen)


async def listar_bitacora_persistida(
    session: AsyncSession, tenant_id: str
) -> List[DictamenDPO]:
    """Obtiene la bitácora del DPO desde PostgreSQL para la organización indicada."""
    return await obtener_bitacora_tenant(session, tenant_id)


async def firmar_acuse_persistido(
    session: AsyncSession, tenant_id: str, dictamen_id: str, acuse_por: str
) -> Optional[DictamenDPO]:
    """Registra en PostgreSQL el acuse de recibo de la alta dirección una sola vez."""
    return await acusar_recibo_alta_direccion(session, tenant_id, dictamen_id, acuse_por)


async def verificar_integridad_bitacora(
    session: AsyncSession, tenant_id: str
) -> Optional[DictamenDPO]:
    """Verifica la cadena SHA-256 de la organización y devuelve el primer dictamen alterado o None."""
    return await verificar_cadena_organizacion(session, tenant_id)


__all__ = [
    "AcuseYaRegistradoError",
    "emitir_dictamen_consultivo",
    "emitir_dictamen_persistido",
    "firmar_acuse_persistido",
    "listar_bitacora_persistida",
    "obtener_bitacora_tenant",
    "registrar_acuse_gerencial",
    "verificar_integridad_bitacora",
]
