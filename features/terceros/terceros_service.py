"""Compuerta pública de la sala ADPA: Terceros (gestión de terceros y encargados de tratamiento).
`¤adpa`

Única vía por la que otras salas y la API acceden a la sala Terceros.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.terceros.domain.models import Tercero

__all__ = [
    "Tercero",
    "listar_terceros_encargados",
]


async def listar_terceros_encargados(
    session: AsyncSession,
) -> Sequence[Tercero]:
    """Lista todos los terceros encargados visibles en el contexto RLS actual."""
    result = await session.execute(select(Tercero))
    return result.scalars().all()


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/terceros/domain/errores.py y se registran al importarlo.
from features.terceros.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===


# === TER-01 ===
# ¤hallazgos ¤evidencias Hallazgos automáticos de terceros (especificación TER-01 §2-§3).
# La sala recibe puertos: la tabla vive en transferencias y los hallazgos en roadmap. Hasta que existan
# app_core/pasillo/transferencias.py#TER-01 y app_core/pasillo/roadmap.py#TER-01, el router los adapta.
from datetime import date as _date  # noqa: E402
from typing import Literal, Optional  # noqa: E402

from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

from app_core.errors import ErrorNegocio  # noqa: E402
from features.terceros.domain import errores as _errores_ter01  # noqa: E402
from features.terceros.services import garantias_engine as motor  # noqa: E402
from features.terceros.services.garantias_engine import (  # noqa: E402
    HallazgoExistente,
    PuertoEvidencias,
    PuertoHallazgos,
    PuertoTerceros,
    TerceroGarantias,
)


class GarantiasEntrada(BaseModel):
    """Campos del PUT; organización y autor salen del token. El rol usa los valores existentes de la tabla."""

    model_config = ConfigDict(extra="forbid")

    rol: Optional[Literal["ENCARGADO", "SUBENCARGADO", "DESTINATARIO"]] = None
    pais: Optional[str] = Field(default=None, pattern=r"^[A-Z]{2}$")
    contrato_sha256: Optional[str] = Field(default=None, min_length=64, max_length=64)
    contrato_vigente_hasta: Optional[_date] = None
    garantia_tipo: Optional[Literal[motor.TIPOS_GARANTIA]] = None  # type: ignore[valid-type]
    garantia_sha256: Optional[str] = Field(default=None, min_length=64, max_length=64)
    criticidad: Optional[Literal[motor.CRITICIDADES]] = None  # type: ignore[valid-type]
    proxima_revision: Optional[_date] = None


def tercero_desde_fila(fila: dict) -> TerceroGarantias:
    return TerceroGarantias(**{k: fila.get(k) for k in TerceroGarantias.__dataclass_fields__})


def reglas_incumplidas(tercero: TerceroGarantias, hoy: _date) -> list[str]:
    """origen_ref de las reglas R1 y R2 que el tercero incumple hoy, sin tocar la base."""
    return [c.origen_ref for c, se_cumple in motor.condiciones(tercero, hoy) if se_cumple]


async def _aplicar(acciones: list, hallazgos: PuertoHallazgos) -> dict:
    creados = cerrados = 0
    for a in acciones:
        if a.tipo == "abrir":
            await hallazgos.abrir(a.origen_ref, a.severidad, a.titulo)
            creados += 1
        elif a.tipo == "reabrir":
            await hallazgos.reabrir(a.hallazgo_id)
            creados += 1
        else:
            await hallazgos.cerrar(a.hallazgo_id)
            cerrados += 1
    return {"hallazgos_creados": creados, "cerrados": cerrados}


async def _existentes(hallazgos: PuertoHallazgos) -> dict[str, HallazgoExistente]:
    return {h.origen_ref: h for h in await hallazgos.listar()}


async def evaluar_terceros(terceros: PuertoTerceros, hallazgos: PuertoHallazgos, hoy: _date) -> dict:
    """R1 a R4 sobre todos los terceros de la organización (también el cron diario)."""
    acciones = motor.decidir(await terceros.listar(), await _existentes(hallazgos), hoy)
    return await _aplicar(acciones, hallazgos)


def _abiertos_de(tercero_id: str, existentes: dict[str, HallazgoExistente]) -> list[dict]:
    salida = []
    for sufijo in (motor.SUFIJO_CONTRATO, motor.SUFIJO_GARANTIA):
        h = existentes.get(motor.origen_ref(tercero_id, sufijo))
        if h is not None and h.estado != "cerrado":
            salida.append({"id": h.id, "origen_ref": h.origen_ref, "estado": h.estado,
                           "regla": sufijo})
    return salida


def _vista(t: TerceroGarantias, existentes: dict[str, HallazgoExistente]) -> dict:
    return {
        "id": t.id, "nombre": t.nombre, "rol": t.rol, "pais": t.pais,
        "contrato_sha256": t.contrato_sha256,
        "contrato_vigente_hasta": t.contrato_vigente_hasta.isoformat() if t.contrato_vigente_hasta else None,
        "garantia_tipo": t.garantia_tipo, "garantia_sha256": t.garantia_sha256,
        "criticidad": t.criticidad,
        "proxima_revision": t.proxima_revision.isoformat() if t.proxima_revision else None,
        "hallazgos": _abiertos_de(t.id, existentes),
    }


async def listar_terceros_con_hallazgos(terceros: PuertoTerceros, hallazgos: PuertoHallazgos) -> list[dict]:
    existentes = await _existentes(hallazgos)
    return [_vista(t, existentes) for t in await terceros.listar()]


async def actualizar_garantias(
    tercero_id: str,
    entrada: GarantiasEntrada,
    terceros: PuertoTerceros,
    hallazgos: PuertoHallazgos,
    evidencias: PuertoEvidencias,
    hoy: _date,
) -> dict:
    """PUT /terceros/{id}/garantias: valida las huellas, guarda y reevalúa solo ese tercero."""
    campos = entrada.model_dump(exclude_unset=True)
    for clave in ("contrato_sha256", "garantia_sha256"):
        if campos.get(clave) is not None:
            huella = evidencias.existe(campos[clave])
            if huella is None:
                raise ErrorNegocio(_errores_ter01.EVIDENCIA_NO_ENCONTRADA)
            campos[clave] = huella
    if await terceros.obtener(tercero_id) is None:
        raise ErrorNegocio(_errores_ter01.TERCERO_NO_ENCONTRADO)
    actualizado = await terceros.actualizar(tercero_id, campos)
    if actualizado is None:
        raise ErrorNegocio(_errores_ter01.TERCERO_NO_ENCONTRADO)
    await _aplicar(motor.decidir([actualizado], await _existentes(hallazgos), hoy), hallazgos)
    return _vista(actualizado, await _existentes(hallazgos))


__all__ += ["GarantiasEntrada", "TerceroGarantias", "HallazgoExistente", "actualizar_garantias",
            "evaluar_terceros", "listar_terceros_con_hallazgos", "reglas_incumplidas", "tercero_desde_fila"]
# === fin TER-01 ===
