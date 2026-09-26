from sqlalchemy import Column, String, DateTime, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import enum
from app_core.database import Base

class TipoSolicitud(str, enum.Enum):
    ACCESO = "ACCESO"
    RECTIFICACION = "RECTIFICACION"
    CANCELACION = "CANCELACION"
    OPOSICION = "OPOSICION"
    PORTABILIDAD = "PORTABILIDAD"

class EstadoSolicitud(str, enum.Enum):
    RECIBIDA = "RECIBIDA"
    EN_ANALISIS = "EN_ANALISIS"
    EN_REQUERIMIENTO = "EN_REQUERIMIENTO" # Si falta información o identidad
    CONTESTADA = "CONTESTADA"
    VENCIDA = "VENCIDA"

class SolicitudARCO(Base):
    """
    Entidad que mapea una solicitud de derechos ARCO+ según la LOPDP de Ecuador.
    Contiene obligatoriamente el tenant_id para RLS (Row-Level Security).
    """
    __tablename__ = "derechos_arco_solicitudes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    tipo_solicitud = Column(Enum(TipoSolicitud), nullable=False)
    estado = Column(Enum(EstadoSolicitud), nullable=False, default=EstadoSolicitud.RECIBIDA)
    
    cedula_solicitante = Column(String(20), nullable=False)
    nombre_solicitante = Column(String(200), nullable=False)
    
    # SLA Normativo: 15 días según LOPDP
    fecha_recepcion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    
    # Expediente probatorio (Hash SHA-256 de la evidencia de respuesta)
    evidencia_respuesta_hash = Column(String(64), nullable=True)
    
    def __repr__(self):
        return f"<SolicitudARCO(id={self.id}, tipo={self.tipo_solicitud}, estado={self.estado})>"
