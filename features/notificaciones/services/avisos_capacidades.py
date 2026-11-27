# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤adpa
"""NOTIF-04: avisos de concesiones y retiros de capacidades editoriales a los operadores activos.

Los cambios se leen solo por el pasillo de la biblioteca (BIB-411) y los operadores, por el de plataforma (OPE-01).
Los avisos usan `avisos_plataforma` de NOTIF-02, con el tipo `capacidad_editorial` y sin recordatorios.
"""
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

TIPO = "capacidad_editorial"
ENLACE = "/plataforma/capacidades"
ENLACE_TEXTO = "Ver capacidades editoriales"
LIMITE_MOTIVO = 200
VENTANA = timedelta(days=7)  # los cambios más antiguos ya se avisaron en una ejecución anterior (UNIQUE evita repetir)
CAPACIDADES = {"editor": "Editor", "revisor_tecnico": "Revisor técnico", "publicador": "Publicador"}
SIN_NOMBRE = "Un operador"


def _plano(texto: str | None) -> str:
    limpio = re.sub(r"[*_`#>\[\]()]", "", texto or "")
    return re.sub(r"\s+", " ", limpio).strip()


def titulo(accion: str) -> str:
    return "Capacidad editorial concedida" if accion == "concedida" else "Capacidad editorial retirada"


def texto_del_aviso(*, accion: str, capacidad: str, por: str | None, a_quien: str | None, para_el_afectado: bool,
                    motivo: str | None) -> str:
    """R2: una frase según quién lo lee y, si hay motivo, «Motivo: «…».» cortado a 200 caracteres."""
    x = CAPACIDADES.get(capacidad, _plano(capacidad))
    quien = _plano(por) or SIN_NOMBRE
    verbo = "concedió" if accion == "concedida" else "retiró"
    if para_el_afectado:
        frase = f"{quien} te {verbo} la capacidad {x}."
    else:
        destino = _plano(a_quien) or "otra persona"
        frase = f"{quien} {verbo} a {destino} la capacidad {x}."
    cuerpo = _plano(motivo)
    if len(cuerpo) > LIMITE_MOTIVO:
        cuerpo = cuerpo[:LIMITE_MOTIVO] + "…"
    return f"{frase} Motivo: «{cuerpo}»." if cuerpo else frase


async def sincronizar(session: AsyncSession, ahora: datetime | None = None, desde: datetime | None = None) -> dict:
    """R1: un aviso por cambio y por operador activo, sin duplicar."""
    from app_core.pasillo import biblioteca, plataforma

    ahora = ahora or datetime.now(timezone.utc)
    cambios = await biblioteca.cambios_de_capacidades(session, desde or ahora - VENTANA)
    operadores = await plataforma.listar_operadores_activos(session)
    nombres = {o["usuario_id"]: o.get("nombre") for o in operadores}
    creados = 0
    for operador in operadores:
        destinatario = operador["usuario_id"]
        await session.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": destinatario})
        for c in cambios:
            hecho = await session.execute(text(
                "INSERT INTO avisos_plataforma (id, usuario_id, tipo, referencia, titulo, texto, enlace) "
                "VALUES (:id, :u, :t, :r, :titulo, :texto, :enlace) "
                "ON CONFLICT ON CONSTRAINT uq_avisos_usuario_tipo_referencia DO NOTHING"
            ), {"id": str(uuid4()), "u": destinatario, "t": TIPO, "r": str(c["id"]), "titulo": titulo(c["accion"]),
                "texto": texto_del_aviso(
                    accion=c["accion"], capacidad=c["capacidad"], por=nombres.get(c["por"]),
                    a_quien=nombres.get(c["usuario_id"]), para_el_afectado=c["usuario_id"] == destinatario,
                    motivo=c.get("motivo")),
                "enlace": ENLACE})
            creados += hecho.rowcount or 0
    return {"creados": creados}
