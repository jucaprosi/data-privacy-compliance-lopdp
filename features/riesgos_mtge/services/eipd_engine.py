# ¤riesgos-eipd ¤mtge-granescala ¤hallazgos
# ¤¤backend-developer
"""MTGE-03: motor de la EIPD guiada de ocho pasos.

Reglas (governance/especificaciones/MTGE-03.md §3):
- R1: obligatoria = gran escala (MTGE) ∨ marca de EIPD del RAT ∨ decisión manual; la manual solo sube.
- R2: cada punto por corregir del paso 5 se registra como hallazgo de origen 'eipd' por un puerto.
  El pasillo de hallazgos (app_core/pasillo/roadmap.py#MTGE-03) aún no está sembrado: el puerto por
  defecto no registra nada y deja hallazgo_id en NULL. Pendiente, no entregado.
- R3: cerrar exige pasos 1..7 y, con residual alto, una decisión. El informe es JSON canónico (claves
  ordenadas, UTF-8) y se guarda su SHA-256. La custodia en evidencias queda pendiente (EVI-04).
- Una EIPD cerrada no se edita: todo UPDATE lleva `cerrada_en IS NULL`.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Protocol

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.riesgos_mtge.domain import errores
from features.riesgos_mtge.domain.eipd import (
    MODELOS_PASO, PASO_DECISION, PASOS_TOTALES, CierreEipd, Eipd, InformeEipd, NivelRiesgo, PuntoCorregir,
)

MOTIVO_GRAN_ESCALA = "el tratamiento es de gran escala según la calificación de la plataforma"
MOTIVO_RAT = "el registro de actividades lo marca para evaluación de impacto"
MOTIVO_MANUAL = "decisión del equipo responsable"
MOTIVO_NINGUNO = "no se identificó un supuesto que la exija"

_COLUMNAS = (
    "id, tratamiento_id, obligatoria, motivo_obligatoriedad, paso_actual, consulta_titulares, ciclo_vida, "
    "necesidad, riesgo_inherente, riesgo_residual, decision, decision_texto, informe_sha256, cerrada_en, creado_en"
)


class PuertoHallazgos(Protocol):
    async def registrar(self, session: AsyncSession, tenant_id: str, user_id: str,
                        origen_ref: str, titulo: str) -> Optional[str]: ...


class HallazgosPendientes:
    """Puerto por defecto mientras no exista app_core/pasillo/roadmap.py#MTGE-03: no registra."""

    async def registrar(self, session, tenant_id, user_id, origen_ref, titulo) -> Optional[str]:
        return None


async def _contexto(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})
    await session.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": user_id})


async def obligatoriedad_legal(session: AsyncSession, tenant_id: str, tratamiento_id: str) -> tuple[bool, str]:
    """R1 sin la parte manual: (exigida, motivo). Lanza 404 si el tratamiento no existe."""
    from app_core.pasillo import rat

    actividad = next((a for a in await rat.listar_actividades_resumen(session, tenant_id)
                      if a.id == tratamiento_id), None)
    if actividad is None:
        raise ErrorNegocio(errores.EIPD_TRATAMIENTO_NO_ENCONTRADO)
    motivos = [m for m, si in ((MOTIVO_GRAN_ESCALA, actividad.es_gran_escala),
                               (MOTIVO_RAT, actividad.requiere_eipd)) if si]
    return bool(motivos), "; ".join(motivos)


