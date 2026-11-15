# ¤conservacion ¤seguridad-tenant
"""Tabla de la sala: `politicas_conservacion` (RLS por tenant_id; la FK a tenants la crea la migración)."""
import uuid

from sqlalchemy import Column, Date, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from app_core.db.base import Base


class PoliticaConservacion(Base):
    __tablename__ = "politicas_conservacion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(64), nullable=False)
    actividad_rat_id = Column(String(64), nullable=False)
    plazo_meses = Column(Integer, nullable=False)
    accion_vencimiento = Column(String(16), nullable=False)
    fecha_proxima_revision = Column(Date, nullable=False)
    estado = Column(String(16), nullable=False, server_default="ACTIVA")
    acta_ejecucion_hash = Column(String(64), nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
