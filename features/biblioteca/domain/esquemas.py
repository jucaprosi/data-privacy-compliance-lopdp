# ¤adpa
# ¤¤developer-architect
"""Contratos del formulario por versión (BIB-201) y lectura de la plantilla como esquema de campos.

El esquema sale de los metadatos `variables_contexto` y `avisos` de la plantilla Markdown: datos, nunca
código. Los datos privados de la organización (valores de `contexto.*`) viven aparte, en la tabla de
borradores; aquí solo hay contratos y reglas puras.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from pydantic import Field
from features.biblioteca.domain.base import Contrato
from features.biblioteca.domain.plantillas_md import leer_metadatos, separar

Valor = str | list[str]
GENERADAS = {"contexto.actividades": "rat"}  # variables que el servidor genera y el usuario no escribe


# ¤adpa
class CampoContexto(Contrato):
    clave: str
    etiqueta: str
    tipo: Literal["texto", "si_no", "lista"] = "texto"
    obligatoria: bool = True
    origen: Literal["captura", "rat"] = "captura"


# ¤adpa
class AvisoActivo(Contrato):
    nivel: Literal["info", "alto"]
    texto: str
    cuando: str


# ¤adpa
class EntradaBorrador(Contrato):
    version_id: str = Field(min_length=1, max_length=36)
    fecha_emision: date | None = None
    contexto: dict[str, Valor] = Field(default_factory=dict, max_length=60)


# ¤adpa
class GuardarBorrador(Contrato):
    """`revision` es la que el cliente vio por última vez; una desfasada se rechaza con 409."""
    revision: int = Field(ge=1)
    fecha_emision: date | None = None
    contexto: dict[str, Valor] = Field(default_factory=dict, max_length=60)


# ¤adpa
class Borrador(Contrato):
    id: str
    version_id: str
    codigo: str
    plantilla_version: str
    fecha_emision: date
    contexto: dict[str, Valor]
    campos: list[CampoContexto]
    contenido_markdown: str
    variables_faltantes: list[str]
    avisos: list[AvisoActivo]
    revisable: bool
    revision: int
    creado_en: datetime
    actualizado_en: datetime


# ¤adpa
@dataclass(frozen=True)
class Plantilla:
    meta: dict
    cuerpo: str

    @property
    def codigo(self) -> str:
        return str(self.meta["codigo"])

    @property
    def version(self) -> str:
        return str(self.meta["version"])

    @property
    def campos(self) -> list[CampoContexto]:
        return [CampoContexto(
            clave=c["clave"], etiqueta=c.get("etiqueta", c["clave"]), tipo=c.get("tipo", "texto"),
            obligatoria=str(c.get("obligatoria", "true")).lower() != "false",
            origen=GENERADAS.get(c["clave"], "captura"),
        ) for c in self.meta.get("variables_contexto") or []]


# ¤adpa
def leer_plantilla(texto: str) -> Plantilla:
    """Separa metadatos y cuerpo. Lanza ValueError si la cabecera no es legible."""
    cabecera, cuerpo = separar(texto)
    return Plantilla(leer_metadatos(cabecera), cuerpo.strip("\n"))


# ¤adpa
def avisos_activos(plantilla: Plantilla, contexto: dict[str, Valor], con_dpd: bool) -> list[AvisoActivo]:
    """Avisos cuya condición se cumple; con la condición cumplida y sin DPD vigente el aviso sube a «alto»."""
    activos = []
    for aviso in plantilla.meta.get("avisos") or []:
        if contexto.get(aviso["cuando"]) != "si":
            continue
        nivel = aviso["nivel"] if con_dpd else "alto"
        activos.append(AvisoActivo(nivel=nivel, texto=aviso["texto"], cuando=aviso["cuando"]))
    return activos
