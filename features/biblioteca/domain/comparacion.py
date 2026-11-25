# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada
# ¤¤developer-architect
"""BIB-407: comparación pura de una versión con la publicada del mismo código (sin base ni red)."""
from datetime import date
from typing import Callable

from pydantic import BaseModel, Field

ESTADO_BASE = "publicada"


# ¤adpa
class CitaCambio(BaseModel):
    clave: str
    norma: str | None = None
    articulo: str | None = None
    url: str | None = None
    verificada: bool = False
    fecha_vigencia: date | None = None


# ¤adpa
class CambioSeccion(BaseModel):
    antes: str
    despues: str
    cita: CitaCambio | None = None


# ¤adpa
class SeccionComparada(BaseModel):
    titulo: str
    cambiada: bool
    cambios: list[CambioSeccion] = Field(default_factory=list)
    texto: str | None = None  # el texto completo de la sección cuando es la primera versión (R1)


# ¤adpa
class Comparacion(BaseModel):
    primera_version: bool
    secciones: list[SeccionComparada] = Field(default_factory=list)


# ¤adpa
def secciones(cuerpo: str) -> list[tuple[str, str]]:
    """Parte el cuerpo por encabezados `##` (R2). Lo anterior al primero va con título vacío."""
    partes: list[tuple[str, list[str]]] = [("", [])]
    for linea in (cuerpo or "").split("\n"):
        if linea.startswith("## "):
            partes.append((linea[3:].strip(), []))
        else:
            partes[-1][1].append(linea)
    return [(titulo, "\n".join(lineas).strip()) for titulo, lineas in partes
            if titulo or "\n".join(lineas).strip()]


# ¤adpa
def elegir_base(versiones: list[dict], identificador: str) -> dict | None:
    """R1: la base es la versión publicada del mismo código, distinta de la comparada."""
    return next((v for v in versiones if v["estado"] == ESTADO_BASE and v["id"] != identificador), None)


# ¤adpa
def resolver_cita(clave: str | None, citas: dict, vigencia: Callable[[str], date | None]) -> CitaCambio | None:
    """R3: la clave de `cambios_ia` resuelta contra citas.json: norma, artículo, URL y si está verificada."""
    if not clave:
        return None
    fuente = citas.get("fuentes", {})
    norma = citas.get("fuente_de", {}).get(clave)
    url = fuente.get(norma, {}).get("url") if norma else None
    articulo = clave.split("-art-", 1)[1] if "-art-" in clave else None
    return CitaCambio(clave=clave, norma=norma, articulo=articulo, url=url,
                      verificada=citas.get("estados", {}).get(clave) == "verificada",
                      fecha_vigencia=vigencia(url) if url else None)


# ¤adpa
def comparar(base: str | None, cuerpo: str, cambios_ia: list[dict] | None, citas: dict,
             vigencia: Callable[[str], date | None] = lambda url: None) -> Comparacion:
    """R1 a R3. Sin base: primera versión, con el texto completo y sin cambios."""
    nuevas = secciones(cuerpo)
    if base is None:
        return Comparacion(primera_version=True, secciones=[
            SeccionComparada(titulo=t, cambiada=False, texto=x) for t, x in nuevas])
    previas = dict(secciones(base))
    titulos = [t for t, _ in nuevas] + [t for t in previas if t not in dict(nuevas)]
    actuales = dict(nuevas)
    resultado = []
    for titulo in titulos:
        antes, despues = previas.get(titulo, ""), actuales.get(titulo, "")
        if antes == despues:
            resultado.append(SeccionComparada(titulo=titulo, cambiada=False))
            continue
        cambios = []
        if cambios_ia is not None:  # versión de la IA: cada cambio con su cita (R3)
            cambios = [CambioSeccion(antes=c.get("antes", ""), despues=c.get("despues", ""),
                                     cita=resolver_cita(c.get("cita"), citas, vigencia))
                       for c in cambios_ia
                       if (c.get("antes") and c["antes"] in antes) or (c.get("despues") and c["despues"] in despues)]
        if not cambios:  # versión cargada a mano, o sección sin cambio declarado: la cita va nula
            cambios = [CambioSeccion(antes=antes, despues=despues)]
        resultado.append(SeccionComparada(titulo=titulo, cambiada=True, cambios=cambios))
    return Comparacion(primera_version=False, secciones=resultado)
