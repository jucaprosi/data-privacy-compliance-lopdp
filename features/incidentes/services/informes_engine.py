# ¤incidentes ¤evidencias ¤rbac-tenant
"""Informes de vulneración para la Autoridad y para los titulares (INC-02, R3).

El informe se arma con la última versión de cada sección y se custodia como evidencia por la compuerta
de evidencias (EVI-04, tipo `informe_incidente`): sin documento custodiado no hay fila (no se registra
una huella sin bytes). Regenerar agrega otra fila; la anterior queda. El informe lo firma quien lo emite.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from features.incidentes.domain.vulneracion import (
    DESTINOS,
    ROLES_INFORMES,
    SECCION_DECISION,
    RolNoAutorizado,
    destinos_de,
    informe_texto,
)
from features.incidentes.services.asistente_engine import datos_para_informe

TIPO_EVIDENCIA = "informe_incidente"
TIPO_MIME = "text/plain"
# Controles del banco de preguntas (D08): 58 «Registro y bitácora de incidentes» para la Autoridad y
# 62 «Comunicación a titulares afectados» para los titulares.
CONTROLES: dict[str, list[str]] = {"spdp": ["P58"], "titulares": ["P62"]}
NOMBRES: dict[str, str] = {"spdp": "informe-autoridad", "titulares": "comunicacion-titulares"}


async def generar_informe(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    rol: str,
    incidente_id: str,
    destino: str,
    custodiar,
    almacen: Optional[Any] = None,
) -> dict[str, str]:
    """Genera y custodia el informe; devuelve {sha256, evidencia_id}. `custodiar` es la capacidad de EVI-04."""
    if rol not in ROLES_INFORMES:
        raise RolNoAutorizado(f"El rol {rol!r} no genera informes.")
    if destino not in DESTINOS:
        raise ErrorNegocio("SECCION_INCOMPLETA", detail="Destino no admitido.")
    await fijar_contexto_rls(session, tenant_id, user_id)
    titulo, estado = await datos_para_informe(session, tenant_id, incidente_id)
    estado.exigir_previas(SECCION_DECISION + 1)
    if destino not in destinos_de(estado.decision):
        raise ErrorNegocio("INFORME_NO_PEDIDO")
    contenido = informe_texto(destino, titulo, estado.secciones).encode("utf-8")
    extra = {"almacen": almacen} if almacen is not None else {}
    custodia = await custodiar(
        session, tenant_id, user_id,
        contenido=contenido, tipo_mime=TIPO_MIME, tipo_evidencia=TIPO_EVIDENCIA,
        control_refs=CONTROLES[destino], nombre=f"{NOMBRES[destino]}-{incidente_id[:8]}.txt", **extra,
    )
    await session.execute(
        text(
            "INSERT INTO incidentes_informes (id, tenant_id, incidente_id, destino, sha256, evidencia_id, emitido_por) "
            "VALUES (:id, :t, :i, :d, :h, :e, :u)"
        ),
        {
            "id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "d": destino,
            "h": custodia["sha256"], "e": custodia["evidencia_id"], "u": user_id,
        },
    )
    await registrar_evento(
        session, tenant_id, "incidente", incidente_id, "informe_generado", user_id,
        {"destino": destino, "sha256": custodia["sha256"], "evidencia_id": custodia["evidencia_id"]},
    )
    return {"sha256": custodia["sha256"], "evidencia_id": custodia["evidencia_id"]}
