from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from app_core.database import Base

class Tercero(Base):
    __tablename__ = "terceros_encargados"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    es_internacional = Column(Boolean, default=False)
