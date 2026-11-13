# ¤hallazgos ¤evidencias ¤adpa
"""TER-01 · Motor puro de hallazgos de terceros (especificación TER-01 §3).

No toca la base: recibe los terceros y los hallazgos `tercero` existentes y devuelve qué abrir, reabrir o
cerrar. La persistencia la hacen los puertos que el servicio recibe (hoy, dobles en las pruebas y
adaptadores en el router; mañana, los pasillos de transferencias y roadmap).

- R1 · Contrato: rol ENCARGADO o SUBENCARGADO sin huella de contrato, o con vigencia vencida ⇒ `alta`.
- R2 · Garantía: país declarado distinto de EC sin huella de garantía ⇒ `critica`. Sin país declarado no
  hay hallazgo (el tercero figura «sin país declarado»). Criterio ESTIMADO hasta el abogado: LOPDP art. 56
  (país con nivel adecuado); el texto dice «garantía no registrada», nunca afirma un incumplimiento.
- R3 · Cierre: si la condición deja de cumplirse, el hallazgo abierto se cierra.
- R4 · Idempotencia por `origen_ref`: un hecho vigente ya abierto no genera acción.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping, Optional, Protocol, Sequence

ROLES_ENCARGADO = frozenset({"ENCARGADO", "SUBENCARGADO"})
PAIS_LOCAL = "EC"
TIPOS_GARANTIA = ("nivel_adecuado", "clausulas_tipo", "normas_corporativas", "autorizacion_spdp", "caso_excepcional")
CRITICIDADES = ("baja", "media", "alta")
TITULO_MAX = 200
SUFIJO_CONTRATO = "contrato"
SUFIJO_GARANTIA = "garantia"


@dataclass(frozen=True)
class TerceroGarantias:
    """Lo que el motor necesita de una fila de `transferencias_terceros`."""

    id: str
    nombre: str
    rol: str
    pais: Optional[str]
    contrato_sha256: Optional[str]
    contrato_vigente_hasta: Optional[date]
    garantia_tipo: Optional[str]
    garantia_sha256: Optional[str]
    criticidad: Optional[str]
    proxima_revision: Optional[date]


@dataclass(frozen=True)
class HallazgoExistente:
    id: str
    origen_ref: str
    estado: str


@dataclass(frozen=True)
class Accion:
    tipo: str  # abrir | reabrir | cerrar
    origen_ref: str
    severidad: str
    titulo: str
    hallazgo_id: Optional[str] = None


@dataclass(frozen=True)
class Condicion:
    origen_ref: str
    severidad: str
    titulo: str


def origen_ref(tercero_id: str, sufijo: str) -> str:
    return f"{tercero_id}:{sufijo}"


def falta_contrato(t: TerceroGarantias, hoy: date) -> bool:
    if t.rol not in ROLES_ENCARGADO:
        return False
    return t.contrato_sha256 is None or (t.contrato_vigente_hasta is not None and t.contrato_vigente_hasta < hoy)


def falta_garantia(t: TerceroGarantias) -> bool:
    return t.pais is not None and t.pais != PAIS_LOCAL and t.garantia_sha256 is None


def condiciones(t: TerceroGarantias, hoy: date) -> list[tuple[Condicion, bool]]:
    """Las dos reglas del tercero, cada una con si se cumple hoy."""
    return [
        (Condicion(origen_ref(t.id, SUFIJO_CONTRATO), "alta",
                   f"Encargado sin contrato vigente: {t.nombre}"[:TITULO_MAX]), falta_contrato(t, hoy)),
        (Condicion(origen_ref(t.id, SUFIJO_GARANTIA), "critica",
                   f"Transferencia internacional con garantía no registrada: {t.nombre}"[:TITULO_MAX]),
         falta_garantia(t)),
    ]


def decidir(
    terceros: Iterable[TerceroGarantias],
    existentes: Mapping[str, HallazgoExistente],
    hoy: date,
) -> list[Accion]:
    """Acciones para dejar los hallazgos `tercero` en el estado que dictan R1 a R4."""
    acciones: list[Accion] = []
    for t in terceros:
        for cond, se_cumple in condiciones(t, hoy):
            previo = existentes.get(cond.origen_ref)
            if se_cumple:
                if previo is None:
                    acciones.append(Accion("abrir", cond.origen_ref, cond.severidad, cond.titulo))
                elif previo.estado == "cerrado":
                    acciones.append(Accion("reabrir", cond.origen_ref, cond.severidad, cond.titulo, previo.id))
            elif previo is not None and previo.estado != "cerrado":
                acciones.append(Accion("cerrar", cond.origen_ref, cond.severidad, cond.titulo, previo.id))
    return acciones


class PuertoTerceros(Protocol):
    async def listar(self) -> Sequence[TerceroGarantias]: ...

    async def obtener(self, tercero_id: str) -> Optional[TerceroGarantias]: ...

    async def actualizar(self, tercero_id: str, campos: dict) -> Optional[TerceroGarantias]: ...


class PuertoHallazgos(Protocol):
    async def listar(self) -> Sequence[HallazgoExistente]: ...

    async def abrir(self, origen_ref: str, severidad: str, titulo: str) -> str: ...

    async def reabrir(self, hallazgo_id: str) -> None: ...

    async def cerrar(self, hallazgo_id: str) -> None: ...


class PuertoEvidencias(Protocol):
    def existe(self, sha256: str) -> Optional[str]: ...
