from sqlalchemy import Column, String, DateTime, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import enum
from app_core.db.base import Base

class TipoSolicitud(str, enum.Enum):
    ACCESO = "ACCESO"
    RECTIFICACION = "RECTIFICACION"
    CANCELACION = "CANCELACION"
    OPOSICION = "OPOSICION"
    PORTABILIDAD = "PORTABILIDAD"
    # DER-06a: leídos desde la base, pero no se pueden crear hasta que DER-06b los active (TIPOS_ACTIVOS).
    SUSPENSION = "SUSPENSION"
    DECISIONES_AUTOMATIZADAS = "DECISIONES_AUTOMATIZADAS"
    QUEJA = "QUEJA"

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
    # DER-03: texto, como tenants.id. La columna física es tenant_id_texto (expand/contract, GCP-07);
    # la vieja tenant_id (uuid) se retira en la contracción.
    tenant_id = Column("tenant_id_texto", String, nullable=False, index=True)  # FK a tenants(id) en la base
    
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
