import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app_core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class TenantORM(Base):
    __tablename__ = 'tenants'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    nombre_comercial = Column(String(255), nullable=False)
    razon_social = Column(String(255), nullable=False)
    ruc_identificacion = Column(String(50), nullable=False, unique=True)
    sector = Column(String(100), nullable=True)
    tamano = Column(String(50), default="PYME")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class RegistroAuditoriaORM(Base):
    __tablename__ = 'registro_auditoria'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey('tenants.id'), nullable=False)
    id_diagnostico = Column(String(100), nullable=False)
    normativa = Column(String(50), default="LOPDP")
    snapshot_hash = Column(String(255), nullable=False)
    fecha_certificacion = Column(DateTime(timezone=True), default=utc_now)

class TareaMitigacionORM(Base):
    __tablename__ = 'tareas_mitigacion'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey('tenants.id'), nullable=False)
    id_diagnostico = Column(String(100), nullable=False)
    descripcion = Column(String(500), nullable=False)
    impacto_riesgo = Column(String(50), nullable=False)
    estado = Column(String(50), default="PENDIENTE")
    fecha_limite = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)