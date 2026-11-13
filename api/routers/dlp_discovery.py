# ¤dlp-muestreo ¤seguridad-tenant ¤rbac-tenant
"""API de la sala Descubrimiento DLP Muestreado (DLP-01).

El cuerpo se lee con tope antes de parsearse y se valida a mano: los errores solo llevan un código, nunca
la entrada (la validación automática de FastAPI devolvería la muestra en `input`).
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.dlp_discovery import dlp_discovery_service as svc

router = APIRouter(prefix="/dlp-discovery", tags=["Descubrimiento de datos"])

# 1000 filas de hasta ~2 KiB: lo que exceda se corta sin leer el resto del cuerpo.
TOPE_CUERPO_BYTES = 2 * 1024 * 1024

_escaneo = require_role(*svc.ROLES_ESCANEO)
_consulta = require_role(*svc.ROLES_CONSULTA)
_vinculo = require_role(*svc.ROLES_VINCULO)


def _error(estado: int, codigo: str, mensaje: str) -> HTTPException:
    return HTTPException(estado, {"codigo": codigo, "mensaje": mensaje})


def _de_dominio(exc: svc.ErrorDlp) -> HTTPException:
    return _error(exc.estado_http, exc.codigo, exc.mensaje)


async def _leer_json_con_tope(request: Request) -> object:
    declarado = request.headers.get("content-length", "")
    if declarado.strip().isdigit() and int(declarado) > TOPE_CUERPO_BYTES:
        raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "DLP_CUERPO_EXCEDE_TOPE", "La muestra es demasiado grande.")
    partes, total = [], 0
    async for trozo in request.stream():
        total += len(trozo)
        if total > TOPE_CUERPO_BYTES:
            raise _error(status.HTTP_413_CONTENT_TOO_LARGE, "DLP_CUERPO_EXCEDE_TOPE", "La muestra es demasiado grande.")
        partes.append(trozo)
    try:
        return json.loads(b"".join(partes))
    except (ValueError, UnicodeDecodeError):
        raise _error(422, "DLP_SOLICITUD_INVALIDA", "La solicitud no es válida.") from None


def _invalida() -> HTTPException:
    return _error(422, "DLP_SOLICITUD_INVALIDA", "La solicitud no es válida.")


@router.post("/escanear-muestra", status_code=status.HTTP_201_CREATED)
async def escanear_muestra(
    request: Request,
    ctx: dict = Depends(_escaneo),
    session: AsyncSession = Depends(get_session),
    cliente: svc.ClienteDlp = Depends(svc.obtener_cliente_dlp),
):
    cuerpo = await _leer_json_con_tope(request)
    if not isinstance(cuerpo, dict):
        raise _invalida()
    # R1 antes de validar el resto: el tope se rechaza con su propio código (aceptación de la especificación).
    limite = cuerpo.get("limite_muestra", svc.LIMITE_POR_DEFECTO)
    filas = cuerpo.get("filas")
    if isinstance(limite, int) and not isinstance(limite, bool):
        try:
            svc.validar_limite(limite, len(filas) if isinstance(filas, list) else 0)
        except svc.MuestraExcedeLimite as exc:
            raise _de_dominio(exc) from None
    try:
        solicitud = svc.SolicitudEscaneo.model_validate(cuerpo)
    except ValidationError:
        raise _invalida() from None
    del cuerpo, filas
    try:
        return await svc.escanear_muestra(
            session, ctx["tenant_id"], ctx.get("user_id"), solicitud.fuente_nombre,
            solicitud.limite_muestra, solicitud.filas, cliente,
        )
    except svc.ErrorDlp as exc:
        raise _de_dominio(exc) from None


@router.get("/escaneos")
async def listar_escaneos(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    return {"escaneos": await svc.listar_escaneos(session, ctx["tenant_id"])}


@router.post("/escaneos/{escaneo_id}/vincular-rat")
async def vincular_al_rat(
    escaneo_id: str,
    request: Request,
    ctx: dict = Depends(_vinculo),
    session: AsyncSession = Depends(get_session),
):
    cuerpo = await _leer_json_con_tope(request)
    try:
        solicitud = svc.SolicitudVinculo.model_validate(cuerpo)
    except ValidationError:
        raise _invalida() from None
    try:
        return await svc.vincular_al_rat(
            session, ctx["tenant_id"], ctx.get("user_id"), escaneo_id,
            solicitud.actividad_rat_id, solicitud.infotypes,
        )
    except svc.ErrorDlp as exc:
        raise _de_dominio(exc) from None
