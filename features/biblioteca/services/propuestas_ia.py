# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada
# ¤¤developer-architect
"""BIB-406: la IA propone versiones de plantillas como autora; las aprueba una persona.

La inferencia y la normativa se usan por sus pasillos (R-ADPA). La versión nace `en_revision`, con
`redactada_por = 'ia'` y `autores = ["ia"]`; quien dispara queda en `responsable_id` y en el origen (R3).
"""
import hashlib
import json
import logging
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.biblioteca.domain.editorial import Capacidad
from features.biblioteca.domain.propuestas_ia import (
    AUTORES_IA, CREADA, EN_REVISION, ORIGEN_PETICION, ORIGEN_RESOLUCION, SIN_CAMBIOS, SalidaPropuestaIA,
    aplicar_cambios, con_version, debe_proponer, plantillas_afectadas, version_siguiente,
)
from features.biblioteca.services.autorizacion import capacidades
from features.biblioteca.services.catalogo import leer_citas

_SISTEMA = (
    "Eres la autora de una versión nueva de una plantilla de protección de datos personales de Ecuador. "
    "Propón solo los cambios que exige el motivo. Cada cambio reemplaza un fragmento literal del texto "
    "actual («antes») por el texto nuevo («despues») y lleva la clave de cita que lo funda, elegida de la "
    "lista de claves verificadas. No cambies estilo ni criterio. Si no hace falta ningún cambio, devuelve "
    "una lista vacía."
)
_PLANTILLA = (
    "Plantilla {codigo}, versión publicada {version}.\n\nMotivo:\n{motivo}\n\n"
    "Claves de cita verificadas:\n{claves}\n\nTexto publicado:\n{cuerpo}"
)

logger = logging.getLogger(__name__)
_redactor_de_prueba = None
_normativa_de_prueba = None


# ¤adpa
def inyectar_redactor_de_prueba(redactor) -> None:
    """SOLO PARA PRUEBAS: corrutina `f(valores) -> (SalidaPropuestaIA, traza|None, modelo)`; None restaura."""
    global _redactor_de_prueba
    _redactor_de_prueba = redactor


# ¤adpa
def inyectar_normativa_de_prueba(obtener) -> None:
    """SOLO PARA PRUEBAS: corrutina `f(id_resolucion) -> objeto con url_fuente, titulo`; None restaura."""
    global _normativa_de_prueba
    _normativa_de_prueba = obtener


# ¤adpa
def _prompt():
    from app_core.pasillo import inferencia as pasillo_inferencia

    return pasillo_inferencia.prompt_versionado("biblioteca.propuesta_plantilla", 1, _SISTEMA, _PLANTILLA)


# ¤adpa
async def _redactar(valores: dict):
    """R2c: generación trazada sin tope, por el pasillo de inferencia (catálogo común, IA-12 R3, NORM-06 R2)."""
    if _redactor_de_prueba is not None:
        return await _redactor_de_prueba(valores)
    from app_core.pasillo import inferencia as pasillo_inferencia

    if not pasillo_inferencia.estado().disponible:
        raise ErrorNegocio("BIB_PROPUESTA_NO_DISPONIBLE")
    no_disponible, _ = pasillo_inferencia.errores()
    modelo = pasillo_inferencia.MODELO_GENERACION
    try:
        salida, traza = await pasillo_inferencia.generar_trazado_sin_tope(
            _prompt(), valores, SalidaPropuestaIA, modelo=modelo)
    except no_disponible as exc:
        raise ErrorNegocio("BIB_PROPUESTA_NO_DISPONIBLE") from exc
    return salida, traza, traza.modelo_version


# ¤adpa
async def _resolucion(id_resolucion: str):
    if _normativa_de_prueba is not None:
        return await _normativa_de_prueba(id_resolucion)
    from app_core.pasillo import inteligencia_normativa as pasillo_normativa

    return await pasillo_normativa.obtener_resolucion(id_resolucion)


# ¤adpa
async def _publicada(session: AsyncSession, codigo: str) -> dict | None:
    fila = (await session.execute(text(
        "SELECT id, codigo, version, ficha, cuerpo_md FROM biblioteca_versiones "
        "WHERE codigo=:codigo AND estado='publicada' AND formato='MD'"
    ), {"codigo": codigo})).mappings().first()
    return dict(fila) if fila else None


# ¤adpa
async def hay_propuesta_en_revision(session: AsyncSession, codigo: str) -> bool:
    """Límite de gasto de la sala: una sola versión de la IA «en_revision» por plantilla."""
    return bool((await session.execute(text(
        "SELECT 1 FROM biblioteca_versiones WHERE codigo=:codigo AND redactada_por='ia' AND estado='en_revision'"
    ), {"codigo": codigo})).scalar())


