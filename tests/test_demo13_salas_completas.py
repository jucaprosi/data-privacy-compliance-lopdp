# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤arbitro
"""DEMO-13: la demo no arranca si le falta el clon de una sala (R1) y `DEMO_INICIADA` no lleva omitidas (R2).

Sin base de datos: el registro de clones (`entrada_engine._clonador`), los repositorios y la auditoría se
sustituyen por dobles en memoria, así que la prueba solo mira el orquestador y el router.

Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - m1, volver a saltar la sala sin clon (`continue` en vez de fallar):
    test_m1_sin_videovigilancia_lanza_demo_incompleta_y_no_clona_nada;
  - m2, comprobar solo la primera sala de `ORDEN_DE_SALAS`:
    test_m1_sin_videovigilancia_lanza_demo_incompleta_y_no_clona_nada (falta la última);
  - volver a poner `salas_omitidas` en el evento: test_m2_seis_salas_en_orden_y_evento_sin_omitidas.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from app_core.security import IdentidadVerificada
from features.demo.domain.errores import ErrorDemo
from features.demo.domain.eventos import EventoDemo
from features.demo.domain.plantilla import ORDEN_DE_SALAS, PLANTILLA_TENANT_ID
from features.demo.services import entrada_engine

AHORA = datetime(2026, 11, 28, 10, 0, tzinfo=timezone.utc)
CORREO = "vendedor.demo13@ventas.invalid"
MENSAJE = "La demo está incompleta: faltan salas por preparar"


def _cuerpo(*salas):
    return {"codigo": "DEMO_INCOMPLETA", "mensaje": MENSAJE, "salas": list(salas)}


class _SesionFalsa:
    """Lo único que el orquestador pide a la sesión: abrir un SAVEPOINT."""

    def __init__(self) -> None:
        self.savepoints = 0

    @asynccontextmanager
    async def _anidada(self):
        self.savepoints += 1
        yield self

    def begin_nested(self):
        return self._anidada()


def _registro(monkeypatch, salas):
    """Sustituye el registro de clones: solo `salas` tienen `clonar_desde_plantilla`. Devuelve las llamadas."""
    llamadas: list[tuple[str, str, str, dict]] = []

    def hacer(sala):
        async def clonar(session, origen, destino, mapa):
            llamadas.append((sala, origen, destino, dict(mapa)))
            return {**mapa, f"id-{sala}": f"{destino}-{sala}"}
        return clonar

    clones = {sala: hacer(sala) for sala in salas}
    monkeypatch.setattr(entrada_engine, "_clonador", lambda sala: clones.get(sala))
    return llamadas


def _sin_base(monkeypatch):
    """Dobles de los repositorios y de la auditoría para `entrar`. Devuelve lo que registran."""
    visto: dict = {"eventos": [], "insertadas": 0}

    async def nada(*_a, **_k):
        return None

    async def cero(*_a, **_k):
        return 0

    async def insertar(session, sub, email, destino, usuario_id, ahora):
        visto["insertadas"] += 1
        return SimpleNamespace(id="sesion-demo13")

    async def registrar_evento(session, tenant, entidad, entidad_id, accion, usuario, payload):
        visto["eventos"].append((accion, payload))

    async def areas(session, tenant_id):
        return [{"id": "a-1", "nombre": "Gerencia"}]

    async def usuarios(session, tenant_id):
        return [{"id": "u-admin", "nombre": "Admin ficticio",
                 "roles": [{"role": "admin_organizacion", "area_id": "a-1"}]}]

    async def configuracion(session, tenant_id):
        return {"nombre_comercial": "Cooperativa Demo"}

    monkeypatch.setattr(entrada_engine.vendedores, "es_autorizado", lambda email: True)
    monkeypatch.setattr(entrada_engine.sesiones_repo, "contar_activas_con_candado", cero)
    monkeypatch.setattr(entrada_engine.sesiones_repo, "obtener_activa", nada)
    monkeypatch.setattr(entrada_engine.sesiones_repo, "insertar", insertar)
    monkeypatch.setattr(entrada_engine.cierre_engine, "vencer_inactivas", nada)
    monkeypatch.setattr(entrada_engine, "fijar_contexto_rls", nada)
    monkeypatch.setattr(entrada_engine, "registrar_evento", registrar_evento)
    monkeypatch.setattr(entrada_engine.pasillo_organizacion, "listar_areas", areas)
    monkeypatch.setattr(entrada_engine.pasillo_organizacion, "listar_usuarios", usuarios)
    monkeypatch.setattr(entrada_engine.pasillo_organizacion, "configuracion_de_organizacion", configuracion)
    return visto


def test_hoy_las_seis_salas_registran_su_clon():
    assert ORDEN_DE_SALAS[-1] == "videovigilancia"
    assert [s for s in ORDEN_DE_SALAS if entrada_engine._clonador(s) is None] == []


@pytest.mark.asyncio
async def test_m1_sin_videovigilancia_lanza_demo_incompleta_y_no_clona_nada(monkeypatch):
    llamadas = _registro(monkeypatch, ORDEN_DE_SALAS[:-1])
    with pytest.raises(ErrorDemo) as e:
        await entrada_engine.copiar_plantilla(_SesionFalsa(), "demo-destino")
    assert e.value.codigo.codigo == "DEMO_INCOMPLETA" and e.value.status_code == 503
    assert e.value.cuerpo() == _cuerpo("videovigilancia")
    assert llamadas == []


@pytest.mark.asyncio
async def test_faltan_varias_se_nombran_todas_en_el_orden_de_salas(monkeypatch):
    llamadas = _registro(monkeypatch, ("organizacion", "roadmap", "evidencias"))
    with pytest.raises(ErrorDemo) as e:
        await entrada_engine.copiar_plantilla(_SesionFalsa(), "demo-destino")
    assert e.value.cuerpo() == _cuerpo("diagnostico", "biblioteca", "videovigilancia")
    assert llamadas == []


@pytest.mark.asyncio
async def test_m2_seis_salas_en_orden_y_evento_sin_omitidas(monkeypatch):
    llamadas = _registro(monkeypatch, ORDEN_DE_SALAS)
    visto = _sin_base(monkeypatch)
    estado = await entrada_engine.entrar(_SesionFalsa(), "sub-demo13", CORREO, AHORA)
    assert [ll[0] for ll in llamadas] == list(ORDEN_DE_SALAS)
    assert {ll[1] for ll in llamadas} == {PLANTILLA_TENANT_ID} and {ll[2] for ll in llamadas} == {estado.tenant_id}
    # Cada sala recibe el mapa que acumularon las anteriores.
    assert [sorted(ll[3]) for ll in llamadas] == [sorted(f"id-{s}" for s in ORDEN_DE_SALAS[:i])
                                                   for i in range(len(ORDEN_DE_SALAS))]
    ((accion, payload),) = visto["eventos"]
    assert accion == EventoDemo.DEMO_INICIADA.value
    assert payload == {"vendedor_email": CORREO} and "salas_omitidas" not in payload


@pytest.mark.asyncio
async def test_entrar_sin_una_sala_da_demo_incompleta_sin_sesion_ni_evento(monkeypatch):
    llamadas = _registro(monkeypatch, ORDEN_DE_SALAS[1:])
    visto = _sin_base(monkeypatch)
    sesion = _SesionFalsa()
    with pytest.raises(ErrorDemo) as e:
        await entrada_engine.entrar(sesion, "sub-demo13", CORREO, AHORA)
    assert e.value.codigo.codigo == "DEMO_INCOMPLETA"  # no se convierte en DEMO_NO_DISPONIBLE
    assert e.value.cuerpo() == _cuerpo("organizacion")
    assert sesion.savepoints == 1 and llamadas == [] and visto == {"eventos": [], "insertadas": 0}


@pytest.mark.asyncio
async def test_post_entrar_responde_503_con_las_salas_que_faltan(monkeypatch):
    from api.routers import demo_sesion
    from app_core.db.session import get_session

    _registro(monkeypatch, ORDEN_DE_SALAS[:-1])
    _sin_base(monkeypatch)
    app = FastAPI()
    app.include_router(demo_sesion.router, prefix="/api/v1")

    async def sesion():
        yield _SesionFalsa()

    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[demo_sesion.identidad_del_vendedor] = lambda: IdentidadVerificada("sub-demo13", CORREO)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo") as c:
        r = await c.post("/api/v1/demo/entrar")
    assert r.status_code == 503
    assert r.json() == _cuerpo("videovigilancia")
