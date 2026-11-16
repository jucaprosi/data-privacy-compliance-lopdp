# ¤adpa ¤conservacion
"""Compuerta pública de la sala Conservación y Bloqueo (PRD §7.1).

Andamiaje de ADPA-09: sin lógica; CON-01 entrega la funcionalidad dentro de su sección.
"""
from __future__ import annotations

# === ADPA-09 ===
# Los códigos de error de esta sala viven en features/conservacion/domain/errores.py y se registran al importarlo.
from features.conservacion.domain import errores as _errores_sala  # noqa: F401
# === fin ADPA-09 ===

# === CON-01 ===
import hashlib
import json
import uuid
from calendar import monthrange
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.conservacion.domain import errores
from features.conservacion.models import PoliticaConservacion
from features.conservacion.schemas import PoliticaEntrada, PoliticaSalida

__all__ = [
    "PoliticaEntrada",
    "PoliticaSalida",
    "ROLES_CONSULTA",
    "ROLES_EJECUCION",
    "DIAS_POR_VENCER",
    "alertas_vencimiento",
    "crear_politica",
    "ejecutar_politica",
    "errores",
    "listar_politicas",
    "politicas_vencidas",
    "router",
]

# ESTIMADO: la ley no fija un aviso previo; el umbral sale de la propuesta de UX/UI aceptada por el CTO (2026-11-15).
DIAS_POR_VENCER = 30

# Crean políticas y registran su ejecución la persona administradora y el implementador; el resto solo consulta.
ROLES_CONSULTA = ("admin_organizacion", "implementador", "dpo", "coordinador", "auditor")
ROLES_EJECUCION = ("admin_organizacion", "implementador")

# Una política cuya acción es BLOQUEO queda BLOQUEADA; la anonimización y la supresión la dejan EJECUTADA.
_ESTADO_TRAS_EJECUTAR = {"BLOQUEO": "BLOQUEADA", "ANONIMIZACION": "EJECUTADA", "SUPRESION": "EJECUTADA"}


def __getattr__(nombre: str):
    # El router se carga al pedirlo (main.py), para que las rutas importen esta compuerta sin ciclo.
    if nombre == "router":
        from features.conservacion.routes.conservacion_routes import router

        return router
    raise AttributeError(nombre)


def _sumar_meses(base: date, meses: int) -> date:
    indice = base.month - 1 + meses
    anio, mes = base.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(base.day, monthrange(anio, mes)[1]))


def semaforo_de(fecha_revision: date, hoy: date) -> str:
    """R3: `vencida` si faltan 0 días o menos; `por_vencer` hasta DIAS_POR_VENCER días; `vigente` si no."""
    dias = (fecha_revision - hoy).days
    if dias <= 0:
        return "vencida"
    return "por_vencer" if dias <= DIAS_POR_VENCER else "vigente"


def _salida(p: PoliticaConservacion, hoy: date) -> PoliticaSalida:
    return PoliticaSalida(
        id=str(p.id),
        actividad_rat_id=p.actividad_rat_id,
        plazo_meses=p.plazo_meses,
        accion_vencimiento=p.accion_vencimiento,
        fecha_proxima_revision=p.fecha_proxima_revision,
        estado=p.estado,
        acta_ejecucion_hash=p.acta_ejecucion_hash,
        creado_en=p.creado_en,
        semaforo=semaforo_de(p.fecha_proxima_revision, hoy) if p.estado == "ACTIVA" else None,
    )


async def listar_politicas(session: AsyncSession, tenant_id: str, hoy: date | None = None) -> list[PoliticaSalida]:
    hoy = hoy or date.today()
    filas = (await session.execute(
        select(PoliticaConservacion).where(PoliticaConservacion.tenant_id == tenant_id)
        .order_by(PoliticaConservacion.fecha_proxima_revision, PoliticaConservacion.creado_en)
    )).scalars().all()
    return [_salida(p, hoy) for p in filas]


