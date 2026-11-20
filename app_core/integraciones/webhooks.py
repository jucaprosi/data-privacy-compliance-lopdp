# ¤¤developer-architect
# ¤api-integraciones ¤seguridad ¤seguridad-tenant
"""Webhooks salientes firmados HMAC-SHA256 con cifrado Fernet y techo del paquete (API-02b).

Invariante: INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED.
- El secreto se genera con 32 bytes aleatorios (`secrets.token_urlsafe`), se cifra con Fernet
  (`WEBHOOKS_CLAVE_CIFRADO`) y solo se devuelve en claro al crear o rotar.
- Validación estricta de destino HTTPS público sin redirecciones (anti-SSRF).
- Firma HMAC-SHA256 con marca de tiempo UTC y ventana de 300 s.
- Entrega síncrona en línea (sin cola) con hasta 3 intentos (esperas 1, 2 y 4 s).
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import socket
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from app_core.integraciones.techos import obtener_techos_integracion

EVENTOS_WEBHOOK: tuple[str, ...] = (
    "webhook.prueba",
    "incidente.registrado",
    "derecho.solicitud_recibida",
    "tarea.validada",
)
VENTANA_SEGUNDOS: int = 300
REINTENTOS: int = 3
ESPERAS_REINTENTO: tuple[int, ...] = (1, 2, 4)
TIMEOUT_SEGUNDOS: int = 5
VARIABLE_CLAVE_CIFRADO: str = "WEBHOOKS_CLAVE_CIFRADO"

ResolverDNS = Callable[[str], Sequence[str]]
FuncionEspera = Callable[[float], Awaitable[None]]


def _cifrador() -> Fernet:
    """Construye el cifrador Fernet leyendo WEBHOOKS_CLAVE_CIFRADO en tiempo de ejecución."""
    clave = os.environ.get(VARIABLE_CLAVE_CIFRADO, "").strip()
    if not clave:
        raise ErrorNegocio(
            "WEBHOOKS_CIFRADO_NO_CONFIGURADO",
            detail="El cifrado de webhooks no está configurado.",
            status_code=503,
        )
    try:
        return Fernet(clave.encode("ascii"))
    except (ValueError, UnicodeEncodeError, TypeError) as exc:
        raise ErrorNegocio(
            "WEBHOOKS_CIFRADO_NO_CONFIGURADO",
            detail="La clave de cifrado de webhooks no es válida.",
            status_code=503,
        ) from exc


def generar_secreto() -> str:
    """Genera un secreto de firma con 32 bytes aleatorios."""
    return secrets.token_urlsafe(32)


def _cifrar_secreto(secreto: str) -> str:
    return _cifrador().encrypt(secreto.encode("utf-8")).decode("ascii")


def _descifrar_secreto(secreto_cifrado: str) -> str:
    cifrador = _cifrador()
    try:
        return cifrador.decrypt(secreto_cifrado.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeEncodeError) as exc:
        raise ErrorNegocio(
            "WEBHOOKS_CIFRADO_NO_CONFIGURADO",
            detail="No se pudo descifrar el secreto del webhook con la clave configurada.",
            status_code=503,
        ) from exc


def _es_ip_publica_segura(ip_texto: str) -> bool:
    """Rechaza direcciones privadas, loopback, enlace local, multicast, reservadas o no globales."""
    if not ip_texto or "%" in ip_texto:
        return False
    try:
        ip = ipaddress.ip_address(ip_texto)
    except ValueError:
        return False

    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        if not _es_ip_publica_segura(str(ip.ipv4_mapped)):
            return False

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or not ip.is_global
    )


def _resolver_dns_sistema(hostname: str, puerto: int = 443) -> list[str]:
    """Resuelve un nombre DNS a direcciones IP usando getaddrinfo del sistema."""
    infos = socket.getaddrinfo(hostname, puerto, type=socket.SOCK_STREAM)
    ips: list[str] = []
    for info in infos:
        direccion = info[4][0]
        if direccion not in ips:
            ips.append(direccion)
    return ips


def _error_url_no_permitida() -> ErrorNegocio:
    return ErrorNegocio(
        "WEBHOOK_URL_NO_PERMITIDA",
        detail="La URL del webhook debe usar https y apuntar a una dirección pública.",
        status_code=422,
    )


def validar_url_webhook(url: str, resolver: ResolverDNS | None = None) -> str:
    """Valida que la URL sea HTTPS y que su destino resuelva únicamente a IPs públicas."""
    limpia = (url or "").strip()
    if not limpia or any(c.isspace() for c in limpia):
        raise _error_url_no_permitida()

    partes = urlsplit(limpia)
    if partes.scheme.lower() != "https" or not partes.netloc or not partes.hostname:
        raise _error_url_no_permitida()
    if partes.username or partes.password:
        raise _error_url_no_permitida()

    try:
        puerto = partes.port
    except ValueError as exc:
        raise _error_url_no_permitida() from exc
    if puerto is not None and not (1 <= puerto <= 65535):
        raise _error_url_no_permitida()

    hostname = partes.hostname.strip()
    if not hostname or "%" in hostname:
        raise _error_url_no_permitida()

    try:
        ipaddress.ip_address(hostname)
        es_ip_literal = True
    except ValueError:
        es_ip_literal = False

    if es_ip_literal:
        if not _es_ip_publica_segura(hostname):
            raise _error_url_no_permitida()
        return limpia

    puerto_destino = puerto or 443
    try:
        ips = list(resolver(hostname) if resolver is not None else _resolver_dns_sistema(hostname, puerto_destino))
    except (OSError, ValueError) as exc:
        raise _error_url_no_permitida() from exc

    if not ips or not all(_es_ip_publica_segura(ip) for ip in ips):
        raise _error_url_no_permitida()

    return limpia


def validar_eventos(eventos: Sequence[str]) -> list[str]:
    """Valida que los eventos no estén vacíos y pertenezcan al catálogo cerrado."""
    if not eventos:
        raise ErrorNegocio(
            "WEBHOOK_EVENTO_DESCONOCIDO",
            detail="Debes seleccionar al menos un evento válido.",
            status_code=422,
        )
    vistos: list[str] = []
    catalogo = set(EVENTOS_WEBHOOK)
    for evento in eventos:
        if not isinstance(evento, str) or evento not in catalogo:
            raise ErrorNegocio(
                "WEBHOOK_EVENTO_DESCONOCIDO",
                detail="Uno o más eventos solicitados no existen en el catálogo.",
                status_code=422,
            )
        if evento not in vistos:
            vistos.append(evento)
    return vistos


def firmar_carga(secreto: str, cuerpo: str | bytes, marca_tiempo: int | None = None) -> tuple[int, str]:
    """Genera (marca_tiempo_utc, 'sha256=<hex>') sobre '<marca>.<cuerpo>'."""
    marca = int(time.time()) if marca_tiempo is None else int(marca_tiempo)
    cuerpo_bytes = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
    mensaje = f"{marca}.".encode("utf-8") + cuerpo_bytes
    firma_hex = hmac.new(secreto.encode("utf-8"), mensaje, hashlib.sha256).hexdigest()
    return marca, f"sha256={firma_hex}"


def verificar_firma(
    secreto: str,
    marca: int | str,
    cuerpo: str | bytes,
    firma: str,
    ahora: int | float | None = None,
) -> bool:
    """Verifica la firma HMAC-SHA256 en tiempo constante y dentro de VENTANA_SEGUNDOS."""
    if not secreto or not isinstance(secreto, str):
        return False
    if not firma or not isinstance(firma, str) or not firma.startswith("sha256="):
        return False
    if isinstance(marca, bool):
        return False
    try:
        marca_int = int(str(marca).strip())
    except (ValueError, TypeError):
        return False

    ahora_ts = time.time() if ahora is None else float(ahora)
    if abs(ahora_ts - marca_int) > VENTANA_SEGUNDOS:
        return False

    _, esperada = firmar_carga(secreto, cuerpo, marca_tiempo=marca_int)
    return hmac.compare_digest(firma, esperada)


async def verificar_techo_webhooks(session: AsyncSession, tenant_id: str) -> None:
    """Valida si el tenant puede crear una nueva suscripción activa; 409 TECHO_WEBHOOKS_ALCANZADO."""
    techos = await obtener_techos_integracion(session, tenant_id)
    maximo = techos["webhooks"]["maximo"]
    activos = techos["webhooks"]["activos"]
    if maximo is not None and activos >= maximo:
        raise ErrorNegocio(
            "TECHO_WEBHOOKS_ALCANZADO",
            detail=f"Se ha alcanzado el límite de webhooks permitidos por el paquete ({maximo}).",
            status_code=409,
        )


def _serializar_suscripcion(row: Mapping[str, Any]) -> dict[str, Any]:
    """Serializa una suscripción sin incluir nunca secreto ni secreto_cifrado."""
    creada = row["creada_en"]
    rotada = row["rotada_en"]
    return {
        "id": str(row["id"]),
        "url": row["url"],
        "eventos": list(row["eventos"] or []),
        "activo": bool(row["activo"]),
        "creada_en": creada.isoformat() if hasattr(creada, "isoformat") else creada,
        "rotada_en": rotada.isoformat() if hasattr(rotada, "isoformat") else rotada,
    }


def _validar_uuid(suscripcion_id: str) -> str:
    try:
        return str(UUID(str(suscripcion_id)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ErrorNegocio(
            "WEBHOOK_NO_ENCONTRADO",
            detail="Suscripción de webhook no encontrada.",
            status_code=404,
        ) from exc


async def crear_suscripcion(
    session: AsyncSession,
    tenant_id: str,
    url: str,
    eventos: Sequence[str],
    usuario_id: str,
    *,
    resolver: ResolverDNS | None = None,
) -> tuple[dict[str, Any], str]:
    """Crea una suscripción de webhook validada, verificando clave Fernet y techo del paquete."""
    _cifrador()
    eventos_validos = validar_eventos(eventos)
    url_valida = validar_url_webhook(url, resolver=resolver)
    await verificar_techo_webhooks(session, tenant_id)

    secreto = generar_secreto()
    secreto_cifrado = _cifrar_secreto(secreto)

    stmt = text(
        """
        INSERT INTO webhooks_suscripciones (tenant_id, url, eventos, secreto_cifrado)
        VALUES (:tenant_id, :url, :eventos, :secreto_cifrado)
        RETURNING id, url, eventos, activo, creada_en, rotada_en
        """
    )
    res = await session.execute(
        stmt,
        {
            "tenant_id": tenant_id,
            "url": url_valida,
            "eventos": eventos_validos,
            "secreto_cifrado": secreto_cifrado,
        },
    )
    row = res.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="webhook_suscripcion",
        entity_id=str(row["id"]),
        action="crear",
        user_id=usuario_id,
        payload={"url": url_valida, "eventos": eventos_validos},
    )

    return _serializar_suscripcion(row), secreto


async def listar_suscripciones(session: AsyncSession, tenant_id: str) -> list[dict[str, Any]]:
    """Lista las suscripciones del tenant sin exponer secreto ni secreto_cifrado."""
    stmt = text(
        """
        SELECT id, url, eventos, activo, creada_en, rotada_en
        FROM webhooks_suscripciones
        WHERE tenant_id = :tenant_id
        ORDER BY creada_en DESC
        """
    )
    res = await session.execute(stmt, {"tenant_id": tenant_id})
    return [_serializar_suscripcion(r) for r in res.mappings().all()]


async def rotar_secreto(
    session: AsyncSession,
    tenant_id: str,
    suscripcion_id: str,
    usuario_id: str,
) -> tuple[dict[str, Any], str]:
    """Rota el secreto de una suscripción activa y devuelve el nuevo secreto en claro una sola vez."""
    _cifrador()
    uid = _validar_uuid(suscripcion_id)

    res_check = await session.execute(
        text(
            """
            SELECT id, url, activo
            FROM webhooks_suscripciones
            WHERE id = :id AND tenant_id = :tenant_id
            """
        ),
        {"id": uid, "tenant_id": tenant_id},
    )
    actual = res_check.mappings().first()
    if not actual:
        raise ErrorNegocio(
            "WEBHOOK_NO_ENCONTRADO",
            detail="Suscripción de webhook no encontrada.",
            status_code=404,
        )
    if not actual["activo"]:
        raise ErrorNegocio(
            "WEBHOOK_DESACTIVADO",
            detail="No se puede rotar el secreto de un webhook desactivado.",
            status_code=409,
        )

    nuevo_secreto = generar_secreto()
    secreto_cifrado = _cifrar_secreto(nuevo_secreto)

    res_upd = await session.execute(
        text(
            """
            UPDATE webhooks_suscripciones
            SET secreto_cifrado = :secreto_cifrado, rotada_en = NOW()
            WHERE id = :id AND tenant_id = :tenant_id
            RETURNING id, url, eventos, activo, creada_en, rotada_en
            """
        ),
        {"id": uid, "tenant_id": tenant_id, "secreto_cifrado": secreto_cifrado},
    )
    row = res_upd.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="webhook_suscripcion",
        entity_id=str(row["id"]),
        action="rotar_secreto",
        user_id=usuario_id,
        payload={"url": row["url"]},
    )

    return _serializar_suscripcion(row), nuevo_secreto


async def desactivar_suscripcion(
    session: AsyncSession,
    tenant_id: str,
    suscripcion_id: str,
    usuario_id: str,
) -> dict[str, Any]:
    """Desactiva definitivamente una suscripción y libera un lugar del techo del paquete."""
    uid = _validar_uuid(suscripcion_id)

    res_check = await session.execute(
        text(
            """
            SELECT id, url, eventos, activo, creada_en, rotada_en
            FROM webhooks_suscripciones
            WHERE id = :id AND tenant_id = :tenant_id
            """
        ),
        {"id": uid, "tenant_id": tenant_id},
    )
    actual = res_check.mappings().first()
    if not actual:
        raise ErrorNegocio(
            "WEBHOOK_NO_ENCONTRADO",
            detail="Suscripción de webhook no encontrada.",
            status_code=404,
        )

    if not actual["activo"]:
        return _serializar_suscripcion(actual)

    res_upd = await session.execute(
        text(
            """
            UPDATE webhooks_suscripciones
            SET activo = FALSE
            WHERE id = :id AND tenant_id = :tenant_id
            RETURNING id, url, eventos, activo, creada_en, rotada_en
            """
        ),
        {"id": uid, "tenant_id": tenant_id},
    )
    row = res_upd.mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="webhook_suscripcion",
        entity_id=str(row["id"]),
        action="desactivar",
        user_id=usuario_id,
        payload={"url": row["url"]},
    )

    return _serializar_suscripcion(row)


async def entregar(
    suscripcion: Mapping[str, Any],
    evento: str,
    datos: Any,
    *,
    resolver: ResolverDNS | None = None,
    transporte: httpx.AsyncBaseTransport | None = None,
    cliente: httpx.AsyncClient | None = None,
    esperar: FuncionEspera | None = None,
    ahora: Callable[[], int] | None = None,
) -> dict[str, Any]:
    """Entrega síncrona firmada con hasta REINTENTOS intentos y re-validación DNS en cada entrega."""
    if evento not in EVENTOS_WEBHOOK:
        raise ErrorNegocio(
            "WEBHOOK_EVENTO_DESCONOCIDO",
            detail="El evento indicado no pertenece al catálogo.",
            status_code=422,
        )

    if not suscripcion.get("activo", True):
        return {"entregado": False, "intentos": 0, "estado_http": None}

    secreto = _descifrar_secreto(str(suscripcion["secreto_cifrado"]))
    url_objetivo = str(suscripcion["url"])
    validar_url_webhook(url_objetivo, resolver=resolver)

    fn_esperar = esperar or asyncio.sleep
    fn_ahora = ahora or (lambda: int(time.time()))

    async def _ejecutar_con_cliente(cli: httpx.AsyncClient) -> dict[str, Any]:
        ultimo_estado: int | None = None
        for intento in range(1, REINTENTOS + 1):
            url_valida = validar_url_webhook(url_objetivo, resolver=resolver)
            marca = int(fn_ahora())
            cuerpo = json.dumps(
                {"evento": evento, "marca_tiempo": marca, "datos": datos},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            _, firma = firmar_carga(secreto, cuerpo, marca_tiempo=marca)
            cabeceras = {
                "Content-Type": "application/json",
                "X-Evydentia-Marca-Tiempo": str(marca),
                "X-Evydentia-Firma": firma,
            }
            try:
                respuesta = await cli.post(
                    url_valida,
                    content=cuerpo.encode("utf-8"),
                    headers=cabeceras,
                    follow_redirects=False,
                    timeout=TIMEOUT_SEGUNDOS,
                )
                ultimo_estado = respuesta.status_code
                if 200 <= respuesta.status_code < 300:
                    return {
                        "entregado": True,
                        "intentos": intento,
                        "estado_http": respuesta.status_code,
                    }
            except httpx.HTTPError:
                ultimo_estado = None

            if intento < REINTENTOS:
                await fn_esperar(ESPERAS_REINTENTO[intento - 1])

        return {
            "entregado": False,
            "intentos": REINTENTOS,
            "estado_http": ultimo_estado,
        }

    if cliente is not None:
        return await _ejecutar_con_cliente(cliente)

    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=TIMEOUT_SEGUNDOS,
        transport=transporte,
    ) as cli_propio:
        return await _ejecutar_con_cliente(cli_propio)


async def probar_suscripcion(
    session: AsyncSession,
    tenant_id: str,
    suscripcion_id: str,
    usuario_id: str,
    *,
    resolver: ResolverDNS | None = None,
    transporte: httpx.AsyncBaseTransport | None = None,
    esperar: FuncionEspera | None = None,
) -> dict[str, Any]:
    """Envía un evento 'webhook.prueba' firmado a la suscripción activa del tenant."""
    _cifrador()
    uid = _validar_uuid(suscripcion_id)

    res = await session.execute(
        text(
            """
            SELECT id, tenant_id, url, eventos, secreto_cifrado, activo, creada_en, rotada_en
            FROM webhooks_suscripciones
            WHERE id = :id AND tenant_id = :tenant_id
            """
        ),
        {"id": uid, "tenant_id": tenant_id},
    )
    row = res.mappings().first()
    if not row:
        raise ErrorNegocio(
            "WEBHOOK_NO_ENCONTRADO",
            detail="Suscripción de webhook no encontrada.",
            status_code=404,
        )
    if not row["activo"]:
        raise ErrorNegocio(
            "WEBHOOK_DESACTIVADO",
            detail="No se puede probar un webhook desactivado.",
            status_code=409,
        )

    resultado = await entregar(
        dict(row),
        "webhook.prueba",
        {"mensaje": "Aviso de prueba EVYDENTIA", "suscripcion_id": str(row["id"])},
        resolver=resolver,
        transporte=transporte,
        esperar=esperar,
    )

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="webhook_suscripcion",
        entity_id=str(row["id"]),
        action="probar",
        user_id=usuario_id,
        payload={
            "entregado": resultado["entregado"],
            "intentos": resultado["intentos"],
            "estado_http": resultado["estado_http"],
        },
    )

    return resultado
