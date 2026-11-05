# ¤adpa ¤rbac-tenant
"""Contratos de revisión documental BIB-301."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

TipoParticipacion = Literal["revision", "asesoria", "supervision"]


class ContratoRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DelegarAutoridad(ContratoRevision):
    usuario_id: str = Field(min_length=1, max_length=255)
    criterio: str = Field(min_length=3, max_length=500)
    vigente_desde: datetime
    vigente_hasta: datetime | None = None


class EnviarRevision(ContratoRevision):
    revisor_id: str = Field(min_length=1, max_length=255)
    tipo_participacion: TipoParticipacion = "revision"


class DictamenRevision(ContratoRevision):
    motivo: str = Field(min_length=3, max_length=2000)


class AprobarRevision(ContratoRevision):
    criterio: str = Field(min_length=3, max_length=2000)


class RevisionDocumental(ContratoRevision):
    id: str
    documento_id: str
    revision: int
    sha256: str
    revisor_id: str
    tipo_participacion: TipoParticipacion
    estado: Literal["asignada", "devuelta", "aprobada"]
    observaciones: str | None
    asignado_por: str
    asignado_en: datetime
    decidido_por: str | None
    decidido_en: datetime | None
    criterio_aprobacion: str | None
    autoridad_id: str | None

