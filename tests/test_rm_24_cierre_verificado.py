# ¤roadmap
"""RM-24: cierre verificado. La hoja de ruta consulta un verificador externo antes de completar.

Casos: sin verificador (idéntico al comportamiento previo), False (409 y la tarea no cambia),
True y None (se completa). Sesión simulada: no toca la base. Solo importa la compuerta de la sala.
"""
from __future__ import annotations

import pytest

from api.errores import ErrorNegocio
from features.roadmap.roadmap_service import (
    TaskStatus,
    registrar_verificador_cierre,
    update_task_status,
)

TENANT, USER, TAREA = "t-rm24", "u-rm24", "tk-rm24"


class _Resultado:
    def __init__(self, fila):
        self._fila = fila

    def mappings(self):
        return self

    def first(self):
        return self._fila


class _Sesion:
    """Guarda las sentencias; el UPDATE devuelve la fila con el estado pedido."""

    def __init__(self):
        self.sentencias: list[tuple[str, dict]] = []

    async def execute(self, sql, params):
        self.sentencias.append((str(sql), params))
        if "UPDATE roadmap_tasks" in str(sql):
            return _Resultado({"id": params["id"], "status": params["status"]})
        return _Resultado(None)

    def updates(self):
        return [p for s, p in self.sentencias if "UPDATE roadmap_tasks" in s]

    def auditorias(self):
        return [p for s, p in self.sentencias if "task_audit_log" in s]


class _Fijo:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.consultas: list[tuple[str, str]] = []

    def evidencia_conforme(self, tenant_id, tarea_id):
        self.consultas.append((tenant_id, tarea_id))
        return self.respuesta


@pytest.fixture(autouse=True)
def _sin_verificador():
    registrar_verificador_cierre(None)
    yield
    registrar_verificador_cierre(None)


@pytest.mark.asyncio
async def test_sin_verificador_completa_como_siempre():
    s = _Sesion()
    r = await update_task_status(s, TENANT, USER, TAREA, TaskStatus.completada)
    assert r == {"id": TAREA, "status": "completada"}
    assert s.updates()[0]["completed_at"] is not None
    assert len(s.auditorias()) == 1


@pytest.mark.asyncio
async def test_verificador_false_rechaza_409_y_no_cambia():
    v = _Fijo(False)
    registrar_verificador_cierre(v)
    s = _Sesion()
    with pytest.raises(ErrorNegocio) as e:
        await update_task_status(s, TENANT, USER, TAREA, TaskStatus.completada)
    assert e.value.code == "RM_CIERRE_SIN_EVIDENCIA"
    assert e.value.status_code == 409
    assert s.updates() == [] and s.auditorias() == []
    assert v.consultas == [(TENANT, TAREA)]


@pytest.mark.asyncio
@pytest.mark.parametrize("respuesta", [True, None])
async def test_verificador_true_o_none_completa(respuesta):
    registrar_verificador_cierre(_Fijo(respuesta))
    s = _Sesion()
    r = await update_task_status(s, TENANT, USER, TAREA, TaskStatus.completada)
    assert r["status"] == "completada"
    assert len(s.updates()) == 1 and len(s.auditorias()) == 1


@pytest.mark.asyncio
async def test_otros_estados_no_consultan_al_verificador():
    v = _Fijo(False)
    registrar_verificador_cierre(v)
    s = _Sesion()
    for nuevo in (TaskStatus.pendiente, TaskStatus.en_progreso, TaskStatus.bloqueada):
        r = await update_task_status(s, TENANT, USER, TAREA, nuevo)
        assert r["status"] == nuevo.value
    assert v.consultas == []


@pytest.mark.asyncio
async def test_retirar_el_verificador_restablece_el_comportamiento():
    registrar_verificador_cierre(_Fijo(False))
    registrar_verificador_cierre(None)
    r = await update_task_status(_Sesion(), TENANT, USER, TAREA, TaskStatus.completada)
    assert r["status"] == "completada"
