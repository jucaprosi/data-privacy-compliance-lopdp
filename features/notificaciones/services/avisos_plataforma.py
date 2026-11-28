# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤adpa
"""NOTIF-02: avisos de la plataforma por versiones de la biblioteca pendientes de revisión técnica.

Las versiones y los revisores se leen solo por el pasillo de la biblioteca (BIB-415); la fecha de vigencia, por el
pasillo normativo (NORM-07). Cada escritura fija la identidad de la persona dueña del aviso (RLS).
"""
import logging
import os
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.zona_negocio import ZONA_NEGOCIO
from features.notificaciones.domain import avisos as av
from features.notificaciones.domain.models import Destinatario
from features.notificaciones.domain.puertos import Notificador
from features.notificaciones.services import correo_versiones

logger = logging.getLogger(__name__)

TIPO = "version_por_revisar"
LIMITE = 50
ENLACE_VERSION = "/biblioteca?version={id}"  # detalle de BIB-408


def _instante(d: date | None) -> datetime | None:
    """Inicio del día (hora de Ecuador) en que toca un recordatorio."""
    return datetime(d.year, d.month, d.day, tzinfo=ZONA_NEGOCIO) if d else None


async def _como(session: AsyncSession, usuario: str) -> None:
    await session.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": usuario})


async def _motivo_de(version: dict, hoy: date) -> tuple[str, date | None]:
    """Línea de motivo y fecha de vigencia de una versión (R2). Lo que no se conoce no se nombra."""
    if version.get("origen_ia") != "resolucion" or not version.get("id_resolucion"):
        return av.motivo(origen="peticion", hoy=hoy), None
    from app_core.pasillo import inteligencia_normativa as normativa

    resolucion = await normativa.obtener_resolucion(version["id_resolucion"])
    vigencia = await normativa.fecha_vigencia_de(version["id_resolucion"])
    norma = getattr(resolucion, "titulo", None) or "una norma"
    return av.motivo(origen="resolucion", norma=norma, vigencia=vigencia, hoy=hoy), vigencia


async def _enviar_correos(por_enviar: list[dict], notificador: Notificador | None, app_base_url: str | None) -> None:
    """NOTIF-03 R1d: el correo sale después del commit; nunca bloquea ni deshace el aviso de la campana."""
    base = (app_base_url if app_base_url is not None else os.environ.get("APP_BASE_URL", "")).strip().rstrip("/")
    if not base:
        logger.warning("NOTIF-03: APP_BASE_URL sin definir; %d correos no se envían", len(por_enviar))
        return
    try:
        activo = notificador or correo_versiones.notificador_de_correo()
        correos = [correo_versiones.construir_correo(
            aviso_id=p["aviso_id"], destinatario=p["destinatario"], plantilla=p["plantilla"], motivo=p["motivo"],
            enlace=base + p["enlace"], recordatorio=p["recordatorio"]) for p in por_enviar]
        await correo_versiones.enviar_correos(activo, correos)
    except Exception as exc:  # noqa: BLE001 - solo el tipo: el mensaje puede traer datos personales
        logger.warning("NOTIF-03: los correos no salieron (%s)", type(exc).__name__)


