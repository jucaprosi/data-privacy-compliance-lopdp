# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤arbitro
"""RM-28: una tarea solo pasa a `completada` con evidencia de doble validación en E1 o mayor.

Contra PostgreSQL 16 local con RLS. Sin TEST_DATABASE_URL se omite. Nunca contra producción.
Todo SQL es texto literal con parámetros enlazados. Solo se importa la compuerta de la sala.

`validated_by = uploaded_by` no se puede sembrar: lo impide `ck_evidence_four_eyes`. El caso equivalente que la
base sí admite es la evidencia sin `uploaded_by` (no hay cuatro ojos comprobables) y se prueba como tal.

Mutaciones documentadas (cada una deja en rojo la prueba que se nombra):
- m1: quitar la llamada a `_exigir_doble_validacion` en `update_task_status` -> test_sin_evidencia_da_409.
- m2: aceptar una sola validación (dejar en el filtro solo la primera del coordinador, el nivel y la marca:
  quitar `validation_status`, `validated_by` y `validado_rol`) -> test_evidencia_que_no_cuenta_da_409[solo_primera].
- m3: evaluar `exigir_cierre_conforme` antes y devolver sin R1 cuando el verificador da True
  -> test_verificador_true_no_salta_r1.
"""
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.errores import ErrorNegocio
from conftest import exigir_base_de_pruebas
from features.roadmap.roadmap_service import TaskStatus, registrar_verificador_cierre, update_task_status

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
CODIGO_R1 = "RM_CIERRE_SIN_DOBLE_VALIDACION"


def _async_url() -> str:
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    exigir_base_de_pruebas()
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


# Evidencia válida: subida por el responsable, primera validación del coordinador, final del DPO, E1.
_VALIDA = {"estado": "approved", "primera": "coord", "rol_primera": "coordinador", "final": "dpo",
           "rol_final": "dpo", "nivel": 1, "revalidar": False, "sube": "resp"}

# Casos que no cuentan (R1): cada uno cambia un solo campo de la evidencia válida.
_NO_CUENTAN = {
    "solo_primera": {"estado": "pending", "final": None, "rol_final": None},
    "sin_quien_subio": {"sube": None},
    "requiere_revalidacion": {"revalidar": True},
    "nivel_e0": {"nivel": 0},
    "sin_nivel": {"nivel": None},
    "final_de_coordinador": {"final": "coord2", "rol_final": "coordinador"},
    "rechazada": {"estado": "rejected"},
}


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


@pytest_asyncio.fixture
async def mundo():
    from app_core.db.session import fijar_contexto_rls

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    ta, tb = _id("rm28-a"), _id("rm28-b")
    u = {clave: _id(f"u-{clave}") for clave in ("resp", "coord", "coord2", "dpo", "auditor", "impl", "resp_b")}
    tareas: dict[str, str] = {}

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :r, :ruc)"
            ), {"i": t, "n": f"Org {t}", "r": f"Org {t} SA", "ruc": f"RUC{t[-12:]}"})
        for uid in u.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                            {"i": uid, "e": f"{uid}@rm28.invalid", "n": uid})
        for t in (ta, tb):
            rm, wv = _id("rm"), _id("wv")
            await fijar_contexto_rls(s, t)
            await s.execute(text(
                "INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:i, :t, 'active', '{}')"
            ), {"i": rm, "t": t})
            await s.execute(text(
                "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) VALUES (:i, :rm, :t, 'Ola', 1)"
            ), {"i": wv, "rm": rm, "t": t})
        await s.commit()

    async def tarea(tenant: str = ta) -> str:
        tk = _id("tk")
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            await s.execute(text(
                "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, description, "
                "priority, status) SELECT CAST(:i AS varchar), w.id, w.tenant_id, 'P13', 'D01', 'Tarea', 'Desc', 'alta', 'pendiente' "
                "FROM roadmap_waves w WHERE w.tenant_id = :t LIMIT 1"
            ), {"i": tk, "t": tenant})
            await s.commit()
        tareas[tk] = tenant
        return tk

    async def evidencia(tk: str, tenant: str = ta, **cambios) -> str:
        datos = {**_VALIDA, **cambios}
        eid = _id("ev")
        primera = u[datos["primera"]] if datos["primera"] else None
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            await s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, clave_objeto, mime_type, file_size, uploaded_by, "
                "validation_status, validated_by, validated_at, validado_rol, nivel_acreditado, requiere_revalidacion, "
                "primera_validacion_por, primera_validacion_en, primera_validacion_rol) "
                "VALUES (:i, :tk, :t, :k, 'application/pdf', 100, :u, :estado, :final, "
                "CASE WHEN CAST(:final AS varchar) IS NOT NULL THEN now() END, :rol_final, CAST(:nivel AS smallint), "
                ":revalidar, :primera, CASE WHEN CAST(:primera AS varchar) IS NOT NULL THEN now() END, :rol_primera)"
            ), {"i": eid, "tk": tk, "t": tenant, "k": f"{tenant}/{tk}/{eid}.pdf",
                "u": u[datos["sube"]] if datos["sube"] else None, "estado": datos["estado"],
                "final": u[datos["final"]] if datos["final"] else None, "rol_final": datos["rol_final"],
                "nivel": datos["nivel"], "revalidar": datos["revalidar"], "primera": primera,
                "rol_primera": datos["rol_primera"] if primera else None})
            await s.commit()
        return eid

    async def cambiar(tk: str, estado: TaskStatus, tenant: str | None = None):
        async with factory() as s:
            fila = await update_task_status(s, tenant or tareas[tk], u["impl"], tk, estado)
            await s.commit()
            return fila

    async def estado_de(tk: str) -> str:
        async with factory() as s:
            await fijar_contexto_rls(s, tareas[tk])
            return (await s.execute(text("SELECT status FROM roadmap_tasks WHERE id = :i"), {"i": tk})).scalar_one()

    try:
        yield {"ta": ta, "tb": tb, "u": u, "tarea": tarea, "evidencia": evidencia, "cambiar": cambiar,
               "estado": estado_de}
    finally:
        async with factory() as s:
            try:
                for t in (ta, tb):
                    await fijar_contexto_rls(s, t)
                    for sentencia in (
                        "DELETE FROM task_audit_log WHERE tenant_id = :t",
                        "DELETE FROM task_evidence WHERE tenant_id = :t",
                        "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                        "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                        "DELETE FROM roadmaps WHERE tenant_id = :t",
                    ):
                        await s.execute(text(sentencia), {"t": t})
                    await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
                await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
                await s.commit()
            except Exception:
                await s.rollback()
        await engine.dispose()


