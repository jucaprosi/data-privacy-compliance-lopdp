# ¤inteligencia-normativa ¤adpa
"""Modelos de la sala Inteligencia Normativa (NORM-01). Tablas globales: el corpus es público y común.

Sin `tenant_id` y sin RLS: `lopdp_app` solo lee; escribe el proceso de monitoreo con un rol propio.
Las crea la migración `norm01_inteligencia_normativa`.
"""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app_core.db.base import Base

SECCIONES = ("resoluciones", "marco_normativo", "consultas_absueltas")
ESTADOS = ("pendiente_revision", "homologada", "observada", "vigente", "reformada", "derogada")
MOTIVOS = ("republicacion", "fe_de_erratas", "cambio_en_fuente")
ORIGENES = ("programado", "manual")
ESTADOS_CORRIDA = ("ok", "parcial", "fallida")


class NormativaResolucion(Base):
    __tablename__ = "normativa_resoluciones"
    __table_args__ = (UniqueConstraint("numero_resolucion", "anio_emision", name="uq_normativa_numero_anio"),)

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    numero_resolucion = Column(String(100), nullable=False)
    anio_emision = Column(Integer, nullable=False)
    titulo = Column(String(500), nullable=False)
    organo_emisor = Column(String(200))
    materia = Column(String(200))
    fecha_publicacion = Column(Date)
    url_fuente = Column(String(1000), nullable=False)
    seccion_fuente = Column(String(30), nullable=False)
    archivo_sha256 = Column(String(64), nullable=False)
    ruta_original = Column(String(500), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=False)
    estado = Column(String(30), nullable=False, server_default="pendiente_revision")
    detectada_en = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    revisada_por = Column(String)
    revisada_en = Column(DateTime(timezone=True))


class NormativaVersion(Base):
    """Inmutable: la migración la protege con un disparador que rechaza UPDATE y DELETE."""

    __tablename__ = "normativa_versiones"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    resolucion_id = Column(UUID(as_uuid=True), ForeignKey("normativa_resoluciones.id"), nullable=False)
    archivo_sha256 = Column(String(64), nullable=False)
    ruta_original = Column(String(500), nullable=False)
    detectada_en = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    motivo = Column(String(30), nullable=False)


class NormativaMonitoreoLog(Base):
    __tablename__ = "normativa_monitoreo_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    inicio = Column(DateTime(timezone=True), nullable=False)
    fin = Column(DateTime(timezone=True))
    origen = Column(String(20), nullable=False)
    documentos_vistos = Column(Integer, nullable=False, server_default="0")
    nuevos = Column(Integer, nullable=False, server_default="0")
    versiones_nuevas = Column(Integer, nullable=False, server_default="0")
    errores = Column(Integer, nullable=False, server_default="0")
    estado = Column(String(20), nullable=False)
    codigos_error = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
