# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""«Mi plantilla» (BIB-103): copia versionada de una plantilla SMARTCIDI para la organización de la sesión.

Editar una plantilla SMARTCIDI nunca la cambia: crea la versión 1 de una copia privada (RLS por organización,
solo INSERT). La plantilla original no se toca; las ediciones siguientes serán versiones nuevas de la copia.
"""
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.services.ficha import fijar_contexto

SQL_ES_COPIA = "SELECT 1 FROM biblioteca_mis_plantillas WHERE plantilla_id=:id LIMIT 1"
SQL_ORIGEN = ("SELECT v.id, v.codigo, v.version, v.cuerpo_md, c.nombre FROM biblioteca_versiones v "
              "LEFT JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
              "WHERE v.id=:id AND v.estado='publicada' AND v.formato='MD'")
SQL_INSERTAR = (
    "INSERT INTO biblioteca_mis_plantillas(id, plantilla_id, version, tenant_id, codigo, nombre, cuerpo_md, sha256, "
    "origen_plantilla_id, origen_version, creada_por) VALUES (:id, :id, 1, :tenant, :codigo, :nombre, :cuerpo, "
    "encode(sha256(convert_to(CAST(:cuerpo AS text),'UTF8')),'hex'), :origen, :origen_version, :usuario)")


# ¤adpa
async def crear_copia(session: AsyncSession, usuario_id: str, tenant_id: str, plantilla_id: str) -> dict:
    """Crea «Mi plantilla» v1 desde una plantilla SMARTCIDI publicada, en la organización de la sesión."""
    await fijar_contexto(session, usuario_id, tenant_id)
    if (await session.execute(text(SQL_ES_COPIA), {"id": plantilla_id})).first() is not None:
        raise ErrorNegocio("BIB_COPIA_SOLO_SMARTCIDI")
    origen = (await session.execute(text(SQL_ORIGEN), {"id": plantilla_id})).mappings().first()
    if origen is None:
        raise ErrorNegocio("BIB_PLANTILLA_NO_ENCONTRADA")
    nuevo = str(uuid4())
    nombre = f"Mi plantilla: {origen['nombre'] or origen['codigo']}"[:200]
    await session.execute(text(SQL_INSERTAR), {
        "id": nuevo, "tenant": tenant_id, "codigo": origen["codigo"], "nombre": nombre, "cuerpo": origen["cuerpo_md"],
        "origen": origen["id"], "origen_version": origen["version"], "usuario": usuario_id})
    return {"id": nuevo, "fuente": "organizacion", "nombre": nombre, "version": 1,
            "origen_plantilla_id": origen["id"], "origen_version": origen["version"]}
