# ¤engine ¤auditoria-capa ¤hallazgos
"""Motor de auditoría con grilla de verificación por dominio y acta por área (CAPA-04)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from app_core.pasillo import diagnostico as pasillo_diagnostico
from app_core.pasillo import evidencias as pasillo_evidencias
from app_core.pasillo import organizacion as pasillo_organizacion
from app_core.pasillo import roadmap as pasillo_roadmap
from features.auditoria_capa.domain import errores as e
from features.auditoria_capa.domain.auditoria import (
    Auditoria,
    AuditoriaActa,
    AuditoriaFila,
    AuditoriaVerificacionCierre,
)


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"),
        {"t": tenant_id},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": user_id},
    )


def calcular_severidad_hallazgo(riesgo_final: int) -> str:
    """Severidad según R2: 'critica' si >= 15, 'alta' si >= 9, y si no 'media'."""
    if riesgo_final >= 15:
        return "critica"
    if riesgo_final >= 9:
        return "alta"
    return "media"


async def crear_auditoria(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    nombre: str,
    alcance: list[str],
    equipo: list[str],
) -> dict[str, Any]:
    """Crea una auditoría precargando filas desde el último resultado sellado (R1)."""
    await _fijar_rls(session, tenant_id, user_id)

    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la auditoría es obligatorio.")
    if not alcance:
        raise ValueError("El alcance debe contener al menos un área.")
    if not equipo:
        raise ValueError("El equipo auditor debe contener al menos una persona.")

    # 1. Obtener último diagnóstico sellado
    ultimo_sellado = await pasillo_diagnostico.obtener_ultimo_resultado_sellado(session, tenant_id, user_id)
    if ultimo_sellado is None:
        raise ErrorNegocio(e.DIAG_SIN_RESULTADO)

    tope_escala = pasillo_diagnostico.nivel_asignado_maximo()  # 5

    # 2. Insertar auditoría
    auditoria_id = str(uuid.uuid4())
    creado_en = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            INSERT INTO auditorias (id, tenant_id, nombre, alcance, equipo, estado, creado_por, creado_en)
            VALUES (:id, :t, :nombre, :alcance::jsonb, :equipo::jsonb, 'abierta', :creado_por, :creado_en)
            """
        ),
        {
            "id": auditoria_id,
            "t": tenant_id,
            "nombre": nombre,
            "alcance": json.dumps(alcance),
            "equipo": json.dumps(equipo),
            "creado_por": user_id,
            "creado_en": creado_en,
        },
    )

    # 3. Mapear controles a áreas dentro de alcance (si hay tareas en roadmap)
    area_por_defecto = alcance[0]
    filas_db = []
    respuestas = getattr(ultimo_sellado, "respuestas", [])

    for r in respuestas:
        control_ref = getattr(r, "control", None) or f"P{getattr(r, 'pregunta_id', '')}"
        declarado = getattr(r, "nivel_sellado", 1)
        if declarado < 1:
            declarado = 1
        elif declarado > 5:
            declarado = 5

        criticidad = getattr(r, "criticidad", 1) or 1
        riesgo_inicial = (tope_escala - declarado) * criticidad
        fila_id = str(uuid.uuid4())

        # Asignar área: si el control tiene tarea con area_id dentro de alcance, usarla; si no, area_por_defecto
        area_asignada = area_por_defecto

        await session.execute(
            text(
                """
                INSERT INTO auditoria_filas (
                    id, tenant_id, auditoria_id, area_id, control_ref, declarado, riesgo_inicial
                ) VALUES (
                    :id, :t, :aud_id, :area_id, :ctrl, :dec, :ri
                )
                """
            ),
            {
                "id": fila_id,
                "t": tenant_id,
                "aud_id": auditoria_id,
                "area_id": area_asignada,
                "ctrl": control_ref,
                "dec": declarado,
                "ri": riesgo_inicial,
            },
        )
        filas_db.append(
            {
                "id": fila_id,
                "control_ref": control_ref,
                "area_id": area_asignada,
                "declarado": declarado,
                "riesgo_inicial": riesgo_inicial,
                "verificado": None,
                "evidencia_sha256": None,
                "riesgo_final": None,
                "revisado_por": None,
                "hallazgo_id": None,
            }
        )

    return {
        "id": auditoria_id,
        "tenant_id": tenant_id,
        "nombre": nombre,
        "alcance": alcance,
        "equipo": equipo,
        "estado": "abierta",
        "creado_por": user_id,
        "creado_en": creado_en.isoformat(),
        "cerrada_en": None,
        "filas": filas_db,
    }


