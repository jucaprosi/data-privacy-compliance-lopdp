# ¤adpa
# ¤¤developer-architect
"""Plantillas Markdown del PMV: verificación sin escritura, carga idempotente y lectura de publicadas.

La carga deja cada plantilla En revisión: nunca publica ni reemplaza en silencio. Publicar sigue el
flujo editorial de BIB-105 (revisión técnica y jurídica y aprobación individual de la propietaria).
"""
import json
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.domain.editorial import Capacidad
from features.biblioteca.domain.plantillas_md import (
    exigir_plantilla_cargable, huella, metadatos_de, validar_plantilla_md,
)
from features.biblioteca.services.autorizacion import autorizar, capacidades
from features.biblioteca.services.editorial import crear_version_md

CARPETA = "data/biblioteca/pmv"
CODIGOS = tuple(f"BIB-{n:03d}" for n in range(1, 13))
# Metadatos de la plantilla que el catálogo guarda en su campo jsonb (los demás tienen columna).
EN_METADATOS = ("ola", "sector", "tamano_empresa", "base_lopdp", "validacion_legal", "fecha_corte_normativo",
                "revision_meses", "variables_contexto", "avisos")


# ¤adpa
def leer_plantillas(raiz: Path) -> dict[str, str]:
    return {ruta.stem: ruta.read_text(encoding="utf-8") for ruta in sorted((raiz / CARPETA).glob("BIB-*.md"))}


# ¤adpa
def verificar_plantillas_pmv(raiz: Path) -> dict:
    """Sin escritura ni base de datos: las doce plantillas, válidas y cargables."""
    plantillas, errores = [], []
    textos = leer_plantillas(raiz)
    if tuple(textos) != CODIGOS:
        errores.append(f"Se esperaban {', '.join(CODIGOS)}; hay {', '.join(textos) or 'ninguna'}")
    for codigo, texto in textos.items():
        fallos = validar_plantilla_md(texto, codigo)
        if not fallos and metadatos_de(texto)["validacion_legal"] == "validada":
            fallos = ["validacion_legal «validada» sin dictamen registrado en el flujo editorial"]
        errores += [f"{codigo}: {fallo}" for fallo in fallos]
        if not fallos:
            meta = metadatos_de(texto)
            plantillas.append({"codigo": codigo, "version": meta["version"], "nombre": meta["nombre"],
                               "validacion_legal": meta["validacion_legal"], "sha256": huella(texto)})
    return {"plantillas": plantillas, "errores": errores}


# ¤adpa
def _fila_catalogo(meta: dict) -> dict:
    return {"nombre": meta["nombre"], "tipo": meta["tipo"], "naturaleza": meta["naturaleza"], "formato": "MD",
            "disponibilidad": "con_archivo", "metadatos": {k: meta[k] for k in EN_METADATOS if k in meta}}


# ¤adpa
async def _plan(session: AsyncSession, texto: str, codigo: str) -> dict:
    """Primera pasada sin escritura: lo existente distinto es conflicto, no reemplazo."""
    meta = exigir_plantilla_cargable(texto, codigo)
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": codigo})
    catalogo = (await session.execute(text(
        "SELECT nombre, tipo, naturaleza, formato, disponibilidad, metadatos FROM biblioteca_catalogo WHERE codigo=:c"
    ), {"c": codigo})).mappings().first()
    fila = _fila_catalogo(meta)
    if catalogo is not None and dict(catalogo) != fila:
        raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    version = (await session.execute(text(
        "SELECT sha256 FROM biblioteca_versiones WHERE codigo=:c AND version=:v"
    ), {"c": codigo, "v": meta["version"]})).first()
    if version is not None and version[0] != huella(texto):
        raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    return {"codigo": codigo, "texto": texto, "meta": meta, "fila": fila,
            "crear_catalogo": catalogo is None, "crear_version": version is None}


# ¤adpa
async def _aplicar(session: AsyncSession, actor: str, paso: dict) -> dict:
    resultado = {"catalogo_creadas": 0, "versiones_creadas": 0}
    if paso["crear_catalogo"]:
        fila = paso["fila"]
        await session.execute(text(
            "INSERT INTO biblioteca_catalogo(codigo, nombre, tipo, naturaleza, formato, disponibilidad, metadatos) "
            "VALUES (:codigo, :nombre, :tipo, :naturaleza, :formato, :disponibilidad, CAST(:metadatos AS jsonb))"
        ), {**fila, "codigo": paso["codigo"], "metadatos": json.dumps(fila["metadatos"], ensure_ascii=False)})
        resultado["catalogo_creadas"] = 1
    if paso["crear_version"]:
        await crear_version_md(session, actor, paso["codigo"], paso["meta"]["version"], paso["texto"])
        resultado["versiones_creadas"] = 1
    return resultado


# ¤adpa
async def cargar_plantilla_md(session: AsyncSession, actor: str, texto: str, codigo: str) -> dict:
    """Carga una plantilla en la transacción del llamador; idempotente por código, versión y huella."""
    await autorizar(session, actor, Capacidad.EDITOR)
    return await _aplicar(session, actor, await _plan(session, texto, codigo))


# ¤adpa
async def cargar_plantillas_pmv(session: AsyncSession, actor: str, raiz: Path) -> dict:
    """Carga las doce en la transacción del llamador; cualquier conflicto revierte todo antes de escribir."""
    informe = verificar_plantillas_pmv(raiz)
    if informe["errores"]:
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    await autorizar(session, actor, Capacidad.EDITOR)
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('pmv', 109))"))
    plan = [await _plan(session, texto, codigo) for codigo, texto in leer_plantillas(raiz).items()]
    total = {"catalogo_creadas": 0, "versiones_creadas": 0}
    for paso in plan:
        for clave, valor in (await _aplicar(session, actor, paso)).items():
            total[clave] += valor
    return total


# ¤adpa
async def listar_publicadas(session: AsyncSession, actor: str) -> list[dict]:
    """Versiones publicadas visibles para un miembro activo de la organización de la sesión.

    No exige capacidad editorial: decide la RLS (estado publicada y membresía vigente). Sin membresía
    en la organización activa, la lista queda vacía.
    """
    await capacidades(session, actor)  # fija app.current_user_id con la identidad ya verificada
    filas = (await session.execute(text(
        "SELECT v.id, v.codigo, v.version, v.formato, v.ficha, v.sha256, v.cuerpo_md, v.creada_en, "
        "c.nombre, c.tipo, c.naturaleza, c.metadatos FROM biblioteca_versiones v "
        "LEFT JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
        "WHERE v.estado='publicada' ORDER BY v.codigo, v.creada_en DESC LIMIT 500"
    ))).mappings().all()
    return [dict(f) for f in filas]
