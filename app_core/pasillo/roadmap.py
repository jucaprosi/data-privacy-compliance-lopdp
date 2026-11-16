# ¤adpa
"""Capacidades de la sala Hoja de Ruta para otras salas."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_hallazgo_de_control_vencido(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
    control_ref: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.control_periodico.value,
        origen_ref=origen_ref,
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
    )


async def cerrar_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.cerrar_hallazgo(session, tenant_id, user_id, hallazgo_id)


# === RAT-05 ===
async def registrar_hallazgo_rat(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str],
    dimension: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.rat.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
        dimension=dimension,
    )


async def listar_hallazgos_rat(session: AsyncSession, tenant_id: str, user_id: str) -> list:
    from features.roadmap import roadmap_service

    return await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, origen=roadmap_service.OrigenHallazgo.rat.value
    )


async def reabrir_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.reabrir_hallazgo(session, tenant_id, user_id, hallazgo_id)
# === fin RAT-05 ===


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===


# === DEMO-03c ===
# ¤demo Copia y siembra de la sala para la demo «Cooperativa Demo»; la lógica vive en el motor de la sala.
async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: dict) -> dict:
    from features.roadmap import roadmap_service

    return await roadmap_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03c ===


# === ORG-15 ===
# ¤cartera
async def contar_hallazgos_abiertos(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Hallazgos en estado `abierto` de la organización (fija su contexto RLS)."""
    from features.roadmap import roadmap_service

    abiertos = await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, estado=roadmap_service.EstadoHallazgo.abierto.value
    )
    return len(abiertos)


async def contar_tareas_vencidas(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Tareas sin completar con fecha de fin anterior a hoy en la zona de negocio (fija su contexto RLS)."""
    from features.roadmap import roadmap_service

    return await roadmap_service.contar_tareas_vencidas(session, tenant_id, user_id)
# === fin ORG-15 ===

# === DIAG-12 ===
# ¤roadmap ¤diagnostico-estados Lectura de las tareas cerradas con evidencia validada, para los estados del diagnóstico.
async def tareas_cerradas_con_evidencia_validada(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Tareas cerradas con evidencia aprobada por el DPO; la consulta vive en la sala Hoja de Ruta."""
    from features.roadmap import roadmap_service

    return await roadmap_service.tareas_cerradas_con_evidencia_validada(session, tenant_id, user_id)
# === fin DIAG-12 ===

# === DIAG-07 ===
# Sección reservada para DIAG-07.
# === fin DIAG-07 ===


# === CAPA-04 ===
async def registrar_hallazgo_auditoria(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str] = None,
) -> tuple[str, bool]:
    """Registra un hallazgo de auditoría (R2)."""
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.auditoria.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
    )


async def es_ejecutor_control(session: AsyncSession, tenant_id: str, user_id: str, control_ref: str) -> bool:
    """True si el usuario es owner de alguna tarea vinculada al control_ref (R3 SoD)."""
    from sqlalchemy import text

    row = (
        await session.execute(
            text("SELECT 1 FROM roadmap_tasks WHERE tenant_id = :t AND control_ref = :c AND owner = :u LIMIT 1"),
            {"t": tenant_id, "c": control_ref, "u": user_id},
        )
    ).scalar_one_or_none()
    return row is not None


async def es_ejecutor_o_cerrador_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> bool:
    """True si el usuario cerró la acción del plan o es ejecutor del control del hallazgo (R3 SoD)."""
    from sqlalchemy import text

    row = (
        await session.execute(
            text(
                """
                SELECT 1 FROM roadmap_tasks t
                WHERE t.tenant_id = :t AND t.hallazgo_id = :h
                  AND (
                    t.owner = :u
                    OR EXISTS (
                        SELECT 1 FROM task_audit_log al
                        WHERE al.task_id = t.id AND al.tenant_id = :t AND al.user_id = :u
                    )
                  )
                LIMIT 1
                """
            ),
            {"t": tenant_id, "h": hallazgo_id, "u": user_id},
        )
    ).scalar_one_or_none()
    if row is not None:
        return True

    h_row = (
        await session.execute(
            text("SELECT control_ref FROM hallazgos WHERE id = :h AND tenant_id = :t"),
            {"h": hallazgo_id, "t": tenant_id},
        )
    ).mappings().first()
    if h_row and h_row.get("control_ref"):
        return await es_ejecutor_control(session, tenant_id, user_id, h_row["control_ref"])
    return False


