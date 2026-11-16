# ¤dpo-cockpit ¤evidencias
"""Motor de las consultas de la organización al DPO (DPO-03).

Visibilidad (R2): el autor ve las suyas; dpo, admin_organizacion y coordinador ven todas de su
organización. Cierre (R1): una sola transacción que agrega la respuesta al hilo, asienta una
OPINION_CONSULTIVA en la bitácora de DPO-01 y guarda la huella canónica del hilo.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.dpo_cockpit.domain import errores as _errores  # noqa: F401  (registra los códigos)
from features.dpo_cockpit.domain.consulta import (
    ASUNTO_MAX,
    ESTADO_ABIERTA,
    ESTADO_CERRADA,
    ESTADOS,
    ROL_DPO,
    ROLES_QUE_VEN_TODAS,
    Consulta,
    MensajeConsulta,
    ahora,
    huella_hilo,
    normalizar_texto,
)
from features.dpo_cockpit.domain.errores import (
    CONSULTA_CERRADA,
    CONSULTA_INVALIDA,
    CONSULTA_NO_ENCONTRADA,
    CONSULTA_SOLO_DPO_RESPONDE,
)
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.services.bitacora_service import registrar_dictamen

_COLS_CONSULTA = "id, tenant_id, asunto, estado, creado_por, creado_en, cerrada_en, dictamen_id, evidencia_sha256"


def _a_consulta(fila) -> Consulta:
    return Consulta(
        id=fila["id"], tenant_id=fila["tenant_id"], asunto=fila["asunto"], estado=fila["estado"],
        creado_por=fila["creado_por"], creado_en=fila["creado_en"], cerrada_en=fila["cerrada_en"],
        dictamen_id=fila["dictamen_id"], evidencia_sha256=fila["evidencia_sha256"],
    )


def _a_mensaje(fila) -> MensajeConsulta:
    return MensajeConsulta(
        id=fila["id"], consulta_id=fila["consulta_id"], secuencia=fila["secuencia"],
        autor_id=fila["autor_id"], autor_rol=fila["autor_rol"], texto=fila["texto"], creado_en=fila["creado_en"],
    )


def _validar_texto(valor: Optional[str], campo: str, maximo: Optional[int] = None) -> str:
    limpio = normalizar_texto(valor)
    if not limpio or (maximo is not None and len(limpio) > maximo):
        raise ErrorNegocio(CONSULTA_INVALIDA, f"Falta o no es válido: {campo}.")
    return limpio


def _ve_todas(rol: str) -> bool:
    return rol in ROLES_QUE_VEN_TODAS


async def _cargar_mensajes(session: AsyncSession, tenant_id: str, ids: list[str]) -> dict[str, list[MensajeConsulta]]:
    if not ids:
        return {}
    filas = (await session.execute(
        text("SELECT id, consulta_id, secuencia, autor_id, autor_rol, texto, creado_en "
             "FROM dpo_consultas_mensajes WHERE tenant_id = :t AND consulta_id = ANY(:ids) "
             "ORDER BY consulta_id, secuencia"),
        {"t": tenant_id, "ids": ids},
    )).mappings().all()
    por: dict[str, list[MensajeConsulta]] = {i: [] for i in ids}
    for f in filas:
        por[f["consulta_id"]].append(_a_mensaje(f))
    return por


async def _obtener(session: AsyncSession, tenant_id: str, consulta_id: str, usuario: str, rol: str,
                   bloquear: bool = False) -> Consulta:
    """Carga la consulta si el usuario puede verla; si no, 404 (no revela que existe)."""
    sql = f"SELECT {_COLS_CONSULTA} FROM dpo_consultas WHERE tenant_id = :t AND id = :i"
    if bloquear:
        sql += " FOR UPDATE"
    fila = (await session.execute(text(sql), {"t": tenant_id, "i": consulta_id})).mappings().first()
    if fila is None or (not _ve_todas(rol) and fila["creado_por"] != usuario):
        raise ErrorNegocio(CONSULTA_NO_ENCONTRADA)
    consulta = _a_consulta(fila)
    consulta.mensajes = (await _cargar_mensajes(session, tenant_id, [consulta.id]))[consulta.id]
    return consulta


async def _agregar(session: AsyncSession, tenant_id: str, consulta_id: str, autor_id: str, autor_rol: str,
                   texto: str) -> MensajeConsulta:
    m = MensajeConsulta(consulta_id=consulta_id, autor_id=autor_id, autor_rol=autor_rol, texto=texto)
    m.secuencia = int((await session.execute(
        text("SELECT COALESCE(MAX(secuencia), 0) + 1 FROM dpo_consultas_mensajes WHERE consulta_id = :c"),
        {"c": consulta_id},
    )).scalar_one())
    m.creado_en = ahora()
    await session.execute(
        text("INSERT INTO dpo_consultas_mensajes (id, tenant_id, consulta_id, secuencia, autor_id, autor_rol, "
             "texto, creado_en) VALUES (:id, :t, :c, :s, :a, :r, :x, :f)"),
        {"id": m.id, "t": tenant_id, "c": consulta_id, "s": m.secuencia, "a": autor_id, "r": autor_rol,
         "x": texto, "f": m.creado_en},
    )
    return m


async def crear_consulta(session: AsyncSession, tenant_id: str, autor_id: str, autor_rol: str,
                         asunto: Optional[str], texto: Optional[str]) -> Consulta:
    asunto_ok = _validar_texto(asunto, "asunto", ASUNTO_MAX)
    texto_ok = _validar_texto(texto, "texto")
    c = Consulta(tenant_id=tenant_id, asunto=asunto_ok, creado_por=autor_id)
    await session.execute(
        text("INSERT INTO dpo_consultas (id, tenant_id, asunto, estado, creado_por, creado_en) "
             "VALUES (:id, :t, :a, 'abierta', :u, :f)"),
        {"id": c.id, "t": tenant_id, "a": asunto_ok, "u": autor_id, "f": c.creado_en},
    )
    c.mensajes.append(await _agregar(session, tenant_id, c.id, autor_id, autor_rol, texto_ok))
    return c


async def listar_consultas(session: AsyncSession, tenant_id: str, usuario: str, rol: str,
                           estado: Optional[str] = None) -> list[Consulta]:
    if estado is not None and estado not in ESTADOS:
        raise ErrorNegocio(CONSULTA_INVALIDA, "El estado no es válido.")
    sql = f"SELECT {_COLS_CONSULTA} FROM dpo_consultas WHERE tenant_id = :t"
    params: dict = {"t": tenant_id}
    if not _ve_todas(rol):
        sql += " AND creado_por = :u"
        params["u"] = usuario
    if estado:
        sql += " AND estado = :e"
        params["e"] = estado
    sql += " ORDER BY creado_en DESC, id DESC"
    consultas = [_a_consulta(f) for f in (await session.execute(text(sql), params)).mappings().all()]
    hilos = await _cargar_mensajes(session, tenant_id, [c.id for c in consultas])
    for c in consultas:
        c.mensajes = hilos[c.id]
    return consultas


async def agregar_mensaje(session: AsyncSession, tenant_id: str, consulta_id: str, autor_id: str,
                          autor_rol: str, texto: Optional[str]) -> MensajeConsulta:
    """Autor o dpo. Solo el mensaje del dpo deja la consulta en «respondida»."""
    texto_ok = _validar_texto(texto, "texto")
    consulta = await _obtener(session, tenant_id, consulta_id, autor_id, autor_rol, bloquear=True)
    if autor_rol != ROL_DPO and consulta.creado_por != autor_id:
        # Ya la ve (admin/coordinador) pero no es suya: solo el autor o el DPO escriben en el hilo.
        raise ErrorNegocio(CONSULTA_SOLO_DPO_RESPONDE)
    if consulta.estado == ESTADO_CERRADA:
        raise ErrorNegocio(CONSULTA_CERRADA)
    m = await _agregar(session, tenant_id, consulta_id, autor_id, autor_rol, texto_ok)
    if autor_rol == ROL_DPO and consulta.estado == ESTADO_ABIERTA:
        await session.execute(
            text("UPDATE dpo_consultas SET estado = 'respondida' WHERE id = :i AND tenant_id = :t"),
            {"i": consulta_id, "t": tenant_id},
        )
    return m


async def cerrar_consulta(session: AsyncSession, tenant_id: str, consulta_id: str, dpo_id: str, rol: str,
                          respuesta: Optional[str]) -> Consulta:
    """Responde y cierra (solo dpo) en una transacción; si algo falla, la consulta no queda cerrada."""
    if rol != ROL_DPO:
        raise ErrorNegocio(CONSULTA_SOLO_DPO_RESPONDE)
    respuesta_ok = _validar_texto(respuesta, "respuesta")
    consulta = await _obtener(session, tenant_id, consulta_id, dpo_id, rol, bloquear=True)
    if consulta.estado == ESTADO_CERRADA:
        raise ErrorNegocio(CONSULTA_CERRADA)
    consulta.mensajes.append(await _agregar(session, tenant_id, consulta_id, dpo_id, rol, respuesta_ok))
    huella = huella_hilo(consulta.id, consulta.asunto, consulta.mensajes)
    dictamen = await registrar_dictamen(session, DictamenDPO(
        tenant_id=tenant_id, dpo_id=dpo_id, tipo=TipoDictamenDPO.OPINION_CONSULTIVA,
        asunto=consulta.asunto, referencia_normativa="POR VERIFICAR", cuerpo=respuesta_ok,
    ))
    cerrada = ahora()
    resultado = await session.execute(
        text("UPDATE dpo_consultas SET estado = 'cerrada', cerrada_en = :c, dictamen_id = :d, "
             "evidencia_sha256 = :h WHERE id = :i AND tenant_id = :t AND estado <> 'cerrada' RETURNING id"),
        {"c": cerrada, "d": dictamen.id, "h": huella, "i": consulta_id, "t": tenant_id},
    )
    if resultado.first() is None:
        raise ErrorNegocio(CONSULTA_CERRADA)
    consulta.estado, consulta.cerrada_en = ESTADO_CERRADA, cerrada
    consulta.dictamen_id, consulta.evidencia_sha256 = dictamen.id, huella
    return consulta


async def obtener_consulta(session: AsyncSession, tenant_id: str, consulta_id: str, usuario: str,
                           rol: str) -> Consulta:
    return await _obtener(session, tenant_id, consulta_id, usuario, rol)
