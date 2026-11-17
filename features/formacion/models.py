# ¤models ¤evidencias ¤rbac-tenant
"""Modelos SQLAlchemy para la sala Formación (FOR-01)."""
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FormacionContenidoDB(Base):
    __tablename__ = "formacion_contenidos"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(String(64), nullable=False, index=True)
    titulo = Column(String(120), nullable=False)
    tipo = Column(String(8), nullable=False)
    referencia = Column(Text, nullable=False)
    creado_por = Column(String(64), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("tipo IN ('pdf', 'video')", name="ck_formacion_contenidos_tipo"),
        CheckConstraint("length(trim(titulo)) >= 1", name="ck_formacion_contenidos_titulo"),
    )


class FormacionPreguntaDB(Base):
    __tablename__ = "formacion_preguntas"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(String(64), nullable=False, index=True)
    contenido_id = Column(UUID(as_uuid=True), ForeignKey("formacion_contenidos.id", ondelete="CASCADE"), nullable=False)
    orden = Column(SmallInteger, nullable=False)
    enunciado = Column(Text, nullable=False)
    opciones = Column(JSON, nullable=False)
    correcta = Column(SmallInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("contenido_id", "orden", name="uq_formacion_preguntas_orden"),
        CheckConstraint("orden >= 0", name="ck_formacion_preguntas_orden"),
        CheckConstraint("correcta >= 0", name="ck_formacion_preguntas_correcta"),
    )


class FormacionAccionDB(Base):
    __tablename__ = "formacion_acciones"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(String(64), nullable=False, index=True)
    contenido_id = Column(UUID(as_uuid=True), ForeignKey("formacion_contenidos.id"), nullable=False)
    nombre = Column(String(120), nullable=False)
    inicio = Column(Date, nullable=False)
    fin = Column(Date, nullable=False)
    nota_minima = Column(Numeric(4, 1), nullable=False, default=70.0)
    creado_por = Column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint("fin >= inicio", name="ck_formacion_acciones_fechas"),
        CheckConstraint("nota_minima BETWEEN 0 AND 100", name="ck_formacion_acciones_nota_minima"),
    )


class FormacionParticipacionDB(Base):
    __tablename__ = "formacion_participaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(String(64), nullable=False, index=True)
    accion_id = Column(UUID(as_uuid=True), ForeignKey("formacion_acciones.id", ondelete="CASCADE"), nullable=False)
    persona_id = Column(String(64), nullable=False)
    enviado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    iniciado_en = Column(DateTime(timezone=True), nullable=True)
    terminado_en = Column(DateTime(timezone=True), nullable=True)
    nota = Column(Numeric(4, 1), nullable=True)
    diploma_sha256 = Column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("accion_id", "persona_id", name="uq_formacion_participaciones_persona"),
    )
