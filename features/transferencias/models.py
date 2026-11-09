"""Modelos propios de la sala transferencias (ADPA-08). ¤adpa ¤transferencias

Tabla `transferencias_terceros`, creada por la migración 20260420_01_terceros_rls.
`tenant_id` es texto, como `tenants.id`; la RLS forzada lo aísla por organización.

Las enumeraciones `RolTercero` y `NivelProteccion` siguen en services/encargados_service.py, que importa
este módulo: aquí las columnas usan sus valores como texto para no crear un import circular. Al ser
enumeraciones de `str`, `NivelProteccion.ADECUADO == "ADECUADO"`.
"""
from sqlalchemy import Boolean, Column, Enum, String, text
from sqlalchemy.dialects.postgresql import UUID

from app_core.db.base import Base

ROLES = ("ENCARGADO", "SUBENCARGADO", "DESTINATARIO")
NIVELES = ("ADECUADO", "ESTANDAR", "NO_ADECUADO")


class TerceroEncargado(Base):
    """Encargado de tratamiento o destinatario de una transferencia internacional, aislado por tenant (RLS)."""
    __tablename__ = "transferencias_terceros"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(String, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    rol = Column(Enum(*ROLES, name="rol_tercero", native_enum=False, length=20), nullable=False)
    pais_destino = Column(String(100), nullable=False)
    nivel_proteccion = Column(Enum(*NIVELES, name="nivel_proteccion", native_enum=False, length=20), nullable=False)
    # Garantías adecuadas (cláusulas contractuales tipo u otro mecanismo legal)
    clausulas_firmadas = Column(Boolean, nullable=False, default=False)

    def es_transferencia_legal(self) -> bool:
        """Poka-Yoke: un país sin nivel adecuado exige garantías firmadas."""
        if self.nivel_proteccion == "ADECUADO":
            return True
        return bool(self.clausulas_firmadas)

    def __repr__(self):
        return f"<TerceroEncargado(id={self.id}, nombre={self.nombre}, legal={self.es_transferencia_legal()})>"
