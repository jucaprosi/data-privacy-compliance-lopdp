"""Modelos de dominio del Módulo 2: RAT Maestro (Registro de Actividades de Tratamiento)."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid

def gen_id() -> str:
    return str(uuid.uuid4())

class BaseLegitimacion(str, Enum):
    CONSENTIMIENTO = "CONSENTIMIENTO"
    OBLIGACION_LEGAL = "OBLIGACION_LEGAL"
    CUMPLIMIENTO_CONTRATO = "CUMPLIMIENTO_CONTRATO"
    PROTECCION_INTERES_VITAL = "PROTECCION_INTERES_VITAL"
    INTERES_LEGITIMO = "INTERES_LEGITIMO"
    MISION_INTERES_PUBLICO = "MISION_INTERES_PUBLICO"

class CategoriaTitular(str, Enum):
    CLIENTES = "CLIENTES"
    EMPLEADOS = "EMPLEADOS"
    PROVEEDORES = "PROVEEDORES"
    PACIENTES = "PACIENTES"
    MENORES_EDAD = "MENORES_EDAD"
    USUARIOS_WEB = "USUARIOS_WEB"

@dataclass
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

class EstadoEIPD(str, Enum):
    EN_PROGRESO = "EN_PROGRESO"
    ACTIVA = "ACTIVA"
    OBSOLETA_REQUIERE_ACTUALIZACION = "OBSOLETA_REQUIERE_ACTUALIZACION"

@dataclass
class EIPD:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    rat_id: str = ""
    estado: EstadoEIPD = EstadoEIPD.EN_PROGRESO
    volumen_titulares_aprobacion: int = 0
    categorias_datos_aprobacion: List[str] = field(default_factory=list)