async def crear_politica(
    session: AsyncSession, tenant_id: str, entrada: PoliticaEntrada, user_id: str | None
) -> PoliticaSalida:
    """R1: la actividad debe existir en el RAT del inquilino, y se consulta solo por el pasillo del RAT."""
    from app_core.pasillo import rat as pasillo_rat

    if entrada.plazo_meses <= 0:
        raise errores.error(errores.CONSERVACION_PLAZO_INVALIDO)
    if not await pasillo_rat.existe_actividad(session, tenant_id, entrada.actividad_rat_id):
        raise errores.error(errores.CONSERVACION_ACTIVIDAD_NO_ENCONTRADA)
    hoy = date.today()
    politica = PoliticaConservacion(
        tenant_id=tenant_id,
        actividad_rat_id=entrada.actividad_rat_id,
        plazo_meses=entrada.plazo_meses,
        accion_vencimiento=entrada.accion_vencimiento,
        fecha_proxima_revision=entrada.fecha_proxima_revision or _sumar_meses(hoy, entrada.plazo_meses),
        estado="ACTIVA",
    )
    session.add(politica)
    await session.flush()
    await session.refresh(politica)
    await registrar_evento(
        session, tenant_id, "politica_conservacion", str(politica.id), "politica_creada",
        user_id=user_id, payload={"actividad_rat_id": politica.actividad_rat_id,
                                  "accion_vencimiento": politica.accion_vencimiento},
    )
    return _salida(politica, hoy)


def _acta(politica: PoliticaConservacion, ejecutada_en: datetime, estado: str) -> dict:
    """Acta de ejecución, sin datos personales; su JSON canónico es lo que se hashea."""
    return {
        "politica_id": str(politica.id),
        "tenant_id": politica.tenant_id,
        "actividad_rat_id": politica.actividad_rat_id,
        "plazo_meses": politica.plazo_meses,
        "accion_vencimiento": politica.accion_vencimiento,
        "estado_resultante": estado,
        "ejecutada_en": ejecutada_en.isoformat(),
    }


def hash_acta(acta: dict) -> str:
    """sha256 del JSON canónico (claves ordenadas, sin espacios) del acta."""
    return hashlib.sha256(json.dumps(acta, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


async def ejecutar_politica(
    session: AsyncSession, tenant_id: str, politica_id: str, user_id: str | None
) -> PoliticaSalida:
    """R2: una sola ejecución. La fila se bloquea (FOR UPDATE) para que dos ejecuciones simultáneas no choquen."""
    try:
        pid = uuid.UUID(str(politica_id))
    except ValueError:
        raise errores.error(errores.CONSERVACION_POLITICA_NO_ENCONTRADA) from None
    politica = (await session.execute(
        select(PoliticaConservacion)
        .where(PoliticaConservacion.id == pid, PoliticaConservacion.tenant_id == tenant_id)
        .with_for_update()
    )).scalars().first()
    if politica is None:
        raise errores.error(errores.CONSERVACION_POLITICA_NO_ENCONTRADA)
    if politica.estado != "ACTIVA":
        raise errores.error(errores.CONSERVACION_YA_EJECUTADA)
    estado = _ESTADO_TRAS_EJECUTAR[politica.accion_vencimiento]
    acta = _acta(politica, datetime.now(timezone.utc), estado)
    politica.acta_ejecucion_hash = hash_acta(acta)
    politica.estado = estado
    await session.flush()
    await registrar_evento(
        session, tenant_id, "politica_conservacion", str(politica.id), "politica_ejecutada",
        user_id=user_id, payload={"acta": acta, "acta_ejecucion_hash": politica.acta_ejecucion_hash},
    )
    return _salida(politica, date.today())


async def politicas_vencidas(session: AsyncSession, tenant_id: str, hoy: date | None = None) -> list[PoliticaSalida]:
    """R3: políticas ACTIVAS con `fecha_proxima_revision <= hoy`; las consume el pasillo hacia el DPO Cockpit."""
    return [p for p in await listar_politicas(session, tenant_id, hoy) if p.semaforo == "vencida"]


async def alertas_vencimiento(session: AsyncSession, tenant_id: str, hoy: date | None = None) -> list:
    """Alertas de vencimiento de retención para el DPO Cockpit, armadas por el pasillo del cockpit."""
    from app_core.pasillo import dpo_cockpit as pasillo_cockpit

    return [pasillo_cockpit.alerta_retencion_vencida(p) for p in await politicas_vencidas(session, tenant_id, hoy)]
# === fin CON-01 ===
