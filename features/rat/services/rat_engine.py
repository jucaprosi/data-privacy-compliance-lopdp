# ¤¤security-engineer
"""Persistencia PostgreSQL del RAT; la transacción pertenece al llamador. ¤rat"""
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from features.rat.domain.models import (
    ActividadRAT, BaseLegitimacion, CategoriaTitular, CondicionHabilitante, rat_actividades,
)
# === RAT-05 ===
from features.rat.services.validaciones_engine import tras_baja_ficha, tras_guardar_ficha
# === fin RAT-05 ===


# ¤rat
def _actividad(fila) -> ActividadRAT:
    datos = dict(fila)
    datos.pop("deleted_at")
    datos["base_legal"] = BaseLegitimacion(datos["base_legal"])
    datos["categorias_titulares"] = [
        CategoriaTitular(c) for c in datos["categorias_titulares"]
    ]
    # === RAT-05 ===
    if datos["condicion_habilitante"] is not None:
        datos["condicion_habilitante"] = CondicionHabilitante(datos["condicion_habilitante"])
    # === fin RAT-05 ===
    return ActividadRAT(**datos)


# ¤rat
class PostgresRATRepository:
    """Sin caché ni commits: RLS, actividad y auditoría comparten la sesión."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def obtener_por_id(self, tenant_id: str, actividad_id: str):
        fila = (await self.session.execute(
            select(rat_actividades).where(
                rat_actividades.c.id == actividad_id,
                rat_actividades.c.tenant_id == tenant_id,
                rat_actividades.c.deleted_at.is_(None),
            ).with_for_update()
        )).mappings().first()
        return _actividad(fila) if fila else None

    # === RAT-05 ===
    async def leer_con_bajas(self, tenant_id: str, actividad_id: str):
        """Solo lectura; incluye las dadas de baja, cuyo histórico se conserva."""
        fila = (await self.session.execute(
            select(rat_actividades).where(
                rat_actividades.c.id == actividad_id,
                rat_actividades.c.tenant_id == tenant_id,
            )
        )).mappings().first()
        return _actividad(fila) if fila else None
    # === fin RAT-05 ===

    async def listar_por_tenant(self, tenant_id: str) -> list[ActividadRAT]:
        filas = (await self.session.execute(
            select(rat_actividades).where(
                rat_actividades.c.tenant_id == tenant_id,
                rat_actividades.c.deleted_at.is_(None),
            ).order_by(rat_actividades.c.codigo, rat_actividades.c.id)
        )).mappings().all()
        return [_actividad(f) for f in filas]

    async def guardar(self, actividad: ActividadRAT) -> ActividadRAT:
        await self.session.execute(insert(rat_actividades).values(**asdict(actividad)))
        return actividad

    async def actualizar(self, actividad: ActividadRAT) -> ActividadRAT:
        await self.session.execute(
            update(rat_actividades).where(
                rat_actividades.c.id == actividad.id,
                rat_actividades.c.tenant_id == actividad.tenant_id,
                rat_actividades.c.deleted_at.is_(None),
            ).values(**asdict(actividad))
        )
        return actividad

    async def dar_de_baja(self, actividad: ActividadRAT) -> None:
        await self.session.execute(
            update(rat_actividades).where(
                rat_actividades.c.id == actividad.id,
                rat_actividades.c.tenant_id == actividad.tenant_id,
                rat_actividades.c.deleted_at.is_(None),
            ).values(deleted_at=datetime.now(timezone.utc), version=actividad.version + 1)
        )


# ¤rat
def _normalizar(actividad: ActividadRAT) -> None:
    if not actividad.codigo:
        actividad.codigo = f"RAT-{actividad.id}"
    if CategoriaTitular.PACIENTES in actividad.categorias_titulares:
        actividad.datos_sensibles = True


# ¤rat
async def crear_o_actualizar_actividad(
    session: AsyncSession, actividad: ActividadRAT, user_id: str | None = None,
) -> ActividadRAT:
    """Crea una actividad; editar requiere id y tenant explícitos."""
    _normalizar(actividad)
    guardada = await PostgresRATRepository(session).guardar(actividad)
    # === RAT-05 ===
    await tras_guardar_ficha(session, guardada, user_id)
    # === fin RAT-05 ===
    return guardada


# ¤rat
async def obtener_actividades_tenant(session: AsyncSession, tenant_id: str):
    return await PostgresRATRepository(session).listar_por_tenant(tenant_id)


# ¤rat
async def editar_actividad(
    session: AsyncSession, tenant_id: str, rat_id: str, cambios: dict,
    user_id: str | None = None,
) -> ActividadRAT | None:
    repo = PostgresRATRepository(session)
    actividad = await repo.obtener_por_id(tenant_id, rat_id)
    if actividad is None:
        return None
    editables = set(asdict(actividad)) - {"id", "tenant_id", "version"}
    if set(cambios) - editables or any(v is None for v in cambios.values()):
        raise ValueError("Campos de actividad no válidos")
    for campo, valor in cambios.items():
        setattr(actividad, campo, valor)
    _normalizar(actividad)
    actividad.version += 1
    await repo.actualizar(actividad)
    # === RAT-05 ===
    await tras_guardar_ficha(session, actividad, user_id)
    # === fin RAT-05 ===
    return actividad


# ¤rat
async def eliminar_actividad(
    session: AsyncSession, tenant_id: str, rat_id: str, user_id: str | None = None,
) -> bool:
    repo = PostgresRATRepository(session)
    actividad = await repo.obtener_por_id(tenant_id, rat_id)
    if actividad is None:
        return False
    await repo.dar_de_baja(actividad)
    # === RAT-05 ===
    await tras_baja_ficha(session, actividad, user_id)
    # === fin RAT-05 ===
    return True
