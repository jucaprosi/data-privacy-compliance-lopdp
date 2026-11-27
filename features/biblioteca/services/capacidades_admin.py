# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤seguridad
# ¤¤developer-architect
"""BIB-117 y BIB-411 · Conceder, retirar y listar capacidades editoriales de la Biblioteca.

Lo usan la API del equipo (`api/routers/biblioteca_capacidades.py`) y `scripts/capacidades_biblioteca.py`.
`lopdp_app` no tiene privilegios sobre `biblioteca_capacidades`: se escribe y se lee por las funciones
`SECURITY DEFINER` de la migración `20261125_bib411_operadores`. Reglas (especificación BIB-411):
- concede y retira cualquier operador activo, a otro operador activo, nunca a sí mismo (R1, R2);
- motivo de al menos 10 caracteres sin espacios al borde (R2);
- solo las tres capacidades del dominio (R6);
- repetir devuelve `vigente` o `sin_vigente`, sin cambiar nada (R2b);
- nunca se borra: retirar es un UPDATE y conceder una capacidad retirada la reactiva; el disparador
  `bib_auditar_capacidad` registra quién, a quién, qué, motivo y fecha (R5).
Ningún rol empresarial (administrador de la organización o de la plataforma) interviene.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.biblioteca.domain.editorial import Capacidad


# ¤adpa
@dataclass(frozen=True)
class CapacidadAsignada:
    usuario_id: str
    capacidad: str
    concedida_por: str
    concedida_en: str
    revocada_en: str | None


# ¤adpa
def _capacidad(valor: str) -> Capacidad:
    try:
        return Capacidad(valor)
    except ValueError:
        raise ErrorNegocio("BIB_CAPACIDAD_INVALIDA") from None


# ¤adpa
MOTIVO_MINIMO = 10
_CODIGOS_BASE = ("BIB_CAPACIDAD_INVALIDA", "BIB_AUTOCONCESION", "BIB_MOTIVO_OBLIGATORIO", "BIB_SOLO_OPERADORES",
                 "BIB_DESTINO_NO_OPERADOR")
_ACTOR = text("SELECT set_config('app.current_user_id', :actor, true)")
_CONCEDER = text("SELECT biblioteca_conceder_capacidad(:u, :c, :m)")
_RETIRAR = text("SELECT biblioteca_retirar_capacidad(:u, :c, :m)")
_EQUIPO = text("SELECT usuario_id, capacidad FROM biblioteca_capacidades_equipo()")
_HISTORIAL = text(
    "SELECT id, usuario_id, capacidad, accion, por, motivo, en FROM biblioteca_historial_capacidades(:u)"
)
_CAMBIOS = text(
    "SELECT id, usuario_id, capacidad, accion, por, motivo, en FROM biblioteca_cambios_capacidades(:desde)"
)
_LISTAR = text(
    "SELECT usuario_id, capacidad, concedida_por, concedida_en::text, revocada_en::text "
    "FROM biblioteca_capacidades ORDER BY usuario_id, capacidad"
)


# ¤adpa
def _motivo(valor: str | None) -> str:
    motivo = (valor or "").strip()
    if len(motivo) < MOTIVO_MINIMO:
        raise ErrorNegocio("BIB_MOTIVO_OBLIGATORIO")
    return motivo


# ¤adpa
def _validar(usuario_id: str, capacidad: str, otorgante: str, motivo: str | None) -> tuple[Capacidad, str]:
    """Validaciones que no tocan la base, en este orden: capacidad, autoconcesión, motivo."""
    cap = _capacidad(capacidad)
    if not usuario_id or not otorgante or usuario_id.strip() == otorgante.strip():
        raise ErrorNegocio("BIB_AUTOCONCESION")
    return cap, _motivo(motivo)


# ¤adpa
async def _exigir_activo(session: AsyncSession, usuario_id: str, codigo: str) -> None:
    """R1: solo cuenta un operador activo de la plataforma (por su pasillo); si no, `codigo`."""
    from app_core.pasillo import plataforma as pasillo_plataforma

    if not await pasillo_plataforma.operador_activo(session, usuario_id):
        raise ErrorNegocio(codigo)


# ¤adpa
async def _escribir(session: AsyncSession, sentencia, usuario_id: str, capacidad: str, otorgante: str,
                    motivo: str | None) -> str:
    cap, motivo = _validar(usuario_id, capacidad, otorgante, motivo)
    await _exigir_activo(session, otorgante, "BIB_SOLO_OPERADORES")
    await _exigir_activo(session, usuario_id, "BIB_DESTINO_NO_OPERADOR")
    await session.execute(_ACTOR, {"actor": otorgante})
    try:
        async with session.begin_nested():
            return (await session.execute(sentencia, {"u": usuario_id, "c": cap.value, "m": motivo})).scalar()
    except DBAPIError as exc:  # la base revalida (R1, R2): su código manda
        codigo = next((c for c in _CODIGOS_BASE if c in str(exc.orig)), None)
        if codigo is None:
            raise
        raise ErrorNegocio(codigo) from None


# ¤adpa
async def conceder(session: AsyncSession, usuario_id: str, capacidad: str, otorgante: str,
                   motivo: str | None) -> str:
    """Concede la capacidad, o la reactiva si estaba retirada. Devuelve `alta`, `reactivacion` o `vigente`."""
    return await _escribir(session, _CONCEDER, usuario_id, capacidad, otorgante, motivo)


# ¤adpa
async def revocar(session: AsyncSession, usuario_id: str, capacidad: str, otorgante: str,
                  motivo: str | None) -> str:
    """Retira una capacidad vigente con UPDATE. Devuelve `revocacion` o `sin_vigente`."""
    return await _escribir(session, _RETIRAR, usuario_id, capacidad, otorgante, motivo)


# ¤adpa
async def listar(session: AsyncSession) -> list[CapacidadAsignada]:
    """Todas las asignaciones, vigentes y retiradas, sin motivos (lo usa el script, con el dueño de la base)."""
    return [CapacidadAsignada(*fila) for fila in (await session.execute(_LISTAR)).all()]


# ¤adpa
async def equipo(session: AsyncSession) -> list[dict]:
    """§2: los operadores activos, cada uno con `usuario_id`, `nombre`, `email`, `ha_entrado` y sus capacidades."""
    from app_core.pasillo import plataforma as pasillo_plataforma

    vigentes: dict[str, list[str]] = {}
    for usuario_id, capacidad in (await session.execute(_EQUIPO)).all():
        vigentes.setdefault(usuario_id, []).append(capacidad)
    return [{**o, "capacidades": sorted(vigentes.get(o["usuario_id"], []))}
            for o in await pasillo_plataforma.listar_operadores_activos(session)]


# ¤adpa
async def historial(session: AsyncSession, usuario_id: str) -> list[dict]:
    """R5: concesiones y retiros de `usuario_id`, con quién, motivo y fecha."""
    return [dict(f) for f in (await session.execute(_HISTORIAL, {"u": usuario_id})).mappings().all()]


# ¤adpa
async def cambios(session: AsyncSession, desde: datetime) -> list[dict]:
    """Para NOTIF-04: concesiones y retiros posteriores a `desde`."""
    return [dict(f) for f in (await session.execute(_CAMBIOS, {"desde": desde})).mappings().all()]
