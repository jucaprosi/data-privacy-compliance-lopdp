# ¤incidentes
"""Compuerta pública de la sala ADPA: Incidentes y vulneraciones (INC-01)."""
from features.incidentes.domain.models import (
    ROLES_CONSULTA,
    ROLES_REGISTRO,
    SEVERIDADES,
    FechaDeteccionFutura,
    Incidente,
)
from features.incidentes.services.bitacora_engine import (
    listar_incidentes,
    primer_incidente_alterado,
    registrar_incidente,
)

__all__ = [
    "ROLES_CONSULTA",
    "ROLES_REGISTRO",
    "SEVERIDADES",
    "FechaDeteccionFutura",
    "Incidente",
    "listar_incidentes",
    "primer_incidente_alterado",
    "registrar_incidente",
]


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/incidentes/domain/errores.py y se registran al importarlo.
from features.incidentes.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===

# === ORG-24 ===

async def contar_vulneraciones_para_ficha(session, tenant_id: str) -> dict:
    """Total de incidentes registrados del tenant (ficha de la organización, ORG-24).

    La bitácora no tiene columna de estado: la bitácora no tiene estado: se cuentan los incidentes registrados.
    """
    from sqlalchemy import text

    n = (await session.execute(text("SELECT count(*) FROM incidentes WHERE tenant_id = :t"), {"t": tenant_id})).scalar_one()
    return {"vulneraciones_registradas": int(n)}


__all__ += ["contar_vulneraciones_para_ficha"]
# === fin ORG-24 ===

# === INC-02 ===
# ¤incidentes ¤hallazgos Asistente de vulneración en ocho secciones, informes y precondición de cierre (R7).
from features.incidentes.domain.vulneracion import (  # noqa: E402
    ROLES_INFORMES,
    ROLES_LECTURA,
    SECCIONES,
    DecisionSinJustificacion,
    RolNoAutorizado,
    SeccionAnteriorIncompleta,
    SeccionInvalida,
)
from features.incidentes.services.asistente_engine import (  # noqa: E402
    HallazgosPorPasillo,
    estado_asistente,
    guardar_seccion,
    notificaciones_por_implementador,
    registrar_notificacion,
    resumen_asistentes,
    tiene_decision,
)
from features.incidentes.services.informes_engine import generar_informe  # noqa: E402


async def exigir_decision_para_cierre(session, tenant_id: str, incidente_id: str) -> None:
    """R7: un incidente con datos personales no se cierra sin la decisión de notificar registrada.

    La llama `cerrar_incidente` (sección INC-03) antes de registrar el evento; el contexto RLS ya está fijado.
    """
    from sqlalchemy import text

    from app_core.errors import ErrorNegocio

    afecta = (
        await session.execute(
            text("SELECT afecta_datos_personales FROM incidentes WHERE id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).scalar_one_or_none()
    if afecta and not await tiene_decision(session, tenant_id, incidente_id):
        raise ErrorNegocio("DECISION_NOTIFICAR_PENDIENTE")


__all__ += [
    "ROLES_INFORMES",
    "ROLES_LECTURA",
    "SECCIONES",
    "DecisionSinJustificacion",
    "HallazgosPorPasillo",
    "RolNoAutorizado",
    "SeccionAnteriorIncompleta",
    "SeccionInvalida",
    "estado_asistente",
    "exigir_decision_para_cierre",
    "generar_informe",
    "guardar_seccion",
    "notificaciones_por_implementador",
    "registrar_notificacion",
    "resumen_asistentes",
    "tiene_decision",
]

# === fin INC-02 ===

# === INC-03 ===
from features.incidentes.domain.estado import (  # noqa: E402
    MOTIVO_MINIMO,
    EstadoIncidente,
    IncidenteNoEncontrado,
    TransicionInvalida,
)
from features.incidentes.services.estado_engine import (  # noqa: E402
    cerrar_incidente as _cerrar_incidente_motor,
    contar_abiertos,
    estado_de,
    estados_de,
    reabrir_incidente,
)

async def cerrar_incidente(session, tenant_id: str, user_id: str, incidente_id: str, motivo: str) -> EstadoIncidente:
    """Cierra el incidente; con datos personales exige antes la decisión de notificar (R7 de INC-02, cesión)."""
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(session, tenant_id, user_id)
    await exigir_decision_para_cierre(session, tenant_id, incidente_id)
    return await _cerrar_incidente_motor(session, tenant_id, user_id, incidente_id, motivo)


__all__ += [
    "MOTIVO_MINIMO",
    "EstadoIncidente",
    "IncidenteNoEncontrado",
    "TransicionInvalida",
    "cerrar_incidente",
    "contar_abiertos",
    "estado_de",
    "estados_de",
    "reabrir_incidente",
]
# === fin INC-03 ===