# ¤adpa
async def _proponer_para(session: AsyncSession, actor: str, codigo: str, motivo: str, origen: str,
                         id_resolucion: str | None) -> dict | None:
    """Pide la redacción y, si queda algún cambio con cita verificada, crea la versión de la IA (R2, R3)."""
    publicada = await _publicada(session, codigo)
    if publicada is None or not publicada["cuerpo_md"]:
        raise ErrorNegocio("BIB_SIN_PUBLICADA")
    if await hay_propuesta_en_revision(session, codigo):
        raise ErrorNegocio("BIB_PROPUESTA_EN_REVISION")
    citas = leer_citas() or {}
    claves = sorted(c for c in citas.get("plantillas", {}).get(codigo, [])
                    if citas.get("estados", {}).get(c) == "verificada")
    salida, traza, modelo = await _redactar({
        "codigo": codigo, "version": publicada["version"], "motivo": motivo,
        "claves": "\n".join(claves), "cuerpo": publicada["cuerpo_md"]})
    cuerpo, aplicados = aplicar_cambios(publicada["cuerpo_md"], salida.cambios, citas)
    if not aplicados:
        return None
    version = version_siguiente(publicada["version"])
    cuerpo = con_version(cuerpo, publicada["version"], version)
    identificador = str(uuid4())
    await session.execute(text("SELECT set_config('app.current_user_id', :actor, true)"), {"actor": actor})
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": codigo})
    async with session.begin_nested():
        await session.execute(text(
            "INSERT INTO biblioteca_versiones(id,codigo,version,formato,ficha,responsable_id,autores,sustituye_id,"
            "cuerpo_md,sha256,redactada_por,modelo_ia,origen_ia,id_resolucion,motivo_ia,cambios_ia) "
            "VALUES (:id,:codigo,:version,'MD',CAST(:ficha AS jsonb),:actor,CAST(:autores AS jsonb),:sustituye,"
            ":cuerpo,:sha,'ia',:modelo,:origen,:resolucion,:motivo,CAST(:cambios AS jsonb))"
        ), {"id": identificador, "codigo": codigo, "version": version,
            "ficha": json.dumps(publicada["ficha"]) if publicada["ficha"] is not None else None,
            "actor": actor, "autores": json.dumps(AUTORES_IA), "sustituye": publicada["id"], "cuerpo": cuerpo,
            "sha": hashlib.sha256(cuerpo.encode("utf-8")).hexdigest(), "modelo": modelo, "origen": origen,
            "resolucion": id_resolucion, "motivo": motivo, "cambios": json.dumps(aplicados, ensure_ascii=False)})
    if traza is not None:
        logger.info("BIB-406 propuesta %s de %s: modelo %s, prompt %s v%s", identificador, codigo,
                    traza.modelo_version, traza.prompt_id, traza.prompt_version)
    from features.biblioteca.services.editorial import leer_version

    return await leer_version(session, identificador)


# ¤adpa
async def proponer(session: AsyncSession, actor: str, codigo: str, motivo: str) -> dict:
    """El botón «Proponer cambio» (R1): la persona que lo pulsa, con `editor` o `revisor_tecnico`."""
    permisos = await capacidades(session, actor)
    if not {Capacidad.EDITOR.value, Capacidad.TECNICO.value} & set(permisos):
        raise ErrorNegocio("BIB_SIN_CAPACIDAD")
    if not motivo.strip():
        raise ErrorNegocio("BIB_PROPUESTA_NO_DISPONIBLE")
    try:
        version = await _proponer_para(session, actor, codigo, motivo, ORIGEN_PETICION, None)
    except ErrorNegocio as exc:
        if exc.code == "BIB_PROPUESTA_EN_REVISION":
            return {"resultado": EN_REVISION, "versiones": []}
        raise
    return {"resultado": CREADA, "versiones": [version]} if version else {"resultado": SIN_CAMBIOS, "versiones": []}


# ¤adpa
async def proponer_por_resolucion(session: AsyncSession, id_resolucion: str, estado: str,
                                  estado_anterior: str | None, actor: str) -> dict:
    """R1: tras revisar una resolución, una versión por cada plantilla publicada que cita su URL oficial.

    El actor es el operador de la plataforma que revisó la resolución; queda en el origen, no como autor.
    """
    if not debe_proponer(estado, estado_anterior):
        return {"resultado": SIN_CAMBIOS, "versiones": []}
    resolucion = await _resolucion(id_resolucion)
    motivo = f"La resolución {getattr(resolucion, 'titulo', id_resolucion)} se revisó como «{estado}»."
    versiones, omitidas = [], []
    for codigo in plantillas_afectadas(leer_citas() or {}, resolucion.url_fuente):
        if await _publicada(session, codigo) is None:
            continue
        try:
            version = await _proponer_para(session, actor, codigo, motivo, ORIGEN_RESOLUCION, id_resolucion)
        except ErrorNegocio as exc:
            if exc.code == "BIB_PROPUESTA_EN_REVISION":  # R2b: se omite y queda en la traza
                omitidas.append(codigo)
                logger.info("BIB-406 %s omitida: ya hay una propuesta de la IA en revisión", codigo)
                continue
            raise
        if version:
            versiones.append(version)
    return {"resultado": CREADA if versiones else SIN_CAMBIOS, "versiones": versiones, "omitidas": omitidas}
