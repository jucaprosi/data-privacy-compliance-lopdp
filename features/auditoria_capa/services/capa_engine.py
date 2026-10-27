"""Motor de Acciones Correctivas y Preventivas (CAPA) con Segregación de Funciones (SoD) persistido en PostgreSQL."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from features.auditoria_capa.domain.models import (
    EstadoCAPA,
    SeveridadHallazgo,
    TicketCAPA,
    capa_tickets,
)


class TicketYaCerradoError(Exception):
    """Se lanza cuando se intenta modificar o volver a cerrar un ticket ya cerrado y verificado."""


def _normalizar_fecha_utc(valor: str | datetime | None) -> datetime:
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
    return dt.astimezone(timezone.utc)


def _fila_a_ticket(fila) -> TicketCAPA:
    datos = dict(fila)
    dt_creacion = _normalizar_fecha_utc(datos["fecha_creacion"])
    fecha_cierre_raw = datos.get("fecha_cierre")
    dt_cierre: Optional[datetime] = None
    if fecha_cierre_raw is not None:
        dt_cierre = _normalizar_fecha_utc(fecha_cierre_raw)
    return TicketCAPA(
        id=datos["id"],
        tenant_id=datos["tenant_id"],
        control_id=datos["control_id"],
        severidad=SeveridadHallazgo(datos["severidad"]),
        descripcion_hallazgo=datos["descripcion_hallazgo"],
        causa_raiz=datos.get("causa_raiz") or "",
        accion_correctiva=datos["accion_correctiva"],
        responsable_implementacion_id=datos["responsable_implementacion_id"],
        creado_por=datos.get("creado_por") or "",
        auditor_verificador_id=datos.get("auditor_verificador_id"),
        estado=EstadoCAPA(datos["estado"]),
        evidencia_cierre_id=datos.get("evidencia_cierre_id"),
        snapshot_normativo=datos.get("snapshot_normativo") or "LOPDP-Ecuador-2021",
        fecha_creacion=dt_creacion,
        fecha_cierre=dt_cierre,
    )


def validar_cierre_sod(
    responsable_implementacion_id: str,
    auditor_id: str,
    evidencia_id: str,
) -> None:
    """Invariante SoD: quien implementa la acción correctiva no puede auditar y cerrarla."""
    if responsable_implementacion_id == auditor_id:
        raise PermissionError(
            "Violación SoD: El implementador de la acción correctiva no puede ser "
            "el auditor que verifica y cierra el hallazgo."
        )
    if not evidencia_id or not evidencia_id.strip():
        raise ValueError(
            "El cierre de un ticket CAPA exige adjuntar el ID de evidencia probatoria."
        )


async def crear_ticket_capa(session: AsyncSession, ticket: TicketCAPA) -> TicketCAPA:
    """Registra un nuevo hallazgo de auditoría o brecha de cumplimiento en PostgreSQL."""
    ticket.estado = EstadoCAPA.ABIERTO
    ticket.auditor_verificador_id = None
    ticket.evidencia_cierre_id = None
    ticket.fecha_cierre = None
    dt_creacion = _normalizar_fecha_utc(ticket.fecha_creacion)
    ticket.fecha_creacion = dt_creacion

    severidad_valor = (
        ticket.severidad.value
        if isinstance(ticket.severidad, SeveridadHallazgo)
        else str(ticket.severidad)
    )
    await session.execute(
        insert(capa_tickets).values(
            id=ticket.id,
            tenant_id=ticket.tenant_id,
            control_id=ticket.control_id,
            severidad=severidad_valor,
            descripcion_hallazgo=ticket.descripcion_hallazgo,
            causa_raiz=ticket.causa_raiz or "",
            accion_correctiva=ticket.accion_correctiva,
            responsable_implementacion_id=ticket.responsable_implementacion_id,
            creado_por=ticket.creado_por or "",
            auditor_verificador_id=None,
            estado=EstadoCAPA.ABIERTO.value,
            evidencia_cierre_id=None,
            snapshot_normativo=ticket.snapshot_normativo or "LOPDP-Ecuador-2021",
            fecha_creacion=dt_creacion,
            fecha_cierre=None,
        )
    )
    return ticket


async def listar_tickets_tenant(
    session: AsyncSession, tenant_id: str
) -> List[TicketCAPA]:
    """Lista los casos CAPA de la organización en orden de creación descendente."""
    filas = (
        await session.execute(
            select(capa_tickets)
            .where(capa_tickets.c.tenant_id == tenant_id)
            .order_by(capa_tickets.c.fecha_creacion.desc(), capa_tickets.c.id.asc())
        )
    ).mappings().all()
    return [_fila_a_ticket(f) for f in filas]


async def cerrar_ticket_verificado(
    session: AsyncSession,
    tenant_id: str,
    ticket_id: str,
    auditor_id: str,
    evidencia_id: str,
) -> TicketCAPA:
    """Cierra un ticket CAPA en PostgreSQL exigiendo verificación independiente (SoD) e inmutabilidad tras el cierre."""
    fila = (
        await session.execute(
            select(capa_tickets)
            .where(
                capa_tickets.c.id == ticket_id,
                capa_tickets.c.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).mappings().first()

    if fila is None:
        raise KeyError(f"Ticket CAPA {ticket_id} no encontrado.")

    if (
        fila["estado"] == EstadoCAPA.CERRADO_VERIFICADO.value
        or fila["fecha_cierre"] is not None
    ):
        raise TicketYaCerradoError(
            f"El ticket CAPA '{ticket_id}' ya se encuentra cerrado y verificado."
        )

    validar_cierre_sod(
        str(fila["responsable_implementacion_id"]),
        auditor_id,
        evidencia_id,
    )

    dt_cierre = datetime.now(timezone.utc)
    evidencia_limpia = evidencia_id.strip()
    resultado = await session.execute(
        update(capa_tickets)
        .where(
            capa_tickets.c.id == ticket_id,
            capa_tickets.c.tenant_id == tenant_id,
            capa_tickets.c.estado != EstadoCAPA.CERRADO_VERIFICADO.value,
        )
        .values(
            estado=EstadoCAPA.CERRADO_VERIFICADO.value,
            auditor_verificador_id=auditor_id,
            evidencia_cierre_id=evidencia_limpia,
            fecha_cierre=dt_cierre,
        )
    )
    if resultado.rowcount == 0:
        raise TicketYaCerradoError(
            f"El ticket CAPA '{ticket_id}' ya se encuentra cerrado y verificado."
        )

    actualizado = dict(fila)
    actualizado["estado"] = EstadoCAPA.CERRADO_VERIFICADO.value
    actualizado["auditor_verificador_id"] = auditor_id
    actualizado["evidencia_cierre_id"] = evidencia_limpia
    actualizado["fecha_cierre"] = dt_cierre
    return _fila_a_ticket(actualizado)


def preparar_ticket_dominio(ticket: TicketCAPA) -> TicketCAPA:
    """Inicializa un ticket en el dominio puro sin estado en memoria."""
    ticket.estado = EstadoCAPA.ABIERTO
    if "::resp=" not in ticket.id:
        ticket.id = f"{ticket.id}::resp={ticket.responsable_implementacion_id}"
    return ticket


def cerrar_ticket_dominio(
    ticket_id: str,
    auditor_id: str,
    evidencia_id: str,
) -> TicketCAPA:
    """Evalúa la regla de dominio SoD sin almacenamiento en memoria."""
    if "::resp=" not in ticket_id:
        raise KeyError(f"Ticket CAPA {ticket_id} no encontrado.")
    base_id, responsable_id = ticket_id.split("::resp=", 1)
    validar_cierre_sod(responsable_id, auditor_id, evidencia_id)
    return TicketCAPA(
        id=base_id,
        responsable_implementacion_id=responsable_id,
        auditor_verificador_id=auditor_id,
        evidencia_cierre_id=evidencia_id.strip(),
        estado=EstadoCAPA.CERRADO_VERIFICADO,
        fecha_cierre=datetime.now(timezone.utc),
    )


__all__ = [
    "TicketYaCerradoError",
    "cerrar_ticket_dominio",
    "cerrar_ticket_verificado",
    "crear_ticket_capa",
    "listar_tickets_tenant",
    "preparar_ticket_dominio",
    "validar_cierre_sod",
]
