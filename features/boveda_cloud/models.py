# ¤boveda-cloud ¤seguridad-tenant
"""Tablas de la sala: `boveda_paquetes` (catálogo global) y `boveda_suscripciones_tenant` (RLS por tenant_id)."""
import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app_core.db.base import Base


class PaqueteBoveda(Base):
    __tablename__ = "boveda_paquetes"

    codigo = Column(String(32), primary_key=True)
    nombre = Column(String(120), nullable=False)
    cuota_almacenamiento_bytes = Column(BigInteger, nullable=True)
    cuota_egress_mensual_bytes = Column(BigInteger, nullable=True)
    peticiones_api_minuto = Column(Integer, nullable=True)
    tokens_ia_mes = Column(BigInteger, nullable=True)
    max_claves_integracion = Column(Integer, nullable=True)
    max_webhooks = Column(Integer, nullable=True)


class SuscripcionBoveda(Base):
    __tablename__ = "boveda_suscripciones_tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(64), nullable=False, unique=True)  # la FK a tenants la crea la migración
    paquete_codigo = Column(String(32), ForeignKey("boveda_paquetes.codigo"), nullable=False)
    cuota_almacenamiento_bytes = Column(BigInteger, nullable=False)
    uso_almacenamiento_bytes = Column(BigInteger, nullable=False, server_default="0")
    cuota_egress_mensual_bytes = Column(BigInteger, nullable=False)
    uso_egress_mensual_bytes = Column(BigInteger, nullable=False, server_default="0")
    certificaciones_heredadas = Column(JSONB, nullable=False)
    estado = Column(String(20), nullable=False, server_default="ACTIVA")
    creado_por = Column(String, nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
