# ¤dlp-muestreo ¤seguridad-tenant
"""Tabla `dlp_escaneos_muestreados` (RLS forzado por tenant_id). Solo tipos y conteos, nunca el dato hallado."""
import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app_core.db.base import Base


class EscaneoMuestreado(Base):
    __tablename__ = "dlp_escaneos_muestreados"
    __table_args__ = (CheckConstraint("limite_muestra BETWEEN 1 AND 1000", name="ck_dlp_limite_muestra"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=False, index=True)
    fuente_nombre = Column(String(160), nullable=False)
    limite_muestra = Column(Integer, nullable=False, default=250, server_default="250")
    infotypes_detectados = Column(JSONB, nullable=False)
    contiene_datos_sensibles = Column(Boolean, nullable=False)
    actividad_rat_id = Column(String(64), nullable=True)
    creado_por = Column(String, nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
