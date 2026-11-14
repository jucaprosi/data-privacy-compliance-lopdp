# ¤incidentes ¤seguridad-tenant ¤arbitro
"""INC-04: la marca «notificación pendiente» del cierre dice la verdad.

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL), con el rol lopdp_app y RLS. Reutiliza
el mundo sintético de INC-03. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from tests.test_inc03_estado_incidente import (  # noqa: F401  (fixtures y apoyos de INC-03)
    MOTIVO,
    _actor,
    _decision_registrada,
    _oidc,
    _post,
    _registrar,
    mundo,
)
from features.incidentes import incidentes_service as inc  # noqa: E402
from app_core.db.session import fijar_contexto_rls  # noqa: E402


async def _cierre_anterior_pendiente(mundo, t, uid, incidente_id):
    """Evento de cierre como lo escribía INC-03 antes de INC-04 (marca 'pendiente')."""
    await fijar_contexto_rls(mundo["s"], t, uid)
    await mundo["s"].execute(
        text(
            "INSERT INTO incidentes_eventos_estado (id, tenant_id, incidente_id, secuencia, tipo, motivo, "
            "decision_notificacion, registrado_por, registrado_en) VALUES "
            "(:id, :t, :i, 1, 'cierre', :m, 'pendiente', :u, :en)"
        ),
        {"id": str(uuid.uuid4()), "t": t, "i": incidente_id, "m": MOTIVO, "u": uid, "en": datetime.now(timezone.utc)},
    )


async def _marca_guardada(mundo, incidente_id):
    return (
        await mundo["s"].execute(
            text(
                "SELECT decision_notificacion FROM incidentes_eventos_estado "
                "WHERE incidente_id = :i ORDER BY secuencia DESC LIMIT 1"
            ),
            {"i": incidente_id},
        )
    ).scalar_one()


@pytest.mark.asyncio
async def test_cierre_con_decision_sin_marca(mundo):
    """Mutación: volver a escribir 'pendiente' en `_cambiar_estado` → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo, afecta_datos_personales=True)
    r = await _post(mundo, "coordinador", incidente.id, "cerrar")
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "cerrado" and r.json()["decision_notificacion"] is None
    assert await _marca_guardada(mundo, incidente.id) is None
    auditoria = (
        await mundo["s"].execute(
            text("SELECT payload::text FROM audit_events WHERE entity_id = :i AND action = 'incidente_cerrado'"),
            {"i": incidente.id},
        )
    ).scalars().all()
    assert auditoria and all("decision_notificacion" not in p for p in auditoria)


@pytest.mark.asyncio
async def test_marca_anterior_con_decision_no_se_muestra(mundo):
    """Mutación: entregar el valor guardado sin comprobar la sección 7 → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo, afecta_datos_personales=True, con_decision=False)
    await _cierre_anterior_pendiente(mundo, t, uid, incidente.id)
    await _decision_registrada(mundo, t, uid, incidente.id)
    assert (await inc.estado_de(mundo["s"], t, incidente.id)).decision_notificacion is None
    estados = await inc.estados_de(mundo["s"], t, uid)
    assert estados[incidente.id].decision_notificacion is None
    assert await _marca_guardada(mundo, incidente.id) == "pendiente"  # la historia no se reescribe


@pytest.mark.asyncio
async def test_marca_anterior_sin_decision_se_conserva(mundo):
    """Mutación: borrar siempre la marca en la lectura → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo, afecta_datos_personales=True, con_decision=False)
    await _cierre_anterior_pendiente(mundo, t, uid, incidente.id)
    assert (await inc.estado_de(mundo["s"], t, incidente.id)).decision_notificacion == "pendiente"
    assert (await inc.estados_de(mundo["s"], t, uid))[incidente.id].decision_notificacion == "pendiente"


@pytest.mark.asyncio
async def test_sin_datos_personales_sin_cambio(mundo):
    """Mutación: escribir 'pendiente' en todo cierre → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo, afecta_datos_personales=False, titulo="Sin datos personales simulado")
    estado = await inc.cerrar_incidente(mundo["s"], t, uid, incidente.id, MOTIVO)
    assert estado.estado == "cerrado" and estado.decision_notificacion is None


@pytest.mark.asyncio
async def test_rls_estado_sin_cambio(mundo):
    """Mutación: quitar FORCE ROW LEVEL SECURITY de incidentes_eventos_estado → rojo."""
    uid, t, _ = _actor(mundo, "coordinador")
    incidente = await _registrar(mundo)
    await inc.cerrar_incidente(mundo["s"], t, uid, incidente.id, MOTIVO)
    uid_b, t_b, _ = _actor(mundo, "coord_b")
    await fijar_contexto_rls(mundo["s"], t_b, uid_b)
    filas = (
        await mundo["s"].execute(
            text("SELECT count(*) FROM incidentes_eventos_estado WHERE incidente_id = :i"), {"i": incidente.id}
        )
    ).scalar_one()
    assert filas == 0
