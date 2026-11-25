# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada
# ¤¤developer-architect
"""BIB-406: reglas puras de las propuestas de la IA (sin base, sin red, sin inferencia).

La IA figura en `autores` con el valor fijo `"ia"`, que no es un usuario (R3, R6).
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app_core.errors import CodigoErrorNegocio
from features.biblioteca.domain.base import Contrato
from features.biblioteca.domain import editorial as _editorial
from features.biblioteca.domain.errores import registrar

AUTOR_IA = "ia"
AUTORES_IA = [AUTOR_IA]
ORIGEN_RESOLUCION, ORIGEN_PETICION = "resolucion", "peticion"
ESTADOS_QUE_PROPONEN = frozenset({"reformada", "derogada"})
SIN_CAMBIOS, CREADA, EN_REVISION = "sin_cambios", "creada", "propuesta_en_revision"

# === BIB-406 ===
registrar(
    CodigoErrorNegocio("BIB_VERSION_IA_NO_EDITABLE", 409,
                       "Una versión redactada por la IA no se edita: devuélvela con observaciones o descártala."),
    CodigoErrorNegocio("BIB_NOTA_DESCARTE_REQUERIDA", 422, "Para descartar una versión escribe una nota."),
    CodigoErrorNegocio("BIB_PROPUESTA_NO_DISPONIBLE", 503,
                       "Las propuestas de la IA no están disponibles en este entorno."),
    CodigoErrorNegocio("BIB_PROPUESTA_EN_REVISION", 409, "Ya hay una propuesta en revisión para esta plantilla."),
    CodigoErrorNegocio("BIB_SIN_PUBLICADA", 409, "La plantilla no tiene una versión publicada de la que partir."),
)
# === fin BIB-406 ===


# ¤adpa
class CambioIA(BaseModel):
    seccion: str = Field(min_length=1, max_length=300)
    antes: str = Field(min_length=1, max_length=20_000)
    despues: str = Field(max_length=20_000)
    cita: str = Field(min_length=1, max_length=200)


# ¤adpa
class SalidaPropuestaIA(BaseModel):
    """Esquema que devuelve la inferencia: los cambios por sección, cada uno con su clave de cita."""
    cambios: list[CambioIA] = Field(default_factory=list, max_length=50)


# ¤adpa
class PedirPropuesta(Contrato):
    codigo: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    motivo: str = Field(min_length=1, max_length=4000)


# ¤adpa
class Descarte(Contrato):
    nota: str = Field(max_length=4000)
    generacion: int = Field(ge=1)


# ¤adpa
class VersionMaestraMd(_editorial.VersionMaestraMd):
    """La versión editorial con su origen (persona o IA) y el nombre de quien la pidió.

    Conserva el nombre del esquema de la API (contrato congelado): solo añade propiedades.
    """
    redactada_por: Literal["persona", "ia"] = "persona"
    modelo_ia: str | None = None
    origen_ia: Literal["resolucion", "peticion"] | None = None
    id_resolucion: str | None = None
    motivo_ia: str | None = None
    cambios_ia: list[dict] | None = None
    nota_descarte: str | None = None
    descartada_por: str | None = None
    descartada_en: datetime | None = None
    solicitante_nombre: str | None = None
    leyenda: dict | None = None  # BIB-410: redacción y aprobación; nula sin aprobación registrada


# ¤adpa
class VistaEditorialMd(_editorial.VistaEditorialMd):
    versiones: list[VersionMaestraMd]


VersionMaestraIA, VistaEditorialIA = VersionMaestraMd, VistaEditorialMd


# ¤adpa
class ResultadoPropuesta(Contrato):
    resultado: Literal["creada", "sin_cambios", "propuesta_en_revision"]
    versiones: list[VersionMaestraMd] = Field(default_factory=list)
    omitidas: list[str] = Field(default_factory=list)


# ¤adpa
def debe_proponer(estado: str, estado_anterior: str | None) -> bool:
    """R1: el estado anterior lo pasa quien llama (NORM-07); la biblioteca no lee el historial normativo.

    Reconfirmar el mismo estado no propone; la primera revisión solo propone si es `reformada` o `derogada`;
    `vigente` propone desde un estado distinto.
    """
    if estado == estado_anterior:
        return False
    if estado in ESTADOS_QUE_PROPONEN:
        return True
    return estado == "vigente" and estado_anterior is not None


# ¤adpa
def plantillas_afectadas(citas: dict, url_fuente: str) -> list[str]:
    """R1: las plantillas con alguna cita cuya fuente tiene la misma URL oficial que la resolución."""
    fuentes = {clave for clave, fuente in citas.get("fuentes", {}).items() if fuente.get("url") == url_fuente}
    fuente_de = citas.get("fuente_de", {})
    return sorted(codigo for codigo, claves in citas.get("plantillas", {}).items()
                  if any(fuente_de.get(clave) in fuentes for clave in claves))


# ¤adpa
def aplicar_cambios(cuerpo: str, cambios: list[CambioIA], citas: dict) -> tuple[str, list[dict]]:
    """R2: aplica solo los cambios con cita `verificada` cuyo texto `antes` está una vez en el cuerpo.

    Devuelve el cuerpo nuevo y los cambios que entraron; sin ninguno, el cuerpo vuelve igual.
    """
    estados = citas.get("estados", {})
    aplicados: list[dict] = []
    for cambio in cambios:
        if estados.get(cambio.cita) != "verificada":
            continue
        if cambio.antes == cambio.despues or cuerpo.count(cambio.antes) != 1:
            continue
        cuerpo = cuerpo.replace(cambio.antes, cambio.despues)
        aplicados.append(cambio.model_dump())
    return cuerpo, aplicados


# ¤adpa
def version_siguiente(version: str) -> str:
    """Sube el parche: 0.2.1 -> 0.2.2; 1.0 -> 1.0.1."""
    partes = version.split(".")
    if len(partes) == 2:
        return f"{version}.1"
    return ".".join(partes[:2] + [str(int(partes[2]) + 1)])


# ¤adpa
def con_version(cuerpo: str, anterior: str, nueva: str) -> str:
    """El cuerpo MD declara su versión en los metadatos: la nueva versión la declara también."""
    linea = f"\nversion: {anterior}\n"
    return cuerpo.replace(linea, f"\nversion: {nueva}\n", 1) if linea in cuerpo else cuerpo
