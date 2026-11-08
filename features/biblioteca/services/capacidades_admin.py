# ¤adpa ¤seguridad
# ¤¤developer-architect
"""BIB-117 · Conceder, revocar y listar capacidades editoriales de la Biblioteca.

Solo lo usa `scripts/capacidades_biblioteca.py`, con la credencial del dueño de la base de una rama de
prueba; no hay endpoint. Reglas (PRD «Biblioteca C» y `DISENO_CAPACIDADES_BIBLIOTECA.md`):
- nadie se concede ni se revoca a sí mismo (también lo exige la base, con un CHECK);
- motivo obligatorio al conceder, revocar y reactivar;
- solo las cuatro capacidades del dominio;
- el otorgante existe y está activo; el destinatario también, al conceder;
- nunca se borra: revocar es un UPDATE, y conceder una capacidad revocada la reactiva. El disparador
  `bib_auditar_capacidad` registra alta, revocación y reactivación.
Ningún rol empresarial (administrador de la organización o de la plataforma) interviene.
"""
from dataclasses import dataclass

from sqlalchemy import text
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
def _motivo(valor: str | None) -> str:
    motivo = (valor or "").strip()
    if not motivo:
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
async def _exigir_activo(session: AsyncSession, usuario_id: str) -> None:
    activo = (await session.execute(
        text("SELECT 1 FROM users WHERE id=:id AND activo AND deleted_at IS NULL"), {"id": usuario_id}
    )).scalar()
    if not activo:
        raise ErrorNegocio("BIB_USUARIO_INACTIVO")


# ¤adpa
async def conceder(session: AsyncSession, usuario_id: str, capacidad: str, otorgante: str,
                   motivo: str | None) -> str:
    """Concede la capacidad, o la reactiva si estaba revocada. Devuelve `alta`, `reactivacion` o `vigente`."""
    cap, motivo = _validar(usuario_id, capacidad, otorgante, motivo)
    await _exigir_activo(session, otorgante)
    await _exigir_activo(session, usuario_id)
    fila = (await session.execute(text(
        "SELECT revocada_en FROM biblioteca_capacidades WHERE usuario_id=:u AND capacidad=:c FOR UPDATE"
    ), {"u": usuario_id, "c": cap.value})).first()
    if fila is None:
        await session.execute(text(
            "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) VALUES (:u,:c,:o,:m)"
        ), {"u": usuario_id, "c": cap.value, "o": otorgante, "m": motivo})
        return "alta"
    if fila.revocada_en is None:
        return "vigente"
    await session.execute(text(
        "UPDATE biblioteca_capacidades SET concedida_por=:o, motivo=:m, concedida_en=now(), "
        "revocada_en=NULL, revocada_por=NULL, motivo_revocacion=NULL "
        "WHERE usuario_id=:u AND capacidad=:c"
    ), {"u": usuario_id, "c": cap.value, "o": otorgante, "m": motivo})
    return "reactivacion"


# ¤adpa
async def revocar(session: AsyncSession, usuario_id: str, capacidad: str, otorgante: str,
                  motivo: str | None) -> str:
    """Revoca una capacidad vigente con UPDATE. Devuelve `revocacion` o `sin_vigente`."""
    cap, motivo = _validar(usuario_id, capacidad, otorgante, motivo)
    await _exigir_activo(session, otorgante)
    resultado = await session.execute(text(
        "UPDATE biblioteca_capacidades SET revocada_en=now(), revocada_por=:o, motivo_revocacion=:m "
        "WHERE usuario_id=:u AND capacidad=:c AND revocada_en IS NULL"
    ), {"u": usuario_id, "c": cap.value, "o": otorgante, "m": motivo})
    return "revocacion" if resultado.rowcount else "sin_vigente"


# ¤adpa
async def listar(session: AsyncSession) -> list[CapacidadAsignada]:
    """Todas las asignaciones, vigentes y revocadas, sin motivos (pueden traer datos personales)."""
    filas = await session.execute(text(
        "SELECT usuario_id, capacidad, concedida_por, concedida_en::text, revocada_en::text "
        "FROM biblioteca_capacidades ORDER BY usuario_id, capacidad"
    ))
    return [CapacidadAsignada(*fila) for fila in filas.all()]
