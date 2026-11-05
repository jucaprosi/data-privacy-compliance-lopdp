# ¤adpa
# ¤¤developer-architect
"""Evaluación de una captura contra el mapa de su ficha (BIB-208): reglas puras, sin BD.

- Campos «D» los pone el servidor: un ID estable se asigna si falta y se conserva al regenerar; el resto
  (calculados y control) se rechaza si llega del cliente.
- «O» vacío y «C» que aplica sin valor son pendientes explícitos: la ficha no queda aceptada.
- Fechas reales (AAAA-MM-DD); un texto o «0» es pendiente, nunca una fecha válida.
- La salida solo lleva valores de filas reales: sin ejemplos, instrucciones ni filas vacías.
- Las reglas específicas de AVI, EIPD y PRO viven en `secciones.py`.
"""
import re
from datetime import date
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from app_core.errors import ErrorNegocio
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca
from features.biblioteca.plantillas.mapas import CampoMapa, MapaFicha

Valor = str | list[str] | None
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NO_APLICA = re.compile(r"^no aplica\s*[:\-–]\s*\S", re.IGNORECASE)
MAX_FILAS = 500


# ¤adpa
class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ¤adpa
class EntradaFicha(_Modelo):
    """`version_anterior` indica regeneración: se emite la siguiente y la anterior queda intacta."""
    filas: list[dict[str, Valor]] = Field(default_factory=list, max_length=MAX_FILAS)
    valores: dict[str, Valor] = Field(default_factory=dict, max_length=120)
    colecciones: dict[str, list[dict[str, Valor]]] = Field(default_factory=dict, max_length=10)
    condiciones: dict[str, bool] = Field(default_factory=dict, max_length=20)
    version_anterior: int | None = Field(default=None, ge=1)


# ¤adpa
class Pendiente(_Modelo):
    campo: str
    motivo: str
    fila: int | None = None


# ¤adpa
class Celda(_Modelo):
    hoja: str
    fila: int
    columna: str
    clave: str
    valor: str


# ¤adpa
class Bloque(_Modelo):
    seccion: str
    clave: str
    valor: str
    indice: int | None = None


# ¤adpa
class ResultadoFicha(_Modelo):
    codigo: str
    modo: Literal["tabla", "secciones"]
    version_esquema: str
    version: int
    aceptada: bool
    pendientes: list[Pendiente]
    ids: list[str] = Field(default_factory=list)
    celdas: list[Celda] = Field(default_factory=list)
    bloques: list[Bloque] = Field(default_factory=list)
    omitidos: list[str] = Field(default_factory=list)
    anexo: list[str] = Field(default_factory=list)
    recomendacion: str | None = None
    estado_generacion: str


# ¤adpa
class ContextoServidor(_Modelo):
    organizacion_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    fecha: date


# ¤adpa
def vacio(valor: Valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, list):
        return not [v for v in valor if str(v).strip()]
    return not str(valor).strip()


# ¤adpa
def texto(valor: Valor) -> str:
    return "; ".join(str(v).strip() for v in valor if str(v).strip()) if isinstance(valor, list) else str(valor).strip()


# ¤adpa
def fecha_real(valor: Valor) -> bool:
    if not isinstance(valor, str) or not FECHA.match(valor):
        return False
    try:
        date.fromisoformat(valor)
    except ValueError:
        return False
    return True


# ¤adpa
def es_servidor(campo: CampoMapa) -> bool:
    return campo.requisito == "D"


# ¤adpa
def rechazar_servidor(campo: CampoMapa, valor: Valor) -> None:
    if not vacio(valor):
        raise ErrorNegocio("BIB_FICHA_INICIAL_CAMPO_SERVIDOR", detail=f"«{campo.clave}» lo asigna el servidor.")


# ¤adpa
def exigir_conocidos(mapa: MapaFicha, claves, extra: tuple[str, ...] = ()) -> None:
    validas = {c.clave for c in mapa.campos} | set(extra)
    desconocidas = sorted(set(claves) - validas)
    if desconocidas:
        raise ErrorNegocio("BIB_FICHA_INICIAL_CAMPO_DESCONOCIDO", detail=f"Campos no definidos: {', '.join(desconocidas)}.")


