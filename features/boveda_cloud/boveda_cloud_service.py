# ¤boveda-cloud ¤seguridad-tenant ¤adpa
"""Compuerta de la sala Bóveda Cloud. Fuera de la sala solo se importa este módulo (o el pasillo)."""
# === BOV-01 ===
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.boveda_cloud.domain import errores
from features.boveda_cloud.schemas import SolicitudAlta, SuscripcionSalida

__all__ = [
    "ROLES_CONSULTA",
    "SolicitudAlta",
    "SuscripcionSalida",
    "crear_suscripcion",
    "errores",
    "limites_uso",
    "obtener_suscripcion",
    "operador_activo",
    "router",
    "techos_integracion",
    "validar_consumo",
]

# Confirmado por el CTO (2026-11-13): solo lectura para estos tres roles; el resto no ve la pantalla.
ROLES_CONSULTA = ("admin_organizacion", "dpo", "coordinador")

# Sentencias por tipo de consumo: diccionario cerrado, nunca se interpola un dato del llamador.
_SQL_CONSUMO = {
    "almacenamiento": (
        "UPDATE boveda_suscripciones_tenant SET uso_almacenamiento_bytes = uso_almacenamiento_bytes + :b, "
        "actualizado_en = now() WHERE tenant_id = :t AND estado = 'ACTIVA' "
        "AND uso_almacenamiento_bytes + :b <= cuota_almacenamiento_bytes RETURNING id",
        errores.BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA,
    ),
    "egress": (
        "UPDATE boveda_suscripciones_tenant SET uso_egress_mensual_bytes = uso_egress_mensual_bytes + :b, "
        "actualizado_en = now() WHERE tenant_id = :t AND estado = 'ACTIVA' "
        "AND uso_egress_mensual_bytes + :b <= cuota_egress_mensual_bytes RETURNING id",
        errores.BOVEDA_CUOTA_EGRESS_EXCEDIDA,
    ),
}


def __getattr__(nombre: str):
    # El router se carga al pedirlo (main.py), para que las rutas importen esta compuerta sin ciclo.
    if nombre == "router":
        from features.boveda_cloud.routes.boveda_paquetes_routes import router

        return router
    raise AttributeError(nombre)


async def obtener_suscripcion(session: AsyncSession, tenant_id: str) -> SuscripcionSalida:
    fila = (await session.execute(
        text("SELECT s.paquete_codigo, p.nombre AS paquete_nombre, s.cuota_almacenamiento_bytes, "
             "s.uso_almacenamiento_bytes, s.cuota_egress_mensual_bytes, s.uso_egress_mensual_bytes, "
             "s.certificaciones_heredadas, s.estado FROM boveda_suscripciones_tenant s "
             "JOIN boveda_paquetes p ON p.codigo = s.paquete_codigo WHERE s.tenant_id = :t"),
        {"t": tenant_id},
    )).mappings().first()
    if fila is None:
        raise errores.error(errores.BOVEDA_SUSCRIPCION_NO_ENCONTRADA)
    datos = dict(fila)
    if isinstance(datos["certificaciones_heredadas"], str):
        datos["certificaciones_heredadas"] = json.loads(datos["certificaciones_heredadas"])
    # CUOTA_EXCEDIDA se deriva al leer (uso >= cuota); la columna solo la mueve el operador (ACTIVA/SUSPENDIDA).
    excedida = (datos["uso_almacenamiento_bytes"] >= datos["cuota_almacenamiento_bytes"]
                or datos["uso_egress_mensual_bytes"] >= datos["cuota_egress_mensual_bytes"])
    if datos["estado"] == "ACTIVA" and excedida:
        datos["estado"] = "CUOTA_EXCEDIDA"
    return SuscripcionSalida(**datos)


