"""Compuerta pública de la sala ADPA: Cockpit del DPD/DPO."""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.services.dpo_engine import (
    AcuseYaRegistradoError,
    emitir_dictamen_consultivo,
    emitir_dictamen_persistido,
    firmar_acuse_persistido,
    listar_bitacora_persistida,
    registrar_acuse_gerencial,
    verificar_integridad_bitacora,
)


async def registrar_dictamen_dpo(
    session: AsyncSession, dictamen: DictamenDPO
) -> DictamenDPO:
    """Emite y persiste un dictamen técnico-consultivo en la bitácora PostgreSQL."""
    return await emitir_dictamen_persistido(session, dictamen)


async def listar_bitacora_dpo(
    session: AsyncSession, tenant_id: str
) -> List[DictamenDPO]:
    """Recupera el historial de dictámenes y advertencias del DPO para el tenant desde PostgreSQL."""
    return await listar_bitacora_persistida(session, tenant_id)


async def firmar_acuse_recibo_dpo(
    session: AsyncSession, tenant_id: str, dictamen_id: str, acuse_por: str
) -> Optional[DictamenDPO]:
    """Registra la constancia de que la alta dirección recibió el dictamen del DPO una sola vez."""
    return await firmar_acuse_persistido(session, tenant_id, dictamen_id, acuse_por)


async def verificar_cadena_bitacora_dpo(
    session: AsyncSession, tenant_id: str
) -> Optional[DictamenDPO]:
    """Recorre los dictámenes de la organización en orden de emisión y devuelve
    el primer dictamen alterado (o None si la cadena es íntegra).
    """
    return await verificar_integridad_bitacora(session, tenant_id)


verificar_cadena_organizacion = verificar_cadena_bitacora_dpo


def emitir_dictamen_dpo(
    dictamen_o_session: DictamenDPO | AsyncSession,
    dictamen: Optional[DictamenDPO] = None,
):
    """Emite un dictamen técnico-consultivo (con AsyncSession persiste en PostgreSQL)."""
    if isinstance(dictamen_o_session, AsyncSession):
        if dictamen is None:
            raise ValueError("Se requiere el dictamen a persistir.")
        return registrar_dictamen_dpo(dictamen_o_session, dictamen)
    return emitir_dictamen_consultivo(dictamen_o_session)


def consultar_bitacora_dpo(session: AsyncSession, tenant_id: str):
    """Recupera el historial de dictámenes y advertencias del DPO para el tenant."""
    return listar_bitacora_dpo(session, tenant_id)


def firmar_acuse_recibo_dictamen(
    dictamen_id_o_session: str | AsyncSession,
    tenant_id: Optional[str] = None,
    dictamen_id: Optional[str] = None,
    acuse_por: str = "alta_direccion",
):
    """Registra la constancia de que la gerencia recibió la recomendación del DPO."""
    if isinstance(dictamen_id_o_session, AsyncSession):
        if tenant_id is None or dictamen_id is None:
            raise ValueError("Se requieren tenant_id y dictamen_id.")
        return firmar_acuse_recibo_dpo(dictamen_id_o_session, tenant_id, dictamen_id, acuse_por)
    return registrar_acuse_gerencial(dictamen_id_o_session, acuse_por)


__all__ = [
    "AcuseYaRegistradoError",
    "DictamenDPO",
    "TipoDictamenDPO",
    "consultar_bitacora_dpo",
    "emitir_dictamen_dpo",
    "firmar_acuse_recibo_dictamen",
    "firmar_acuse_recibo_dpo",
    "listar_bitacora_dpo",
    "registrar_dictamen_dpo",
    "verificar_cadena_bitacora_dpo",
    "verificar_cadena_organizacion",
]


# === DPO-02 ===
# ¤dpo-informe-anual
from datetime import date as _date  # noqa: E402

from features.dpo_cockpit.domain.inscripcion import InscripcionSPDP  # noqa: E402
from features.dpo_cockpit.services.informe_anual_engine import (  # noqa: E402
    armar_informe,
    renderizar_documento,
)
from features.dpo_cockpit.services.inscripcion_engine import (  # noqa: E402
    historial_inscripcion,
    inscripcion_vigente,
    registrar_inscripcion,
)


async def generar_informe_anual_dpo(session: AsyncSession, tenant_id: str, anio: int) -> dict:
    """Informe de un año de la organización, armado desde su bitácora y su inscripción vigente."""
    return await armar_informe(session, tenant_id, anio)


def documento_informe_anual_dpo(informe: dict) -> str:
    """Documento descargable del informe, con la huella de la cadena en el pie."""
    return renderizar_documento(informe)


async def registrar_inscripcion_spdp(
    session: AsyncSession,
    tenant_id: str,
    registrado_por: str,
    inscrito: bool,
    fecha_inscripcion: Optional[_date],
    numero_tramite: Optional[str],
) -> InscripcionSPDP:
    """Agrega una entrada al historial de inscripción de la organización (solo de alta)."""
    return await registrar_inscripcion(
        session, tenant_id, registrado_por, inscrito, fecha_inscripcion, numero_tramite
    )


async def consultar_historial_inscripcion_spdp(
    session: AsyncSession, tenant_id: str
) -> List[InscripcionSPDP]:
    """Historial de inscripción de la organización, de la más reciente a la más antigua."""
    return await historial_inscripcion(session, tenant_id)


async def consultar_inscripcion_spdp_vigente(
    session: AsyncSession, tenant_id: str
) -> Optional[InscripcionSPDP]:
    """La inscripción vigente (la última registrada) o None."""
    return await inscripcion_vigente(session, tenant_id)


__all__ += [
    "consultar_historial_inscripcion_spdp",
    "consultar_inscripcion_spdp_vigente",
    "documento_informe_anual_dpo",
    "generar_informe_anual_dpo",
    "registrar_inscripcion_spdp",
]
# === fin DPO-02 ===
