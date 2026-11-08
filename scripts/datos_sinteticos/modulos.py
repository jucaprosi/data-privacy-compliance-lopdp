# ¤entorno-pruebas ¤seguridad-tenant
"""Datos de ejemplo de los demás módulos para el entorno de pruebas (EP-10).

Cada registro entra por la compuerta `_service.py` de su sala, nunca por sus tablas. Antes de
registrar, la siembra lee por la compuerta de lectura de la sala: un identificador determinista
por organización hace que la segunda corrida encuentre lo ya sembrado y no cree nada.

Salas sembradas (lista cerrada de la ficha EP-10): rat, dpo_cockpit y auditoria_capa.
Faltantes: derechos_arco (su compuerta fija un tenant al azar; la corrige DER-03) y, sin alta
reconocible en su compuerta, riesgos_mtge, incidentes, terceros,
transferencias, roadmap y diagnostico.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from scripts.datos_sinteticos.organizaciones import (
    ORGANIZACIONES,
    OrganizacionFicticia,
    correo_ficticio,
    id_de_usuario,
)


@dataclass(frozen=True)
class SalaSembrada:
    nombre: str
    leer_ids: Callable[[object, str], Awaitable[set[str]]]
    registrar: Callable[[object, OrganizacionFicticia, str], Awaitable[None]]


def id_ejemplo(sala: str, org_id: str) -> str:
    """Identificador estable del registro de ejemplo de una sala en una organización."""
    return f"ep10-{sala}-{org_id}"


async def _fijar_tenant(session, tenant_id: str) -> None:
    """Contexto RLS de la organización para las compuertas (lo mismo que hace get_tenant_session)."""
    from sqlalchemy import text

    await session.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tenant_id})


# --- rat -------------------------------------------------------------------------------------------

async def _leer_rat(session, tenant_id: str) -> set[str]:
    from features.rat import rat_service

    return {a.id for a in await rat_service.listar_actividades_rat(session, tenant_id)}


async def _registrar_rat(session, org: OrganizacionFicticia, rid: str) -> None:
    from features.rat import rat_service

    await rat_service.registrar_actividad_rat(session, rat_service.ActividadRAT(
        id=rid, tenant_id=org.id, codigo=f"RAT-EP10-{org.id}".upper(),
        nombre="Gestión de clientes (FICTICIA)", area_responsable="Unidad de pruebas ficticia",
        finalidad="Ejemplo sintético del entorno de pruebas.",
        base_legal=rat_service.BaseLegitimacion.CUMPLIMIENTO_CONTRATO,
        categorias_titulares=[rat_service.CategoriaTitular.CLIENTES],
        categorias_datos=["identificacion", "contacto"], volumen_titulares_estimado=100,
        medio_soporte="digital", plazo_conservacion="5 años", medidas_seguridad=["cifrado"],
        origen="manual",
    ))


# --- dpo_cockpit -----------------------------------------------------------------------------------

async def _leer_dpo(session, tenant_id: str) -> set[str]:
    from features.dpo_cockpit import dpo_cockpit_service

    return {d.id for d in await dpo_cockpit_service.listar_bitacora_dpo(session, tenant_id)}


async def _registrar_dpo(session, org: OrganizacionFicticia, rid: str) -> None:
    from features.dpo_cockpit import dpo_cockpit_service

    await dpo_cockpit_service.registrar_dictamen_dpo(session, dpo_cockpit_service.DictamenDPO(
        id=rid, tenant_id=org.id, dpo_id=id_de_usuario(correo_ficticio(org.id, "dpo")),
        tipo=dpo_cockpit_service.TipoDictamenDPO.OPINION_CONSULTIVA,
        asunto="Opinión consultiva de ejemplo (FICTICIA)", referencia_normativa="LOPDP art. 50",
        cuerpo="Dictamen sintético del entorno de pruebas; no vinculante.",
    ))


# --- auditoria_capa --------------------------------------------------------------------------------

async def _leer_capa(session, tenant_id: str) -> set[str]:
    from features.auditoria_capa import auditoria_capa_service

    return {t.id for t in await auditoria_capa_service.listar_tickets_capa(session, tenant_id)}


async def _registrar_capa(session, org: OrganizacionFicticia, rid: str) -> None:
    from features.auditoria_capa import auditoria_capa_service

    await auditoria_capa_service.registrar_hallazgo_capa(session, auditoria_capa_service.TicketCAPA(
        id=rid, tenant_id=org.id, control_id="EP10-CTRL-01",
        severidad=auditoria_capa_service.SeveridadHallazgo.OBSERVACION,
        descripcion_hallazgo="Hallazgo de ejemplo (FICTICIO) del entorno de pruebas.",
        causa_raiz="Dato sintético.", accion_correctiva="Revisar el control de ejemplo.",
        responsable_implementacion_id=id_de_usuario(correo_ficticio(org.id, "coordinacion")),
        creado_por=id_de_usuario(correo_ficticio(org.id, "admin")),
    ))


SALAS: tuple[SalaSembrada, ...] = (
    SalaSembrada("rat", _leer_rat, _registrar_rat),
    SalaSembrada("dpo_cockpit", _leer_dpo, _registrar_dpo),
    SalaSembrada("auditoria_capa", _leer_capa, _registrar_capa),
)


async def sembrar_modulos(session, conteo) -> None:
    """Un registro de ejemplo por sala y organización ficticia, sin duplicar."""
    for org in ORGANIZACIONES:
        await _fijar_tenant(session, org.id)
        for sala in SALAS:
            rid = id_ejemplo(sala.nombre, org.id)
            existe = rid in await sala.leer_ids(session, org.id)
            if not existe:
                await sala.registrar(session, org, rid)
            conteo(f"modulo_{sala.nombre}", not existe)
        await session.commit()
