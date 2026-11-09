from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from app_core.db.base import Base

# --- INICIO ADPA-08 ---
class Tercero(Base):
    """Tabla terceros_encargados (migración 20260420_01_terceros_rls); tenant en texto, como tenants.id."""
    __tablename__ = "terceros_encargados"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    es_internacional = Column(Boolean, nullable=False, default=False)
# --- FIN ADPA-08 ---
