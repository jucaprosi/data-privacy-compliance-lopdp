"""Modelos base y tipos transversales para multi-tenancy y auditoría."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class BaseEntity:
    id: str = field(default_factory=generate_uuid)
    tenant_id: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

@dataclass
class Tenant(BaseEntity):
    nombre_comercial: str = ""
    razon_social: str = ""
    ruc_identificacion: str = ""
    sector: str = ""
    tamano: str = "PYME"
    activo: bool = True