async def _rechazo(m, tk, tenant=None) -> ErrorNegocio:
    with pytest.raises(ErrorNegocio) as error:
        await m["cambiar"](tk, TaskStatus.completada, tenant)
    return error.value


@pytest.mark.asyncio
async def test_sin_evidencia_da_409(mundo):
    tk = await mundo["tarea"]()
    error = await _rechazo(mundo, tk)
    assert (error.code, error.status_code) == (CODIGO_R1, 409)
    assert await mundo["estado"](tk) == "pendiente"


@pytest.mark.asyncio
@pytest.mark.parametrize("caso", sorted(_NO_CUENTAN))
async def test_evidencia_que_no_cuenta_da_409(mundo, caso):
    tk = await mundo["tarea"]()
    await mundo["evidencia"](tk, **_NO_CUENTAN[caso])
    error = await _rechazo(mundo, tk)
    assert (error.code, error.status_code) == (CODIGO_R1, 409)
    assert await mundo["estado"](tk) == "pendiente"


@pytest.mark.asyncio
@pytest.mark.parametrize("final", ["dpo", "auditor"])
@pytest.mark.parametrize("nivel", [1, 4])
async def test_coordinador_mas_dpo_o_auditor_en_e1_o_mas_completa(mundo, final, nivel):
    tk = await mundo["tarea"]()
    await mundo["evidencia"](tk, nivel=0)  # una evidencia que no cuenta no estorba a la que sí
    await mundo["evidencia"](tk, final=final, rol_final=final, nivel=nivel)
    fila = await mundo["cambiar"](tk, TaskStatus.completada)
    assert fila["status"] == "completada" and fila["completed_at"] is not None
    assert await mundo["estado"](tk) == "completada"


@pytest.mark.asyncio
async def test_con_doble_validacion_el_verificador_false_sigue_rechazando(mundo):
    tk = await mundo["tarea"]()
    await mundo["evidencia"](tk)
    verificador = _Fijo(False)
    registrar_verificador_cierre(verificador)
    error = await _rechazo(mundo, tk)
    assert (error.code, error.status_code) == ("RM_CIERRE_SIN_EVIDENCIA", 409)
    assert verificador.consultas == [(mundo["ta"], tk)]
    assert await mundo["estado"](tk) == "pendiente"


@pytest.mark.asyncio
async def test_verificador_true_no_salta_r1(mundo):
    tk = await mundo["tarea"]()
    registrar_verificador_cierre(_Fijo(True))
    error = await _rechazo(mundo, tk)
    assert error.code == CODIGO_R1
    assert await mundo["estado"](tk) == "pendiente"


@pytest.mark.asyncio
async def test_r1_va_antes_que_el_verificador(mundo):
    tk = await mundo["tarea"]()
    verificador = _Fijo(False)
    registrar_verificador_cierre(verificador)
    error = await _rechazo(mundo, tk)
    assert error.code == CODIGO_R1
    assert verificador.consultas == []


@pytest.mark.asyncio
async def test_evidencia_valida_de_otro_tenant_no_cuenta(mundo):
    tk = await mundo["tarea"]()
    # Fila que dice ser de la organización B pero apunta a la tarea de A.
    await mundo["evidencia"](tk, tenant=mundo["tb"])
    error = await _rechazo(mundo, tk)
    assert error.code == CODIGO_R1
    assert await mundo["estado"](tk) == "pendiente"


@pytest.mark.asyncio
async def test_reabrir_no_exige_evidencia(mundo):
    tk = await mundo["tarea"]()
    await mundo["evidencia"](tk)
    assert (await mundo["cambiar"](tk, TaskStatus.completada))["status"] == "completada"
    for nuevo in (TaskStatus.en_progreso, TaskStatus.pendiente, TaskStatus.bloqueada):
        fila = await mundo["cambiar"](tk, nuevo)
        assert fila["status"] == nuevo.value and fila["completed_at"] is None


@pytest.mark.asyncio
async def test_otros_estados_sin_evidencia_no_cambian(mundo):
    tk = await mundo["tarea"]()
    for nuevo in (TaskStatus.en_progreso, TaskStatus.bloqueada, TaskStatus.pendiente):
        assert (await mundo["cambiar"](tk, nuevo))["status"] == nuevo.value
