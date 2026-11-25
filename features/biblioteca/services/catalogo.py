# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Catálogo de plantillas (BIB-102): lectura autorizada de las versiones publicadas.

El servidor decide quién ve qué: la organización sale de la sesión y el usuario de la identidad ya
verificada. Un usuario sin membresía vigente recibe BIB_SIN_ACCESO, no una lista vacía, para que la
pantalla distinga «no hay nada» de «no tienes permiso». Solo se listan versiones publicadas: una
editora ve también las que están en revisión por su capacidad editorial, y aquí se excluyen.
"""
import json
from datetime import timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from app_core.zona_negocio import ZONA_NEGOCIO
from features.biblioteca.domain.leyenda import leyenda_de
from features.biblioteca.domain.plantillas_md import TIPOS
from features.biblioteca.domain.validacion import validacion_de_texto
from features.biblioteca.services.autorizacion import capacidades

RUTA_CITAS = Path(__file__).resolve().parents[3] / "data" / "biblioteca" / "pmv" / "citas.json"


# ¤adpa
@lru_cache(maxsize=1)
def leer_citas() -> dict | None:
    """citas.json (generado por scripts/verificar_citas_plantillas.py --generar); None si no existe."""
    if not RUTA_CITAS.exists():
        return None
    return json.loads(RUTA_CITAS.read_bytes().decode("utf-8"))


# ¤adpa
async def huellas_por_url_fuente() -> dict[str, str]:
    """Puerto: url_fuente -> sha256 de la última versión que el módulo de inteligencia normativa conoce.

    El proveedor por defecto devuelve `{}`: R2 no se dispara y la validación descansa en R1. El enlace real
    al módulo (NORM) sustituye este proveedor; los tests lo sustituyen. Se llama una vez por lista.
    """
    return {}

# ¤adpa
async def leyendas_de_versiones(session: AsyncSession, ids: list[str]) -> dict[str, dict | None]:
    """BIB-410 R1 a R3: la leyenda de cada versión, desde la revisión técnica aprobada de esa generación.

    El nombre visible sale de `users` (nunca el correo) y la fecha es la de negocio de Guayaquil. Sin revisión aprobada
    de una persona no autora, o sin nombre visible, la leyenda es `None`. Tres lecturas para toda la lista, sin N+1.
    """
    if not ids:
        return {}
    consulta = lambda sql, nombre: text(sql).bindparams(bindparam(nombre, expanding=True))  # noqa: E731
    versiones = (await session.execute(consulta(
        "SELECT id, estado, redactada_por, autores, generacion FROM biblioteca_versiones WHERE id IN :ids", "ids"),
        {"ids": list(ids)})).mappings().all()
    revisiones = (await session.execute(consulta(
        "SELECT version_id, generacion, revisor_id, creada_en FROM biblioteca_revisiones "
        "WHERE version_id IN :ids AND tipo='tecnica' AND aprobado ORDER BY creada_en", "ids"),
        {"ids": list(ids)})).mappings().all()
    autores = {v["id"]: list(v["autores"] or []) for v in versiones}
    aprobada: dict[str, dict] = {}
    for r in revisiones:  # la última aprobada de la generación vigente por una persona que no es autora
        v = next(x for x in versiones if x["id"] == r["version_id"])
        if r["generacion"] == v["generacion"] and r["revisor_id"] not in autores[v["id"]]:
            aprobada[v["id"]] = r
    personas = {i for v in versiones if v["redactada_por"] != "ia" for i in autores[v["id"]]} | {r["revisor_id"] for r in aprobada.values()}
    nombres = {}
    if personas:
        nombres = {f["id"]: f["nombre"] for f in (await session.execute(consulta(
            "SELECT id, nombre FROM users WHERE id IN :ids", "ids"), {"ids": sorted(personas)})).mappings().all()}
    salida: dict[str, dict | None] = {}
    for v in versiones:
        r = aprobada.get(v["id"])
        fecha = r["creada_en"] if r else None
        if fecha is not None:
            fecha = (fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)).astimezone(ZONA_NEGOCIO).date()
        salida[v["id"]] = leyenda_de(v["estado"], v["redactada_por"], [nombres.get(i, "") for i in autores[v["id"]]],
                                     nombres.get(r["revisor_id"]) if r else None, fecha)
    return salida


FUENTES = ("catalogo", "organizacion")
# Un solo estado es descargable; las entradas planificadas o sin archivo nunca lo son.
ESTADO_DESCARGABLE = "publicada"
LIMITE = 500


class PlantillaCatalogo(BaseModel):
    id: str
    codigo: str
    nombre: str | None
    tipo: str | None
    fuente: Literal["catalogo", "organizacion"]
    version: str
    formato: str
    validacion_legal: str | None
    ola: int | None
    estado: str
    descargable: bool
    leyenda: dict | None = None  # BIB-410: redacción y aprobación; nula sin aprobación registrada


# ¤adpa
def descargable(estado: str, formato: str | None) -> bool:
    """Solo una versión publicada con archivo (DOCX o XLSX) se ofrece para descargar.

    Las plantillas Markdown se usan en la organización, no se descargan como maestro.
    """
    return estado == ESTADO_DESCARGABLE and formato in ("DOCX", "XLSX")


# ¤adpa
def _entero(valor: object) -> int | None:
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


# ¤adpa
def _validar_filtros(fuente: str | None, tipo: str | None, ola: int | None) -> None:
    if fuente is not None and fuente not in FUENTES:
        raise ErrorNegocio("BIB_FILTRO_INVALIDO", f"fuente debe ser una de: {', '.join(FUENTES)}.")
    if tipo is not None and tipo not in TIPOS:
        raise ErrorNegocio("BIB_FILTRO_INVALIDO", "tipo no es una categoría del catálogo.")
    if ola is not None and ola < 1:
        raise ErrorNegocio("BIB_FILTRO_INVALIDO", "ola debe ser un entero positivo.")


# ¤adpa
def _como_plantilla(fila: dict, versiones: dict[str, str], leyenda: dict | None = None) -> PlantillaCatalogo:
    metadatos = fila["metadatos"] or {}
    return PlantillaCatalogo(
        id=fila["id"], codigo=fila["codigo"], nombre=fila["nombre"], tipo=fila["tipo"], fuente="catalogo",
        version=fila["version"], formato=fila["formato"], validacion_legal=validacion_de_texto(fila["cuerpo_md"] or "", leer_citas(), versiones),
        ola=_entero(metadatos.get("ola")), estado=fila["estado"],
        descargable=descargable(fila["estado"], fila["formato"]), leyenda=leyenda,
    )


# ¤adpa ¤rbac-tenant
async def listar_catalogo(session: AsyncSession, actor: str, fuente: str | None = None,
                          tipo: str | None = None, ola: int | None = None) -> list[PlantillaCatalogo]:
    """Plantillas publicadas visibles para un miembro vigente de la organización de la sesión.

    La organización de la sesión la fija quien abre la sesión (get_tenant_session). «Mi plantilla» de
    la organización no tiene almacén todavía (las copias son de BIB-103): esa fuente responde vacía.
    """
    _validar_filtros(fuente, tipo, ola)
    await capacidades(session, actor)  # fija app.current_user_id con la identidad ya verificada
    if not (await session.execute(text("SELECT biblioteca_miembro_activo()"))).scalar():
        raise ErrorNegocio("BIB_SIN_ACCESO")
    if fuente == "organizacion":
        return []
    filas = (await session.execute(text(
        "SELECT v.id, v.codigo, v.version, v.formato, v.estado, v.cuerpo_md, c.nombre, c.tipo, c.metadatos "
        "FROM biblioteca_versiones v LEFT JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
        "WHERE v.estado='publicada' AND (CAST(:tipo AS text) IS NULL OR c.tipo=:tipo) "
        "AND (CAST(:ola AS integer) IS NULL OR c.metadatos->>'ola'=CAST(:ola AS text)) "
        "ORDER BY v.codigo, v.version LIMIT :limite"
    ), {"tipo": tipo, "ola": ola, "limite": LIMITE})).mappings().all()
    versiones = await huellas_por_url_fuente()  # una sola lectura por lista, sin N+1
    leyendas = await leyendas_de_versiones(session, [f["id"] for f in filas])
    return [_como_plantilla(dict(f), versiones, leyendas.get(f["id"])) for f in filas]
