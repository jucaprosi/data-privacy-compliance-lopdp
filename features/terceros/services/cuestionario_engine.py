"""Motor de cuestionarios de garantías de encargados (TER-02).
`¤terceros` `¤seguridad` `¤evidencias`
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.terceros.domain.cuestionario import (
    CODIGO_ENLACE_NO_VALIDO,
    DIAS_VIGENCIA_DEFAULT,
    DIAS_VIGENCIA_MAX,
    DIAS_VIGENCIA_MIN,
    MAX_TAMANO_ARCHIVO_BYTES,
    PREGUNTAS_TER_02_1,
    VERSION_CUESTIONARIO,
    Cuestionario,
    DecisionRevision,
)
from features.terceros.domain.errores import (
    ARCHIVO_DEMASIADO_GRANDE,
    CODIGO_ENLACE_NO_VALIDO,
    CUESTIONARIO_NO_ENCONTRADO,
    CUESTIONARIO_NO_RESPONDIDO,
    DIAS_VIGENCIA_FUERA_DE_RANGO,
    PROXIMA_REVISION_OBLIGATORIA,
    RESPUESTA_INCOMPLETA,
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def crear_enlace_cuestionario(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    tercero_id: str,
    dias_vigencia: int = DIAS_VIGENCIA_DEFAULT,
) -> tuple[dict[str, Any], str]:
    """R1: Genera un enlace único de un uso con vigencia de 1 a 30 días."""
    if not (DIAS_VIGENCIA_MIN <= dias_vigencia <= DIAS_VIGENCIA_MAX):
        raise ErrorNegocio(DIAS_VIGENCIA_FUERA_DE_RANGO)

    cuestionario_id = str(uuid4())
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    ahora = datetime.now(timezone.utc)
    caduca_en = ahora + timedelta(days=dias_vigencia)

    await session.execute(
        text("""
            INSERT INTO terceros_cuestionarios (
                id, tenant_id, tercero_id, version_cuestionario, token_hash,
                caduca_en, estado, creado_por, creado_en
            ) VALUES (
                :id, :t, :tercero_id, :ver, :th, :caduca, 'enviado', :creado_por, :ahora
            )
        """),
        {
            "id": cuestionario_id,
            "t": tenant_id,
            "tercero_id": str(tercero_id),
            "ver": VERSION_CUESTIONARIO,
            "th": token_hash,
            "caduca": caduca_en,
            "creado_por": user_id,
            "ahora": ahora,
        },
    )

    url = f"/proveedor/{token}"
    datos = {
        "id": cuestionario_id,
        "url": url,
        "caduca_en": caduca_en.isoformat(),
        "token": token,
    }
    return datos, url


async def listar_cuestionarios_tercero(
    session: AsyncSession,
    tenant_id: str,
    tercero_id: str,
) -> list[dict[str, Any]]:
    """Lista los cuestionarios de un tercero en orden cronológico inverso."""
    filas = (
        await session.execute(
            text("""
                SELECT id, tercero_id, version_cuestionario, estado, caduca_en,
                       proxima_revision, creado_en, revisado_en, comentario_revision, informe_sha256
                FROM terceros_cuestionarios
                WHERE tenant_id = :t AND tercero_id = :tid
                ORDER BY creado_en DESC
            """),
            {"t": tenant_id, "tid": str(tercero_id)},
        )
    ).mappings().all()

    return [
        {
            "id": f["id"],
            "tercero_id": f["tercero_id"],
            "version_cuestionario": f["version_cuestionario"],
            "estado": f["estado"],
            "caduca_en": f["caduca_en"].isoformat() if f["caduca_en"] else None,
            "proxima_revision": f["proxima_revision"].isoformat() if f["proxima_revision"] else None,
            "creado_en": f["creado_en"].isoformat() if f["creado_en"] else None,
            "revisado_en": f["revisado_en"].isoformat() if f["revisado_en"] else None,
            "comentario_revision": f["comentario_revision"],
            "informe_sha256": f["informe_sha256"],
        }
        for f in filas
    ]


async def obtener_por_token(
    session: AsyncSession,
    token: str,
) -> dict[str, Any]:
    """R2 & R5: Resuelve el token mediante la función SECURITY DEFINER y valida vigencia y estado."""
    token_hash = _hash_token(token)
    fila = (
        await session.execute(
            text("SELECT id, tenant_id, organizacion, version_cuestionario, caduca_en, estado FROM terceros_cuestionario_por_token(:th)"),
            {"th": token_hash},
        )
    ).mappings().first()

    if not fila:
        raise ErrorNegocio(CODIGO_ENLACE_NO_VALIDO)

    ahora = datetime.now(timezone.utc)
    if fila["estado"] != "enviado" or fila["caduca_en"] < ahora:
        raise ErrorNegocio(CODIGO_ENLACE_NO_VALIDO)

    return {
        "id": fila["id"],
        "tenant_id": fila["tenant_id"],
        "organizacion": fila["organizacion"],
        "caduca_en": fila["caduca_en"].isoformat(),
        "version_cuestionario": fila["version_cuestionario"],
        "preguntas": [p.serializar() for p in PREGUNTAS_TER_02_1],
    }


def validar_respuestas(
    respuestas: dict[str, Any],
    archivos_por_pregunta: dict[str, Any],
) -> None:
    """R3: Valida completitud, tipos y evidencias obligatorias según §1.2."""
    for p in PREGUNTAS_TER_02_1:
        valor = respuestas.get(p.id)

        # Preguntas condicionales
        if p.id == "G07":
            g06 = respuestas.get("G06")
            es_si = g06 is True or str(g06).lower() in ("si", "sí", "true")
            if es_si:
                if not valor or not str(valor).strip():
                    raise ErrorNegocio(RESPUESTA_INCOMPLETA)
                if p.id not in archivos_por_pregunta:
                    raise ErrorNegocio(RESPUESTA_INCOMPLETA)
            continue

        if p.id == "G15":
            g14 = respuestas.get("G14")
            es_si = g14 is True or str(g14).lower() in ("si", "sí", "true")
            if es_si:
                if not valor or not str(valor).strip():
                    raise ErrorNegocio(RESPUESTA_INCOMPLETA)
                if p.id not in archivos_por_pregunta:
                    raise ErrorNegocio(RESPUESTA_INCOMPLETA)
            continue

        # Preguntas obligatorias
        if p.obligatoria:
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                raise ErrorNegocio(RESPUESTA_INCOMPLETA)

        # Validación específica de tipo
        if p.tipo == "si_no_evidencia":
            es_si = valor is True or str(valor).lower() in ("si", "sí", "true")
            if es_si and p.id not in archivos_por_pregunta:
                raise ErrorNegocio(RESPUESTA_INCOMPLETA)


async def responder_cuestionario(
    session: AsyncSession,
    token: str,
    respuestas: dict[str, Any],
    archivos: list[dict[str, Any]],  # [{"pregunta_id": str, "nombre": str, "contenido": bytes, "mime": str}]
) -> dict[str, Any]:
    """R3: Registra las respuestas del proveedor y custodia las evidencias adjuntadas."""
    info = await obtener_por_token(session, token)
    cuestionario_id = info["id"]
    tenant_id = info["tenant_id"]

    archivos_por_pregunta = {a["pregunta_id"]: a for a in archivos}
    validar_respuestas(respuestas, archivos_por_pregunta)

    # Custodia de evidencias mediante pasillo
    from app_core.pasillo.evidencias import custodiar_archivo_proveedor

    evidencias_registradas = []
    for a in archivos:
        contenido = a["contenido"]
        if len(contenido) > MAX_TAMANO_ARCHIVO_BYTES:
            raise ErrorNegocio(ARCHIVO_DEMASIADO_GRANDE)

        custodia = await custodiar_archivo_proveedor(
            session,
            tenant_id,
            contenido=contenido,
            nombre=a["nombre"],
            tipo_mime=a.get("mime", "application/octet-stream"),
        )
        evidencias_registradas.append({
            "pregunta_id": a["pregunta_id"],
            "sha256": custodia.get("sha256", hashlib.sha256(contenido).hexdigest()),
            "nombre": a["nombre"],
            "tamano": len(contenido),
        })

    # Fijar contexto RLS antes de actualizar
    from app_core.db.session import fijar_contexto_rls
    await fijar_contexto_rls(session, tenant_id)

    await session.execute(
        text("""
            UPDATE terceros_cuestionarios
            SET estado = 'respondido',
                respuestas = CAST(:resp AS JSONB),
                evidencias = CAST(:evid AS JSONB)
            WHERE id = :id AND tenant_id = :t
        """),
        {
            "id": cuestionario_id,
            "t": tenant_id,
            "resp": json.dumps(respuestas),
            "evid": json.dumps(evidencias_registradas),
        },
    )

    return {"estado": "respondido"}


def _generar_texto_informe(
    organizacion: str,
    cuestionario: dict[str, Any],
    tercero_nombre: str,
) -> bytes:
    """R7: Genera el informe textual de garantías con cada pregunta, respuesta y cita legal."""
    lineas = [
        "================================================================================",
        f"INFORME DE EVALUACIÓN DE GARANTÍAS DEL ENCARGADO - {VERSION_CUESTIONARIO}",
        "================================================================================",
        f"Organización Responsable: {organizacion}",
        f"Encargado / Proveedor:   {tercero_nombre}",
        f"Cuestionario ID:         {cuestionario['id']}",
        f"Fecha de Evaluación:     {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "================================================================================",
        "",
        "DETALLE DE GARANTÍAS EVALUADAS:",
        "",
    ]

    respuestas = cuestionario.get("respuestas") or {}
    for p in PREGUNTAS_TER_02_1:
        resp = respuestas.get(p.id, "No aplica")
        lineas.append(f"[{p.id}] {p.enunciado}")
        lineas.append(f"    Cita Legal: {p.cita}")
        lineas.append(f"    Respuesta:  {resp}")
        lineas.append("")

    lineas.append("================================================================================")
    lineas.append("FIN DEL INFORME")
    return "\n".join(lineas).encode("utf-8")


async def revisar_cuestionario(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    cuestionario_id: str,
    decision: DecisionRevision,
    comentario: str | None = None,
    proxima_revision: date | None = None,
) -> dict[str, Any]:
    """R4: Aplica la revisión de garantías (conforme, correccion o rechazado)."""
    fila = (
        await session.execute(
            text("""
                SELECT c.*, COALESCE(t.nombre_comercial, t.razon_social, 'Organización') as org_nombre
                FROM terceros_cuestionarios c
                JOIN tenants t ON t.id = c.tenant_id
                WHERE c.id = :id AND c.tenant_id = :t
            """),
            {"id": cuestionario_id, "t": tenant_id},
        )
    ).mappings().first()

    if not fila:
        raise ErrorNegocio(CUESTIONARIO_NO_ENCONTRADO)

    if fila["estado"] == "enviado":
        raise ErrorNegocio(CUESTIONARIO_NO_RESPONDIDO)

    tercero_id = fila["tercero_id"]

    # Obtener nombre del tercero
    tercero_row = (
        await session.execute(
            text("SELECT nombre FROM transferencias_terceros WHERE id = :tid AND tenant_id = :t"),
            {"tid": tercero_id, "t": tenant_id},
        )
    ).mappings().first()
    tercero_nombre = tercero_row["nombre"] if tercero_row else f"Tercero {tercero_id}"

    ahora = datetime.now(timezone.utc)

    if decision == "conforme":
        if proxima_revision is None:
            raise ErrorNegocio(PROXIMA_REVISION_OBLIGATORIA)

        # Generar y custodiar informe
        contenido_informe = _generar_texto_informe(fila["org_nombre"], dict(fila), tercero_nombre)
        from app_core.pasillo.evidencias import custodiar_informe_garantias
        custodia = await custodiar_informe_garantias(
            session,
            tenant_id,
            user_id,
            contenido=contenido_informe,
            nombre=f"Informe_Garantias_{tercero_nombre}_{ahora.strftime('%Y%m%d')}.txt",
        )
        informe_sha256 = custodia.get("sha256", hashlib.sha256(contenido_informe).hexdigest())

        # Actualizar cuestionario
        await session.execute(
            text("""
                UPDATE terceros_cuestionarios
                SET estado = 'conforme',
                    revisado_por = :u,
                    revisado_en = :ahora,
                    comentario_revision = :com,
                    informe_sha256 = :sha,
                    proxima_revision = :prox
                WHERE id = :id AND tenant_id = :t
            """),
            {
                "id": cuestionario_id,
                "t": tenant_id,
                "u": user_id,
                "ahora": ahora,
                "com": comentario,
                "sha": informe_sha256,
                "prox": proxima_revision,
            },
        )

        # Actualizar proxima_revision en transferencias_terceros
        await session.execute(
            text("""
                UPDATE transferencias_terceros
                SET proxima_revision = :prox
                WHERE id = :tid AND tenant_id = :t
            """),
            {"tid": tercero_id, "t": tenant_id, "prox": proxima_revision},
        )

        # Cerrar hallazgo garantia si existe
        from app_core.pasillo.roadmap import cerrar_hallazgo_garantia_tercero
        await cerrar_hallazgo_garantia_tercero(session, tenant_id, user_id, tercero_id)

        return {
            "estado": "conforme",
            "informe_sha256": informe_sha256,
            "proxima_revision": proxima_revision.isoformat(),
        }

    elif decision == "correccion":
        await session.execute(
            text("""
                UPDATE terceros_cuestionarios
                SET estado = 'correccion',
                    revisado_por = :u,
                    revisado_en = :ahora,
                    comentario_revision = :com
                WHERE id = :id AND tenant_id = :t
            """),
            {
                "id": cuestionario_id,
                "t": tenant_id,
                "u": user_id,
                "ahora": ahora,
                "com": comentario,
            },
        )

        # Genera un nuevo cuestionario con vigencia por defecto
        nuevo, url_nueva = await crear_enlace_cuestionario(
            session, tenant_id, user_id, tercero_id, dias_vigencia=DIAS_VIGENCIA_DEFAULT
        )
        return {
            "estado": "correccion",
            "url_nueva": url_nueva,
            "cuestionario_nuevo_id": nuevo["id"],
        }

    elif decision == "rechazado":
        await session.execute(
            text("""
                UPDATE terceros_cuestionarios
                SET estado = 'rechazado',
                    revisado_por = :u,
                    revisado_en = :ahora,
                    comentario_revision = :com
                WHERE id = :id AND tenant_id = :t
            """),
            {
                "id": cuestionario_id,
                "t": tenant_id,
                "u": user_id,
                "ahora": ahora,
                "com": comentario,
            },
        )

        # Abrir hallazgo tercero de severidad alta
        from app_core.pasillo.roadmap import abrir_hallazgo_rechazo_tercero
        await abrir_hallazgo_rechazo_tercero(session, tenant_id, user_id, tercero_id, tercero_nombre)

        return {"estado": "rechazado"}

    raise ValueError(f"Decisión de revisión no reconocida: {decision}")


async def contar_pendientes_revision(session: AsyncSession, tenant_id: str) -> int:
    """Contador de cuestionarios en estado respondido para dpo_cockpit."""
    return (
        await session.execute(
            text("SELECT count(*) FROM terceros_cuestionarios WHERE tenant_id = :t AND estado = 'respondido'"),
            {"t": tenant_id},
        )
    ).scalar() or 0