async def comprobar_accion_cerrada_con_evidencia(session: AsyncSession, tenant_id: str, hallazgo_id: str) -> tuple[bool, Optional[str]]:
    """Valida que las tareas asociadas al hallazgo estén completadas y tengan evidencia approved (R5)."""
    from sqlalchemy import text

    tasks = (
        await session.execute(
            text("SELECT id, status FROM roadmap_tasks WHERE tenant_id = :t AND hallazgo_id = :h"),
            {"t": tenant_id, "h": hallazgo_id},
        )
    ).mappings().all()
    if not tasks:
        return False, "No existen tareas asociadas al hallazgo."
    for task in tasks:
        if task["status"] != "completada":
            return False, f"La tarea {task['id']} no está completada."
        ev_approved = (
            await session.execute(
                text(
                    "SELECT 1 FROM task_evidence WHERE tenant_id = :t AND task_id = :tid AND validation_status = 'approved' LIMIT 1"
                ),
                {"t": tenant_id, "tid": task["id"]},
            )
        ).scalar_one_or_none()
        if not ev_approved:
            return False, f"La tarea {task['id']} no cuenta con evidencia aprobada."
    return True, None


async def listar_hallazgos_auditoria_para_verificar(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Lista los hallazgos de origen auditoria con su tarea asociada para la vista del auditor."""
    from sqlalchemy import text

    rows = (
        await session.execute(
            text(
                """
                SELECT h.id, h.titulo, h.control_ref, h.severidad, h.estado,
                       t.id AS task_id, t.title AS task_title, t.owner AS task_owner, t.completed_at
                FROM hallazgos h
                LEFT JOIN roadmap_tasks t ON t.hallazgo_id = h.id AND t.tenant_id = h.tenant_id
                WHERE h.tenant_id = :t AND h.origen = 'auditoria'
                ORDER BY h.creado_en DESC
                """
            ),
            {"t": tenant_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]
# === fin CAPA-04 ===

# === MTGE-03 ===
async def registrar_hallazgo_eipd(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
) -> tuple[str, bool]:
    """R2 de MTGE-03: cada punto por corregir de una EIPD es un hallazgo de origen 'eipd' y severidad alta."""
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.eipd.value,
        origen_ref=origen_ref,
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=None,
    )
# === fin MTGE-03 ===

# === TER-01 ===
# ¤hallazgos Hallazgos de origen `tercero` (contrato y garantía); cerrar y reabrir usan las funciones de arriba.
async def registrar_hallazgo_tercero(
    session: AsyncSession, tenant_id: str, user_id: str, origen_ref: str, severidad: str, titulo: str
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.tercero.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
    )


async def listar_hallazgos_tercero(session: AsyncSession, tenant_id: str, user_id: str) -> list:
    from features.roadmap import roadmap_service

    return await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, origen=roadmap_service.OrigenHallazgo.tercero.value
    )
# === fin TER-01 ===


# === INC-02 ===
# ¤incidentes ¤hallazgos Cada lección aprendida de una vulneración es un hallazgo de origen «incidente» (INC-02, R4).
async def registrar_hallazgo_incidente(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.incidente.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=None,
    )
# === fin INC-02 ===

# === ADPA-12 ===
# ¤adpa Carga automática de capacidades del pasillo por ficha (app_core/pasillo/roadmap_fichas/<ficha>.py).
import importlib as _importlib  # noqa: E402
import pkgutil as _pkgutil  # noqa: E402
from pathlib import Path as _Path  # noqa: E402


def _cargar_fichas_pasillo(
    paquete: str = "app_core.pasillo.roadmap_fichas",
    carpeta: _Path | None = None,
    espacio: dict[str, object] | None = None,
    importar=_importlib.import_module,
) -> list[str]:
    destino = globals() if espacio is None else espacio
    ruta = (_Path(__file__).resolve().parent / "roadmap_fichas") if carpeta is None else carpeta
    if not ruta.is_dir():
        return []
    cargados: list[str] = []
    for _, nombre_mod, _ in sorted(_pkgutil.iter_modules([str(ruta)]), key=lambda item: item[1]):
        if nombre_mod.startswith("_"):
            continue
        mod = importar(f"{paquete}.{nombre_mod}")
        exportados = getattr(mod, "__all__", None)
        if not isinstance(exportados, (list, tuple)) or not exportados:
            raise ValueError(f"{paquete}.{nombre_mod}: debe declarar __all__ no vacío")
        for simbolo in exportados:
            valor = getattr(mod, simbolo)
            if simbolo in destino and destino[simbolo] is not valor:
                raise ValueError(f"Colisión en pasillo {paquete}: '{simbolo}' repetido en {nombre_mod}")
            destino[simbolo] = valor
        cargados.append(nombre_mod)
    return cargados


FICHAS_PASILLO_CARGADAS = _cargar_fichas_pasillo()
# === fin ADPA-12 ===



# === TER-02 ===
# === fin TER-02 ===

# === CAPA-03 ===
# ¤hallazgos ¤controles-periodicos Hallazgo de un control reabierto porque su evidencia venció (RM-21).
async def registrar_hallazgo_de_evidencia_vencida(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
    control_ref: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.control_periodico.value,
        origen_ref=origen_ref[:roadmap_service.ORIGEN_REF_MAX],
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
    )
# === fin CAPA-03 ===