async def _fila(session: AsyncSession, eipd_id: str):
    fila = (await session.execute(text(f"SELECT {_COLUMNAS} FROM eipd WHERE id = :id"), {"id": eipd_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio(errores.EIPD_NO_ENCONTRADA)
    return fila


async def _puntos(session: AsyncSession, eipd_id: str) -> list[PuntoCorregir]:
    filas = (await session.execute(text(
        "SELECT id, texto, hallazgo_id FROM eipd_incumplimientos WHERE eipd_id = :e ORDER BY texto, id"),
        {"e": eipd_id})).mappings().all()
    return [PuntoCorregir(**f) for f in filas]


async def _armar(session: AsyncSession, tenant_id: str, fila) -> Eipd:
    por_ley, _ = await obligatoriedad_legal(session, tenant_id, fila["tratamiento_id"])
    return Eipd(**fila, obligatoria_por_ley=por_ley, puntos=await _puntos(session, fila["id"]))


async def crear_eipd(session: AsyncSession, tenant_id: str, user_id: str, tratamiento_id: str) -> Eipd:
    await _contexto(session, tenant_id, user_id)
    por_ley, motivo = await obligatoriedad_legal(session, tenant_id, tratamiento_id)
    eipd_id = str(uuid.uuid4())
    await session.execute(text(
        "INSERT INTO eipd (id, tenant_id, tratamiento_id, obligatoria, motivo_obligatoriedad, paso_actual, creado_por) "
        "VALUES (:id, :t, :tr, :o, :m, 1, :u)"),
        {"id": eipd_id, "t": tenant_id, "tr": tratamiento_id, "o": por_ley, "m": motivo or MOTIVO_NINGUNO, "u": user_id})
    await session.flush()
    return await _armar(session, tenant_id, await _fila(session, eipd_id))


async def obtener_eipd(session: AsyncSession, tenant_id: str, user_id: str, eipd_id: str) -> Eipd:
    await _contexto(session, tenant_id, user_id)
    return await _armar(session, tenant_id, await _fila(session, eipd_id))


async def listar_eipd(session: AsyncSession, tenant_id: str, user_id: str,
                      tratamiento_id: Optional[str] = None) -> list[Eipd]:
    await _contexto(session, tenant_id, user_id)
    filtro, params = ("WHERE tratamiento_id = :tr", {"tr": tratamiento_id}) if tratamiento_id else ("", {})
    filas = (await session.execute(text(f"SELECT {_COLUMNAS} FROM eipd {filtro} ORDER BY creado_en DESC, id"),
                                   params)).mappings().all()
    return [await _armar(session, tenant_id, f) for f in filas]


async def _actualizar(session: AsyncSession, eipd_id: str, n: int, campos: dict) -> None:
    asignaciones = ", ".join(f"{c} = :{c}" for c in campos)
    sep = ", " if asignaciones else ""
    resultado = await session.execute(text(
        f"UPDATE eipd SET {asignaciones}{sep}paso_actual = GREATEST(paso_actual, :sig) "
        "WHERE id = :id AND cerrada_en IS NULL"),
        {**campos, "sig": min(n + 1, PASOS_TOTALES), "id": eipd_id})
    if resultado.rowcount != 1:
        raise ErrorNegocio(errores.EIPD_CERRADA)


async def guardar_paso(session: AsyncSession, tenant_id: str, user_id: str, eipd_id: str, n: int, cuerpo: dict,
                       hallazgos: Optional[PuertoHallazgos] = None) -> Eipd:
    modelo = MODELOS_PASO.get(n)
    if modelo is None:
        raise ErrorNegocio(errores.EIPD_PASO_INVALIDO)
    try:
        datos = modelo.model_validate(cuerpo)
    except ValidationError as exc:
        raise ErrorNegocio(errores.EIPD_PASO_INVALIDO, detail=exc.errors()[0]["msg"]) from None
    await _contexto(session, tenant_id, user_id)
    fila = await _fila(session, eipd_id)
    if fila["cerrada_en"] is not None:
        raise ErrorNegocio(errores.EIPD_CERRADA)
    campos: dict = {}
    if n == 1:
        por_ley, motivo = await obligatoriedad_legal(session, tenant_id, fila["tratamiento_id"])
        if por_ley and not datos.obligatoria:
            raise ErrorNegocio(errores.EIPD_OBLIGATORIA)
        campos = {"obligatoria": por_ley or datos.obligatoria,
                  "motivo_obligatoriedad": motivo if por_ley else (MOTIVO_MANUAL if datos.obligatoria else MOTIVO_NINGUNO)}
    elif n == 2:
        campos = {"consulta_titulares": datos.consulta_titulares}
    elif n == 3:
        campos = {"ciclo_vida": json.dumps({"fases": datos.fases, "amenazas": datos.amenazas}, ensure_ascii=False)}
    elif n == 4:
        campos = {"necesidad": datos.necesidad}
    elif n == 5:
        await _registrar_puntos(session, tenant_id, user_id, eipd_id, datos.puntos, hallazgos or HallazgosPendientes())
    elif n == 6:
        campos = {"riesgo_inherente": datos.riesgo_inherente.value, "riesgo_residual": datos.riesgo_residual.value}
    elif n == PASO_DECISION:
        campos = {"decision": datos.decision.value if datos.decision else None,
                  "decision_texto": (datos.decision_texto or "").strip() or None}
    if n == 3:
        await session.execute(text(
            "UPDATE eipd SET ciclo_vida = CAST(:cv AS jsonb), paso_actual = GREATEST(paso_actual, 4) "
            "WHERE id = :id AND cerrada_en IS NULL"), {"cv": campos["ciclo_vida"], "id": eipd_id})
    else:
        await _actualizar(session, eipd_id, n, campos)
    await session.flush()
    return await _armar(session, tenant_id, await _fila(session, eipd_id))


async def _registrar_puntos(session, tenant_id, user_id, eipd_id, puntos, hallazgos: PuertoHallazgos) -> None:
    """R2: los puntos ya guardados no se repiten (sin DELETE); cada punto nuevo, un hallazgo."""
    existentes = {p.texto for p in await _puntos(session, eipd_id)}
    numero = len(existentes)
    for texto in dict.fromkeys(puntos):
        if texto in existentes:
            continue
        numero += 1
        hallazgo_id = await hallazgos.registrar(session, tenant_id, user_id, f"{eipd_id}:{numero}",
                                                f"Evaluación de impacto: {texto}")
        await session.execute(text(
            "INSERT INTO eipd_incumplimientos (id, tenant_id, eipd_id, texto, hallazgo_id) VALUES (:id, :t, :e, :x, :h)"),
            {"id": str(uuid.uuid4()), "t": tenant_id, "e": eipd_id, "x": texto, "h": hallazgo_id})


def informe_canonico(eipd: Eipd) -> tuple[dict, str]:
    """JSON determinista (claves ordenadas, UTF-8, sin espacios) y su SHA-256."""
    datos = eipd.model_dump(mode="json", exclude={"informe_sha256", "cerrada_en", "obligatoria_por_ley"})
    datos["puntos"] = [{"texto": p["texto"]} for p in datos["puntos"]]
    crudo = json.dumps(datos, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return datos, hashlib.sha256(crudo).hexdigest()


async def cerrar_eipd(session: AsyncSession, tenant_id: str, user_id: str, eipd_id: str) -> CierreEipd:
    eipd = await obtener_eipd(session, tenant_id, user_id, eipd_id)
    if eipd.cerrada_en is not None:
        raise ErrorNegocio(errores.EIPD_CERRADA)
    if eipd.paso_actual < PASOS_TOTALES:
        raise ErrorNegocio(errores.EIPD_PASO_INCOMPLETO)
    if eipd.riesgo_residual == NivelRiesgo.alto and eipd.decision is None:
        raise ErrorNegocio(errores.EIPD_SIN_DECISION)
    _, huella = informe_canonico(eipd)
    resultado = await session.execute(text(
        "UPDATE eipd SET informe_sha256 = :h, cerrada_en = :c WHERE id = :id AND cerrada_en IS NULL"),
        {"h": huella, "c": datetime.now(timezone.utc), "id": eipd_id})
    if resultado.rowcount != 1:
        raise ErrorNegocio(errores.EIPD_CERRADA)
    await session.flush()
    return CierreEipd(informe_sha256=huella)


async def informe_eipd(session: AsyncSession, tenant_id: str, user_id: str, eipd_id: str) -> InformeEipd:
    eipd = await obtener_eipd(session, tenant_id, user_id, eipd_id)
    datos, huella = informe_canonico(eipd)
    return InformeEipd(informe=datos, informe_sha256=eipd.informe_sha256 or huella,
                       integro=eipd.informe_sha256 is not None and eipd.informe_sha256 == huella)
