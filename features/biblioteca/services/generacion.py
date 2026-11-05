# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Generación de Word y Excel desde un borrador (BIB-205).

1. Se toma una instantánea del borrador: plantilla íntegra y su huella, esquema, valores de la
   organización (por `FuentesDatos`, como BIB-201) y respuestas del formulario.
2. `construir` calcula el archivo solo desde la instantánea: es determinista.
3. Modo borrador: admite faltantes, marca BORRADOR y los lista. Modo revisión: exige obligatorios y
   condicionales y rechaza cualquier marca sin resolver.
4. Se guarda instantánea, checksum, archivo y estado en `biblioteca_generaciones` (solo inserción, RLS).
Generar un archivo no aprueba el documento ni cierra ninguna acción.
"""
import hashlib
import json
from collections.abc import Mapping
from datetime import date
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.domain.esquemas import GENERADAS, Plantilla, leer_plantilla
from features.biblioteca.domain.generacion import (
    ESTADOS, MIME, Generacion, Guia, InstantaneaGeneracion, PedirGeneracion,
)
from features.biblioteca.services.borradores import FuentesDatos
from features.biblioteca.services.generador_docx import generar_docx
from features.biblioteca.services.generador_xlsx import generar_xlsx
from features.biblioteca.services.rellenado import (
    datos_de_tratamiento, datos_del_documento, fichas_de_actividades, rellenar,
)
from features.biblioteca.services.salida import bloques, preparar, residuos, separar_guia
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

COLUMNAS = ("id, borrador_id, modo, formato, estado, plantilla_sha256, instantanea_sha256, archivo_sha256, "
            "nombre_archivo, bytes, faltantes, creado_en")
LISTAR = f"SELECT {COLUMNAS} FROM biblioteca_generaciones WHERE borrador_id=:b ORDER BY creado_en DESC, id"
LEER = f"SELECT {COLUMNAS} FROM biblioteca_generaciones WHERE id=:id"
ARCHIVO = "SELECT formato, nombre_archivo, archivo, archivo_sha256 FROM biblioteca_generaciones WHERE id=:id"
BORRADOR = ("SELECT id, version_id, contexto, fecha_emision, plantilla_md, plantilla_sha256 "
            "FROM biblioteca_borradores WHERE id=:id")
INSERTAR = ("INSERT INTO biblioteca_generaciones(id, tenant_id, borrador_id, modo, formato, estado, plantilla_sha256, "
            "instantanea, instantanea_sha256, archivo, archivo_sha256, bytes, faltantes, nombre_archivo, creado_por) "
            "VALUES (:id, :t, :b, :modo, :formato, :estado, :psha, CAST(:inst AS jsonb), :isha, :archivo, :asha, "
            ":bytes, CAST(:faltan AS jsonb), :nombre, :u)")


# ¤adpa
async def _fijar_contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": actor})


# ¤adpa
async def _borrador(session: AsyncSession, borrador_id: str) -> Mapping:
    fila = (await session.execute(text(BORRADOR), {"id": borrador_id})).mappings().first()
    if fila is None:  # la RLS oculta los de otra organización
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")
    return fila


# ¤adpa
async def tomar_instantanea(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str,
                            fila: Mapping) -> InstantaneaGeneracion:
    """Mismos valores que ve el editor de BIB-201, congelados para esta generación."""
    plantilla = leer_plantilla(fila["plantilla_md"])
    organizacion: dict[str, object] = dict(await fuentes.organizacion(session, tenant_id))
    organizacion.update(datos_del_documento(plantilla, fila["fecha_emision"]))
    dpd = await fuentes.dpd_vigente(session, tenant_id)
    organizacion["dpo.designado"] = dpd is not None
    if dpd is not None:
        organizacion.update({"dpo.nombre": dpd.get("nombre"), "dpo.correo": dpd.get("correo"),
                             "dpo.fecha_designacion": dpd.get("fecha_designacion")})
    guardado = fila["contexto"] if isinstance(fila["contexto"], dict) else json.loads(fila["contexto"])
    contexto: dict = dict(guardado)
    if "tratamiento." in plantilla.cuerpo or any(c.origen == "rat" for c in plantilla.campos):
        actividades = await fuentes.actividades(session, tenant_id)
        organizacion.update(datos_de_tratamiento(actividades))
        if actividades and any(c.origen == "rat" for c in plantilla.campos):
            for clave in GENERADAS:
                contexto[clave] = fichas_de_actividades(actividades)
    return InstantaneaGeneracion(
        version_id=fila["version_id"], plantilla_md=fila["plantilla_md"], plantilla_sha256=fila["plantilla_sha256"],
        esquema=[c.model_dump() for c in plantilla.campos], organizacion=organizacion, contexto=contexto,
        fecha_emision=fila["fecha_emision"].isoformat(), procedencia=None)


# ¤adpa
def construir(instantanea: InstantaneaGeneracion, pedido: PedirGeneracion) -> tuple[bytes, list[str], str]:
    """(archivo, faltantes, nombre) calculados solo desde la instantánea."""
    datos = instantanea.como_dict()
    plantilla = leer_plantilla(datos["plantilla_md"])
    uso, _ = separar_guia(plantilla.cuerpo)
    contenido, faltantes = rellenar(Plantilla(plantilla.meta, uso), datos["organizacion"], datos["contexto"])
    opcionales = {c["clave"] for c in datos["esquema"] if not c.get("obligatoria", True)}
    borrador = pedido.modo == "borrador"
    texto, bloqueantes = preparar(contenido, faltantes, opcionales, borrador)
    if not borrador:
        if bloqueantes:
            raise ErrorNegocio("BIB_GEN_INCOMPLETA", "Faltan: " + ", ".join(bloqueantes[:20]))
        restos = residuos(texto)
        if restos:
            raise ErrorNegocio("BIB_GEN_SALIDA_INVALIDA", "Quedan marcas: " + " ".join(restos))
    partes = bloques(texto)
    marca = bloqueantes if borrador else None
    if pedido.formato == "docx":
        archivo = generar_docx(partes, marca)
    else:
        valores = {**datos["organizacion"], **{k: v for k, v in datos["contexto"].items() if k not in GENERADAS}}
        archivo = generar_xlsx(f"{plantilla.codigo} · {plantilla.meta.get('nombre', '')}", valores, partes,
                               date.fromisoformat(datos["fecha_emision"]), marca)
    nombre = f"{plantilla.codigo}-v{plantilla.version}-{ESTADOS[pedido.modo]}.{pedido.formato}"
    return archivo, bloqueantes, nombre


# ¤adpa
def _generacion(fila: Mapping) -> Generacion:
    faltan = fila["faltantes"] if isinstance(fila["faltantes"], list) else json.loads(fila["faltantes"])
    return Generacion(**{**dict(fila), "faltantes": faltan})


# ¤adpa
async def generar(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str, borrador_id: str,
                  pedido: PedirGeneracion) -> Generacion:
    await _fijar_contexto(session, tenant_id, actor)
    instantanea = await tomar_instantanea(session, fuentes, tenant_id, await _borrador(session, borrador_id))
    archivo, faltantes, nombre = construir(instantanea, pedido)
    identificador = str(uuid4())
    await session.execute(text(INSERTAR), {
        "id": identificador, "t": tenant_id, "b": borrador_id, "modo": pedido.modo, "formato": pedido.formato,
        "estado": ESTADOS[pedido.modo], "psha": instantanea.plantilla_sha256,
        "inst": json.dumps(instantanea.como_dict(), ensure_ascii=False, sort_keys=True),
        "isha": instantanea.sha256, "archivo": archivo, "asha": huella_bytes(archivo), "bytes": len(archivo),
        "faltan": json.dumps(faltantes, ensure_ascii=False), "nombre": nombre, "u": actor})
    return _generacion((await session.execute(text(LEER), {"id": identificador})).mappings().one())


# ¤adpa
def huella_bytes(archivo: bytes) -> str:
    return hashlib.sha256(archivo).hexdigest()


# ¤adpa
async def listar_generaciones(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str) -> list[Generacion]:
    await _fijar_contexto(session, tenant_id, actor)
    await _borrador(session, borrador_id)
    return [_generacion(f) for f in (await session.execute(text(LISTAR), {"b": borrador_id})).mappings()]


# ¤adpa
async def archivo_generado(session: AsyncSession, tenant_id: str, actor: str,
                           generacion_id: str) -> tuple[bytes, str, str, str]:
    """(bytes, tipo MIME, nombre, sha256). Se comprueba la huella antes de entregar."""
    await _fijar_contexto(session, tenant_id, actor)
    fila = (await session.execute(text(ARCHIVO), {"id": generacion_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_GEN_NO_ENCONTRADA")
    datos = bytes(fila["archivo"])
    if huella_bytes(datos) != fila["archivo_sha256"]:
        raise ErrorNegocio("BIB_GEN_NO_ENCONTRADA")
    return datos, MIME[fila["formato"]], fila["nombre_archivo"], fila["archivo_sha256"]


# ¤adpa
async def guia_de_borrador(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str) -> Guia:
    """Instrucciones, ejemplos y fuentes de la plantilla, aparte del documento de uso."""
    await _fijar_contexto(session, tenant_id, actor)
    plantilla = leer_plantilla((await _borrador(session, borrador_id))["plantilla_md"])
    _, guia = separar_guia(plantilla.cuerpo)
    fuentes = f"{plantilla.meta.get('base_lopdp', '')} (corte normativo {plantilla.meta.get('fecha_corte_normativo', '')})"
    return Guia(codigo=plantilla.codigo, guia_markdown=guia, fuentes=fuentes.strip())


__all__ = ["construir", "generar", "listar_generaciones", "archivo_generado", "guia_de_borrador",
           "tomar_instantanea", "huella_bytes"]
