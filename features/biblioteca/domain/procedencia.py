# ¤adpa
# ¤¤developer-architect
"""Procedencia por campo de los datos reutilizados (BIB-202): reglas puras, sin base de datos ni red.

Cada valor precargado conserva de dónde sale (fuente e ID), su revisión, su fecha y su estado de
validación. Si la fuente no lleva historial ni versión, no se inventa ninguna: la revisión queda vacía,
se declara la limitación y la huella del valor (sha256) con la fecha de lectura hace de instantánea.
"""
import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal
from pydantic import Field
from features.biblioteca.domain.base import Contrato

TipoFuente = Literal["organizacion", "dpd", "rat", "diagnostico"]
EstadoValidacion = Literal["validado", "sin_validar"]
SIN_HISTORIAL = ("La fuente no guarda historial ni versión: se conserva la huella sha256 del valor y la "
                 "fecha de lectura; no hay revisión de origen.")
MARCA_INSTANTANEA = "instantanea_procedencia"
MARCA_PROPUESTA = "propuesta_correccion"


# ¤adpa
@dataclass(frozen=True)
class RegistroFuente:
    """Un registro canónico leído por la compuerta de su sala; Biblioteca no lo escribe nunca."""
    fuente: TipoFuente
    fuente_id: str
    valores: Mapping[str, object]
    revision: str | None = None
    fecha: datetime | date | None = None
    validador: str | None = None
    leido_en: datetime | None = None
    prefijo: str = ""
    extra: Mapping[str, object] = field(default_factory=dict)


# ¤adpa
class OrigenCampo(Contrato):
    clave: str
    valor: str
    fuente: TipoFuente
    fuente_id: str
    revision: str | None
    fecha: str | None
    validador: str | None
    estado: EstadoValidacion
    limitacion: str | None = None
    huella: str


# ¤adpa
class Instantanea(Contrato):
    documento_id: str | None = None
    revision_documento: int | None = None
    campos: list[OrigenCampo]
    sha256: str
    tomada_en: datetime | None = None


# ¤adpa
class CambioFuente(Contrato):
    clave: str
    emitido: str | None
    actual: str | None


# ¤adpa
class AvisoCambios(Contrato):
    documento_id: str
    cambiado: bool
    cambios: list[CambioFuente]
    emitida: Instantanea
    actual: Instantanea


# ¤adpa
class EntradaPropuesta(Contrato):
    clave: str = Field(min_length=1, max_length=200)
    valor_propuesto: str = Field(min_length=1, max_length=2000)
    motivo: str = Field(min_length=3, max_length=1000)


# ¤adpa
class PropuestaCorreccion(Contrato):
    documento_id: str
    clave: str
    valor_canonico: str
    valor_propuesto: str
    motivo: str
    estado: Literal["propuesto"] = "propuesto"
    fuente: TipoFuente
    fuente_id: str


# ¤adpa
def a_texto(valor: object) -> str:
    """Forma canónica de un valor para mostrarlo y para la huella."""
    if valor is None:
        return ""
    if isinstance(valor, (list, tuple)):
        return "; ".join(t for t in (a_texto(v) for v in valor) if t)
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return str(getattr(valor, "value", valor)).strip()


# ¤adpa
def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ¤adpa
def origenes(registros: Iterable[RegistroFuente]) -> list[OrigenCampo]:
    """Un origen por valor realmente existente; un valor vacío no se precarga ni se inventa."""
    campos: list[OrigenCampo] = []
    for r in registros:
        fecha = r.fecha or r.leido_en
        for clave, bruto in r.valores.items():
            valor = a_texto(bruto)
            if not valor:
                continue
            campos.append(OrigenCampo(
                clave=r.prefijo + clave, valor=valor, fuente=r.fuente, fuente_id=r.fuente_id,
                revision=r.revision, fecha=a_texto(fecha) or None, validador=r.validador,
                estado="validado" if r.validador else "sin_validar",
                limitacion=None if r.revision else SIN_HISTORIAL, huella=_sha(valor)))
    return sorted(campos, key=lambda c: c.clave)


# ¤adpa
def huella(campos: Iterable[OrigenCampo]) -> str:
    """sha256 determinista de clave, valor, fuente y revisión (el orden de entrada no importa)."""
    filas = sorted([c.clave, c.valor, c.fuente, c.fuente_id, c.revision or ""] for c in campos)
    return _sha(json.dumps(filas, ensure_ascii=False, separators=(",", ":")))


# ¤adpa
def instantanea(campos: list[OrigenCampo], documento_id: str | None = None, revision: int | None = None,
                tomada_en: datetime | None = None) -> Instantanea:
    return Instantanea(documento_id=documento_id, revision_documento=revision, campos=campos,
                       sha256=huella(campos), tomada_en=tomada_en)


# ¤adpa
def comparar(emitida: Instantanea, actuales: list[OrigenCampo]) -> list[CambioFuente]:
    """Campos cuyo valor canónico difiere del emitido; la instantánea emitida no se toca."""
    antes = {c.clave: c.valor for c in emitida.campos}
    ahora = {c.clave: c.valor for c in actuales}
    return [CambioFuente(clave=k, emitido=antes.get(k), actual=ahora.get(k))
            for k in sorted(antes.keys() | ahora.keys()) if antes.get(k) != ahora.get(k)]
