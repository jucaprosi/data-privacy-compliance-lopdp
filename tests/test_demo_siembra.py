# ¤demo ¤seguridad-tenant
"""DEMO-03: siembra idempotente de la plantilla «Cooperativa Demo».

Las pruebas con base corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas,
nunca producción).
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from features.demo.domain.plantilla import ORDEN_DE_SALAS, PLANTILLA_TENANT_ID
from scripts.demo import sembrar_plantilla as siembra

PLANTILLA = siembra.cargar_plantilla()
TID = PLANTILLA_TENANT_ID
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ROLES_OPERATIVOS = {"coordinador", "implementador", "responsable_area", "admin_organizacion"}


# --- Plantilla -------------------------------------------------------------------------------------

# ORG-22 añadió al auditor: la plantilla tiene seis personas, una por rol.
def test_seis_personas_ficticias_con_correo_invalid():
    personas = PLANTILLA["personas"]
    assert len(personas) == 6
    assert all(p["correo"].endswith(".invalid") for p in personas)
    assert len({p["correo"] for p in personas}) == 6


def test_cada_persona_tiene_un_solo_rol_y_estan_los_seis():
    roles = [p["rol"] for p in PLANTILLA["personas"]]
    assert sorted(roles) == sorted(
        ["admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area", "auditor"])


def test_plantilla_es_demo_con_tope_cinco():
    assert "id" not in PLANTILLA["tenant"]
    assert PLANTILLA["tenant"]["es_demo"] is True
    assert PLANTILLA["ia_tope_organizacion"]["tope"] == 5


def test_cada_bloque_del_json_es_una_sala_del_orden():
    bloques = siembra.bloques_de_salas(PLANTILLA)
    assert bloques, "la plantilla debe declarar datos de ciclo"
    sin_sala = set(bloques) - set(ORDEN_DE_SALAS)
    assert not sin_sala, f"bloques sin sala en ORDEN_DE_SALAS: {sin_sala}"


def test_el_id_de_la_plantilla_solo_esta_en_el_contrato():
    raiz = Path(__file__).resolve().parents[1]
    permitidos = {"features/demo/domain/plantilla.py"}
    con_literal = set()
    for carpeta in ("app_core", "features", "scripts", "api", "data", "tests", "frontend/src"):
        for ruta in (raiz / carpeta).rglob("*"):
            if ruta.suffix in {".py", ".json", ".ts", ".tsx"} and "node_modules" not in ruta.parts:
                if PLANTILLA_TENANT_ID in ruta.read_text(encoding="utf-8", errors="ignore"):
                    con_literal.add(ruta.relative_to(raiz).as_posix())
    assert con_literal == permitidos


# --- Compuerta de la sala demo -------------------------------------------------------------------
# Mutaciones documentadas:
#  - si sembrar_plantilla.py vuelve a importar features.demo.domain.plantilla, fallan
#    test_el_script_solo_entra_por_la_compuerta y tests/test_adpa_bulkhead.py[demo];
#  - si se añaden nombres a demo_service.__all__, falla test_la_reexportacion_no_entra_en_all (las firmas
#    congeladas las vigila tests/test_demo_contrato.py, de DEMO-00);
#  - si se quita la reexportación de demo_service (o define su propia copia), falla
#    test_la_compuerta_reexporta_la_misma_constante.

SEIS_FIRMAS_DEMO_00 = {"entrar", "terminar", "estado", "cambiar_persona", "resolver_usuario", "vencer_inactivas"}


def test_el_script_solo_entra_por_la_compuerta():
    arbol = ast.parse(Path(siembra.__file__).read_text(encoding="utf-8"))
    modulos = {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module}
    modulos |= {a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in modulos if m.startswith("features.demo.domain")}, modulos
    assert "features.demo.demo_service" in modulos


def test_la_reexportacion_no_entra_en_all():
    from features.demo import demo_service

    assert set(demo_service.__all__) == SEIS_FIRMAS_DEMO_00


def test_la_compuerta_reexporta_la_misma_constante():
    from features.demo import demo_service
    from features.demo.domain import plantilla

    assert demo_service.PLANTILLA_TENANT_ID is plantilla.PLANTILLA_TENANT_ID
    assert demo_service.ORDEN_DE_SALAS is plantilla.ORDEN_DE_SALAS


# --- Guardia ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("entorno", ["pruebas", "produccion", "local"])
def test_fuera_de_demo_se_niega(monkeypatch, capsys, entorno):
    monkeypatch.setenv("APP_ENV", entorno)
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://u:p@localhost:1/x")
    assert siembra.main() == 2
    err = capsys.readouterr().err
    assert "rechazada" in err and "postgresql" not in err


def test_huella_de_produccion_en_la_url_se_niega(monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", "huella-prod-simulada")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://u:p@huella-prod-simulada.invalid/x")
    assert siembra.main() == 2
    assert "huella-prod-simulada" not in capsys.readouterr().err


# --- Siembra con PostgreSQL real -------------------------------------------------------------------

async def _estado(session) -> tuple[dict, str]:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": TID})
    consultas = {
        "tenant": "SELECT id, es_demo FROM tenants WHERE id = :t",
        "areas": "SELECT codigo, nivel FROM areas WHERE tenant_id = :t AND deleted_at IS NULL ORDER BY codigo",
        "roles": "SELECT u.email, r.role, a.codigo FROM user_tenant_roles r JOIN users u ON u.id = r.user_id "
                 "LEFT JOIN areas a ON a.id = r.area_id WHERE r.tenant_id = :t "
                 "AND (r.valid_to IS NULL OR r.valid_to > now()) ORDER BY 1, 2",
        "tope": "SELECT tope FROM ia_tope_organizacion WHERE tenant_id = :t",
    }
    filas, h = {}, hashlib.sha256()
    for nombre, sql in consultas.items():
        filas[nombre] = [tuple(f) for f in (await session.execute(text(sql), {"t": TID})).all()]
        h.update(repr((nombre, filas[nombre])).encode())
    return filas, h.hexdigest()


@pytest.mark.asyncio
async def test_dos_corridas_dejan_el_mismo_estado(db_engine, capsys):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with fabrica() as s:
        await siembra.sembrar(s)
    async with fabrica() as s:
        estado_1, hash_1 = await _estado(s)
    async with fabrica() as s:
        segunda = await siembra.sembrar(s)
    async with fabrica() as s:
        estado_2, hash_2 = await _estado(s)

    assert hash_1 == hash_2
    assert all(d["creados"] == 0 for k, d in segunda.items() if k != "salas_sin_alta"), segunda
    # Hasta DEMO-03a a 03f, ninguna sala con datos de ciclo tiene sembrar_en_plantilla.
    assert set(segunda.get("salas_sin_alta", [])) <= set(siembra.bloques_de_salas(PLANTILLA))
    assert estado_1["tenant"] == [(TID, True)]
    assert estado_1["tope"] == [(5,)]
    assert len(estado_1["areas"]) == 3

    print(siembra.formatear(segunda))
    assert not CORREO.search(capsys.readouterr().out)


@pytest.mark.asyncio
async def test_un_rol_por_persona_y_dpo_sin_rol_operativo(db_engine):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with fabrica() as s:
        await siembra.sembrar(s)
    async with fabrica() as s:
        estado, _ = await _estado(s)

    por_persona: dict[str, list[str]] = {}
    for correo, rol, _area in estado["roles"]:
        por_persona.setdefault(correo, []).append(rol)
    assert all(len(r) == 1 for r in por_persona.values()), por_persona
    dpo = por_persona["dpo@cooperativa-demo.invalid"]
    assert dpo == ["dpo"] and not ROLES_OPERATIVOS & set(dpo)
    assert all(c.endswith(".invalid") for c in por_persona)
    assert ("creditos@cooperativa-demo.invalid", "responsable_area", "DEMO-UNID-CREDITOS") in estado["roles"]
    assert len(por_persona) == 6
    assert por_persona["auditoria@cooperativa-demo.invalid"] == ["auditor"]
