from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter(prefix="/arco", tags=["ARCO"])

class ArcoSolicitud(BaseModel):
    id: str
    tenant_id: str
    titular_id: str
    tipo_derecho: str
    estado: str

# In memory store for mock RLS
_arco_store = []

@router.post("/solicitudes")
def crear_solicitud(payload: ArcoSolicitud, authorization: Optional[str] = Header(None)):
    _arco_store.append(payload)
    return {"status": "success", "solicitud": payload}

@router.get("/solicitudes")
def listar_solicitudes(authorization: Optional[str] = Header(None)):
    # Mock RLS extracting tenant from authorization token
    tenant = authorization.replace("Bearer ", "") if authorization else None
    if not tenant:
        return []
    # RLS Enforcement Mock: only return rows matching the tenant
    filtered = [s for s in _arco_store if s.tenant_id == tenant]
    return filtered
