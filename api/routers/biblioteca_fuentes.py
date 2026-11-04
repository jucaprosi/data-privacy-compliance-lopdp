# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Reutilización y procedencia de datos (BIB-202). La organización sale de la sesión, no del cuerpo.

Aquí se conectan, en solo lectura, las compuertas de Organización (ORG-14 y designaciones) y RAT con
Biblioteca, que no las importa. Ningún adaptador escribe en su fuente. Se declara lo que cada fuente
no guarda: Organización y la designación no tienen versión; el RAT tiene número de versión pero no
fecha ni validador. Diagnóstico no ofrece por su compuerta valores precargables por campo y no se usa.
"""
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.organizacion import organizacion_service
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/fuentes", tags=["Biblioteca procedencia"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
EDITORES = ("admin_organizacion", "dpo", "coordinador", "implementador")
CAMPOS_RAT = ("nombre", "finalidad", "base_legal", "categorias_datos", "destinatarios", "plazo_conservacion")


# ¤adpa
async def _registros(session: AsyncSession, tenant_id: str) -> list[biblioteca.RegistroFuente]:
    ahora = datetime.now(timezone.utc)
    valores = (await organizacion_service.obtener_variables_documentales(session, tenant_id))["valores"]
    registros = [biblioteca.RegistroFuente(fuente="organizacion", fuente_id=tenant_id, valores=valores, leido_en=ahora)]
    for d in await organizacion_service.listar_designaciones_formales(
            session, tenant_id, organizacion_service.TipoDesignacion.dpd):
        if d["revocada_at"] is None and (d["valid_to"] is None or d["valid_to"] > ahora):
            registros.append(biblioteca.RegistroFuente(
                fuente="dpd", fuente_id=str(d["id"]), fecha=d["fecha_designacion"], leido_en=ahora,
                valores={"dpo.nombre": d["usuario_nombre"], "dpo.correo": d["usuario_email"],
                         "dpo.fecha_designacion": d["fecha_designacion"]}))
            break
    for a in await rat_service.listar_actividades_rat(session, tenant_id):
        datos = vars(a)
        codigo = str(datos.get("codigo") or datos["id"])
        registros.append(biblioteca.RegistroFuente(
            fuente="rat", fuente_id=str(datos["id"]), revision=str(datos.get("version") or "") or None,
            leido_en=ahora, prefijo=f"rat.{codigo}.", valores={c: datos.get(c) for c in CAMPOS_RAT}))
    return registros


FUENTES = biblioteca.PuertoFuentes(registros=_registros)


# ¤adpa
@router.get("/procedencia", response_model=biblioteca.Instantanea)
async def procedencia(session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.procedencia_actual(session, FUENTES, ctx["tenant_id"], ctx["user_id"])


# ¤adpa
@router.post("/documentos/{documento_id}/instantanea", status_code=201, response_model=biblioteca.Instantanea)
async def emitir(documento_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.emitir_instantanea(session, FUENTES, ctx["tenant_id"], ctx["user_id"], documento_id)


# ¤adpa
@router.get("/documentos/{documento_id}/cambios", response_model=biblioteca.AvisoCambios)
async def cambios(documento_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.cambios_de_fuente(session, FUENTES, ctx["tenant_id"], ctx["user_id"], documento_id)


# ¤adpa
@router.post("/documentos/{documento_id}/propuestas", status_code=201, response_model=biblioteca.PropuestaCorreccion)
async def proponer(documento_id: str, entrada: biblioteca.EntradaPropuesta, session: Sesion,
                   ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.proponer_correccion(session, FUENTES, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)
