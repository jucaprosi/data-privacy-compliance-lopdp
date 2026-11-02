# ¤adpa
"""Adaptador del puerto de tratamientos del alta de la organización (ORG-16) sobre la compuerta de RAT.

La sala organizacion no conoce a rat: su motor define el puerto `PuertoTratamientos` y el router
inyecta este adaptador. La compuerta se importa en el cuerpo de cada método para no formar un ciclo
de importación (RAT importa organizacion). Aquí no hay lógica de negocio."""
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class TratamientoExistente:
    id: str
    codigo: str
    origen: str


class AdaptadorTratamientosRat:
    async def listar(self, session: AsyncSession, tenant_id: str) -> list[TratamientoExistente]:
        from features.rat import rat_service

        return [
            TratamientoExistente(id=a.id, codigo=a.codigo, origen=a.origen or "")
            for a in await rat_service.listar_actividades_rat(session, tenant_id)
        ]

    async def registrar(self, session: AsyncSession, tenant_id: str, user_id: str, nuevo: Any) -> None:
        """`nuevo` trae codigo, nombre, finalidad, base_legal (texto del catálogo) y origen."""
        from features.rat import rat_service

        # La compuerta no reexporta la enumeración: se toma del tipo del campo `base_legal`.
        base = type(rat_service.ActividadRAT.__dataclass_fields__["base_legal"].default)
        await rat_service.registrar_actividad_rat(session, rat_service.ActividadRAT(
            tenant_id=tenant_id, codigo=nuevo.codigo, nombre=nuevo.nombre, finalidad=nuevo.finalidad,
            base_legal=base(nuevo.base_legal), origen=nuevo.origen,
        ), user_id)

    async def editar(
        self, session: AsyncSession, tenant_id: str, user_id: str, tratamiento_id: str,
        nombre: str, finalidad: str,
    ) -> None:
        from features.rat import rat_service

        await rat_service.editar_actividad_rat(
            session, tenant_id, tratamiento_id, {"nombre": nombre, "finalidad": finalidad}, user_id,
        )