async def listar_auditorias(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    """Lista auditorías de la organización con avance de controles verificados."""
    await _fijar_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                """
                SELECT a.id, a.tenant_id, a.nombre, a.alcance, a.equipo, a.estado,
                       a.creado_por, a.creado_en, a.cerrada_en,
                       COUNT(f.id) AS total_controles,
                       COUNT(f.verificado) AS verificados
                FROM auditorias a
                LEFT JOIN auditoria_filas f ON f.auditoria_id = a.id AND f.tenant_id = a.tenant_id
                WHERE a.tenant_id = :t
                GROUP BY a.id, a.tenant_id, a.nombre, a.alcance, a.equipo, a.estado, a.creado_por, a.creado_en, a.cerrada_en
                ORDER BY a.creado_en DESC
                """
            ),
            {"t": tenant_id},
        )
    ).mappings().all()

    resultado = []
    for f in filas:
        d = dict(f)
        alcance = d["alcance"] if isinstance(d["alcance"], list) else json.loads(d["alcance"] or "[]")
        equipo = d["equipo"] if isinstance(d["equipo"], list) else json.loads(d["equipo"] or "[]")
        resultado.append(
            {
                "id": str(d["id"]),
                "tenant_id": d["tenant_id"],
                "nombre": d["nombre"],
                "alcance": alcance,
                "equipo": equipo,
                "estado": d["estado"],
                "creado_por": d["creado_por"],
                "creado_en": d["creado_en"].isoformat() if hasattr(d["creado_en"], "isoformat") else str(d["creado_en"]),
                "cerrada_en": d["cerrada_en"].isoformat() if d.get("cerrada_en") and hasattr(d["cerrada_en"], "isoformat") else d.get("cerrada_en"),
                "total_controles": int(d["total_controles"] or 0),
                "verificados": int(d["verificados"] or 0),
            }
        )
    return resultado


