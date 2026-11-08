# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Servicio de archivos de plantilla y tokens temporales de descarga (BIB-104).

Ofrece el contrato interno de objetos que BIB-106 amplía con análisis y valida nombres,
tipos MIME y firmas de tokens temporales de descarga de maestros editables (DOCX/XLSX).
"""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Literal
import jwt
from pydantic import Field
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.base import Contrato

FORMATOS_EDITABLES = ("DOCX", "XLSX")

TIPOS_MIME = {
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# === SEC-16 ===
# INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD: la clave se lee al firmar, no al importar. En la nube solo
# vale SESSION_SECRET; el alias SECRET_KEY y la clave fija quedan para desarrollo.
CLAVE_FIRMA_DESARROLLO = "bib-104-descarga-segura-clave-temporal"


# ¤adpa
def secreto_firma_descargas() -> str:
    """Clave de firma de los enlaces de descarga. En la nube, sin `SESSION_SECRET`, lanza `RuntimeError`."""
    from app_core.config import corre_en_cloud_run

    secreto = (os.environ.get("SESSION_SECRET") or "").strip()
    if secreto:
        return secreto
    if corre_en_cloud_run():
        raise RuntimeError(
            "INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD: falta SESSION_SECRET; no se firman enlaces de descarga."
        )
    return (os.environ.get("SECRET_KEY") or "").strip() or CLAVE_FIRMA_DESARROLLO
# === fin SEC-16 ===


AUDIENCIA_TOKEN = "biblioteca_descargas"
ALGORITMO_TOKEN = "HS256"


# ¤adpa
class ObjetoArchivoMaestro(Contrato):
    """Contrato interno de archivo maestro descargable para interoperar con análisis (BIB-106)."""
    plantilla_id: str = Field(min_length=1)
    codigo: str = Field(min_length=1)
    version: str = Field(min_length=1)
    formato: Literal["DOCX", "XLSX"]
    nombre_archivo: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    tamano_bytes: int = Field(gt=0)
    estado_analisis: Literal["limpio", "pendiente", "rechazado"] = "limpio"


# ¤adpa
def tipo_mime(formato: str) -> str:
    """Devuelve el tipo MIME para un formato editable admitido."""
    formato_norm = (formato or "").strip().upper()
    mime = TIPOS_MIME.get(formato_norm)
    if not mime:
        raise ErrorNegocio("BIB_PLANTILLA_NO_DESCARGABLE", f"Formato '{formato}' no es editable (DOCX o XLSX).")
    return mime


# ¤adpa
def limpiar_nombre(nombre: str) -> str:
    """Sanea caracteres no alfanuméricos manteniendo guiones y puntos."""
    seguro = re.sub(r"[^\w.\-]", "_", nombre.strip())
    return re.sub(r"_+", "_", seguro)


# ¤adpa
def nombre_descarga(codigo: str, version: str, formato: str, nombre_original: str | None = None) -> str:
    """Genera el nombre de archivo seguro incluyendo código, versión y formato editable."""
    formato_norm = (formato or "").strip().upper()
    ext = f".{formato_norm.lower()}"
    if not (formato_norm in FORMATOS_EDITABLES):
        raise ErrorNegocio("BIB_PLANTILLA_NO_DESCARGABLE")

    if nombre_original:
        limpio = limpiar_nombre(nombre_original)
        if limpio.lower().endswith(ext):
            limpio = limpio[:-len(ext)]
        return f"{codigo}_v{version}_{limpio}{ext}"
    return f"{codigo}_v{version}{ext}"


# ¤adpa
def generar_token_descarga(
    tenant_id: str,
    usuario_id: str,
    plantilla_id: str,
    version: str,
    expira_segundos: int = 300,
) -> str:
    """Genera un token temporal firmado para autorizar la descarga del archivo maestro."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario_id,
        "tid": tenant_id,
        "pid": plantilla_id,
        "ver": version,
        "exp": ahora + timedelta(seconds=expira_segundos),
        "iat": ahora,
        "aud": AUDIENCIA_TOKEN,
    }
    return jwt.encode(payload, secreto_firma_descargas(), algorithm=ALGORITMO_TOKEN)


# ¤adpa
def verificar_token_descarga(token: str) -> dict:
    """Verifica y decodifica el token temporal firmado de descarga."""
    secreto = secreto_firma_descargas()  # SEC-16: fuera del try; sin clave en la nube es un fallo de configuración
    try:
        return jwt.decode(
            token,
            secreto,
            algorithms=[ALGORITMO_TOKEN],
            audience=AUDIENCIA_TOKEN,
        )
    except jwt.ExpiredSignatureError:
        raise ErrorNegocio("BIB_TOKEN_DESCARGA_INVALIDO", "El enlace temporal de descarga ha caducado.") from None
    except Exception:
        raise ErrorNegocio("BIB_TOKEN_DESCARGA_INVALIDO", "El enlace temporal de descarga no es válido.") from None


# ¤adpa
def cabeceras_descarga(nombre_archivo: str, tamano: int, mime: str) -> dict[str, str]:
    """Cabeceras seguras para streaming de descarga."""
    return {
        "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        "Content-Type": mime,
        "Content-Length": str(tamano),
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
    }