# ¤adpa
def revisar_valor(campo: CampoMapa, valor: Valor, fila: int | None, aplica: bool,
                  tratamientos: frozenset[str] | None) -> list[Pendiente]:
    """Pendientes de un campo editable. `aplica` indica si un «C» es exigible en este contexto."""
    if vacio(valor):
        if campo.requisito == "O":
            return [Pendiente(campo=campo.clave, fila=fila, motivo="Obligatorio antes de generar para revisión.")]
        if aplica:
            return [Pendiente(campo=campo.clave, fila=fila, motivo=campo.regla or "Condicional que aplica: complételo.")]
        return []
    plano = texto(valor)
    if plano.lower() == "no aplica" and campo.requisito == "C":
        return [Pendiente(campo=campo.clave, fila=fila, motivo="«No aplica» necesita su motivo (No aplica: …).")]
    if campo.valores and plano not in campo.valores:
        return [Pendiente(campo=campo.clave, fila=fila, motivo=f"Valor no permitido; opciones: {', '.join(campo.valores)}.")]
    if campo.tipo == "date" and not fecha_real(valor):
        return [Pendiente(campo=campo.clave, fila=fila, motivo="Fecha inválida: use AAAA-MM-DD real.")]
    if campo.clave in ("tratamiento_id", "tratamiento_ids"):
        referencias = valor if isinstance(valor, list) else [plano]
        if tratamientos is None:
            return [Pendiente(campo=campo.clave, fila=fila, motivo="No se pudo verificar el tratamiento en el RAT.")]
        ajenas = [r for r in referencias if r not in tratamientos]
        if ajenas:
            return [Pendiente(campo=campo.clave, fila=fila, motivo="Tratamiento inexistente en el RAT de la organización.")]
    return []


def _id_estable(valor: Valor) -> str:
    if vacio(valor):
        return str(uuid4())
    try:
        return str(UUID(texto(valor)))
    except ValueError as exc:
        raise ErrorNegocio("BIB_FICHA_INICIAL_CAMPO_SERVIDOR",
                           detail="El ID lo genera el servidor; solo se reenvía el que ya asignó.") from exc


# ¤adpa
def evaluar_tabla(mapa: MapaFicha, entrada: EntradaFicha, tratamientos: frozenset[str] | None) -> ResultadoFicha:
    """INV-01, INV-02, RAT-01 y LEG-01: una fila por registro, salida hasta la última fila real."""
    if mapa.codigo == "PLA-01":
        raise ErrorNegocio("BIB_FICHA_INICIAL_SOLO_LECTURA")
    pendientes: list[Pendiente] = []
    celdas: list[Celda] = []
    ids: list[str] = []
    id_campo = next(c for c in mapa.campos if es_servidor(c) and c.tipo == "uuid")
    if not entrada.filas:
        pendientes.append(Pendiente(campo="filas", motivo="La ficha necesita al menos un registro."))
    for indice, fila in enumerate(entrada.filas):
        exigir_conocidos(mapa, fila)
        numero = indice + 1
        identificador = _id_estable(fila.get(id_campo.clave))
        ids.append(identificador)
        for campo in mapa.campos:
            valor: Valor = identificador if campo is id_campo else fila.get(campo.clave)
            if campo is not id_campo and es_servidor(campo):
                rechazar_servidor(campo, valor)
                continue
            if campo is not id_campo:
                pendientes += revisar_valor(campo, valor, numero, campo.requisito == "C", tratamientos)
            if not vacio(valor) and campo.hoja and campo.columna and campo.primera_fila:
                celdas.append(Celda(hoja=campo.hoja, fila=campo.primera_fila + indice, columna=campo.columna,
                                    clave=campo.clave, valor=texto(valor)))
    if len(set(ids)) != len(ids):
        pendientes.append(Pendiente(campo=id_campo.clave, motivo="Dos filas comparten el mismo ID."))
    return ResultadoFicha(
        codigo=mapa.codigo, modo="tabla", version_esquema=mapa.version_esquema,
        version=(entrada.version_anterior or 0) + 1, aceptada=not pendientes, pendientes=pendientes,
        ids=ids, celdas=celdas, estado_generacion=mapa.estado_generacion,
    )