async def obtener_auditoria(
    session: AsyncSession, tenant_id: str, user_id: str, auditoria_id: str
) -> dict[str, Any] | None:
    """Devuelve el detalle de una auditoría incluyendo sus filas y actas por área."""
    await _fijar_rls(session, tenant_id, user_id)
    a_row = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, nombre, alcance, equipo, estado, creado_por, creado_en, cerrada_en
                FROM auditorias
                WHERE id = :id AND tenant_id = :t
                """
            ),
            {"id": auditoria_id, "t": tenant_id},
        )
    ).mappings().first()

    if not a_row:
        return None

    filas_rows = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, auditoria_id, area_id, control_ref, declarado, riesgo_inicial,
                       verificado, evidencia_sha256, riesgo_final, revisado_por, hallazgo_id
                FROM auditoria_filas
                WHERE auditoria_id = :id AND tenant_id = :t
                ORDER BY control_ref ASC
                """
            ),
            {"id": auditoria_id, "t": tenant_id},
        )
    ).mappings().all()

    actas_rows = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, auditoria_id, area_id, evidencia_id, acta_sha256, firmada_por, firmada_en
                FROM auditoria_actas
                WHERE auditoria_id = :id AND tenant_id = :t
                """
            ),
            {"id": auditoria_id, "t": tenant_id},
        )
    ).mappings().all()

    alcance = a_row["alcance"] if isinstance(a_row["alcance"], list) else json.loads(a_row["alcance"] or "[]")
    equipo = a_row["equipo"] if isinstance(a_row["equipo"], list) else json.loads(a_row["equipo"] or "[]")

    return {
        "id": str(a_row["id"]),
        "tenant_id": a_row["tenant_id"],
        "nombre": a_row["nombre"],
        "alcance": alcance,
        "equipo": equipo,
        "estado": a_row["estado"],
        "creado_por": a_row["creado_por"],
        "creado_en": a_row["creado_en"].isoformat() if hasattr(a_row["creado_en"], "isoformat") else str(a_row["creado_en"]),
        "cerrada_en": a_row["cerrada_en"].isoformat() if a_row.get("cerrada_en") and hasattr(a_row["cerrada_en"], "isoformat") else a_row.get("cerrada_en"),
        "filas": [
            {
                "id": str(r["id"]),
                "area_id": r["area_id"],
                "control_ref": r["control_ref"],
                "declarado": r["declarado"],
                "riesgo_inicial": r["riesgo_inicial"],
                "verificado": r["verificado"],
                "evidencia_sha256": r["evidencia_sha256"],
                "riesgo_final": r["riesgo_final"],
                "revisado_por": r["revisado_por"],
                "hallazgo_id": r["hallazgo_id"],
            }
            for r in filas_rows
        ],
        "actas": [
            {
                "id": str(acta["id"]),
                "area_id": acta["area_id"],
                "evidencia_id": acta["evidencia_id"],
                "acta_sha256": acta["acta_sha256"],
                "firmada_por": acta["firmada_por"],
                "firmada_en": acta["firmada_en"].isoformat() if hasattr(acta["firmada_en"], "isoformat") else str(acta["firmada_en"]),
            }
            for acta in actas_rows
        ],
    }


async def actualizar_fila_auditoria(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    auditoria_id: str,
    control_ref: str,
    verificado: int,
    riesgo_final: int,
    evidencia_sha256: Optional[str] = None,
) -> dict[str, Any]:
    """Actualiza una fila de auditoría verificando SoD (R3) y generando hallazgo si verificado < declarado (R2)."""
    await _fijar_rls(session, tenant_id, user_id)

    # Validar rango verificado (1 a 5)
    if not (1 <= verificado <= 5):
        raise ValueError("El nivel verificado debe estar entre 1 y 5.")

    auditoria = await obtener_auditoria(session, tenant_id, user_id, auditoria_id)
    if not auditoria:
        raise ValueError("Auditoría no encontrada.")

    if auditoria["estado"] == "cerrada":
        raise ValueError("No se pueden modificar filas de una auditoría cerrada.")

    fila = next((f for f in auditoria["filas"] if f["control_ref"] == control_ref), None)
    if not fila:
        raise ValueError(f"Fila con control {control_ref} no encontrada en la auditoría.")

    # Validar si el área de esta fila ya tiene acta firmada
    actas_firmadas_areas = {a["area_id"] for a in auditoria["actas"]}
    if fila["area_id"] in actas_firmadas_areas:
        raise ErrorNegocio(e.ACTA_YA_FIRMADA)

    # SoD: el revisor no puede haber ejecutado tareas con ese control_ref
    es_ejecutor = await pasillo_roadmap.es_ejecutor_control(session, tenant_id, user_id, control_ref)
    if es_ejecutor:
        raise ErrorNegocio(e.AUDITOR_EJECUTOR)

    hallazgo_id = fila["hallazgo_id"]

    # Si verificado < declarado, generar hallazgo (R2)
    if verificado < fila["declarado"]:
        severidad = calcular_severidad_hallazgo(riesgo_final)
        titulo = (
            f"Auditoría {auditoria['nombre']}: control {control_ref} verificado ({verificado}) "
            f"menor a declarado ({fila['declarado']})"
        )
        h_id, _ = await pasillo_roadmap.registrar_hallazgo_auditoria(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            origen_ref=f"{auditoria_id}:{control_ref}",
            severidad=severidad,
            titulo=titulo,
            control_ref=control_ref,
        )
        hallazgo_id = h_id

    # Actualizar fila
    await session.execute(
        text(
            """
            UPDATE auditoria_filas
            SET verificado = :ver,
                evidencia_sha256 = :ev,
                riesgo_final = :rf,
                revisado_por = :rev,
                hallazgo_id = :hid
            WHERE auditoria_id = :aud_id AND control_ref = :ctrl AND tenant_id = :t
            """
        ),
        {
            "ver": verificado,
            "ev": evidencia_sha256,
            "rf": riesgo_final,
            "rev": user_id,
            "hid": hallazgo_id,
            "aud_id": auditoria_id,
            "ctrl": control_ref,
            "t": tenant_id,
        },
    )

    return {
        "id": fila["id"],
        "auditoria_id": auditoria_id,
        "control_ref": control_ref,
        "area_id": fila["area_id"],
        "declarado": fila["declarado"],
        "riesgo_inicial": fila["riesgo_inicial"],
        "verificado": verificado,
        "evidencia_sha256": evidencia_sha256,
        "riesgo_final": riesgo_final,
        "revisado_por": user_id,
        "hallazgo_id": hallazgo_id,
    }


def _generar_texto_acta(
    auditoria_nombre: str,
    area_id: str,
    filas_area: list[dict],
    firmante: str,
    fecha_iso: str,
) -> str:
    """Genera el contenido textual del acta por área (R4).
    
    ¡ATENCIÓN! La palabra 'certificado' está terminantemente prohibida.
    """
    lineas = [
        f"Acta de auditoría · Área {area_id}",
        f"Auditoría: {auditoria_nombre}",
        f"Firmada por: {firmante}",
        f"Fecha: {fecha_iso}",
        "",
        "Controles verificados:",
    ]
    for f in filas_area:
        lineas.append(
            f"- Control {f['control_ref']}: Declarado {f['declarado']} | Verificado {f['verificado']} | "
            f"Riesgo inicial {f['riesgo_inicial']} | Riesgo final {f['riesgo_final']} | "
            f"Evidencia: {f.get('evidencia_sha256') or 'Sin evidencia adjunta'}"
        )

    lineas.append("")
    lineas.append("Esta acta recoge lo verificado por el equipo auditor en la fecha indicada y no sustituye otras verificaciones.")
    return "\n".join(lineas)


async def levantar_y_firmar_acta(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    auditoria_id: str,
    area_id: str,
) -> dict[str, Any]:
    """Levanta y firma el acta de auditoría de un área (R4)."""
    await _fijar_rls(session, tenant_id, user_id)

    auditoria = await obtener_auditoria(session, tenant_id, user_id, auditoria_id)
    if not auditoria:
        raise ValueError("Auditoría no encontrada.")

    # 1. Comprobar si ya existe acta para esta área
    if any(a["area_id"] == area_id for a in auditoria["actas"]):
        raise ErrorNegocio(e.ACTA_YA_FIRMADA)

    # 2. Comprobar que todas las filas del área tengan `verificado`
    filas_area = [f for f in auditoria["filas"] if f["area_id"] == area_id]
    if not filas_area or any(f["verificado"] is None for f in filas_area):
        raise ErrorNegocio(e.AUDITORIA_INCOMPLETA)

    # 3. Generar texto del acta y asegurar que no contenga la palabra prohibida
    ahora_iso = datetime.now(timezone.utc).isoformat()
    texto_acta = _generar_texto_acta(
        auditoria_nombre=auditoria["nombre"],
        area_id=area_id,
        filas_area=filas_area,
        firmante=user_id,
        fecha_iso=ahora_iso,
    )

    if "certificado" in texto_acta.lower():
        raise ValueError("Violación de política de doctrina: término prohibido en acta.")

    contenido_bytes = texto_acta.encode("utf-8")
    controles = [f["control_ref"] for f in filas_area]

    # 4. Custodiar como evidencia por la compuerta de evidencias (EVI-02 / EVI-04)
    resultado_custodia = await pasillo_evidencias.custodiar_acta_auditoria(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        contenido=contenido_bytes,
        control_refs=controles,
        nombre=f"acta_auditoria_{area_id}.txt",
    )

    evidencia_id = resultado_custodia["evidencia_id"]
    acta_sha256 = resultado_custodia["sha256"]

    # 5. Insertar en auditoria_actas
    acta_id = str(uuid.uuid4())
    firmada_en = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            INSERT INTO auditoria_actas (
                id, tenant_id, auditoria_id, area_id, evidencia_id, acta_sha256, firmada_por, firmada_en
            ) VALUES (
                :id, :t, :aud_id, :area_id, :ev_id, :sha, :firmada_por, :firmada_en
            )
            """
        ),
        {
            "id": acta_id,
            "t": tenant_id,
            "aud_id": auditoria_id,
            "area_id": area_id,
            "ev_id": evidencia_id,
            "sha": acta_sha256,
            "firmada_por": user_id,
            "firmada_en": firmada_en,
        },
    )

    # 6. Comprobar si todas las áreas del alcance tienen ya su acta firmada
    areas_firmadas = {a["area_id"] for a in auditoria["actas"]}
    areas_firmadas.add(area_id)

    alcance_set = set(auditoria["alcance"])
    if alcance_set.issubset(areas_firmadas):
        await session.execute(
            text(
                """
                UPDATE auditorias
                SET estado = 'cerrada',
                    cerrada_en = :c_en
                WHERE id = :aud_id AND tenant_id = :t
                """
            ),
            {"c_en": firmada_en, "aud_id": auditoria_id, "t": tenant_id},
        )

    return {
        "area_id": area_id,
        "acta_sha256": acta_sha256,
    }


