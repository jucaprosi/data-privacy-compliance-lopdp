# ¤adpa
# ¤¤developer-architect
"""Contratos E1; sin persistencia privada ni implementaciones de otras tareas."""
from datetime import datetime
from typing import Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ¤adpa
class Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


# ¤adpa
class ObjetoDocumento(Contrato):
    tenant_id: str = Field(min_length=1)
    objeto_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0)
    estado_analisis: Literal["pendiente", "limpio", "rechazado"]


# ¤adpa
class DocumentoEmpresa(Contrato):
    tenant_id: str = Field(min_length=1)
    documento_id: str = Field(min_length=1)
    origen: Literal["externo", "generado"]
    version_maestra_id: str | None = None


# ¤adpa
class RevisionDocumento(Contrato):
    tenant_id: str = Field(min_length=1)
    documento_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    objeto: ObjetoDocumento
    autor_id: str = Field(min_length=1)
    creada_en: datetime

    @model_validator(mode="after")
    def mismo_tenant(self) -> "RevisionDocumento":
        if self.objeto.tenant_id != self.tenant_id:
            raise ValueError("La revisión y su objeto deben pertenecer a la misma organización")
        return self


# ¤adpa
class EventoDocumento(Contrato):
    tenant_id: str = Field(min_length=1)
    documento_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    accion: str = Field(min_length=1)
    instante: datetime


# ¤adpa
class PuertoDocumentos(Protocol):
    """BIB-106 implementará pertenencia, RLS y referencias del mismo tenant."""
    async def obtener(self, tenant_id: str, documento_id: str) -> DocumentoEmpresa: ...


# ¤adpa
class PuertoObjetos(Protocol):
    async def leer(self, tenant_id: str, objeto_id: str) -> bytes: ...


# ¤adpa
class PuertoAuditoria(Protocol):
    async def registrar(self, evento: EventoDocumento) -> None: ...
