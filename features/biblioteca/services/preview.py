# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Vista previa y fidelidad (BIB-206).

La vista previa sale de la misma instantánea (`tomar_instantanea`) y del mismo modelo de salida
(`separar_guia` → `rellenar` → `preparar` → `bloques`) que el archivo de BIB-205, y además calcula con
`construir` la huella exacta del archivo que se emitiría. Lleva la revisión del borrador y la huella de la
instantánea: si el borrador se edita, cualquiera de las dos cambia y la vista previa anterior queda
obsoleta (`BIB_PREVIEW_OBSOLETA`); emitir desde ella se rechaza.
Previsualizar no genera, no aprueba ni cierra ninguna acción.
"""
from collections.abc import Mapping
from typing import Literal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.base import Contrato
from features.biblioteca.domain.esquemas import Plantilla, leer_plantilla
from features.biblioteca.domain.generacion import (
    ESTADOS, Formato, Generacion, InstantaneaGeneracion, Modo, PedirGeneracion,
)
from features.biblioteca.services.borradores import FuentesDatos
from features.biblioteca.services.generacion import _fijar_contexto, construir, generar, huella_bytes, tomar_instantanea
from features.biblioteca.services.rellenado import rellenar
from features.biblioteca.services.salida import bloques, preparar, residuos, separar_guia
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

BORRADOR = ("SELECT id, version_id, contexto, fecha_emision, plantilla_md, plantilla_sha256, revision "
            "FROM biblioteca_borradores WHERE id=:id")
BLOQUEAR = BORRADOR + " FOR UPDATE"


# ¤adpa
class BloqueVista(Contrato):
    tipo: Literal["titulo", "parrafo", "lista", "cita", "tabla"]
    texto: str = ""
    nivel: int = 0
    filas: list[list[str]] = []


# ¤adpa
class VistaPrevia(Contrato):
    borrador_id: str
    revision: int
    modo: Modo
    formato: Formato
    estado: Literal["borrador", "para_revision"]
    plantilla_sha256: str
    instantanea_sha256: str
    archivo_sha256: str
    nombre_archivo: str
    faltantes: list[str]
    bloques: list[BloqueVista]


# ¤adpa
class EmitirDesdeVista(Contrato):
    modo: Modo
    formato: Formato
    revision: int
    instantanea_sha256: str


# ¤adpa
def modelo_de_salida(instantanea: InstantaneaGeneracion, pedido: PedirGeneracion) -> list[BloqueVista]:
    """Bloques que entran en el archivo, por el mismo camino que `construir`."""
    datos = instantanea.como_dict()
    plantilla = leer_plantilla(datos["plantilla_md"])
    uso, _ = separar_guia(plantilla.cuerpo)
    contenido, faltantes = rellenar(Plantilla(plantilla.meta, uso), datos["organizacion"], datos["contexto"])
    opcionales = {c["clave"] for c in datos["esquema"] if not c.get("obligatoria", True)}
    texto, _ = preparar(contenido, faltantes, opcionales, pedido.modo == "borrador")
    if pedido.modo != "borrador" and residuos(texto):
        raise ErrorNegocio("BIB_GEN_SALIDA_INVALIDA", "Quedan marcas: " + " ".join(residuos(texto)))
    return [BloqueVista(tipo=b.tipo, texto=b.texto, nivel=b.nivel, filas=b.filas) for b in bloques(texto)]


# ¤adpa
def vista_de(instantanea: InstantaneaGeneracion, pedido: PedirGeneracion, borrador_id: str,
             revision: int) -> VistaPrevia:
    """Vista previa pura; `construir` valida igual que al emitir y da la huella del archivo."""
    archivo, faltantes, nombre = construir(instantanea, pedido)
    return VistaPrevia(
        borrador_id=borrador_id, revision=revision, modo=pedido.modo, formato=pedido.formato,
        estado=ESTADOS[pedido.modo], plantilla_sha256=instantanea.plantilla_sha256,
        instantanea_sha256=instantanea.sha256, archivo_sha256=huella_bytes(archivo), nombre_archivo=nombre,
        faltantes=faltantes, bloques=modelo_de_salida(instantanea, pedido))


# ¤adpa
async def _borrador(session: AsyncSession, borrador_id: str, bloquear: bool = False) -> Mapping:
    fila = (await session.execute(text(BLOQUEAR if bloquear else BORRADOR), {"id": borrador_id})).mappings().first()
    if fila is None:  # la RLS oculta los de otra organización
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")
    return fila


# ¤adpa
async def previsualizar(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                        borrador_id: str, pedido: PedirGeneracion) -> VistaPrevia:
    await _fijar_contexto(session, tenant_id, actor)
    fila = await _borrador(session, borrador_id)
    instantanea = await tomar_instantanea(session, fuentes, tenant_id, fila)
    return vista_de(instantanea, pedido, borrador_id, fila["revision"])


# ¤adpa
def exigir_vigente(vista: VistaPrevia, revision: int, instantanea_sha256: str) -> None:
    """Una vista previa de otra revisión u otros datos ya no representa el archivo."""
    if vista.revision != revision or vista.instantanea_sha256 != instantanea_sha256:
        raise ErrorNegocio("BIB_PREVIEW_OBSOLETA")


# ¤adpa
async def emitir_desde_vista(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                             borrador_id: str, pedido: EmitirDesdeVista) -> Generacion:
    """Genera el archivo solo si la vista previa que vio el usuario sigue vigente."""
    await _fijar_contexto(session, tenant_id, actor)
    fila = await _borrador(session, borrador_id, bloquear=True)
    salida = PedirGeneracion(modo=pedido.modo, formato=pedido.formato)
    actual = vista_de(await tomar_instantanea(session, fuentes, tenant_id, fila), salida, borrador_id,
                      fila["revision"])
    exigir_vigente(actual, pedido.revision, pedido.instantanea_sha256)
    generada = await generar(session, fuentes, tenant_id, actor, borrador_id, salida)
    if generada.instantanea_sha256 != actual.instantanea_sha256 or generada.archivo_sha256 != actual.archivo_sha256:
        raise ErrorNegocio("BIB_PREVIEW_OBSOLETA")
    return generada


__all__ = ["BloqueVista", "VistaPrevia", "EmitirDesdeVista", "modelo_de_salida", "vista_de", "previsualizar",
           "exigir_vigente", "emitir_desde_vista"]
