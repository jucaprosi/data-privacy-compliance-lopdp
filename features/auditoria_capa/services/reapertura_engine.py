# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤controles-periodicos ¤evidencias-vigencia ¤hallazgos ¤rbac-tenant
"""Reapertura de controles periódicos por evidencia vencida (CAPA-03).

Reglas (governance/tareas/CAPA-03.md):
- Un control `vigente` cuya última verificación se apoya en una evidencia vencida pasa a `vencido` y
  produce un hallazgo por la compuerta de `roadmap` (origen `control_periodico`), uno por vencimiento.
- La vigencia se lee solo por la compuerta de `evidencias` (EVI-02); esta sala no guarda ninguna.
- Un control reabierto por su evidencia vuelve a `vigente` cuando su última evidencia está vigente otra vez
  (verificación nueva o documento renovado) y su fecha periódica no ha pasado; el hallazgo se cierra.
Cada operación fija el contexto RLS y además filtra por `tenant_id`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import evidencias, roadmap
from features.auditoria_capa.domain.control_periodico import hoy_guayaquil

PREFIJO_HUELLA = 32


@dataclass(frozen=True)
class ResultadoReapertura:
    reabiertos: int
    hallazgos_creados: int
    restablecidos: int

    def a_dict(self) -> dict:
        return {
            "reabiertos": self.reabiertos,
            "hallazgos_creados": self.hallazgos_creados,
            "restablecidos": self.restablecidos,
        }


def clave_evidencia_vencida(control_id: str, huella: str, vencio_el: date) -> str:
    """Clave de origen del hallazgo: cada vencimiento de la evidencia de un control es un hecho distinto."""
    return f"{control_id}:ev:{huella[:PREFIJO_HUELLA]}:{vencio_el.isoformat()}"


def evidencia_vencida(vencimientos: dict, huella: Optional[str], hoy: date) -> Optional[date]:
    """Fecha de vencimiento si la huella tiene documento y ya venció; None si está vigente o sin vigencia conocida."""
    if huella is None or huella not in vencimientos:
        return None
    vencio_el = vencimientos[huella]
    return vencio_el if vencio_el is not None and vencio_el < hoy else None


_CANDIDATOS = (
    "SELECT c.id, c.nombre, c.control_ref, c.estado, c.proxima_verificacion, c.hallazgo_vigente_id, "
    "(SELECT v.evidencia_sha256 FROM verificaciones_control v "
    " WHERE v.tenant_id = c.tenant_id AND v.control_id = c.id "
    " ORDER BY v.verificado_en DESC, v.id DESC LIMIT 1) AS huella "
    "FROM controles_periodicos c WHERE c.tenant_id = :t AND c.estado IN ('vigente', 'vencido') "
    "ORDER BY c.id FOR UPDATE OF c"
)


async def reabrir_por_evidencia_vencida(
    session: AsyncSession, tenant_id: str, user_id: str
) -> ResultadoReapertura:
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (await session.execute(text(_CANDIDATOS), {"t": tenant_id})).mappings().all()
    huellas = sorted({f["huella"] for f in filas if f["huella"]})
    vencimientos = await evidencias.vigencia_por_huella(session, tenant_id, user_id, huellas)
    await fijar_contexto_rls(session, tenant_id, user_id)
    hoy = hoy_guayaquil()

    reabiertos = creados = restablecidos = 0
    for fila in filas:
        vencio_el = evidencia_vencida(vencimientos, fila["huella"], hoy)
        if fila["estado"] == "vigente" and vencio_el is not None:
            hallazgo_id, creado = await roadmap.registrar_hallazgo_de_evidencia_vencida(
                session,
                tenant_id,
                user_id,
                origen_ref=clave_evidencia_vencida(fila["id"], fila["huella"], vencio_el),
                titulo=f"Evidencia vencida del control: {fila['nombre']}",
                control_ref=fila["control_ref"],
            )
            await session.execute(
                text(
                    "UPDATE controles_periodicos SET estado = 'vencido', hallazgo_vigente_id = :h, "
                    "actualizado_en = now() WHERE tenant_id = :t AND id = :id"
                ),
                {"h": hallazgo_id, "t": tenant_id, "id": fila["id"]},
            )
            await registrar_evento(
                session, tenant_id, "control_periodico", fila["id"], "reabierto_por_evidencia", user_id,
                {"hallazgo_id": hallazgo_id, "evidencia_sha256": fila["huella"], "vencio_el": vencio_el.isoformat()},
            )
            reabiertos += 1
            creados += int(creado)
        elif (
            fila["estado"] == "vencido"
            and vencio_el is None
            and fila["huella"] in vencimientos
            and fila["proxima_verificacion"] >= hoy
        ):
            # Solo vuelve el control que reabrió su evidencia: el vencido por fecha sigue esperando verificación.
            await session.execute(
                text(
                    "UPDATE controles_periodicos SET estado = 'vigente', hallazgo_vigente_id = NULL, "
                    "actualizado_en = now() WHERE tenant_id = :t AND id = :id"
                ),
                {"t": tenant_id, "id": fila["id"]},
            )
            if fila["hallazgo_vigente_id"]:
                await roadmap.cerrar_hallazgo(session, tenant_id, user_id, fila["hallazgo_vigente_id"])
            await registrar_evento(
                session, tenant_id, "control_periodico", fila["id"], "restablecido_por_evidencia", user_id,
                {"evidencia_sha256": fila["huella"]},
            )
            restablecidos += 1
    return ResultadoReapertura(reabiertos=reabiertos, hallazgos_creados=creados, restablecidos=restablecidos)
