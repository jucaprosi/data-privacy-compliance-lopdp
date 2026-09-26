# ¤¤modelos-regulacion-rag
"""Modelos de dominio del Módulo de Regulación como Código y Copiloto RAG."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class TipoNorma(str, Enum):
    CONSTITUCION = "CONSTITUCION"
    LEY_ORGANICA = "LEY_ORGANICA"
    REGLAMENTO_GENERAL = "REGLAMENTO_GENERAL"
    RESOLUCION_SPDP = "RESOLUCION_SPDP"
    GUIA_OFICIAL = "GUIA_OFICIAL"
    ESTANDAR_TECNICO = "ESTANDAR_TECNICO"

@dataclass
class UnidadNormativa:
    id: str
    tipo: TipoNorma
    emisor: str
    numero_o_titulo: str
    articulo_o_seccion: str
    texto_oficial: str
    vigente: bool = True
    fecha_vigencia: str = ""
    fuente_url: str = ""
    version: str = ""
    es_resumen: bool = False
    palabras_clave: tuple[str, ...] = ()
    titulo: str = ""

@dataclass
class ConsultaRAGInput:
    pregunta: str
    tenant_id: str

@dataclass
class RespuestaRAGOutput:
    respuesta: str
    citas_normativas: List[str]
    confianza: float
    fuente_oficial_verificada: bool
