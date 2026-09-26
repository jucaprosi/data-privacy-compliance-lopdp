from sqlalchemy import Column, String, Boolean, Enum, text
from sqlalchemy.dialects.postgresql import UUID
import enum
from app_core.database import Base

class RolTercero(str, enum.Enum):
    ENCARGADO = "ENCARGADO"
    SUBENCARGADO = "SUBENCARGADO"
    DESTINATARIO = "DESTINATARIO"

class NivelProteccion(str, enum.Enum):
    ADECUADO = "ADECUADO"
    ESTANDAR = "ESTANDAR"
    NO_ADECUADO = "NO_ADECUADO"

class TerceroEncargado(Base):
    """
    Entidad que mapea un Encargado de Tratamiento o Destinatario de Transferencia
    Internacional, garantizando que el DPO o titular del tenant evalúe su nivel de protección.
    Aislado por tenant_id (RLS).
    """
    __tablename__ = "transferencias_terceros"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    nombre = Column(String(200), nullable=False)
    rol = Column(Enum(RolTercero), nullable=False)
    pais_destino = Column(String(100), nullable=False)
    nivel_proteccion = Column(Enum(NivelProteccion), nullable=False)
    
    # Garantías adecuadas (Standard Contractual Clauses u otros mecanismos legales)
    clausulas_firmadas = Column(Boolean, nullable=False, default=False)
    
    # Poka-Yoke: no se puede transferir a países NO_ADECUADOS sin garantías (clausulas_firmadas=True)
    
    def es_transferencia_legal(self) -> bool:
        if self.nivel_proteccion == NivelProteccion.ADECUADO:
            return True
        # Si no es adecuado o es estándar, requiere garantías (ej. cláusulas)
        return self.clausulas_firmadas

    def __repr__(self):
        return f"<TerceroEncargado(id={self.id}, nombre={self.nombre}, legal={self.es_transferencia_legal()})>"
