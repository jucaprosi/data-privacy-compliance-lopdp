# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Guardado de borradores con revisión esperada atómica y recuperación de conflictos (BIB-207).

El `UPDATE` solo escribe si la fila sigue en la revisión que el cliente vio (`WHERE revision=:rev`): dos
editores que parten de la misma revisión no se pisan, aunque no haya bloqueo previo. Si otra persona guardó
antes, se responde 409 con la versión vigente y la lista de campos que difieren, para comparar y recuperar.
Recuperar es volver a guardar los cambios propios sobre la revisión vigente: nunca se descarta nada en silencio.
"""
import json
from collections.abc import Mapping
from datetime import date
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.domain.base import Contrato
from features.biblioteca.domain.esquemas import GuardarBorrador, leer_plantilla
from features.biblioteca.services.validacion import validar_contexto
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

LEER = ("SELECT id, contexto, fecha_emision, revision, plantilla_md, actualizado_por, actualizado_en "
        "FROM biblioteca_borradores WHERE id=:id")
GUARDAR = ("UPDATE biblioteca_borradores SET contexto=CAST(:ctx AS jsonb), fecha_emision=:fecha, "
           "revision=revision+1, actualizado_por=:u, actualizado_en=now() "
           "WHERE id=:id AND revision=:rev RETURNING revision")


# ¤adpa
class Diferencia(Contrato):
    clave: str
    mio: object | None = None
    vigente: object | None = None


# ¤adpa
class Conflicto(Contrato):
    """Lo que el cliente necesita para comparar: la versión vigente y en qué difiere de la suya."""
    borrador_id: str
    revision_esperada: int
    revision_vigente: int
    contexto_vigente: dict
    fecha_vigente: date
    diferencias: list[Diferencia] = Field(default_factory=list)


# ¤adpa
class Guardado(Contrato):
    borrador_id: str
    revision: int


# ¤adpa
class ErrorConflicto(ErrorNegocio):
    """409 con la comparación adjunta; el router la devuelve en el cuerpo."""

    def __init__(self, conflicto: Conflicto):
        super().__init__("BIB_CONFLICTO_EDICION")
        self.conflicto = conflicto


# ¤adpa
async def _fijar_contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": actor})


# ¤adpa
def _contexto(fila: Mapping) -> dict:
    return fila["contexto"] if isinstance(fila["contexto"], dict) else json.loads(fila["contexto"])


# ¤adpa
def comparar(mio: Mapping, vigente: Mapping) -> list[Diferencia]:
    """Campos cuyo valor difiere entre lo que quiere guardar el cliente y lo vigente, en orden estable."""
    return [Diferencia(clave=k, mio=mio.get(k), vigente=vigente.get(k))
            for k in sorted(set(mio) | set(vigente)) if mio.get(k) != vigente.get(k)]


# ¤adpa
async def _leer(session: AsyncSession, borrador_id: str) -> Mapping:
    fila = (await session.execute(text(LEER), {"id": borrador_id})).mappings().first()
    if fila is None:  # la RLS oculta los de otra organización
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")
    return fila


# ¤adpa
async def guardar_con_revision(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str,
                               entrada: GuardarBorrador) -> Guardado:
    """Guarda solo si la revisión esperada sigue vigente; si no, `ErrorConflicto` (409) con la comparación."""
    await _fijar_contexto(session, tenant_id, actor)
    fila = await _leer(session, borrador_id)
    contexto = validar_contexto(leer_plantilla(fila["plantilla_md"]).campos, entrada.contexto)
    nueva = (await session.execute(text(GUARDAR), {
        "ctx": json.dumps(contexto, ensure_ascii=False), "fecha": entrada.fecha_emision or fila["fecha_emision"],
        "u": actor, "id": borrador_id, "rev": entrada.revision})).scalar()
    if nueva is None:
        vigente = await _leer(session, borrador_id)
        raise ErrorConflicto(Conflicto(
            borrador_id=borrador_id, revision_esperada=entrada.revision, revision_vigente=vigente["revision"],
            contexto_vigente=_contexto(vigente), fecha_vigente=vigente["fecha_emision"],
            diferencias=comparar(contexto, _contexto(vigente))))
    return Guardado(borrador_id=borrador_id, revision=nueva)


__all__ = ["Conflicto", "Diferencia", "ErrorConflicto", "Guardado", "comparar", "guardar_con_revision"]
