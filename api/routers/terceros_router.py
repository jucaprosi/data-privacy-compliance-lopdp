from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from app_core.database import get_db_session
from features.terceros.domain.models import Tercero

router = APIRouter(prefix="/terceros", tags=["Terceros"])

class TerceroSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    es_internacional: bool
    
    model_config = ConfigDict(from_attributes=True)

@router.get("/encargados", response_model=List[TerceroSchema])
async def listar_terceros(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Tercero))
    return result.scalars().all()
