from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_tenant_session
from features.terceros import terceros_service

router = APIRouter(prefix="/terceros", tags=["Terceros"])

class TerceroSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    es_internacional: bool

    model_config = ConfigDict(from_attributes=True)

@router.get("/encargados", response_model=List[TerceroSchema])
async def listar_terceros(session: AsyncSession = Depends(get_tenant_session)):
    return await terceros_service.listar_terceros_encargados(session)
