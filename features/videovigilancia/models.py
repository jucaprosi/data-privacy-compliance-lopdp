# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv ¤seguridad-tenant
"""Tabla `cctv_camaras_inventario` (RLS forzado por tenant_id)."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from app_core.db.base import Base


class CamaraInventario(Base):
    __tablename__ = "cctv_camaras_inventario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(64), nullable=False, index=True)  # la FK a tenants la crea la migración
    nombre_ubicacion = Column(String(160), nullable=False)
    codec = Column(String(16), nullable=False)
    modo_grabacion = Column(String(32), nullable=False)
    audio_ambiental_activo = Column(Boolean, nullable=False, default=False, server_default="false")
    mascara_privacidad_activa = Column(Boolean, nullable=False, default=True, server_default="true")
    plazo_retencion_dias = Column(Integer, nullable=False, default=15, server_default="15")
    estado_conformidad = Column(String(32), nullable=False, default="CONFORME", server_default="CONFORME")
    actividad_rat_id = Column(String(64), nullable=True)
    creado_por = Column(String, nullable=False)  # del token, nunca del cuerpo
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
