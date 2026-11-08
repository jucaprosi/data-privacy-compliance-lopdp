# -*- coding: utf-8 -*-
# ¤demo
# ¤rbac-tenant
"""DEMO-00: contrato de la sala demo (compuerta, dominio, repositorio, pasillo y migración).

Las pruebas de base corren sobre PostgreSQL real (`TEST_DATABASE_URL`, con la credencial del dueño
del esquema) dentro de transacciones que se revierten. Solo datos generados y correos `.invalid`.
"""
from __future__ import annotations

import ast
import asyncio
import importlib
import inspect
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SALA = RAIZ / "features" / "demo"
MIGRACION = RAIZ / "alembic" / "versions" / "20261121_demo_sesiones.py"
FIRMAS = {"entrar", "terminar", "estado", "cambiar_persona", "resolver_usuario", "vencer_inactivas"}


# --- Compuerta ---------------------------------------------------------------------------------

def test_la_compuerta_expone_exactamente_las_seis_firmas():
    from features.demo import demo_service

    publicas = {
        nombre
        for nombre, valor in vars(demo_service).items()
        if inspect.iscoroutinefunction(valor) and not nombre.startswith("_") and valor.__module__ == demo_service.__name__
    }
    assert publicas == FIRMAS
    assert set(demo_service.__all__) == FIRMAS


def test_la_compuerta_se_importa_sin_ningun_motor(monkeypatch):
    for nombre in [m for m in sys.modules if m.startswith("features.demo")]:
        monkeypatch.delitem(sys.modules, nombre)
    demo_service = importlib.import_module("features.demo.demo_service")
    assert not [m for m in sys.modules if m.startswith("features.demo.services")]
    if not (SALA / "services").exists():
        with pytest.raises(NotImplementedError, match="DEMO-02"):
            asyncio.run(demo_service.vencer_inactivas(None))
        with pytest.raises(NotImplementedError, match="DEMO-01"):
            asyncio.run(demo_service.resolver_usuario(None, "sub-generado"))


def test_el_pasillo_solo_importa_la_compuerta_dentro_de_las_funciones():
    arbol = ast.parse((RAIZ / "app_core" / "pasillo" / "demo.py").read_text(encoding="utf-8"))
    de_modulo = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert all("features" not in (getattr(n, "module", "") or "") for n in de_modulo)
    dentro = [n for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module == "features.demo"]
    assert dentro and all(a.name == "demo_service" for n in dentro for a in n.names)


# --- Dominio ----------------------------------------------------------------------------------

def test_esta_vencida_59_no_60_si():
    from features.demo.domain.sesion import TOPE, esta_vencida

    inicio = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
    assert esta_vencida(inicio, inicio + timedelta(minutes=59)) is False
    assert esta_vencida(inicio, inicio + timedelta(minutes=60)) is True
    assert TOPE == 20


def test_la_sesion_guarda_una_lista_de_tenants():
    from features.demo.domain.sesion import SesionDemo

    s = SesionDemo(id="s", vendedor_sub="sub", vendedor_email="v@ventas.invalid", tenant_ids=("t1",))
    assert s.tenant_ids == ("t1",)


@pytest.mark.parametrize(
    "nombre,status,mensaje",
    [
        ("DEMO_NO_AUTORIZADO", 403, "No autorizado para la demo"),
        ("DEMO_OCUPADA", 409, "Demo ocupada, intenta en unos minutos"),
        ("DEMO_VENCIDA", 401, "Tu demostración terminó"),
        ("DEMO_PERSONA_AJENA", 403, "Esa persona no pertenece a tu demostración"),
        ("DEMO_NO_DISPONIBLE", 503, "No pudimos preparar la demo; intenta de nuevo"),
    ],
)
def test_los_cinco_errores(nombre, status, mensaje):
    from app_core.errors import CATALOGO_ERRORES
    from features.demo.domain import errores

    error = errores.ErrorDemo(getattr(errores, nombre))
    assert error.status_code == status
    assert error.cuerpo() == {"codigo": nombre, "mensaje": mensaje}
    assert CATALOGO_ERRORES[nombre].status_code == status


def test_seis_personas_en_orden_y_rol_inicial():
    from features.demo.domain.personas import ETIQUETAS, ORDEN_DE_ROLES, ROL_INICIAL, PersonaDemo, ordenar

    assert ORDEN_DE_ROLES == ("admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area", "auditor")
    assert ROL_INICIAL == "admin_organizacion"
    assert set(ETIQUETAS) == set(ORDEN_DE_ROLES)
    desordenadas = [PersonaDemo(f"u-{r}", r, r, ETIQUETAS[r]) for r in reversed(ORDEN_DE_ROLES)]
    assert tuple(p.rol for p in ordenar(desordenadas)) == ORDEN_DE_ROLES


