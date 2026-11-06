# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Descarga controlada de plantillas Word/Excel (BIB-104).

Comprueba actor, empresa de contexto, permisos y estado publicado en el servidor.
Genera enlaces temporales firmados, gestiona el streaming seguro de archivos maestros
y registra la auditoría con RLS forzado en `biblioteca_descargas`, sin atribuir
cumplimiento legal automático.
"""
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.base import Contrato
from features.biblioteca.services.archivos import (
    FORMATOS_EDITABLES,
    cabeceras_descarga,
    generar_token_descarga,
    nombre_descarga,
    tipo_mime,
    verificar_token_descarga,
)

AVISO_LEGAL_DESCARGA = "La descarga de esta plantilla no atribuye cumplimiento legal automático de la LOPDP."


# ¤adpa
class EnlaceDescarga(Contrato):
    """Enlace temporal y metadatos de la descarga segura."""
    plantilla_id: str
    codigo: str
    version: str
    formato: str
    nombre_archivo: str
    url_descarga: str
    expira_en_segundos: int
    aviso_legal: str = AVISO_LEGAL_DESCARGA


# ¤adpa
async def fijar_contexto(session: AsyncSession, tenant_id: str, usuario_id: str) -> None:
    """Fija tenant_id y user_id en la sesión para que actúe la RLS."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true), "
             "set_config('app.current_user_id', :u, true)"),
        {"t": tenant_id, "u": usuario_id},
    )


# ¤adpa
async def verificar_miembro_activo(session: AsyncSession) -> None:
    """Comprueba que el actor sea miembro activo de la empresa de contexto."""
    activo = (await session.execute(text("SELECT biblioteca_miembro_activo()"))).scalar()
    if not activo:
        raise ErrorNegocio("BIB_DESCARGA_DENEGADA")


# ¤adpa
async def _obtener_version(session: AsyncSession, plantilla_id: str) -> dict:
    """Obtiene la fila de la versión en biblioteca_versiones."""
    fila = (await session.execute(
        text("SELECT id, codigo, version, formato, estado, nombre_archivo, sha256, archivo "
             "FROM biblioteca_versiones WHERE id = :id"),
        {"id": plantilla_id},
    )).mappings().first()
    if not fila:
        raise ErrorNegocio("BIB_PLANTILLA_NO_DISPONIBLE")
    return dict(fila)


# ¤adpa
def _validar_descargable(version: dict) -> None:
    """Valida que la versión esté publicada, en formato editable y con archivo."""
    # Mutación decisiva BIB-104: permitir descarga de versión retirada debe hacer fallar los tests de permisos.
    if version["estado"] != "publicada":
        raise ErrorNegocio("BIB_DESCARGA_DENEGADA", "Solo se pueden descargar versiones publicadas.")
    if version["formato"] not in FORMATOS_EDITABLES:
        raise ErrorNegocio(
            "BIB_PLANTILLA_NO_DESCARGABLE",
            f"El formato {version['formato']} no es editable para descarga directa.",
        )
    if not version.get("archivo"):
        raise ErrorNegocio("BIB_ARCHIVO_NO_DISPONIBLE")


# ¤adpa
async def registrar_auditoria_descarga(
    session: AsyncSession,
    tenant_id: str,
    usuario_id: str,
    plantilla_id: str,
    version: str,
) -> str:
    """Registra la auditoría en biblioteca_descargas bajo RLS forzada."""
    registro_id = str(uuid4())
    await session.execute(
        text("""
            INSERT INTO biblioteca_descargas (id, tenant_id, usuario_id, plantilla_id, version)
            VALUES (:id, :t, :u, :p, :v)
        """),
        {"id": registro_id, "t": tenant_id, "u": usuario_id, "p": plantilla_id, "v": version},
    )
    return registro_id


# ¤adpa
async def generar_enlace_descarga(
    session: AsyncSession,
    tenant_id: str,
    usuario_id: str,
    plantilla_id: str,
    duracion_segundos: int = 300,
) -> EnlaceDescarga:
    """Prepara la descarga generando un enlace temporal firmado."""
    await fijar_contexto(session, tenant_id, usuario_id)
    await verificar_miembro_activo(session)

    version = await _obtener_version(session, plantilla_id)
    _validar_descargable(version)

    token = generar_token_descarga(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        plantilla_id=plantilla_id,
        version=version["version"],
        expira_segundos=duracion_segundos,
    )
    nombre = nombre_descarga(
        codigo=version["codigo"],
        version=version["version"],
        formato=version["formato"],
        nombre_original=version.get("nombre_archivo"),
    )
    url_relativa = f"/api/v1/biblioteca/descargas/{plantilla_id}/archivo?token={token}"

    return EnlaceDescarga(
        plantilla_id=plantilla_id,
        codigo=version["codigo"],
        version=version["version"],
        formato=version["formato"],
        nombre_archivo=nombre,
        url_descarga=url_relativa,
        expira_en_segundos=duracion_segundos,
        aviso_legal=AVISO_LEGAL_DESCARGA,
    )


# ¤adpa
async def ejecutar_descarga(
    session: AsyncSession,
    tenant_id: str,
    usuario_id: str,
    plantilla_id: str,
    token: str | None = None,
) -> tuple[bytes, str, str, dict[str, str]]:
    """Ejecuta la descarga controlada, audita la acción y devuelve los bytes y cabeceras."""
    if token:
        datos_token = verificar_token_descarga(token)
        if datos_token.get("pid") != plantilla_id or datos_token.get("tid") != tenant_id:
            raise ErrorNegocio("BIB_TOKEN_DESCARGA_INVALIDO")

    await fijar_contexto(session, tenant_id, usuario_id)
    await verificar_miembro_activo(session)

    version = await _obtener_version(session, plantilla_id)
    _validar_descargable(version)

    archivo_bytes = version["archivo"]
    if isinstance(archivo_bytes, memoryview):
        archivo_bytes = bytes(archivo_bytes)

    await registrar_auditoria_descarga(
        session, tenant_id, usuario_id, plantilla_id, version["version"]
    )

    nombre = nombre_descarga(
        codigo=version["codigo"],
        version=version["version"],
        formato=version["formato"],
        nombre_original=version.get("nombre_archivo"),
    )
    mime = tipo_mime(version["formato"])
    cabeceras = cabeceras_descarga(nombre, len(archivo_bytes), mime)

    return archivo_bytes, nombre, mime, cabeceras
