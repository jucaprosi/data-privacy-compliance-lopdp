# ¤adpa
# ¤¤developer-architect
"""Mapas de captura/salida de las ocho fichas iniciales (BIB-208).

La fuente es el contrato propuesto del kit (`backlog_y_esquemas.json`, `template_form_schemas`): este
módulo solo lo lee y lo tipa. Cinco fichas se capturan en tabla (una fila por registro, salida en la
hoja «Registro» desde la fila 6) y tres por secciones (asistente, salida por bloques del Word).
Los mapas son v1.0-propuestos: no equivalen a maestros publicados ni a revisión jurídica.
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

_RAIZ = Path(__file__).resolve().parents[3]
ESQUEMAS_KIT = _RAIZ / "data/biblioteca/kit_v1/especificacion/backlog_y_esquemas.json"

TABULARES = ("INV-01", "INV-02", "RAT-01", "LEG-01", "PLA-01")
POR_SECCIONES = ("EIPD-00", "AVI-01", "PRO-01")
CODIGOS = TABULARES + POR_SECCIONES

Modo = Literal["tabla", "secciones"]
Requisito = Literal["O", "C", "D"]


# ¤adpa
@dataclass(frozen=True)
class CampoMapa:
    clave: str
    etiqueta: str
    tipo: str
    requisito: Requisito
    valores: tuple[str, ...]
    regla: str
    editable: bool
    hoja: str | None = None
    columna: str | None = None
    primera_fila: int | None = None
    seccion: str | None = None
    token: str | None = None


# ¤adpa
@dataclass(frozen=True)
class MapaFicha:
    codigo: str
    modo: Modo
    version_esquema: str
    plantilla: str
    interfaz: str
    campos: tuple[CampoMapa, ...]
    colecciones: dict
    validaciones: tuple[str, ...]
    estado_generacion: str

    def campo(self, clave: str) -> CampoMapa | None:
        return next((c for c in self.campos if c.clave == clave), None)

    @property
    def secciones(self) -> tuple[str, ...]:
        vistas: list[str] = []
        for c in self.campos:
            if c.seccion and c.seccion not in vistas:
                vistas.append(c.seccion)
        return tuple(vistas)


def _campo(crudo: dict) -> CampoMapa:
    salida = crudo.get("output")
    tabla = salida if isinstance(salida, dict) else {}
    return CampoMapa(
        clave=crudo["key"], etiqueta=crudo.get("label") or crudo["key"].replace("_", " ").capitalize(),
        tipo=crudo["type"], requisito=crudo["requirement"], valores=tuple(crudo.get("allowed_values") or ()),
        regla=crudo.get("condition_or_validation") or crudo.get("validation") or "",
        editable=bool(crudo.get("editable", True)), hoja=tabla.get("sheet"), columna=tabla.get("column"),
        primera_fila=tabla.get("first_data_row"), seccion=crudo.get("section"), token=crudo.get("legacy_token"),
    )


# ¤adpa
@lru_cache(maxsize=1)
def mapas() -> dict[str, MapaFicha]:
    datos = json.loads(ESQUEMAS_KIT.read_text(encoding="utf-8"))
    leidos: dict[str, MapaFicha] = {}
    for esquema in datos["template_form_schemas"]:
        codigo = esquema["code"]
        leidos[codigo] = MapaFicha(
            codigo=codigo, modo="tabla" if codigo in TABULARES else "secciones",
            version_esquema=esquema["schema_version"], plantilla=esquema["source_template"],
            interfaz=esquema["ui"], campos=tuple(_campo(c) for c in esquema["fields"]),
            colecciones=esquema.get("canonical_collections") or {},
            validaciones=tuple(esquema.get("business_validations") or ()),
            estado_generacion=esquema.get("generation_state", ""),
        )
    if set(leidos) != set(CODIGOS):
        raise ValueError(f"El kit no trae las ocho fichas esperadas: {sorted(leidos)}")
    return leidos


# ¤adpa
def mapa(codigo: str) -> MapaFicha | None:
    return mapas().get(codigo)