def test_contrato_de_estado_sin_correo_ni_sub():
    from features.demo.domain.contrato import CAMPOS_ESTADO, CAMPOS_PERSONA, EstadoDemo
    from features.demo.domain.personas import ETIQUETAS, ORDEN_DE_ROLES, PersonaDemo

    personas = tuple(PersonaDemo(f"u-{r}", f"Persona {r}", r, ETIQUETAS[r]) for r in ORDEN_DE_ROLES)
    cuerpo = EstadoDemo("tenant-demo-generado", "Cooperativa Demo", personas[0], personas).a_dict()
    assert tuple(cuerpo) == CAMPOS_ESTADO
    assert len(cuerpo["personas"]) == 6
    assert all(tuple(p) == CAMPOS_PERSONA for p in cuerpo["personas"])
    texto = repr(cuerpo)
    assert "@" not in texto and "sub" not in cuerpo and "vendedor" not in texto


def test_eventos_y_protocolo_de_plantilla():
    from features.demo.domain.eventos import EventoDemo
    from features.demo.domain.plantilla import ORDEN_DE_SALAS, ClonadorDePlantilla

    assert {e.value for e in EventoDemo} == {"DEMO_INICIADA", "DEMO_CAMBIO_PERSONA", "DEMO_TERMINADA", "DEMO_VENCIDA"}
    assert ORDEN_DE_SALAS[0] == "organizacion"
    assert list(inspect.signature(ClonadorDePlantilla.__call__).parameters) == ["self", "session", "origen", "destino", "mapa_ids"]


# --- Sin borrado ni correos en registros --------------------------------------------------------

def test_el_repositorio_no_borra():
    for archivo in (SALA / "repo").rglob("*.py"):
        assert not re.search(r"\bDELETE\b", archivo.read_text(encoding="utf-8"), re.IGNORECASE), archivo


def test_la_migracion_no_concede_delete_a_lopdp_app():
    fuente = MIGRACION.read_text(encoding="utf-8")
    concesiones = re.findall(r"GRANT\s+([^;\"]+?)\s+ON\s+demo_sesiones\s+TO\s+lopdp_app", fuente, re.IGNORECASE)
    assert concesiones == ["SELECT, INSERT, UPDATE"]
    assert "ON DELETE SET NULL" in fuente
    assert "WHERE estado = 'activa'" in fuente


def test_la_sala_no_registra_correos():
    for archivo in SALA.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and getattr(nodo.func, "attr", "") in {"debug", "info", "warning", "error", "exception"}:
                assert "email" not in ast.unparse(nodo), archivo


# --- Base de datos real -----------------------------------------------------------------------

def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _sembrar(cur, sufijo: str) -> tuple[str, str]:
    tenant, usuario = f"t-demo00-{sufijo}", f"u-demo00-{sufijo}"
    cur.execute(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
        "VALUES (%s, 'Cooperativa Demo', 'Cooperativa Demo', %s, true)",
        (tenant, f"99{uuid.uuid4().int % 10**11:011d}"),
    )
    cur.execute("INSERT INTO users (id, email, nombre) VALUES (%s, %s, 'Persona Demo')", (usuario, f"{usuario}@demo.invalid"))
    return tenant, usuario


def test_al_borrar_el_tenant_la_sesion_queda_sin_tenant_ni_persona():
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_url()) as conn:
        try:
            with conn.cursor() as cur:
                tenant, usuario = _sembrar(cur, uuid.uuid4().hex[:8])
                cur.execute(
                    "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email, tenant_id, persona_usuario_id) "
                    "VALUES (%s, %s, 'vendedor@ventas.invalid', %s, %s)",
                    ("s-" + tenant, "sub-" + tenant, tenant, usuario),
                )
                cur.execute("DELETE FROM users WHERE id = %s", (usuario,))
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant,))
                cur.execute("SELECT tenant_id, persona_usuario_id, vendedor_sub FROM demo_sesiones WHERE id = %s", ("s-" + tenant,))
                assert cur.fetchone() == (None, None, "sub-" + tenant)
        finally:
            conn.rollback()


def test_lopdp_app_no_puede_borrar_sesiones():
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT has_table_privilege('lopdp_app', 'demo_sesiones', p) FROM unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE']) p")
            assert [f[0] for f in cur.fetchall()] == [True, True, True, False]
            cur.execute("SELECT relrowsecurity FROM pg_class WHERE relname = 'demo_sesiones'")
            assert cur.fetchone() == (False,)
        conn.rollback()


def test_dos_altas_activas_simultaneas_del_mismo_vendedor_solo_una_prospera():
    psycopg = pytest.importorskip("psycopg")
    url = _url()
    sub = f"sub-demo00-{uuid.uuid4().hex[:8]}"
    barrera = threading.Barrier(2)
    resultados: list[str] = []

    def alta() -> None:
        with psycopg.connect(url) as conn:
            try:
                with conn.cursor() as cur:
                    barrera.wait()
                    cur.execute(
                        "INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email) VALUES (%s, %s, 'vendedor@ventas.invalid')",
                        (str(uuid.uuid4()), sub),
                    )
                conn.commit()
                resultados.append("ok")
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                resultados.append("unica")

    hilos = [threading.Thread(target=alta) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(30)
    try:
        assert sorted(resultados) == ["ok", "unica"]
    finally:
        # Limpieza con la credencial del dueño: la fila es de esta prueba (la aplicación nunca borra).
        with psycopg.connect(url) as conn:
            conn.execute("DELETE FROM demo_sesiones WHERE vendedor_sub = %s", (sub,))
            conn.commit()