async def sincronizar(session: AsyncSession, ahora: datetime | None = None, *,
                      notificador: Notificador | None = None, app_base_url: str | None = None) -> dict:
    """R1, R3 y R4: crea los avisos que faltan, cierra los de versiones ya revisadas y envía los recordatorios.

    NOTIF-03: tras confirmar los avisos (commit propio) envía el correo de cada aviso nuevo y de cada recordatorio.
    """
    from app_core.pasillo import biblioteca, plataforma

    ahora = ahora or datetime.now(timezone.utc)
    hoy = av.hoy_ecuador(ahora)
    versiones = await biblioteca.versiones_en_revision(session)
    revisores = await biblioteca.revisores_tecnicos(session)
    contactos = {o["usuario_id"]: o for o in await plataforma.listar_operadores_activos(session)} if revisores else {}
    por_enviar: list[dict] = []

    def _por_enviar(usuario: str, aviso_id: str, v: dict, enlace: str, recordatorio: str | None) -> None:
        contacto = contactos.get(usuario)
        if contacto and (contacto.get("email") or "").strip():
            por_enviar.append({
                "aviso_id": aviso_id, "plantilla": v["titulo"], "motivo": v["_motivo"], "enlace": enlace,
                "recordatorio": recordatorio,
                "destinatario": Destinatario(user_id=usuario, email=contacto["email"],
                                             nombre=contacto.get("nombre") or "", tenant_id="")})

    abiertas = {v["id"] for v in versiones}
    resultado = {"creados": 0, "recordatorios": 0, "cerrados": 0}
    for v in versiones:
        motivo, vigencia = await _motivo_de(v, hoy)
        v["_motivo"], v["_vigencia"] = motivo, vigencia
    for usuario in revisores:
        await _como(session, usuario)
        for v in versiones:
            creado = av.hoy_ecuador(v["creada_en"]) if v.get("creada_en") else hoy
            proximo = (av.programa(creado, v["_vigencia"]) or [None])[0]
            aviso_id, enlace = str(uuid4()), ENLACE_VERSION.format(id=v["id"])
            hecho = await session.execute(text(
                "INSERT INTO avisos_plataforma (id, usuario_id, tipo, referencia, titulo, texto, enlace, "
                "proximo_recordatorio) VALUES (:id, :u, :t, :r, :titulo, :texto, :enlace, :proximo) "
                "ON CONFLICT ON CONSTRAINT uq_avisos_usuario_tipo_referencia DO NOTHING"
            ), {"id": aviso_id, "u": usuario, "t": TIPO, "r": v["id"], "titulo": av.titulo(v["titulo"]),
                "texto": v["_motivo"], "enlace": enlace, "proximo": _instante(proximo)})
            resultado["creados"] += hecho.rowcount or 0
            if hecho.rowcount:
                _por_enviar(usuario, aviso_id, v, enlace, None)
        pendientes = (await session.execute(text(
            "SELECT id, referencia, texto, creado_en, recordatorios_hechos FROM avisos_plataforma "
            "WHERE usuario_id=:u AND tipo=:t AND pendiente"), {"u": usuario, "t": TIPO})).mappings().all()
        por_id = {v["id"]: v for v in versiones}
        for a in pendientes:
            if a["referencia"] not in abiertas:
                await session.execute(text(
                    "UPDATE avisos_plataforma SET pendiente=false, enlace=NULL, texto=texto || :fin, "
                    "proximo_recordatorio=NULL, actualizado_en=now() WHERE id=:id"),
                    {"id": a["id"], "fin": "\n" + av.TEXTO_FIN})
                resultado["cerrados"] += 1
                continue
            vigencia = por_id[a["referencia"]]["_vigencia"]
            creado = av.hoy_ecuador(a["creado_en"])
            fechas = av.programa(creado, vigencia)
            n = a["recordatorios_hechos"]
            if n >= len(fechas) or fechas[n] > hoy:
                continue
            siguiente = fechas[n + 1] if n + 1 < len(fechas) else None
            texto_recordatorio = av.recordatorio(vigencia=vigencia, hoy=hoy, creado=creado)
            await session.execute(text(
                "UPDATE avisos_plataforma SET texto=texto || :extra, leido_en=NULL, "
                "recordatorios_hechos=recordatorios_hechos+1, proximo_recordatorio=:proximo, actualizado_en=now() "
                "WHERE id=:id"),
                {"id": a["id"], "extra": "\n" + texto_recordatorio, "proximo": _instante(siguiente)})
            resultado["recordatorios"] += 1
            _por_enviar(usuario, str(a["id"]), por_id[a["referencia"]], ENLACE_VERSION.format(id=a["referencia"]),
                        texto_recordatorio)
    if por_enviar:
        await session.commit()  # R1d: primero se confirman los avisos; el correo es después y no los deshace
        await _enviar_correos(por_enviar, notificador, app_base_url)
    return resultado


async def listar(session: AsyncSession, usuario: str, filtro: str = "todos", antes: str | None = None) -> dict:
    """Los 50 avisos más recientes de la persona y el número sin leer. `antes` es el `creado_en` del último visto."""
    await _como(session, usuario)
    params: dict = {"u": usuario, "limite": LIMITE, "solo_sin_leer": filtro == "sin_leer", "antes": antes}
    filas = (await session.execute(text(
        "SELECT id, titulo, texto, enlace, leido_en IS NOT NULL AS leido, pendiente, creado_en FROM avisos_plataforma "
        "WHERE usuario_id=:u AND (NOT :solo_sin_leer OR leido_en IS NULL) "
        "AND (CAST(:antes AS timestamptz) IS NULL OR creado_en < CAST(:antes AS timestamptz)) "
        "ORDER BY creado_en DESC, id LIMIT :limite"), params)).mappings().all()
    sin_leer = (await session.execute(text(
        "SELECT count(*) FROM avisos_plataforma WHERE usuario_id=:u AND leido_en IS NULL"), {"u": usuario})).scalar_one()
    return {"avisos": [dict(f) for f in filas], "sin_leer": sin_leer}


async def marcar_leido(session: AsyncSession, usuario: str, aviso_id: str) -> bool:
    """Marca un aviso propio como leído; un aviso ajeno o inexistente no se ve (RLS) y devuelve False."""
    await _como(session, usuario)
    hecho = await session.execute(text(
        "UPDATE avisos_plataforma SET leido_en=COALESCE(leido_en, now()), actualizado_en=now() "
        "WHERE id=:id AND usuario_id=:u"), {"id": aviso_id, "u": usuario})
    return bool(hecho.rowcount)
