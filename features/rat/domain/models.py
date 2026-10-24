# ¤¤security-engineer
"""Modelos de dominio del Módulo 2: RAT Maestro (Registro de Actividades de Tratamiento)."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid

from sqlalchemy import (MetaData, Table, Column, String, Text, JSON, Boolean,
                        Integer, DateTime)

# ¤rat
def gen_id() -> str:
    return str(uuid.uuid4())

# ¤rat
class BaseLegitimacion(str, Enum):
    CONSENTIMIENTO = "CONSENTIMIENTO"
    OBLIGACION_LEGAL = "OBLIGACION_LEGAL"
    CUMPLIMIENTO_CONTRATO = "CUMPLIMIENTO_CONTRATO"
    PROTECCION_INTERES_VITAL = "PROTECCION_INTERES_VITAL"
    INTERES_LEGITIMO = "INTERES_LEGITIMO"
    MISION_INTERES_PUBLICO = "MISION_INTERES_PUBLICO"

# ¤rat
class CategoriaTitular(str, Enum):
    CLIENTES = "CLIENTES"
    EMPLEADOS = "EMPLEADOS"
    PROVEEDORES = "PROVEEDORES"
    PACIENTES = "PACIENTES"
    MENORES_EDAD = "MENORES_EDAD"
    USUARIOS_WEB = "USUARIOS_WEB"

@dataclass
# ¤rat
class ActividadRAT:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    codigo: str = ""
    nombre: str = ""
    area_responsable: str = ""
    finalidad: str = ""
    base_legal: BaseLegitimacion = BaseLegitimacion.CONSENTIMIENTO
    categorias_titulares: List[CategoriaTitular] = field(default_factory=list)
    categorias_datos: List[str] = field(default_factory=list)
    datos_sensibles: bool = False
    volumen_titulares_estimado: int = 0
    transferencia_internacional: bool = False
    requiere_eipd: bool = False
    es_gran_escala: bool = False
    version: int = 1
    medio_soporte: str = ""
    encargados: List[str] = field(default_factory=list)
    destinatarios: List[str] = field(default_factory=list)
    pais_transferencia: str = ""
    plazo_conservacion: str = ""
    medidas_seguridad: List[str] = field(default_factory=list)
    nivel_riesgo: str = ""
    decisiones_automatizadas: bool = False
    volumen_titulares_12_meses: int = 0
    observaciones_dpo: str = ""
    origen: str = "manual"

# ¤rat
class EstadoEIPD(str, Enum):
    EN_PROGRESO = "EN_PROGRESO"
    ACTIVA = "ACTIVA"
    OBSOLETA_REQUIERE_ACTUALIZACION = "OBSOLETA_REQUIERE_ACTUALIZACION"

@dataclass
# ¤rat
class EIPD:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    rat_id: str = ""
    estado: EstadoEIPD = EstadoEIPD.EN_PROGRESO
    volumen_titulares_aprobacion: int = 0
    categorias_datos_aprobacion: List[str] = field(default_factory=list)


# ¤rat
# Metadatos locales de la sala: no crean tablas ni abren conexiones.
rat_actividades = Table(
    "rat_actividades", MetaData(),
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    *[Column(c, Text, nullable=False) for c in (
        "codigo", "nombre", "area_responsable", "finalidad", "base_legal",
        "medio_soporte", "pais_transferencia", "plazo_conservacion",
        "nivel_riesgo", "observaciones_dpo", "origen",
    )],
    *[Column(c, JSON, nullable=False) for c in (
        "categorias_titulares", "categorias_datos", "encargados",
        "destinatarios", "medidas_seguridad",
    )],
    *[Column(c, Boolean, nullable=False) for c in (
        "datos_sensibles", "transferencia_internacional", "requiere_eipd",
        "es_gran_escala", "decisiones_automatizadas",
    )],
    Column("volumen_titulares_estimado", Integer, nullable=False),
    Column("volumen_titulares_12_meses", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
)
