"""Servicio de Bitácora Inviolable del DPO persistida en PostgreSQL (Art. 50 LOPDP)."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import List, Optional

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO, dpo_dictamenes

GENESIS_HASH = "0" * 64


class AcuseYaRegistradoError(Exception):
    """Se lanza cuando se intenta firmar el acuse de recibo más de una vez."""


def _normalizar_fecha_utc(valor: str | datetime | None) -> tuple[datetime, str]:
    if isinstance(valor, datetime):
        dt = valor if valor.tzinfo is not None else valor.replace(tzinfo=timezone.utc)
    elif isinstance(valor, str) and valor.strip():
        normalizado = valor.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalizado)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt, dt.isoformat()


def _fila_a_dictamen(fila) -> DictamenDPO:
    datos = dict(fila)
    dt_emision, _ = _normalizar_fecha_utc(datos["fecha_emision"])
    fecha_acuse_raw = datos.get("fecha_acuse")
    dt_acuse: Optional[datetime] = None
    if fecha_acuse_raw is not None:
        dt_acuse, _ = _normalizar_fecha_utc(fecha_acuse_raw)
    tipo_raw = datos["tipo"]
    tipo = (
        TipoDictamenDPO(tipo_raw)
        if tipo_raw in TipoDictamenDPO.__members__
        else TipoDictamenDPO.OPINION_CONSULTIVA
    )
    return DictamenDPO(
        id=datos["id"],
        tenant_id=datos["tenant_id"],
        dpo_id=datos["dpo_id"],
        tipo=tipo,
        asunto=datos["asunto"],
        referencia_normativa=datos["referencia_normativa"],
        cuerpo=datos["cuerpo"],
        fecha_emision=dt_emision,
        es_vinculante=bool(datos["es_vinculante"]),
        prev_hash=datos["prev_hash"],
        sha256_hash=datos["sha256_hash"],
        acuse_recibo_alta_direccion=bool(datos["acuse_recibo_alta_direccion"]),
        acuse_por=datos.get("acuse_por"),
        fecha_acuse=dt_acuse,
    )


def calcular_hash_dictamen(dictamen: DictamenDPO, prev_hash: str) -> str:
    """Calcula el hash SHA-256 encadenado al registro previo de la misma organización."""
    _, fecha_iso = _normalizar_fecha_utc(dictamen.fecha_emision)
    tipo_valor = dictamen.tipo.value if isinstance(dictamen.tipo, TipoDictamenDPO) else str(dictamen.tipo)
    payload = {
        "id": dictamen.id,
        "tenant_id": dictamen.tenant_id,
        "dpo_id": dictamen.dpo_id,
        "tipo": tipo_valor,
        "asunto": dictamen.asunto,
        "referencia_normativa": dictamen.referencia_normativa,
        "cuerpo": dictamen.cuerpo,
        "fecha_emision": fecha_iso,
        "es_vinculante": False,
        "prev_hash": prev_hash,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def registrar_dictamen(session: AsyncSession, dictamen: DictamenDPO) -> DictamenDPO:
    """Persiste un dictamen en PostgreSQL encadenando su huella SHA-256 por organización."""
    dictamen.es_vinculante = False
    dictamen.acuse_recibo_alta_direccion = False
    dictamen.acuse_por = None
    dictamen.fecha_acuse = None

    dt_emision, _ = _normalizar_fecha_utc(dictamen.fecha_emision)
    ultimo = (
        await session.execute(
            select(dpo_dictamenes.c.sha256_hash, dpo_dictamenes.c.fecha_emision)
            .where(dpo_dictamenes.c.tenant_id == dictamen.tenant_id)
            .order_by(dpo_dictamenes.c.fecha_emision.desc(), dpo_dictamenes.c.id.desc())
            .limit(1)
            .with_for_update()
        )
    ).mappings().first()

    if ultimo is not None:
        dt_ultimo, _ = _normalizar_fecha_utc(ultimo["fecha_emision"])
        if dt_emision <= dt_ultimo:
            dt_emision = dt_ultimo + timedelta(microseconds=1)
        prev_hash = str(ultimo["sha256_hash"])
    else:
        prev_hash = GENESIS_HASH

    dictamen.fecha_emision = dt_emision
    dictamen.prev_hash = prev_hash
    dictamen.sha256_hash = calcular_hash_dictamen(dictamen, prev_hash)

    tipo_valor = dictamen.tipo.value if isinstance(dictamen.tipo, TipoDictamenDPO) else str(dictamen.tipo)
    await session.execute(
        insert(dpo_dictamenes).values(
            id=dictamen.id,
            tenant_id=dictamen.tenant_id,
            dpo_id=dictamen.dpo_id,
            tipo=tipo_valor,
            asunto=dictamen.asunto,
            referencia_normativa=dictamen.referencia_normativa,
            cuerpo=dictamen.cuerpo,
            fecha_emision=dt_emision,
            es_vinculante=False,
            prev_hash=dictamen.prev_hash,
            sha256_hash=dictamen.sha256_hash,
            acuse_recibo_alta_direccion=False,
            acuse_por=None,
            fecha_acuse=None,
        )
    )
    return dictamen


async def obtener_bitacora_tenant(session: AsyncSession, tenant_id: str) -> List[DictamenDPO]:
    """Lista los dictámenes de la organización en orden de emisión."""
    filas = (
        await session.execute(
            select(dpo_dictamenes)
            .where(dpo_dictamenes.c.tenant_id == tenant_id)
            .order_by(dpo_dictamenes.c.fecha_emision.asc(), dpo_dictamenes.c.id.asc())
        )
    ).mappings().all()
    return [_fila_a_dictamen(f) for f in filas]


async def acusar_recibo_alta_direccion(
    session: AsyncSession,
    tenant_id: str,
    dictamen_id: str,
    acuse_por: str,
) -> Optional[DictamenDPO]:
    """Registra el acuse de recibo de la alta dirección una sola vez sobre un dictamen de su organización."""
    fila = (
        await session.execute(
            select(dpo_dictamenes)
            .where(
                dpo_dictamenes.c.id == dictamen_id,
                dpo_dictamenes.c.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).mappings().first()

    if fila is None:
        return None

    if fila["acuse_recibo_alta_direccion"] or fila["fecha_acuse"] is not None:
        raise AcuseYaRegistradoError(
            f"El dictamen '{dictamen_id}' ya cuenta con acuse de recibo de la alta dirección."
        )

    dt_acuse = datetime.now(timezone.utc)
    resultado = await session.execute(
        update(dpo_dictamenes)
        .where(
            dpo_dictamenes.c.id == dictamen_id,
            dpo_dictamenes.c.tenant_id == tenant_id,
            dpo_dictamenes.c.acuse_recibo_alta_direccion.is_(False),
            dpo_dictamenes.c.fecha_acuse.is_(None),
        )
        .values(
            acuse_recibo_alta_direccion=True,
            acuse_por=acuse_por,
            fecha_acuse=dt_acuse,
        )
    )
    if resultado.rowcount == 0:
        raise AcuseYaRegistradoError(
            f"El dictamen '{dictamen_id}' ya cuenta con acuse de recibo de la alta dirección."
        )

    actualizado = dict(fila)
    actualizado["acuse_recibo_alta_direccion"] = True
    actualizado["acuse_por"] = acuse_por
    actualizado["fecha_acuse"] = dt_acuse
    return _fila_a_dictamen(actualizado)


async def verificar_cadena_organizacion(
    session: AsyncSession, tenant_id: str
) -> Optional[DictamenDPO]:
    """Recorre los dictámenes de la organización en orden de emisión y devuelve
    el primer dictamen alterado (o None si la cadena es íntegra).
    """
    dictamenes = await obtener_bitacora_tenant(session, tenant_id)
    expected_prev = GENESIS_HASH
    for dictamen in dictamenes:
        expected_hash = calcular_hash_dictamen(dictamen, expected_prev)
        if dictamen.prev_hash != expected_prev or dictamen.sha256_hash != expected_hash:
            return dictamen
        expected_prev = dictamen.sha256_hash
    return None