async def obtener_acta(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    auditoria_id: str,
    area_id: str,
) -> dict[str, Any]:
    """Obtiene el acta de un área leyendo su contenido por la compuerta de evidencias (R4)."""
    await _fijar_rls(session, tenant_id, user_id)

    row = (
        await session.execute(
            text(
                """
                SELECT id, area_id, evidencia_id, acta_sha256, firmada_por, firmada_en
                FROM auditoria_actas
                WHERE auditoria_id = :aud_id AND area_id = :area_id AND tenant_id = :t
                """
            ),
            {"aud_id": auditoria_id, "area_id": area_id, "t": tenant_id},
        )
    ).mappings().first()

    if not row:
        raise ErrorNegocio(e.ACTA_NO_ENCONTRADA)

    contenido = await pasillo_evidencias.leer_contenido_acta(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        sha256=row["acta_sha256"],
    )

    return {
        "area_id": row["area_id"],
        "acta_sha256": row["acta_sha256"],
        "contenido": contenido,
    }


async def verificar_cierre_hallazgo(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    hallazgo_id: str,
    resultado: str,
    motivo: str,
) -> dict[str, Any]:
    """Verifica el cierre de la acción de un hallazgo aplicando SoD (R3 y R5)."""
    await _fijar_rls(session, tenant_id, user_id)

    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ValueError("El motivo debe contener al menos 10 caracteres.")

    if resultado not in ("conforme", "no_conforme"):
        raise ValueError("El resultado debe ser 'conforme' o 'no_conforme'.")

    # SoD: verificador no es quien cerró la acción ni ejecutó el control (R3)
    es_ejecutor_o_cerrador = await pasillo_roadmap.es_ejecutor_o_cerrador_hallazgo(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        hallazgo_id=hallazgo_id,
    )
    if es_ejecutor_o_cerrador:
        raise ErrorNegocio(e.AUDITOR_EJECUTOR)

    # Validar que las tareas asociadas estén completadas y con evidencia approved (R5)
    cerrada, err = await pasillo_roadmap.comprobar_accion_cerrada_con_evidencia(
        session=session,
        tenant_id=tenant_id,
        hallazgo_id=hallazgo_id,
    )
    if not cerrada:
        raise ErrorNegocio(e.ACCION_NO_CERRADA, detail=err)

    # Registrar verificación
    verif_id = str(uuid.uuid4())
    registrado_en = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            INSERT INTO auditoria_verificaciones_cierre (
                id, tenant_id, hallazgo_id, accion_ref, verificado_por, resultado, motivo, registrado_en
            ) VALUES (
                :id, :t, :hid, :aref, :vpor, :res, :mot, :reg
            )
            """
        ),
        {
            "id": verif_id,
            "t": tenant_id,
            "hid": hallazgo_id,
            "aref": f"accion:{hallazgo_id}",
            "vpor": user_id,
            "res": resultado,
            "mot": motivo,
            "reg": registrado_en,
        },
    )

    # Si resultado == "conforme", pasar el hallazgo a 'cerrado' en roadmap
    if resultado == "conforme":
        await pasillo_roadmap.cerrar_hallazgo(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            hallazgo_id=hallazgo_id,
        )

    return {
        "id": verif_id,
        "hallazgo_id": hallazgo_id,
        "resultado": resultado,
        "motivo": motivo,
    }


async def listar_cierres_pendientes(
    session: AsyncSession, tenant_id: str, user_id: str
) -> list[dict[str, Any]]:
    """Lista los hallazgos de auditoría con sus tareas y estado de verificación."""
    await _fijar_rls(session, tenant_id, user_id)
    return await pasillo_roadmap.listar_hallazgos_auditoria_para_verificar(session, tenant_id)