async def crear_suscripcion(session: AsyncSession, alta: SolicitudAlta, creado_por: str | None) -> SuscripcionSalida:
    """Alta por el operador: fija el contexto RLS de esa organización solo para esta transacción."""
    paquete = (await session.execute(
        text("SELECT codigo, cuota_almacenamiento_bytes, cuota_egress_mensual_bytes FROM boveda_paquetes "
             "WHERE codigo = :c"), {"c": alta.paquete_codigo},
    )).mappings().first()
    if paquete is None:
        raise errores.error(errores.BOVEDA_PAQUETE_NO_ENCONTRADO)
    personalizado = paquete["cuota_almacenamiento_bytes"] is None or paquete["cuota_egress_mensual_bytes"] is None
    if personalizado:
        if alta.cuota_almacenamiento_bytes is None or alta.cuota_egress_mensual_bytes is None:
            raise errores.error(errores.BOVEDA_CUOTA_PERSONALIZADA_REQUERIDA)
        almacenamiento, egress = alta.cuota_almacenamiento_bytes, alta.cuota_egress_mensual_bytes
    else:
        # Un paquete del catálogo usa sus cuotas; las del cuerpo no las cambian.
        almacenamiento, egress = paquete["cuota_almacenamiento_bytes"], paquete["cuota_egress_mensual_bytes"]
    existe = (await session.execute(text("SELECT 1 FROM tenants WHERE id = :t"), {"t": alta.tenant_id})).first()
    if existe is None:
        raise errores.error(errores.BOVEDA_ORGANIZACION_NO_ENCONTRADA)
    await fijar_contexto_rls(session, alta.tenant_id)
    insertada = (await session.execute(
        text("INSERT INTO boveda_suscripciones_tenant (tenant_id, paquete_codigo, cuota_almacenamiento_bytes, "
             "cuota_egress_mensual_bytes, creado_por) VALUES (:t, :p, :a, :e, :u) "
             "ON CONFLICT (tenant_id) DO NOTHING RETURNING id"),
        {"t": alta.tenant_id, "p": paquete["codigo"], "a": almacenamiento, "e": egress, "u": creado_por},
    )).first()
    if insertada is None:
        raise errores.error(errores.BOVEDA_SUSCRIPCION_YA_EXISTE)
    await registrar_evento(
        session, alta.tenant_id, "boveda_suscripcion", str(insertada[0]), "alta_por_operador",
        # El operador no es usuario de la organización (audit_events.user_id es FK a users): va en el payload.
        user_id=None, payload={"paquete_codigo": paquete["codigo"], "operador_id": creado_por},
    )
    return await obtener_suscripcion(session, alta.tenant_id)


async def operador_activo(session: AsyncSession, email: str, sub: str | None) -> dict | None:
    """Operador de plataforma activo por correo o `sub` de Google (mismo criterio que ORG-09); solo lectura."""
    fila = (await session.execute(
        text("SELECT id::text AS id, email FROM operadores_plataforma WHERE activo AND "
             "(LOWER(email) = :e OR (google_sub IS NOT NULL AND google_sub = :s))"),
        {"e": (email or "").strip().lower(), "s": sub or ""},
    )).mappings().first()
    return dict(fila) if fila else None


async def validar_consumo(session: AsyncSession, tenant_id: str, tipo: str, bytes_solicitados: int) -> None:
    """R1 y R2: suma el consumo solo si cabe en la cuota, en un único UPDATE condicional (sin carreras).

    No se expone por HTTP: la llaman por el pasillo las salas que suben archivos o emiten URLs firmadas.
    Al rechazar no persiste CUOTA_EXCEDIDA (decisión del Arquitecto, 2026-11-13).
    """
    if tipo not in _SQL_CONSUMO:
        raise ValueError("tipo de consumo desconocido")
    if bytes_solicitados <= 0:
        raise ValueError("bytes_solicitados debe ser positivo")
    sql, codigo_excedido = _SQL_CONSUMO[tipo]
    if (await session.execute(text(sql), {"t": tenant_id, "b": bytes_solicitados})).first() is not None:
        return
    estado = (await session.execute(
        text("SELECT estado FROM boveda_suscripciones_tenant WHERE tenant_id = :t"), {"t": tenant_id},
    )).scalar()
    if estado is None:
        raise errores.error(errores.BOVEDA_SUSCRIPCION_NO_ENCONTRADA)
    if estado == "SUSPENDIDA":
        raise errores.error(errores.BOVEDA_SUSCRIPCION_SUSPENDIDA)
    raise errores.error(codigo_excedido)


async def _paquete_de(session: AsyncSession, tenant_id: str):
    fila = (await session.execute(
        text("SELECT p.peticiones_api_minuto, p.tokens_ia_mes, p.max_claves_integracion, p.max_webhooks "
             "FROM boveda_suscripciones_tenant s JOIN boveda_paquetes p ON p.codigo = s.paquete_codigo "
             "WHERE s.tenant_id = :t"), {"t": tenant_id},
    )).mappings().first()
    if fila is None:
        raise errores.error(errores.BOVEDA_SUSCRIPCION_NO_ENCONTRADA)
    return fila


async def techos_integracion(session: AsyncSession, tenant_id: str) -> dict:
    """Techos de API-02 según el paquete; None = personalizado (lo fija el operador)."""
    p = await _paquete_de(session, tenant_id)
    return {"claves": p["max_claves_integracion"], "webhooks": p["max_webhooks"]}


async def limites_uso(session: AsyncSession, tenant_id: str) -> dict:
    """Solo dato: SEC-13c lo conectará al limitador; hoy ningún limitador lo usa."""
    p = await _paquete_de(session, tenant_id)
    return {"peticiones_api_minuto": p["peticiones_api_minuto"], "tokens_ia_mes": p["tokens_ia_mes"]}
# === fin BOV-01 ===
