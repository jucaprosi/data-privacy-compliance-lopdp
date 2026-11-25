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
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
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
async def versiones_del_modulo() -> dict[str, str]:
    """fuente_id -> archivo_sha256 de la última versión que el módulo de inteligencia normativa conoce.

    Hoy el módulo no descarga en ningún entorno (BIB-403 §1): no hay versiones y el control de versión de
    R2 no se dispara. Se llama una sola vez por lista. NORM-04 lo conecta al pasillo; los tests lo sustituyen.
    """
    return {}

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
def _como_plantilla(fila: dict, versiones: dict[str, str]) -> PlantillaCatalogo:
    metadatos = fila["metadatos"] or {}
    return PlantillaCatalogo(
        id=fila["id"], codigo=fila["codigo"], nombre=fila["nombre"], tipo=fila["tipo"], fuente="catalogo",
        version=fila["version"], formato=fila["formato"], validacion_legal=validacion_de_texto(fila["cuerpo_md"] or "", leer_citas(), versiones),
        ola=_entero(metadatos.get("ola")), estado=fila["estado"],
        descargable=descargable(fila["estado"], fila["formato"]),
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
    versiones = await versiones_del_modulo()  # una sola lectura por lista, sin N+1
    return [_como_plantilla(dict(f), versiones) for f in filas]
